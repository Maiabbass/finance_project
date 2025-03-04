from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FinancialData, UserProfile


class FinancialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialData
        fields = '__all__'  # يمكنك تخصيص الحقول حسب الحاجة

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False  # سيحتاج المستخدم إلى التحقق قبل التفعيل
        )
        UserProfile.objects.create(user=user)  # إنشاء ملف شخصي تلقائيًا
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)



class FinancialDataSerializer(serializers.ModelSerializer):
    percent_change_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialData
        fields = '__all__'  # سيتم تضمين جميع الحقول تلقائيًا
    
    def get_percent_change_formatted(self, obj):
        if obj.percent_change:
            return f"{obj.percent_change:+.2f}%"
        return "0.00%"


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone_number', 'address', 'birth_date', 
                 'nationality', 'balance', 'is_trader', 'profile_picture']
