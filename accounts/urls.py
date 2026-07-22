from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Email Verification
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # AJAX Endpoints
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),
]
