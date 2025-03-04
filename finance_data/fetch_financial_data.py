import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from decimal import Decimal, InvalidOperation
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import numpy as np
from textblob import TextBlob

# إعداد الـ Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CurrencyDataFetcher:
    def __init__(self):
        self.currency_pairs = [
            'CAD=X', 'EUR=X', 'GBP=X', 'JPY=X', 'AUD=X', 'CNY=X', 
            'SGD=X', 'CHF=X', 'NZD=X', 'SEK=X', 'NOK=X', 'MXN=X',
            'SAR=X', 'AED=X', 'KWD=X'
        ]
        self.session = self._create_session()
        
    def _create_session(self):
        """Create a session with retry strategy"""
        session = requests.Session()
        retry = Retry(
            total=10,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504, 429]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def estimate_volume(self, data: pd.DataFrame) -> Decimal:
        """Estimate trading volume based on price movement and volatility"""
        try:
            high_low_range = data['High'] - data['Low']
            previous_close = data['Close'].shift(1)
            tr1 = high_low_range
            tr2 = abs(data['High'] - previous_close)
            tr3 = abs(data['Low'] - previous_close)
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            returns = data['Close'].pct_change()
            volatility = returns.rolling(window=14).std()
            tick_count = (data['Close'] != data['Close'].shift(1)).rolling(window=14).sum()
            
            last_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0
            last_volatility = volatility.iloc[-1] if not pd.isna(volatility.iloc[-1]) else 0
            last_tick_count = tick_count.iloc[-1] if not pd.isna(tick_count.iloc[-1]) else 0
            
            base_volume = (last_atr * 1000000) * (1 + last_volatility) * last_tick_count
            
            currency_multipliers = {
                'EUR=X': 1.2, 'JPY=X': 1.1, 'GBP=X': 1.0, 'AUD=X': 0.8,
                'CAD=X': 0.7, 'CHF=X': 0.7, 'CNY=X': 0.6, 'SGD=X': 0.5,
                'NZD=X': 0.4, 'SEK=X': 0.4, 'NOK=X': 0.3, 'MXN=X': 0.3,
                'SAR=X': 0.3, 'AED=X': 0.3, 'KWD=X': 0.5
            }
            
            hour = datetime.now().hour
            if 8 <= hour <= 16:
                time_multiplier = 1.5
            elif 4 <= hour <= 7 or 17 <= hour <= 20:
                time_multiplier = 1.0
            else:
                time_multiplier = 0.5
                
            pair_multiplier = currency_multipliers.get(data.name, 1.0) if hasattr(data, 'name') else 1.0
            final_volume = base_volume * pair_multiplier * time_multiplier
            
            return Decimal(str(round(float(final_volume), 0)))
            
        except Exception as e:
            logger.error(f"Error estimating volume: {str(e)}")
            return Decimal('0')

    def safe_decimal_convert(self, value: float, default: Optional[str] = None) -> Optional[Decimal]:
        """Safely converts a value to Decimal"""
        if pd.isna(value):
            return Decimal(default) if default else None
        try:
            return Decimal(str(round(float(value), 6)))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default) if default else None

    def download_ticker_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Download data with retry logic"""
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            data = ticker.history(period='60d', interval='1d')
            time.sleep(5)  # زيادة التأخير إلى 5 ثواني لتجنب حظر الطلبات
            if data is None or data.empty or len(data.index) == 0:
                logger.warning(f"No data available for {symbol}")
                return None
            data.name = symbol  # Add symbol name to DataFrame
            return data
        except Exception as e:
            logger.error(f"Failed to download data for {symbol}: {str(e)}")
            return None

    def fetch_market_sentiment(self) -> Decimal:
        """Fetch market sentiment from news sources"""
        try:
            api_key = "88cb2843436440ccaeb736e9399c6e62"  # استبدل بمفتاح API الخاص بك
            url = f"https://newsapi.org/v2/everything?q=stock+market&apiKey={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                sentiments = [TextBlob(article['title']).sentiment.polarity for article in articles]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                return Decimal(str(round(avg_sentiment, 4)))
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error fetching market sentiment: {str(e)}")
            return Decimal('0')

    def fetch_economic_news(self) -> str:
        """Fetch economic news from news sources"""
        try:
            api_key = "88cb2843436440ccaeb736e9399c6e62"  # استبدل بمفتاح API الخاص بك
            url = f"https://newsapi.org/v2/everything?q=economy&apiKey={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                news_titles = [article['title'] for article in articles]
                return "\n".join(news_titles)  # إرجاع عناوين الأخبار كسلسلة نصية
            return ""
        except Exception as e:
            logger.error(f"Error fetching economic news: {str(e)}")
            return ""

    def fetch_yahoo_finance_data(self, symbol: str) -> Optional[Dict]:
        try:
            data = self.download_ticker_data(symbol)
            if data is None or len(data) < 14:  # تأكد من وجود بيانات كافية
                logger.warning(f"Not enough data to calculate indicators for {symbol}")
                return None

            latest = data.iloc[-1] if len(data.index) > 0 else None
            if latest is None:
                return None

            estimated_volume = self.estimate_volume(data)
            close_prices = data['Close'].astype(float).ffill()  # استبدال fillna(method='ffill') بـ ffill()
            
            # حساب RSI
            rsi_value = None
            if len(close_prices) >= 14:
                try:
                    price_diff = close_prices.diff()
                    gains = price_diff.where(price_diff > 0, 0)
                    losses = -price_diff.where(price_diff < 0, 0)
                    avg_gains = gains.rolling(window=14).mean()
                    avg_losses = losses.rolling(window=14).mean()
                    rs = avg_gains / avg_losses
                    rsi = 100 - (100 / (1 + rs))
                    rsi_value = self.safe_decimal_convert(rsi.iloc[-1])
                except Exception as e:
                    logger.warning(f"Failed to calculate RSI for {symbol}: {str(e)}")

            # حساب MACD
            macd_value = None
            macd_signal = None
            macd_hist = None
            if len(close_prices) >= 26:
                try:
                    ema12 = close_prices.ewm(span=12, adjust=False).mean()
                    ema26 = close_prices.ewm(span=26, adjust=False).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    macd_histogram = macd_line - signal_line
                    macd_value = self.safe_decimal_convert(macd_line.iloc[-1])
                    macd_signal = self.safe_decimal_convert(signal_line.iloc[-1])
                    macd_hist = self.safe_decimal_convert(macd_histogram.iloc[-1])
                except Exception as e:
                    logger.warning(f"Failed to calculate MACD for {symbol}: {str(e)}")

            # حساب المتوسطات المتحركة (50-MA و 200-MA)
            ma_50 = close_prices.rolling(window=50).mean()
            ma_200 = close_prices.rolling(window=200).mean()
            
            # تجنب الأخطاء في حالة عدم وجود بيانات كافية للمتوسطات المتحركة
            close_50ma_diff = None
            close_200ma_diff = None
            
            if len(ma_50) > 0 and not pd.isna(ma_50.iloc[-1]):
                close_50ma_diff = close_prices.iloc[-1] - ma_50.iloc[-1]
                
            if len(ma_200) > 0 and not pd.isna(ma_200.iloc[-1]):
                close_200ma_diff = close_prices.iloc[-1] - ma_200.iloc[-1]

            # حساب بولينجر باند
            ma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()
            
            upper_bb = None
            lower_bb = None
            
            if len(ma_20) > 0 and not pd.isna(ma_20.iloc[-1]) and len(std_20) > 0 and not pd.isna(std_20.iloc[-1]):
                upper_bb = ma_20.iloc[-1] + (2 * std_20.iloc[-1])
                lower_bb = ma_20.iloc[-1] - (2 * std_20.iloc[-1])

            # حساب مؤشر ستوكاستيك (%K و %D)
            high_14 = data['High'].rolling(window=14).max()
            low_14 = data['Low'].rolling(window=14).min()
            
            k_percent = None
            d_percent = None
            
            if (len(high_14) > 0 and not pd.isna(high_14.iloc[-1]) and 
                len(low_14) > 0 and not pd.isna(low_14.iloc[-1]) and
                high_14.iloc[-1] - low_14.iloc[-1] != 0):
                
                k_value = 100 * ((close_prices.iloc[-1] - low_14.iloc[-1]) / 
                                (high_14.iloc[-1] - low_14.iloc[-1]))
                k_percent = self.safe_decimal_convert(k_value)
                
                if len(data) >= 17:  # 14 + 3 أيام إضافية للمتوسط
                    k_values = []
                    for i in range(-3, 0):
                        if (not pd.isna(high_14.iloc[i]) and not pd.isna(low_14.iloc[i]) and 
                            high_14.iloc[i] - low_14.iloc[i] != 0):
                            k_day = 100 * ((close_prices.iloc[i] - low_14.iloc[i]) / 
                                        (high_14.iloc[i] - low_14.iloc[i]))
                            k_values.append(k_day)
                    
                    if k_values:
                        d_value = sum(k_values) / len(k_values)
                        d_percent = self.safe_decimal_convert(d_value)

            # حساب ATR (متوسط المدى الحقيقي)
            high_low = data['High'] - data['Low']
            high_close = abs(data['High'] - data['Close'].shift(1))
            low_close = abs(data['Low'] - data['Close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            atr_value = None
            if len(atr) > 0:
                atr_value = atr.iloc[-1]

            # حساب التقلب (Volatility)
            returns = close_prices.pct_change()
            volatility = returns.rolling(window=14).std()
            volatility_value = None
            if len(volatility) > 0:
                volatility_value = volatility.iloc[-1]

            # التنبؤ بالسعر المرتفع التالي (Next_High)
            recent_highs = data['High'].tail(5)
            next_high = recent_highs.mean() if len(recent_highs) > 0 else None
            high_change = None
            if next_high is not None and not pd.isna(next_high) and not pd.isna(close_prices.iloc[-1]) and close_prices.iloc[-1] != 0:
                high_change = ((next_high - close_prices.iloc[-1]) / close_prices.iloc[-1]) * 100

            result = {
                'open_price': self.safe_decimal_convert(latest.get('Open', 0), '0'),
                'high_price': self.safe_decimal_convert(latest.get('High', 0), '0'),
                'low_price': self.safe_decimal_convert(latest.get('Low', 0), '0'),
                'close_price': self.safe_decimal_convert(latest.get('Close', 0), '0'),
                'adj_close': self.safe_decimal_convert(latest.get('Close', 0), '0'),
                'volume': estimated_volume,
                'rsi': rsi_value,
                'macd': macd_value,
                'macd_signal': macd_signal,
                'macd_hist': macd_hist,
                'ma_50': self.safe_decimal_convert(ma_50.iloc[-1] if len(ma_50) > 0 else None),
                'ma_200': self.safe_decimal_convert(ma_200.iloc[-1] if len(ma_200) > 0 else None),
                'close_50ma_diff': self.safe_decimal_convert(close_50ma_diff),
                'close_200ma_diff': self.safe_decimal_convert(close_200ma_diff),
                'upper_bb': self.safe_decimal_convert(upper_bb),
                'lower_bb': self.safe_decimal_convert(lower_bb),
                'k_percent': k_percent,
                'd_percent': d_percent,
                'atr': self.safe_decimal_convert(atr_value),
                'volatility': self.safe_decimal_convert(volatility_value),
                'next_high': self.safe_decimal_convert(next_high),
                'high_change': self.safe_decimal_convert(high_change)
            }

            return result

        except Exception as e:
            logger.error(f"Error processing data for {symbol}: {str(e)}")
            return None
    

    def fetch_interest_rate(self) -> Decimal:
        """Fetches interest rate from multiple sources"""
        try:
            sources = ["^IRX", "^FVX", "^TNX"]
            for source in sources:
                data = self.download_ticker_data(source)
                if data is not None and not data.empty and len(data.index) > 0:
                    return self.safe_decimal_convert(data['Close'].iloc[-1], '5.25')
                time.sleep(2)  # تأخير بين الطلبات
            return Decimal('5.25')
        except Exception as e:
            logger.error(f"Error fetching interest rate: {str(e)}")
            return Decimal('5.25')

    def fetch_dxy(self) -> Decimal:
        """Fetches US Dollar Index from multiple sources"""
        try:
            sources = ['DX-Y.NYB', '^DXY', 'UUP']
            for source in sources:
                data = self.download_ticker_data(source)
                if data is not None and not data.empty and len(data.index) > 0:
                    return self.safe_decimal_convert(data['Close'].iloc[-1], '103.5')
                time.sleep(2)  # تأخير بين الطلبات
            return Decimal('103.5')
        except Exception as e:
            logger.error(f"Error fetching DXY data: {str(e)}")
            return Decimal('103.5')

    def fetch_inflation(self) -> Decimal:
        """Fetches inflation data from multiple sources"""
        try:
            sources = ["https://api.worldbank.org/v2/country/US/indicator/FP.CPI.TOTL?format=json"]
            for url in sources:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 1 and data[1] and data[1][0]:
                            return self.safe_decimal_convert(data[1][0]['value'], '3.1')
                except Exception as source_error:
                    logger.warning(f"Error with source {url}: {str(source_error)}")
            return Decimal('3.1')
        except Exception as e:
            logger.error(f"Error fetching inflation data: {str(e)}")
            return Decimal('3.1')

    def calculate_percent_change(self, current_price: Decimal, symbol: str, 
                               today: datetime.date, FinancialData) -> Decimal:
        """Calculate percent change from previous day"""
        try:
            yesterday_data = FinancialData.objects.filter(
                ticker=symbol,
                date=today - timedelta(days=1)
            ).first()
            if yesterday_data and yesterday_data.close_price:
                return ((current_price - yesterday_data.close_price) / 
                        yesterday_data.close_price * 100)
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error calculating percent change for {symbol}: {str(e)}")
            return Decimal('0')

    def update_daily_data(self):
        """Update daily data for all currency pairs"""
        from django.apps import apps
        if not apps.ready:
            logger.error("Django apps are not ready!")
            return
            
        from .models import FinancialData
        
        today = datetime.now().date()
        logger.info(f"Starting daily update for {today}")
        
        economic_indicators = {
            'interest_rate': self.fetch_interest_rate(),
            'inflation': self.fetch_inflation(),
            'dxy': self.fetch_dxy(),
            'market_sentiment': self.fetch_market_sentiment(),
            'economic_news': self.fetch_economic_news()
        }
        logger.info(f"Economic indicators fetched: {economic_indicators}")
        
        for i, symbol in enumerate(self.currency_pairs):
            try:
                logger.info(f"Processing {symbol} ({i + 1}/{len(self.currency_pairs)})")
                
                if i % 5 == 0 and i != 0:
                    logger.info("Waiting for 10 seconds to avoid rate limiting...")
                    time.sleep(10)
                
                data = self.fetch_yahoo_finance_data(symbol)
                if data:
                    logger.info(f"Data fetched for {symbol}: {data}")
                    percent_change = self.calculate_percent_change(
                        data['close_price'], symbol, today, FinancialData
                    )
                    logger.info(f"Percent change calculated for {symbol}: {percent_change}")
                    
                    FinancialData.objects.update_or_create(
                        date=today,
                        ticker=symbol,
                        defaults={
                            **data,
                            'percent_change': percent_change,
                            **economic_indicators
                        }
                    )
                    logger.info(f"Successfully updated data for {symbol}")
                else:
                    logger.error(f"No data available to update for {symbol}")
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {str(e)}")

    def run_daily_update(self):
        """Function to run daily update"""
        from django.apps import apps
        if not apps.ready:
            from django.core.exceptions import AppRegistryNotReady
            raise AppRegistryNotReady(
                "Django apps aren't loaded yet. Make sure Django is properly initialized."
            )
                
        self.update_daily_data()