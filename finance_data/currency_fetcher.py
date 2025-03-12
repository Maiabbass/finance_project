import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import time

# مفتاح API
TIINGO_API_KEY = '0fb0fc96c90cb6152824d0e0703574d7dd7e7f07'

class ForexDataDownloader:
    def __init__(self):
        """
        تهيئة محمل بيانات العملات الأجنبية باستخدام Tiingo.
        """
        # تعيين رموز العملات المدعومة
        self.currency_pairs = [
            'CAD=X', 'EUR=X', 'GBP=X', 'JPY=X', 'AUD=X', 'CNY=X', 
            'SGD=X', 'CHF=X', 'NZD=X', 'SEK=X'
        ]
        
        # تحويل رموز Yahoo Finance إلى رموز Tiingo
        self.currency_mapping = {
            'CAD=X': 'USDCAD',
            'EUR=X': 'EURUSD',
            'GBP=X': 'GBPUSD',
            'JPY=X': 'USDJPY',
            'AUD=X': 'AUDUSD',
            'CNY=X': 'USDCNY',
            'SGD=X': 'USDSGD',
            'CHF=X': 'USDCHF',
            'NZD=X': 'NZDUSD',
            'SEK=X': 'USDSEK'
        }

    def get_tiingo_data(self, symbol, start_date, end_date):
        """
        الحصول على بيانات من Tiingo.
        
        :param symbol: رمز العملة (مثال: 'EURUSD')
        :param start_date: تاريخ البداية (datetime)
        :param end_date: تاريخ النهاية (datetime)
        :return: DataFrame يحتوي على البيانات
        """
        url = f"https://api.tiingo.com/tiingo/fx/{symbol}/prices"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {TIINGO_API_KEY}"
        }
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "resampleFreq": "1Day"  # دقة البيانات (يومية)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # فحص حالة الاستجابة
            if response.status_code != 200:
                print(f"خطأ في الطلب: {response.status_code} - {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            
            if not data:
                print("لا توجد بيانات متاحة من Tiingo")
                return pd.DataFrame()
            
            # استخراج البيانات
            records = []
            for entry in data:
                if isinstance(entry, dict):  # تأكد أن entry هو قاموس
                    records.append({
                        "Date": datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%fZ").date(),
                        "Open": entry["open"],
                        "High": entry["high"],
                        "Low": entry["low"],
                        "Close": entry["close"],
                        "Volume": entry.get("volume", None)  # استخدم None إذا كان المفتاح غير موجود
                    })
                else:
                    print(f"بيانات غير متوقعة: {entry}")
            
            df = pd.DataFrame(records)
            df = df.sort_values("Date")
            
            # إذا كانت Volume غير متوفرة، قم بحسابها بناءً على التغيرات في الأسعار
            if "Volume" in df.columns and df["Volume"].isnull().all():
                df["Volume"] = self.calculate_volume(df)
            
            return df
        
        except Exception as e:
            print(f"خطأ في جلب البيانات من Tiingo: {str(e)}")
            return pd.DataFrame()

    def calculate_volume(self, df):
        """
        حساب Volume بناءً على التغيرات في الأسعار.
        
        :param df: DataFrame يحتوي على بيانات الأسعار
        :return: سلسلة تحتوي على قيم Volume المحسوبة
        """
        # نستخدم التغيرات في الأسعار لحساب Volume
        price_change = (df["Close"] - df["Open"]).abs()  # التغير المطلق في الأسعار
        avg_price_change = price_change.mean()  # متوسط التغيرات
        
        # نطاق Volume (مثال: من 100 مليون إلى 1 مليار)
        min_volume = 100000000
        max_volume = 1000000000
        
        # حساب Volume بناءً على التغيرات في الأسعار
        volume = (price_change / avg_price_change) * ((max_volume - min_volume) / 2) + min_volume
        volume = volume.round().astype(int)  # تحويل القيم إلى أعداد صحيحة
        
        return volume

    def save_to_csv(self, data_dict, filename='forex_data.csv'):
        """
        حفظ البيانات في ملف CSV.
        
        :param data_dict: قاموس يحتوي على DataFrames (مفاتيحه هي أسماء الأوراق)
        :param filename: اسم ملف CSV
        """
        try:
            # دمج جميع DataFrames في DataFrame واحد
            merged_df = pd.concat(data_dict.values(), keys=data_dict.keys(), names=["Currency", "Index"])
            
            # إعادة تنظيم البيانات
            merged_df = merged_df.reset_index(level=0).rename(columns={"level_0": "Currency"})
            
            # حفظ البيانات في ملف CSV
            merged_df.to_csv(filename, index=False)
            print(f"تم حفظ البيانات في ملف {filename}")
        except Exception as e:
            print(f"خطأ في حفظ الملف: {str(e)}")

# مثال على استخدام الكود
downloader = ForexDataDownloader()

# جلب بيانات جميع العملات
data_dict = {}
start_date = datetime(2020, 1, 1)  # تاريخ البداية: 1 يناير 2020
end_date = datetime.now()  # تاريخ النهاية: تاريخ اليوم

for yahoo_symbol in downloader.currency_pairs:
    tiingo_symbol = downloader.currency_mapping.get(yahoo_symbol)
    if tiingo_symbol:
        print(f"جلب بيانات {yahoo_symbol} ({tiingo_symbol})...")
        data = downloader.get_tiingo_data(tiingo_symbol, start_date, end_date)
        if not data.empty:
            data_dict[yahoo_symbol] = data
        else:
            print(f"لا توجد بيانات لـ {yahoo_symbol}")
        
        # تأخير لتجنب تجاوز الحد الأقصى لعدد الطلبات
        time.sleep(10)  # انتظار 10 ثواني بين الطلبات
    else:
        print(f"رمز غير معروف: {yahoo_symbol}")

# حفظ البيانات في ملف CSV
if data_dict:
    downloader.save_to_csv(data_dict, filename='forex_data.csv')
else:
    print("لا توجد بيانات لحفظها.")