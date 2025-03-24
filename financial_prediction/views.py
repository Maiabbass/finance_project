
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from financial_prediction.predictor import FinancialPredictor
from datetime import datetime

# إنشاء كائن من الفئة FinancialPredictor
predictor = FinancialPredictor()

@csrf_exempt
def predict_api(request):
    """
    API للتنبؤ المالي بناءً على تاريخ ورمز شركة.
    تتوقع طلب POST مع بيانات JSON تحتوي على التاريخ ورمز الشركة.
    """
    if request.method == 'POST':
        try:
            # تحليل بيانات JSON من الطلب
            data = json.loads(request.body)
            
            # استخراج التاريخ ورمز الشركة من البيانات
            date_str = data.get('date')
            ticker = data.get('ticker')
            
            # التحقق من وجود البيانات المطلوبة
            if not date_str or not ticker:
                return JsonResponse({
                    'success': False,
                    'error': 'الرجاء توفير التاريخ ورمز الشركة.'
                }, status=400)
            
            # الحصول على التنبؤ
            prediction, error = predictor.predict(date_str, ticker)
            
            if error:
                return JsonResponse({
                    'success': False,
                    'error': error
                }, status=400)
            
            # إرجاع نتيجة التنبؤ كاستجابة JSON
            return JsonResponse({
                'success': True,
                'date': date_str,
                'ticker': ticker,
                'prediction': prediction
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'بيانات JSON غير صالحة.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # إذا لم يكن الطلب POST
    return JsonResponse({
        'success': False,
        'error': 'يرجى استخدام طلب POST مع بيانات JSON.'
    }, status=405)