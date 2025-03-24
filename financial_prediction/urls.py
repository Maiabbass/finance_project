from django.urls import path
from . import views

app_name = 'financial_prediction'

urlpatterns = [
    path('api/predict/', views.predict_api, name='predict_api'),
]