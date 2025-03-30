from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import torch
import torch.nn as nn
import numpy as np
import joblib
from datetime import datetime, timedelta
import os
from finance_data.models import FinancialData  # استيراد النموذج الخاص بك
import pandas as pd

class NeuralNetwork(nn.Module):
    def __init__(self, num_feature):
        super(NeuralNetwork, self).__init__()
        self.lstm = nn.LSTM(num_feature, 64, batch_first=True)
        self.fc = nn.Linear(64, num_feature)

    def forward(self, x):
        output, (hidden, cell) = self.lstm(x)
        x = self.fc(hidden)
        return x

class FinancialPredictor:
    def __init__(self):
        self.num_features = 7  # عدد الخصائص المستخدمة
        self.model = NeuralNetwork(self.num_features)

        # تحميل الأوزان
        weights_path = os.path.join(os.path.dirname(__file__), "models", "saved_weights_all (1).pt")
        self.model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu')))
        self.model.eval()

        # تحميل المقياس
        scaler_path = os.path.join(os.path.dirname(__file__), "models", "scaler_all.pkl")
        self.scaler = joblib.load(scaler_path)

    def calculate_moving_averages(self, df):
        """حساب المتوسطات المتحركة"""
        df["5d_sma"] = df["Close"].astype(float).rolling(5).mean().fillna(df["Close"])
        df["9d_sma"] = df["Close"].astype(float).rolling(9).mean().fillna(df["Close"])
        df["17d_sma"] = df["Close"].astype(float).rolling(17).mean().fillna(df["Close"])
        return df

    def preprocess_data(self, queryset):
        """معالجة البيانات وإعدادها للتنبؤ"""
        # تحويل QuerySet إلى DataFrame
        df = pd.DataFrame.from_records(queryset.values())
        
        # تحويل الأعمدة إلى الأنواع الصحيحة
        columns_to_convert = ['open_price', 'high_price', 'low_price', 'close_price']
        for col in columns_to_convert:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # إعادة تسمية الأعمدة
        df = df.rename(columns={
            'open_price': 'Open', 
            'high_price': 'High', 
            'low_price': 'Low', 
            'close_price': 'Close'
        })
        
        # التأكد من ترتيب البيانات تصاعدياً حسب التاريخ
        df = df.sort_values('date')
        
        # حساب المتوسطات المتحركة
        df = self.calculate_moving_averages(df)
        
        return df

    def predict_price(self, data):
        """التنبؤ بالسعر"""
        data_tensor = torch.tensor(data, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            prediction = self.model(data_tensor)
        predicted_scaled = prediction.numpy().flatten()
        predicted_original = self.scaler.inverse_transform(predicted_scaled.reshape(-1, 1)).flatten()
        return predicted_original[-1]

    def predict(self, date_str, ticker):
        try:
            # تحويل التاريخ
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            # جلب البيانات من قاعدة البيانات
            queryset = FinancialData.objects.filter(
                ticker=ticker,
                date__lt=date_obj
            ).order_by('-date')[:12]  # زيادة العدد إلى 12 للسماح بحساب المتوسطات المتحركة

            if queryset.count() < 11:
                return None, "لا توجد بيانات كافية قبل هذا التاريخ للتنبؤ."

            # معالجة البيانات
            data_df = self.preprocess_data(queryset)

            # تجهيز البيانات للتنبؤ
            data_input = data_df.iloc[-11:][
                ["Open", "High", "Low", "5d_sma", "9d_sma", "17d_sma", "Close"]
            ].values.astype(np.float64)

            # تحجيم البيانات
            data_scaled = np.zeros_like(data_input, dtype=np.float64)
            for i in range(data_input.shape[1]):
                data_scaled[:, i] = self.scaler.transform(data_input[:, i].reshape(-1, 1)).flatten()

            # التنبؤ
            prediction = self.predict_price(data_scaled)

            return round(float(prediction), 4), None

        except FinancialData.DoesNotExist:
            return None, "ملف البيانات الخاص بهذه الشركة غير موجود."
        except Exception as e:
            return None, str(e)