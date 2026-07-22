from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'communities', views.CommunityViewSet, basename='community')
router.register(r'opportunities', views.OpportunityViewSet, basename='opportunity')
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'resources', views.ResourceViewSet, basename='resource')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

app_name = 'api'

urlpatterns = [
    # Authentication
    path('auth/', include([
        path('register/', views.RegisterView.as_view(), name='register'),
        path('login/', views.LoginView.as_view(), name='login'),
        path('logout/', views.LogoutView.as_view(), name='logout'),
        path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
        path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
        path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
        path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    ])),
    
    # User Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    
    # Activities
    path('activities/', views.ActivityListView.as_view(), name='activities'),
    
    # Search
    path('search/', views.SearchView.as_view(), name='search'),
    
    # API Root
    path('', include(router.urls)),
]