import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from decimal import Decimal, InvalidOperation
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import numpy as np
from textblob import TextBlob
import csv
import os
import json
from datetime import datetime, date, timedelta

# إعداد الـ Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialDataFetcher:
    def __init__(self):
        self.currency_pairs = [
            'CAD=X', 'EUR=X', 'GBP=X', 'JPY=X', 'AUD=X', 'CNY=X', 
            'SGD=X', 'CHF=X', 'NZD=X', 'SEK=X', 'NOK=X', 'MXN=X',
            'SAR=X', 'AED=X', 'KWD=X'
        ]

        self.session = self._create_session()
        
    def _create_session(self):
        """إنشاء جلسة مع استراتيجية إعادة المحاولة"""
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

    def safe_decimal_convert(self, value: Any, default: str = '0') -> Decimal:
        """تحويل آمن للقيمة إلى Decimal"""
        if pd.isna(value) or value is None:
            return Decimal(default)
        try:
            return Decimal(str(round(float(value), 6)))
        except (InvalidOperation, TypeError, ValueError) as e:
            logger.warning(f"Error converting value to Decimal: {str(e)}, using default: {default}")
            return Decimal(default)

    def download_ticker_data(self, symbol: str, start_date: str = "2008-01-01", end_date: str = None) -> Optional[pd.DataFrame]:
        """تنزيل البيانات مع منطق إعادة المحاولة"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            logger.info(f"Downloading data for {symbol} from {start_date} to {end_date}")
            ticker = yf.Ticker(symbol, session=self.session)
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            time.sleep(2)  # تأخير لتجنب الحظر
            
            if data is None or data.empty or len(data.index) == 0:
                logger.warning(f"No data available for {symbol}")
                return None
                
            # تحويل جميع البيانات الرقمية
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')


            if 'Volume' not in data.columns or data['Volume'].isna().all() or (data['Volume'] == 0).all():
                # For forex pairs, generate synthetic volume based on volatility
                high_low_range = abs(data['High'] - data['Low'])
                avg_range = high_low_range.mean()
                data['Volume'] = (high_low_range / avg_range if avg_range > 0 else 1) * 1000000
                logger.info(f"Generated synthetic volume data for {symbol}")        
            
             

            data.name = symbol  # إضافة اسم الرمز إلى DataFrame
            return data
            
        except Exception as e:
            logger.error(f"Failed to download data for {symbol}: {str(e)}")
            return None

    def calculate_percent_change(self, data: pd.DataFrame) -> pd.Series:
        """حساب نسبة التغير اليومية"""
        if 'Close' in data.columns:
            return data['Close'].pct_change() * 100
        return pd.Series(index=data.index, dtype=float)



    def fetch_dxy_index(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """جلب بيانات مؤشر الدولار (DXY)"""
        try:
            # تجربة رمز بديل، فبعض الأحيان يختلف الرمز حسب مزود البيانات
            dxy_data = self.download_ticker_data('DX-Y.NYB', start_date, end_date)
            
            # إذا كانت البيانات فارغة، جرب رمزاً آخر
            if dxy_data is None or dxy_data.empty:
                logger.info("Trying alternative DXY symbol...")
                dxy_data = self.download_ticker_data('DXY', start_date, end_date)
                
            # إذا لا تزال فارغة، جرب رمز ثالث
            if dxy_data is None or dxy_data.empty:
                logger.info("Trying third DXY symbol...")
                dxy_data = self.download_ticker_data('USDX', start_date, end_date)
            
            # تأكد من أن البيانات ليست فارغة قبل إرجاعها
            if dxy_data is not None and not dxy_data.empty:
                logger.info(f"Successfully fetched DXY data with {len(dxy_data)} rows")
                return dxy_data
            else:
                logger.warning("Could not fetch DXY data with any symbol")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch DXY index: {str(e)}")
            return None



    def fetch_interest_rates(self) -> Dict[str, float]:
        """جلب أسعار الفائدة لعملات مختلفة"""
        # هذه بيانات تقريبية، يمكن استبدالها بمصدر API حقيقي
        default_rates = {
            'USD': 5.50,  # الدولار الأمريكي
            'EUR': 4.00,  # اليورو
            'GBP': 5.25,  # الجنيه الإسترليني
            'JPY': 0.10,  # الين الياباني
            'CAD': 5.00,  # الدولار الكندي
            'AUD': 4.35,  # الدولار الأسترالي
            'CNY': 3.45,  # اليوان الصيني
            'SGD': 3.68,  # الدولار السنغافوري
            'CHF': 1.75,  # الفرنك السويسري
            'NZD': 5.50,  # الدولار النيوزيلندي
            'SEK': 4.00,  # الكرونة السويدية
            'NOK': 4.50,  # الكرونة النرويجية
            'MXN': 11.25,  # البيزو المكسيكي
            'SAR': 6.00,  # الريال السعودي
            'AED': 5.15,  # الدرهم الإماراتي
            'KWD': 4.25,  # الدينار الكويتي
        }
        
        try:
            # يمكن استبدال هذا بـ API حقيقي في المستقبل
            return default_rates
        except Exception as e:
            logger.error(f"Failed to fetch interest rates: {str(e)}")
            return default_rates

    def fetch_inflation_rates(self) -> Dict[str, float]:
        """جلب معدلات التضخم لعملات مختلفة"""
        # هذه بيانات تقريبية، يمكن استبدالها بمصدر API حقيقي
        default_inflation = {
            'USD': 3.2,  # الدولار الأمريكي
            'EUR': 2.9,  # اليورو
            'GBP': 3.4,  # الجنيه الإسترليني
            'JPY': 2.8,  # الين الياباني
            'CAD': 3.1,  # الدولار الكندي
            'AUD': 3.5,  # الدولار الأسترالي
            'CNY': 0.7,  # اليوان الصيني
            'SGD': 3.0,  # الدولار السنغافوري
            'CHF': 1.8,  # الفرنك السويسري
            'NZD': 4.0,  # الدولار النيوزيلندي
            'SEK': 2.3,  # الكرونة السويدية
            'NOK': 3.0,  # الكرونة النرويجية
            'MXN': 4.4,  # البيزو المكسيكي
            'SAR': 2.0,  # الريال السعودي
            'AED': 3.5,  # الدرهم الإماراتي
            'KWD': 3.2,  # الدينار الكويتي
        }
        
        try:
            # يمكن استبدال هذا بـ API حقيقي في المستقبل
            return default_inflation
        except Exception as e:
            logger.error(f"Failed to fetch inflation rates: {str(e)}")
            return default_inflation

    def fetch_market_sentiment(self) -> Decimal:
        """جلب المشاعر السوقية من مصادر الأخبار"""
        try:
            api_key = "88cb2843436440ccaeb736e9399c6e62"  # استبدل بمفتاح API الخاص بك
            url = f"https://newsapi.org/v2/everything?q=stock+market+forex&apiKey={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                sentiments = [TextBlob(article['title']).sentiment.polarity for article in articles]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                return self.safe_decimal_convert(avg_sentiment)
            return Decimal('0')
        except Exception as e:
            logger.error(f"Error fetching market sentiment: {str(e)}")
            return Decimal('0')

    def fetch_economic_news(self) -> str:
        """جلب الأخبار الاقتصادية من مصادر الأخبار"""
        try:
            api_key = "88cb2843436440ccaeb736e9399c6e62"  # استبدل بمفتاح API الخاص بك
            url = f"https://newsapi.org/v2/everything?q=economy+forex+currency&apiKey={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                if not articles:
                    return ""
                
                # استخراج العناوين والأوصاف المختصرة للأخبار
                news_items = []
                for article in articles[:5]:  # استخدام أهم 5 أخبار فقط
                    news_items.append(f"{article['title']} - {article['description'][:100]}...")
                
                return "\n".join(news_items)  # إرجاع الأخبار كسلسلة نصية
            return ""
        except Exception as e:
            logger.error(f"Error fetching economic news: {str(e)}")
            return ""

    def calculate_label(self, data: Dict) -> str:
        """تحديد توصية الشراء/البيع بناءً على المؤشرات الفنية"""
        try:
            # تحويل القيم إلى أرقام للمقارنة
            rsi = float(data.get('rsi', 50))
            macd = float(data.get('macd', 0))
            macd_signal = float(data.get('macd_signal', 0))
            k_percent = float(data.get('k_percent', 50))
            d_percent = float(data.get('d_percent', 50))
            close_50ma_diff = float(data.get('close_50ma_diff', 0))
            
            # مجموع النقاط للشراء والبيع
            buy_points = 0
            sell_points = 0
            
            # تحليل RSI
            if rsi < 30:
                buy_points += 2  # ذروة البيع
            elif rsi > 70:
                sell_points += 2  # ذروة الشراء
                
            # تحليل MACD
            if macd > macd_signal:
                buy_points += 1  # إشارة شراء
            elif macd < macd_signal:
                sell_points += 1  # إشارة بيع
                
            # تحليل ستوكاستيك
            if k_percent < 20 and d_percent < 20:
                buy_points += 1  # منطقة ذروة البيع
            elif k_percent > 80 and d_percent > 80:
                sell_points += 1  # منطقة ذروة الشراء
                
            # المتوسط المتحرك 50
            if close_50ma_diff > 0:
                buy_points += 1  # السعر فوق المتوسط المتحرك
            else:
                sell_points += 1  # السعر تحت المتوسط المتحرك
                
            # اتخاذ القرار النهائي
            if buy_points > sell_points and buy_points >= 3:
                return "Buy"
            elif sell_points > buy_points and sell_points >= 3:
                return "Sell"
            else:
                return "Hold"
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error calculating label: {str(e)}")
            return "Neutral"


    
    def calculate_financial_data(self, symbol: str, start_date: str = "2008-01-01", end_date: str = None) -> List[Dict]:
        """حساب جميع البيانات المالية المطلوبة للرمز"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            # تنزيل بيانات الرمز
            data = self.download_ticker_data(symbol, start_date, end_date)
            if data is None or len(data) < 14:
                logger.warning(f"Not enough data to calculate indicators for {symbol}")
                return []
                
            # تحميل بيانات DXY
            dxy_data = self.fetch_dxy_index(start_date, end_date)
            
            # جلب أسعار الفائدة ومعدلات التضخم
            interest_rates = self.fetch_interest_rates()
            inflation_rates = self.fetch_inflation_rates()
            
            # تحديد عملة الرمز
            currency_code = symbol.split('=')[0] if '=' in symbol else 'USD'
            interest_rate = interest_rates.get(currency_code, 0)
            inflation = inflation_rates.get(currency_code, 0)
            
            # حساب نسبة التغير
            percent_change = self.calculate_percent_change(data)
            
            # البيانات النهائية
            results = []
            
            # تأكد من تحويل البيانات الرقمية
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # حساب المؤشرات الفنية
            close_prices = data['Close'].astype(float).ffill()
            
            # حساب RSI
            price_diff = close_prices.diff()
            gains = price_diff.where(price_diff > 0, 0)
            losses = -price_diff.where(price_diff < 0, 0)
            avg_gains = gains.rolling(window=14).mean()
            avg_losses = losses.rolling(window=14).mean()
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            
            # حساب MACD
            ema12 = close_prices.ewm(span=12, adjust=False).mean()
            ema26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            # حساب المتوسطات المتحركة
            ma_50 = close_prices.rolling(window=50).mean()
            ma_200 = close_prices.rolling(window=200).mean()
            
            # حساب بولينجر باند
            ma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()
            upper_bb = ma_20 + (2 * std_20)
            lower_bb = ma_20 - (2 * std_20)
            
            # حساب ستوكاستيك
            high_14 = data['High'].rolling(window=14).max()
            low_14 = data['Low'].rolling(window=14).min()
            k_values = pd.Series(index=data.index, dtype=float)
            
            for i in range(len(data)):
                if i >= 14 and high_14.iloc[i] - low_14.iloc[i] != 0:
                    k_values.iloc[i] = 100 * ((close_prices.iloc[i] - low_14.iloc[i]) / 
                                            (high_14.iloc[i] - low_14.iloc[i]))
            
            d_values = k_values.rolling(window=3).mean()
            
            # حساب ATR
            high_low = data['High'] - data['Low']
            high_close = abs(data['High'] - data['Close'].shift(1))
            low_close = abs(data['Low'] - data['Close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            
            # حساب التقلب
            volatility = close_prices.pct_change().rolling(window=14).std() * 100
            
            # جلب المشاعر السوقية والأخبار الاقتصادية
            market_sentiment = self.fetch_market_sentiment()
            economic_news = self.fetch_economic_news()
            
            # معالجة كل يوم من البيانات
            for i in range(len(data)):
                if i < 200:  # تخطي الأيام الأولى حتى تتراكم بيانات كافية للمؤشرات
                    continue
                
                date = data.index[i].date()
                date_timestamp = pd.Timestamp(date)
                
                # تعديل جزء الحصول على قيمة DXY في دالة calculate_financial_data
                dxy_value = None
                if dxy_data is not None:
                    if dxy_data.index.tzinfo is not None:
                     
                      
                        date_timestamp = date_timestamp.tz_localize(dxy_data.index.tzinfo)
                    # تحويل التاريخ إلى سلسلة نصية بنفس تنسيق فهرس dxy_data
                    
                    # البحث عن أقرب تاريخ متاح إذا لم يكن التاريخ المطلوب متاحاً
                    if date_timestamp in dxy_data.index:
                        dxy_value = dxy_data.loc[date_timestamp, 'Close'] if 'Close' in dxy_data.columns else None
                    else:
                        # البحث عن أقرب تاريخ سابق
                        # تحويل فهرس dxy_data إلى قائمة لتسهيل المقارنة
                        dxy_index_list = list(dxy_data.index)
                        available_dates = [d for d in dxy_index_list if d < date_timestamp]
                        if available_dates:
                            closest_date = max(available_dates)
                            dxy_value = dxy_data.loc[closest_date, 'Close'] if 'Close' in dxy_data.columns else None
                            logger.info(f"Using closest available DXY date: {closest_date} for {date}")
                
                # حساب التنبؤ بالقمة التالية
                recent_highs = data['High'].iloc[i-5:i].mean() if i >= 5 else None
                high_change = None
                
                if recent_highs is not None and not pd.isna(recent_highs) and not pd.isna(close_prices.iloc[i]) and close_prices.iloc[i] != 0:
                    high_change = ((recent_highs - close_prices.iloc[i]) / close_prices.iloc[i]) * 100
                
                # إنشاء قاموس النتائج
                result = {
                    'date': date,
                    'ticker': symbol,
                    'open_price': self.safe_decimal_convert(data['Open'].iloc[i]),
                    'high_price': self.safe_decimal_convert(data['High'].iloc[i]),
                    'low_price': self.safe_decimal_convert(data['Low'].iloc[i]),
                    'close_price': self.safe_decimal_convert(data['Close'].iloc[i]),
                    'adj_close': self.safe_decimal_convert(data['Close'].iloc[i]),
                    'volume': self.safe_decimal_convert(data['Volume'].iloc[i] if 'Volume' in data.columns else 1000000),

                    
                    'volume': self.safe_decimal_convert(
                        data['Volume'].iloc[i] if ('Volume' in data.columns and 
                                                data['Volume'].iloc[i] > 0 and 
                                                not pd.isna(data['Volume'].iloc[i])) 
                        else 1000000
                    ),                    'rsi': self.safe_decimal_convert(rsi.iloc[i] if i < len(rsi) else None),
                    'macd': self.safe_decimal_convert(macd_line.iloc[i] if i < len(macd_line) else None),
                    'macd_signal': self.safe_decimal_convert(signal_line.iloc[i] if i < len(signal_line) else None),
                    'macd_hist': self.safe_decimal_convert(macd_histogram.iloc[i] if i < len(macd_histogram) else None),
                    'percent_change': self.safe_decimal_convert(percent_change.iloc[i] if i < len(percent_change) else None),
                    'interest_rate': self.safe_decimal_convert(interest_rate),
                    'inflation': self.safe_decimal_convert(inflation),
                    'dxy': self.safe_decimal_convert(dxy_value),
                    'ma_50': self.safe_decimal_convert(ma_50.iloc[i] if i < len(ma_50) else None),
                    'ma_200': self.safe_decimal_convert(ma_200.iloc[i] if i < len(ma_200) else None),
                    'close_50ma_diff': self.safe_decimal_convert((close_prices.iloc[i] - ma_50.iloc[i]) if i < len(ma_50) and not pd.isna(ma_50.iloc[i]) else None),
                    'close_200ma_diff': self.safe_decimal_convert((close_prices.iloc[i] - ma_200.iloc[i]) if i < len(ma_200) and not pd.isna(ma_200.iloc[i]) else None),
                    'upper_bb': self.safe_decimal_convert(upper_bb.iloc[i] if i < len(upper_bb) else None),
                    'lower_bb': self.safe_decimal_convert(lower_bb.iloc[i] if i < len(lower_bb) else None),
                    'k_percent': self.safe_decimal_convert(k_values.iloc[i] if i < len(k_values) else None),
                    'd_percent': self.safe_decimal_convert(d_values.iloc[i] if i < len(d_values) else None),
                    'atr': self.safe_decimal_convert(atr.iloc[i] if i < len(atr) else None),
                    'volatility': self.safe_decimal_convert(volatility.iloc[i] if i < len(volatility) else None),
                    'next_high': self.safe_decimal_convert(recent_highs),
                    'high_change': self.safe_decimal_convert(high_change),
                    'market_sentiment': market_sentiment,
                    'economic_news': economic_news if i == len(data) - 1 else None  # فقط للبيانات الأخيرة
                }
                
                # إضافة التصنيف (شراء/بيع/انتظار)
                result['label'] = self.calculate_label(result)
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating financial data for {symbol}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())  # إضافة تتبع الخطأ الكامل للتشخيص
            return []

    def save_to_csv(self, data: List[Dict], filename: str = "financial_data.csv"):
        """حفظ البيانات إلى ملف CSV"""
        if not data:
            logger.warning("No data to save to CSV.")
            return
            
        try:
            keys = data[0].keys()
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
                logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")

    def save_to_json(self, data: List[Dict], filename: str = "financial_data.json"):
        """حفظ البيانات إلى ملف JSON"""
        if not data:
            logger.warning("No data to save to JSON.")
            return
            
        try:
            # تحويل كائنات Decimal إلى float لسهولة التعامل مع JSON
            json_data = []
            for item in data:
                json_item = {}
                for key, value in item.items():
                    if isinstance(value, Decimal):
                        json_item[key] = float(value)
                    elif isinstance(value, datetime.date):
                        json_item[key] = value.isoformat()
                    else:
                        json_item[key] = value
                json_data.append(json_item)
                
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to JSON: {str(e)}")

    def prepare_data_for_django_model(self, data: List[Dict]) -> List[Dict]:
        """تجهيز البيانات لنموذج Django"""
        processed_data = []
        
        for item in data:
            model_data = {
                'date': item['date'] if isinstance(item['date'], date) else datetime.strptime(item['date'], '%Y-%m-%d').date(),
                'ticker': item['ticker'],
                'open_price': item['open_price'],
                'high_price': item['high_price'],
                'low_price': item['low_price'],
                'close_price': item['close_price'],
                'adj_close': item['adj_close'],
                'volume': item['volume'],
                'rsi': item.get('rsi'),
                'macd': item.get('macd'),
                'macd_signal': item.get('macd_signal'),
                'macd_hist': item.get('macd_hist'),
                'percent_change': item.get('percent_change'),
                'interest_rate': item.get('interest_rate'),
                'inflation': item.get('inflation'),
                'dxy': item.get('dxy'),
                'label': item.get('label'),
                'ma_50': item.get('ma_50'),
                'ma_200': item.get('ma_200'),
                'close_50ma_diff': item.get('close_50ma_diff'),
                'close_200ma_diff': item.get('close_200ma_diff'),
                'upper_bb': item.get('upper_bb'),
                'lower_bb': item.get('lower_bb'),
                'k_percent': item.get('k_percent'),
                'd_percent': item.get('d_percent'),
                'atr': item.get('atr'),
                'volatility': item.get('volatility'),
                'next_high': item.get('next_high'),
                'high_change': item.get('high_change'),
                'market_sentiment': item.get('market_sentiment'),
                'economic_news': item.get('economic_news')
            }
            processed_data.append(model_data)
            
        return processed_data

    def run_data_collection(self, start_date: str = "2023-01-01", end_date: str = None):
        """تشغيل عملية جمع البيانات لجميع الأزواج"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        all_data = []
        
        for symbol in self.currency_pairs:
            logger.info(f"Processing {symbol}...")
            symbol_data = self.calculate_financial_data(symbol, start_date, end_date)
            
            if symbol_data:
                all_data.extend(symbol_data)
                logger.info(f"Collected {len(symbol_data)} data points for {symbol}")
            else:
                logger.warning(f"No data collected for {symbol}")
        
        # حفظ البيانات
        if all_data:
            self.save_to_csv(all_data, "financial_data.csv")
            self.save_to_json(all_data, "financial_data.json")
            
            # تجهيز البيانات لنموذج Django
            django_data = self.prepare_data_for_django_model(all_data)
            self.save_to_json(django_data, "django_financial_data.json")
            
            logger.info(f"Total collected data points: {len(all_data)}")
        else:
            logger.warning("No data collected for any symbol")
            
        return all_data


# إذا تم تشغيل البرنامج مباشرة
if __name__ == "__main__":
    print("Starting financial data collection...")
    fetcher = FinancialDataFetcher()
    data = fetcher.run_data_collection(start_date="2008-01-01")
    print(f"Finished collecting {len(data) if data else 0} data points.")