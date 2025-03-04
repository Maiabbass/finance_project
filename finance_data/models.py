from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.contrib.auth import get_user_model

User  = get_user_model()
   
class FinancialData(models.Model):
    date = models.DateField()
    ticker = models.CharField(max_length=10)
    
    open_price = models.DecimalField(max_digits=10, decimal_places=6)
    high_price = models.DecimalField(max_digits=10, decimal_places=6)
    low_price = models.DecimalField(max_digits=10, decimal_places=6)
    close_price = models.DecimalField(max_digits=10, decimal_places=6)
    adj_close = models.DecimalField(max_digits=10, decimal_places=6, null=False)
    volume = models.DecimalField(max_digits=20, decimal_places=6)

    rsi = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    macd = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    macd_hist = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    percent_change = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    interest_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    inflation = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    dxy = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    label = models.CharField(max_length=20, null=True, blank=True)  # يمكن أن يكون "Buy" أو "Sell" بناءً على المودل
      
    ma_50 = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    ma_200 = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    close_50ma_diff = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    close_200ma_diff = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    upper_bb = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    lower_bb = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    k_percent = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    d_percent = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    atr = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    volatility = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    next_high = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    high_change = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    market_sentiment = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    economic_news = models.TextField(null=True, blank=True)  # إضافة حقل للأخبار الاقتصادية

    class Meta:
        unique_together = ('date', 'ticker')

    def __str__(self):
        
        return f"{self.ticker} - {self.date}"




class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # رصيد المستخدم
    is_trader = models.BooleanField(default=False)  # هل المستخدم متداول؟
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    otp_code = models.CharField(max_length=6, null=True, blank=True)  # تخزين الرمز
    otp_expiry = models.DateTimeField(null=True, blank=True)  # وقت انتهاء صلاحية الرمز

    reset_token = models.CharField(max_length=255, null=True, blank=True)  # إضافة هذا الحقل

    def generate_otp(self):
        otp = ''.join(random.choices(string.digits, k=6))  
        self.otp_code = otp
        self.otp_expiry = timezone.now() + timedelta(minutes=10)  # صلاحية الرمز لمدة 10 دقائق
        self.save()

    def validate_otp(self, otp):
        if self.otp_code == otp and timezone.now() < self.otp_expiry:
            return True
        return False

    def __str__(self):
        return self.user.username 








# جدول الصفقات
class Trade(models.Model):
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell')
    ]
    
    TRADE_STATUS = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    ticker = models.CharField(max_length=10)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    entry_price = models.DecimalField(max_digits=10, decimal_places=6)
    exit_price = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    exit_date = models.DateTimeField(null=True, blank=True)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRADE_STATUS, default='OPEN')
    stop_loss = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    take_profit = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    leverage = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(null=True, blank=True)

    def calculate_profit_loss(self):
        if self.exit_price and self.status == 'CLOSED':
            if self.trade_type == 'BUY':
                self.profit_loss = (self.exit_price - self.entry_price) * self.quantity * self.leverage
            else:
                self.profit_loss = (self.entry_price - self.exit_price) * self.quantity * self.leverage
            self.profit_loss -= self.commission
            self.save()
        return self.profit_loss

    def close_trade(self, exit_price):
        self.exit_price = exit_price
        self.exit_date = timezone.now()
        self.status = 'CLOSED'
        self.calculate_profit_loss()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.ticker} - {self.trade_type}"

# جدول التوقعات
class PredictionModel(models.Model):
    PREDICTION_PERIODS = [
        ('1D', 'One Day'),
        ('1W', 'One Week'),
        ('1M', 'One Month')
    ]
    
    PREDICTION_TYPES = [
        ('PRICE', 'Price Prediction'),
        ('TREND', 'Trend Prediction'),
        ('VOLATILITY', 'Volatility Prediction')
    ]

    ticker = models.CharField(max_length=10)
    prediction_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=6)
    prediction_period = models.CharField(max_length=2, choices=PREDICTION_PERIODS)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    model_version = models.CharField(max_length=50)
    features_used = models.JSONField()
    actual_price = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prediction_type = models.CharField(max_length=20, choices=PREDICTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_accuracy(self):
        if self.actual_price and self.predicted_price:
            diff = abs(self.actual_price - self.predicted_price)
            self.accuracy = (1 - (diff / self.actual_price)) * 100
            self.save()
        return self.accuracy

    def __str__(self):
        return f"{self.ticker} - {self.prediction_date} - {self.prediction_type}"

# جدول التحليلات
class TradingAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    period_start = models.DateField()
    period_end = models.DateField()
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_profit_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    largest_gain = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    largest_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_holding_period = models.DurationField(null=True)
    risk_reward_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def calculate_analytics(self):
        trades = Trade.objects.filter(
            user=self.user,
            entry_date__date__range=(self.period_start, self.period_end),
            status='CLOSED'
        )
        
        self.total_trades = trades.count()
        self.winning_trades = trades.filter(profit_loss__gt=0).count()
        self.losing_trades = trades.filter(profit_loss__lt=0).count()
        
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
            
        self.total_profit_loss = sum(trade.profit_loss or 0 for trade in trades)
        self.largest_gain = max((trade.profit_loss or 0) for trade in trades)
        self.largest_loss = min((trade.profit_loss or 0) for trade in trades)
        
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.period_start} to {self.period_end}"

# جدول إدارة المخاطر
class RiskManagement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='risk_management')
    max_position_size = models.DecimalField(max_digits=10, decimal_places=2)
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2)
    max_total_risk = models.DecimalField(max_digits=5, decimal_places=2)
    stop_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    take_profit_ratio = models.DecimalField(max_digits=5, decimal_places=2)
    max_trades_per_day = models.IntegerField()
    risk_per_trade = models.DecimalField(max_digits=5, decimal_places=2)
    
    def check_risk_limits(self, trade_amount):
        # التحقق من حدود المخاطر اليومية
        daily_trades = Trade.objects.filter(
            user=self.user,
            entry_date__date=timezone.now().date()
        ).count()
        
        if daily_trades >= self.max_trades_per_day:
            return False, "تجاوزت الحد الأقصى للصفقات اليومية"
            
        if trade_amount > self.max_position_size:
            return False, "تجاوزت الحد الأقصى لحجم المركز"
            
        daily_loss = Trade.objects.filter(
            user=self.user,
            exit_date__date=timezone.now().date(),
            profit_loss__lt=0
        ).aggregate(models.Sum('profit_loss'))['profit_loss__sum'] or 0
        
        if abs(daily_loss) > self.max_daily_loss:
            return False, "تجاوزت الحد الأقصى للخسارة اليومية"
            
        return True, "ضمن حدود المخاطر المسموح بها"

    def __str__(self):
        return f"Risk Management - {self.user.username}"

# جدول التنبيهات
class Alert(models.Model):
    ALERT_TYPES = [
        ('PRICE', 'Price Alert'),
        ('TECHNICAL', 'Technical Indicator'),
        ('VOLUME', 'Volume Alert'),
        ('NEWS', 'News Alert')
    ]
    
    ALERT_CONDITIONS = [
        ('ABOVE', 'Above'),
        ('BELOW', 'Below'),
        ('CROSSES', 'Crosses')
    ]
    
    NOTIFICATION_METHODS = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    ticker = models.CharField(max_length=10)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    condition = models.CharField(max_length=20, choices=ALERT_CONDITIONS)
    value = models.DecimalField(max_digits=10, decimal_places=6)
    is_active = models.BooleanField(default=True)
    notification_method = models.CharField(max_length=20, choices=NOTIFICATION_METHODS)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def check_alert_condition(self, current_price):
        if not self.is_active:
            return False
            
        if self.condition == 'ABOVE' and current_price > self.value:
            return True
        elif self.condition == 'BELOW' and current_price < self.value:
            return True
        elif self.condition == 'CROSSES':
            # يحتاج إلى منطق إضافي للتحقق من التقاطع
            pass
            
        return False

    def trigger_alert(self):
        self.last_triggered = timezone.now()
        self.save()
        # إضافة منطق إرسال الإشعارات

    def __str__(self):
        return f"{self.user.username} - {self.ticker} - {self.alert_type}"



