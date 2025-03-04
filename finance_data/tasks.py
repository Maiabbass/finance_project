from celery import shared_task
import logging
import django
django.setup()
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg
from django.contrib.auth import get_user_model
from decimal import Decimal
#from .currency_data_fetcher import CurrencyDataFetcher
from .models import (
    FinancialData, Trade, PredictionModel, TradingAnalytics,
    Alert, UserProfile, RiskManagement
)
from .fetch_financial_data import CurrencyDataFetcher

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='finance_data.tasks.update_currency_data'
)
def update_currency_data(self):
    """
    Task to update currency data.
    """
    try:
        logger.info(f"Started updating currency data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # إنشاء كائن من CurrencyDataFetcher واستدعاء run_daily_update
        fetcher = CurrencyDataFetcher()
        fetcher.run_daily_update()
        
        logger.info(f"Currency data updated successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return "Currency data updated successfully"
    
    except Exception as e:
        error_msg = f"Error occurred while updating currency data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise self.retry(exc=e)

@shared_task
def simple_test_task():
    """
    A simple test task to ensure Celery is working properly.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Test task executed at {current_time}")
    return f"Test task succeeded at {current_time}"


# 2. تحديث التوقعات
@shared_task
def update_predictions():
    """تحديث التوقعات اليومية لكل العملات"""
    try:
        today = timezone.now().date()
        tickers = FinancialData.objects.values_list('ticker', flat=True).distinct()
        
        for ticker in tickers:
            # جلب البيانات التاريخية
            historical_data = FinancialData.objects.filter(
                ticker=ticker,
                date__gte=today - timedelta(days=30)
            ).order_by('date')
            
            if not historical_data.exists():
                continue
                
            # حساب التوقعات (هنا يمكنك استخدام نموذج التعلم الآلي الخاص بك)
            last_price = historical_data.last().close_price
            predicted_price = last_price * Decimal('1.001')  # مثال بسيط
            
            # تخزين التوقعات
            PredictionModel.objects.create(
                ticker=ticker,
                prediction_date=today,
                predicted_price=predicted_price,
                prediction_period='1D',
                confidence_score=Decimal('0.75'),
                model_version='1.0',
                features_used={'price_history': True}
            )
        
        logger.info("Predictions updated successfully")
    except Exception as e:
        logger.error(f"Error updating predictions: {str(e)}")

# 3. تحديث التحليلات
@shared_task
def update_trading_analytics():
    """تحديث تحليلات التداول لكل المستخدمين"""
    try:
        today = timezone.now().date()
        period_start = today - timedelta(days=30)
        
        for user in User.objects.filter(profile__is_trader=True):
            analytics, created = TradingAnalytics.objects.get_or_create(
                user=user,
                period_start=period_start,
                period_end=today
            )
            analytics.calculate_analytics()
        
        logger.info("Trading analytics updated successfully")
    except Exception as e:
        logger.error(f"Error updating trading analytics: {str(e)}")

# 4. فحص التنبيهات
@shared_task
def check_alerts():
    """فحص جميع التنبيهات النشطة"""
    try:
        active_alerts = Alert.objects.filter(is_active=True)
        
        for alert in active_alerts:
            try:
                # جلب آخر سعر
                latest_price = FinancialData.objects.filter(
                    ticker=alert.ticker
                ).latest('date').close_price
                
                if alert.check_alert_condition(latest_price):
                    alert.trigger_alert()
                    
            except Exception as alert_error:
                logger.error(f"Error processing alert {alert.id}: {str(alert_error)}")
                
        logger.info("Alerts checked successfully")
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")

# 5. تحديث حالة الصفقات
@shared_task
def update_trade_statuses():
    """تحديث حالة الصفقات المفتوحة"""
    try:
        open_trades = Trade.objects.filter(status='OPEN')
        
        for trade in open_trades:
            try:
                latest_price = FinancialData.objects.filter(
                    ticker=trade.ticker
                ).latest('date').close_price
                
                # فحص Stop Loss
                if trade.stop_loss:
                    if (trade.trade_type == 'BUY' and latest_price <= trade.stop_loss) or \
                       (trade.trade_type == 'SELL' and latest_price >= trade.stop_loss):
                        trade.close_trade(latest_price)
                        continue
                
                # فحص Take Profit
                if trade.take_profit:
                    if (trade.trade_type == 'BUY' and latest_price >= trade.take_profit) or \
                       (trade.trade_type == 'SELL' and latest_price <= trade.take_profit):
                        trade.close_trade(latest_price)
                        
            except Exception as trade_error:
                logger.error(f"Error processing trade {trade.id}: {str(trade_error)}")
                
        logger.info("Trade statuses updated successfully")
    except Exception as e:
        logger.error(f"Error updating trade statuses: {str(e)}")

# 6. تحديث إحصائيات المستخدمين
@shared_task
def update_user_statistics():
    """تحديث إحصائيات جميع المستخدمين"""
    try:
        for profile in UserProfile.objects.filter(is_trader=True):
            try:
                # حساب إجمالي الأرباح/الخسائر
                total_pnl = Trade.objects.filter(
                    user=profile.user,
                    status='CLOSED'
                ).aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0
                
                # تحديث الرصيد
                profile.balance = total_pnl
                profile.save()
                
            except Exception as profile_error:
                logger.error(f"Error updating profile {profile.id}: {str(profile_error)}")
                
        logger.info("User statistics updated successfully")
    except Exception as e:
        logger.error(f"Error updating user statistics: {str(e)}")