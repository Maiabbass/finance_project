import pandas as pd
import yfinance as yf
import requests



def fetch_interest_rate(start='2008-01-01', end='2024-01-01'):
    """ يجلب أسعار الفائدة """
    try:
        treasury_ticker = "^IRX"
        interest_data = yf.download(treasury_ticker, start=start, end=end)
        interest_data.index = pd.to_datetime(interest_data.index)
        interest_data = interest_data[['Close']].rename(columns={'Close': 'InterestRate'})
        return interest_data
    except Exception as e:
        print(f"ERROR: {e}")
        return pd.DataFrame()


def fetch_inflation():
    """ يجلب بيانات التضخم من البنك الدولي """
    try:
        url = "https://api.worldbank.org/v2/country/US/indicator/FP.CPI.TOTL?format=json"
        response = requests.get(url)
        data = response.json()
        inflation_data = [(pd.to_datetime(item['date']), item['value']) for item in data[1] if item['value'] is not None]
        return pd.DataFrame(inflation_data, columns=['Date', 'Inflation']).set_index('Date')
    except Exception as e:
        print(f"ERROR : {e}")
        return pd.DataFrame()



def fetch_dxy(start='2008-01-01', end='2024-01-01'):
    """ يجلب مؤشر الدولار الأمريكي """
    try:
        dxy = yf.download('DX-Y.NYB', start=start, end=end)
        dxy.index = pd.to_datetime(dxy.index)
        return dxy[['Close']].rename(columns={'Close': 'DXY'})
    except Exception as e:
        print(f"ERROR : {e}")
        return pd.DataFrame()



def resample_to_match(df, target_index):
    """ إعادة تعيين مستوى مؤشر DataFrame ليتوافق مع المؤشر المستهدف """
    if df.empty:
        return df
    return df.reindex(target_index).fillna(method='ffill')

 

def main():
    """ تشغيل جميع الوظائف وجلب البيانات كاملة """
    start_date = '2008-01-01'
    end_date = '2024-01-01'
    
    try:
        # جلب الملف الأصلي أولاً
        file_path = "C:/Users/Zaher/Desktop/Data/updated_file_complete.csv"
        original_data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
        
        # جلب البيانات الأخرى
        interest_rate = fetch_interest_rate(start=start_date, end=end_date)
        inflation = fetch_inflation()
        dxy = fetch_dxy(start=start_date, end=end_date)
        
        # المحاذاة باستخدام مؤشر البيانات الأصلية
        interest_rate = resample_to_match(interest_rate, original_data.index)
        inflation = resample_to_match(inflation, original_data.index)
        dxy = resample_to_match(dxy, original_data.index)
        
        # دمج البيانات الجديدة مع الملف الأصلي
        merged_data = original_data.copy()
        merged_data['InterestRate'] = interest_rate['InterestRate']
        merged_data['Inflation'] = inflation['Inflation']
        merged_data['DXY'] = dxy['DXY']
        
        # حفظ الملف المحدث
        merged_data.to_csv(file_path)

        print("OK")
    except Exception as e:
        print(f"ERROR : {e}")

if __name__ == "__main__":
    main()