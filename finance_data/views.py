from datetime import timedelta, timezone , datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db.models import Max
from finance_data.permissions import IsAdmin , IsUser
from .models import FinancialData, UserProfile
from .serializers import *
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
import csv
from django.http import JsonResponse


class FinancialDataListView(APIView):
    permission_classes = [AllowAny]
       
    def get(self, request):
        ticker = request.query_params.get('ticker')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = FinancialData.objects.all()
        if ticker:
            queryset = queryset.filter(ticker=ticker)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        serializer = FinancialDataSerializer(queryset, many=True)
        return Response(serializer.data)



class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                is_active=False,
                is_staff=False
            )
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.generate_otp()

            send_mail(
                'Verify Your Email',
                f'Your verification code is: {profile.otp_code}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            return Response({'message': 'Check your email for verification code', 'user_id': user.id},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        try:
            user = User.objects.get(id=user_id)
            profile = user.profile

            if profile.validate_otp(otp):
                user.is_active = True
                user.save()
                profile.otp_code = None
                profile.otp_expiry = None
                profile.save()

                refresh = RefreshToken.for_user(user)
                return Response({'message': 'Registration successful', 'refresh': str(refresh), 'access': str(refresh.access_token), 'user_id': user.id})
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                refresh = RefreshToken.for_user(user)
                return Response({'refresh': str(refresh), 'access': str(refresh.access_token), 'user_id': user.id})
            return Response({'error': 'Please verify your email first'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        token = get_random_string(length=32)
        user.profile.reset_token = token
        user.profile.save()

        reset_link = f"{request.build_absolute_uri('/api/set-new-password/')}{token}"
        send_mail('Reset Your Password', f'Click to reset: {reset_link}', settings.EMAIL_HOST_USER, [email])

        return Response({'message': 'Check your email for reset link'}, status=status.HTTP_200_OK)




class SetNewPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        # البحث عن الـ UserProfile باستخدام الـ reset_token
        profile = UserProfile.objects.filter(reset_token=token).first()
        if not profile:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        # الحصول على المستخدم المرتبط بالـ UserProfile
        user = profile.user

        # تأكيد وجود كلمة المرور في الطلب
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        # تعيين كلمة المرور الجديدة وحذف الـ reset_token
        user.set_password(password)
        profile.reset_token = None  # مسح الـ reset_token بعد إعادة تعيين كلمة المرور
        profile.save()
        user.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
    



class PromoteUserToAdminView(APIView):

    permission_classes = [IsAdmin]  

    def post(self, request):
        user_id = request.data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
            user.is_staff = True  # تحويله إلى مسؤول
            user.save()

            return Response({'message': 'User promoted to admin successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        



class FinancialMarketView(APIView):
    def get(self, request):
        """
        الحصول على بيانات السوق مع دعم الفلترة
        """
        queryset = FinancialData.objects.all()
        
        # فلترة حسب رمز العملة
        ticker = request.query_params.get('ticker')
        if ticker:
            queryset = queryset.filter(ticker__iexact=ticker)  # استخدام iexact لجعل الفلترة غير حساسة لحالة الأحرف
        
        # فلترة حسب التاريخ
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        
        # تحويل queryset إلى بيانات JSON
        serializer = FinancialDataSerializer(queryset, many=True)
        
        # إرجاع الاستجابة
        if queryset.exists():
            return Response(serializer.data)
        else:
            return Response({"message": "لا توجد بيانات مطابقة للمعايير المحددة."}, status=status.HTTP_404_NOT_FOUND)


    def post(self, request):
        serializer = FinancialDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)  # طباعة الأخطاء للتحقق منها
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FinancialMarketDetailView(APIView):
    def get_object(self, pk):
        
        try:
            return FinancialData.objects.get(pk=pk)
        except FinancialData.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        الحصول على تفاصيل بيانات سوق محددة
        """
        instance = self.get_object(pk)
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = FinancialDataSerializer(instance)
        return Response(serializer.data)

    def put(self, request, pk):
        """
        تحديث بيانات سوق محددة
        """
        instance = self.get_object(pk)
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = FinancialDataSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        حذف بيانات سوق محددة
        """
        instance = self.get_object(pk)
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class LatestMarketDataView(APIView):
    def get(self, request):
        """
        الحصول على أحدث بيانات السوق
        """
        latest = FinancialData.objects.values('ticker').annotate(latest_date=Max('date')).order_by('ticker')
        
        # الآن نحتاج إلى الحصول على السجلات الكاملة بناءً على أحدث التواريخ
        latest_data = []
        for item in latest:
            ticker = item['ticker']
            date = item['latest_date']
            latest_record = FinancialData.objects.get(ticker=ticker, date=date)
            latest_data.append(latest_record)

        serializer = FinancialDataSerializer(latest_data, many=True)
        return Response(serializer.data)
    
    

class MarketSummaryView(APIView):
    def get(self, request):
        """
        الحصول على ملخص السوق
        """
        today = timezone.now().date()
        queryset = FinancialData.objects.filter(date=today)
        
        gainers = queryset.filter(percent_change__gt=0).order_by('-percent_change')[:5]
        losers = queryset.filter(percent_change__lt=0).order_by('percent_change')[:5]
        most_active = queryset.order_by('-volume')[:5]
        
        summary = {
            'gainers': FinancialDataSerializer(gainers, many=True).data,
            'losers': FinancialDataSerializer(losers, many=True).data,
            'most_active': FinancialDataSerializer(most_active, many=True).data
        }
        
        return Response(summary)

class TechnicalAnalysisView(APIView):
    def get(self, request, pk):
        """
        الحصول على التحليل الفني لعملة محددة
        """
        try:
            instance = FinancialData.objects.get(pk=pk)
        except FinancialData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        analysis = {
            'rsi': instance.rsi,
            'macd': instance.macd,
            'macd_signal': instance.macd_signal,
            'macd_hist': instance.macd_hist,
            'recommendation': instance.label,
            'price_change': instance.percent_change
        }
        
        return Response(analysis) 




class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """عرض بيانات البروفايل"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def patch(self, request):
        """تحديث بيانات البروفايل والحالات الخاصة"""
        profile = request.user.profile
        
        # التعامل مع حالة المتداول
        if 'is_trader' in request.data:
            # التحقق من الشروط المطلوبة
            if not all([
                profile.phone_number,
                profile.address,
                profile.birth_date,
                profile.nationality
            ]):
                return Response({
                    'error': 'يجب إكمال جميع البيانات الشخصية أولاً',
                    'missing_fields': [
                        field for field in ['phone_number', 'address', 'birth_date', 'nationality']
                        if not getattr(profile, field)
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
            profile.is_trader = True
        
        # التعامل مع تحديث الرصيد
        if 'balance' in request.data:
            try:
                new_balance = Decimal(request.data.get('balance', 0))
                if new_balance < 0:
                    return Response({
                        'error': 'الرصيد لا يمكن أن يكون بالسالب'
                    }, status=status.HTTP_400_BAD_REQUEST)
                profile.balance = new_balance
            except (ValueError, TypeError):
                return Response({
                    'error': 'قيمة الرصيد غير صالحة'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # تحديث باقي البيانات
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'تم تحديث البيانات بنجاح',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class UploadFinancialData(APIView):
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        file = request.FILES['file']
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            # تحويل التاريخ من MM/DD/YYYY إلى YYYY-MM-DD
            date_obj = datetime.strptime(row['Date'], '%m/%d/%Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')

            data = {
                'date': formatted_date,
                'ticker': 'XRP/USDT',
                'open_price': row['Open'],
                'high_price': row['High'],
                'low_price': row['Low'],
                'close_price': row['Price'],
                'volume': row['Vol'],
                'percent_change': row['Change %'].rstrip('%'),
                'adj_close': row['Price'], 
            }
            serializer = FinancialDataSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return JsonResponse(serializer.errors, status=400)

        return JsonResponse({"message": "Data uploaded successfully"}, status=201)
    



class FinancialDataModel(APIView):
    def get(self, request, *args, **kwargs):

        date_str = request.query_params.get('date', None)
        if not date_str:
            return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        start_date = date - timedelta(days=15)

        financial_data = FinancialData.objects.filter(
            date__range=[start_date, date]
        ).order_by('date')  # ترتيب البيانات حسب التاريخ

        serializer = FinancialDataModelSerializer(financial_data, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)