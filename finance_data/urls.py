from django.urls import path
from .views import *

urlpatterns = [
    #تسجيل الدخول وتوزيع الصلاحيات
    path('get-financial-data/', FinancialDataListView.as_view(), name='get-financial-data'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify-registration/', VerifyRegistrationView.as_view(), name='verify-registration'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('set-new-password/<str:token>/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('promote-user/', PromoteUserToAdminView.as_view(), name='promote-user'),
    
    #لواجهه السوق المالي 
    path('financial-data/', FinancialMarketView.as_view(), name='financial-market'),
    path('financial-data/<int:pk>/', FinancialMarketDetailView.as_view(), name='financial-market-detail'),
    path('financial-data/latest/', LatestMarketDataView.as_view(), name='latest-market-data'),
    path('financial-data/summary/', MarketSummaryView.as_view(), name='market-summary'),
    path('financial-data/technical-analysis/<int:pk>/', TechnicalAnalysisView.as_view(), name='technical-analysis'),

    #لتعديل البروفايل
    path('profile/', UserProfileView.as_view(), name='user-profile'),


    #لتحميل الداتا 
    path('upload/', UploadFinancialData.as_view(), name='upload-financial-data'),

    #لارسال البيانات لمودل الذكاء
    path('financial-data-For-Model/', FinancialDataModel.as_view(), name='financial-data'),


    # بإرجاع بيانات سعر العملة في تاريخ معين بناءً على ticker و date.
    path('currency-price/', CurrencyPriceAPIView.as_view(), name='currency-price'),





    # API لحساب الفرق بين سعر الشراء والبيع بناءً على بيانات FinancialData
    path('currency-difference/', CurrencyDifferenceAPIView.as_view(), name='currency-difference'),



    # API لحساب الربح من قاعدة البيانات
    path('profit/', ProfitCalculatorAPIView.as_view(), name='profit-calculator'),


    # API لحساب سعر البيع
    path('selling-price/', SellingPriceAPIView.as_view(), name='selling-price'),


]
       


