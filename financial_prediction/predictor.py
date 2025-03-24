import torch
import os
import numpy as np
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
from finance_data.models import FinancialData  # استيراد النموذج من التطبيق الصحيح

# تعريف بنية النموذج المطابقة للأوزان المحفوظة
class FinancialModel(torch.nn.Module):
    def __init__(self):
        super(FinancialModel, self).__init__()
        self.lstm = torch.nn.LSTM(input_size=7, hidden_size=64, num_layers=1, batch_first=True)
        self.fc = torch.nn.Linear(64, 7)

    def forward(self, x):
        output, _ = self.lstm(x)
        output = self.fc(output[:, -1, :])
        return output

class FinancialPredictor:
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_loaded = False

    def load_model(self):
        if self.model_loaded:
            return True
        try:
            model_path = 'C:\\finance_project\\financial_prediction\\models\\saved_weights_all (1).pt'

            self.model = FinancialModel()
            checkpoint = torch.load(model_path, map_location=self.device)

            print(f"نوع البيانات المحملة: {type(checkpoint)}")
            print(f"المفاتيح المتاحة: {checkpoint.keys()}")

            # التأكد من تطابق أسماء وأشكال الطبقات
            print("Model state dict:")
            for k, v in self.model.state_dict().items():
                print(f"{k} --> {v.shape}")

            print("Checkpoint state dict:")
            for k, v in checkpoint.items():
                print(f"{k} --> {v.shape if hasattr(v, 'shape') else 'No shape'}")

            self.model.load_state_dict(checkpoint)
            self.model.eval()
            self.model_loaded = True
            return True

        except Exception as e:
            print(f"خطأ في تحميل النموذج: {e}")
            return False

    def get_data_for_prediction(self, date_str, ticker):
        """
        استخراج بيانات 25 يوم سابقة بالإضافة لتاريخ محدد لتحضير مدخلات النموذج
        """
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_date = target_date - timedelta(days=25)

            financial_data = FinancialData.objects.filter(
                ticker=ticker,
                date__gte=start_date,
                date__lte=target_date
            ).order_by('date')

            print("Financial Data:", financial_data)

            if financial_data.count() < 26:
                return None, "لا توجد بيانات كافية للتنبؤ. يجب توفر بيانات 25 يوم سابقة على الأقل."

            features = []
            for data in financial_data:
                day_of_week = data.date.weekday()  # (0-6)
                features.append([
                    float(data.open_price),
                    float(data.high_price),
                    float(data.low_price),
                    float(data.close_price),
                    float(data.volume),
                    float(data.percent_change) if data.percent_change else 0.0,
                    day_of_week
                ])

            print("Features prepared for prediction:", features)
            return np.array(features, dtype=np.float32), None

        except ValueError:
            return None, "صيغة التاريخ غير صحيحة. الرجاء استخدام صيغة YYYY-MM-DD."
        except Exception as e:
            return None, f"حدث خطأ أثناء استخراج البيانات: {str(e)}"

    def predict(self, date_str, ticker):
        if not self.load_model():
            return None, "فشل تحميل النموذج"

        input_data, error = self.get_data_for_prediction(date_str, ticker)
        if error:
            return None, error

        try:
            input_tensor = torch.tensor(input_data, dtype=torch.float32).unsqueeze(0).to(self.device)
            print("Input Tensor Shape:", input_tensor.shape)
            print("Input Tensor:", input_tensor)

            with torch.no_grad():
                prediction = self.model(input_tensor)

            print("Model prediction before formatting:", prediction)
            print("All predicted values:", prediction[0].detach().cpu().numpy())

            # استخراج القيمة الرابعة كتوقع للتغير بالنسبة المئوية
            predicted_value = prediction[0, 3].item()

            formatted_prediction = f"{predicted_value:.2f}%"
            if predicted_value > 0:
                formatted_prediction = f"+{formatted_prediction}"
            else:
                formatted_prediction = f"{formatted_prediction}"

            print("Formatted Prediction:", formatted_prediction)
            return formatted_prediction, None

        except Exception as e:
            return None, f"خطأ في التنبؤ: {str(e)}"
