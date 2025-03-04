from django.urls import path
from .views import *

urlpatterns = [
    #لمودل الذكاء
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
       
]

