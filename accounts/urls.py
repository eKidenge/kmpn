# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # ============================================================
    # DASHBOARD - Role-Based Redirect & Dashboards
    # ============================================================
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Role-Specific Dashboards
    path('dashboard/super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/executive/', views.executive_dashboard, name='executive_dashboard'),
    path('dashboard/moderator/', views.moderator_dashboard, name='moderator_dashboard'),
    path('dashboard/member/', views.member_dashboard, name='member_dashboard'),
    path('dashboard/basic-member/', views.basic_member_dashboard, name='basic_member_dashboard'),
    path('dashboard/alumni/', views.alumni_dashboard, name='alumni_dashboard'),
    path('dashboard/researcher/', views.researcher_dashboard, name='researcher_dashboard'),
    path('dashboard/partner/', views.partner_dashboard, name='partner_dashboard'),
    path('dashboard/guest/', views.guest_dashboard, name='guest_dashboard'),
    path('dashboard/prospective/', views.prospective_member_dashboard, name='prospective_member_dashboard'),
    
    # ============================================================
    # PROFILE
    # ============================================================
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # ============================================================
    # ALUMNI SPECIFIC VIEWS (ADD THESE)
    # ============================================================
    path('alumni/mentorship/', views.alumni_mentorship, name='alumni_mentorship'),
    path('alumni/directory/', views.alumni_directory, name='alumni_directory'),
    path('alumni/events/', views.alumni_events, name='alumni_events'),
    path('alumni/mentors/', views.alumni_mentors, name='alumni_mentors'),
    path('alumni/jobs/', views.alumni_jobs, name='alumni_jobs'),
    path('alumni/research/', views.alumni_research, name='alumni_research'),
    path('alumni/giving/', views.alumni_giving, name='alumni_giving'),
    path('alumni/resources/', views.alumni_resources, name='alumni_resources'),
    path('alumni/stories/', views.alumni_stories, name='alumni_stories'),
    path('alumni/update/', views.alumni_profile_update, name='alumni_profile_update'),
    
    # ============================================================
    # MEMBERSHIP
    # ============================================================
    path('membership/renew/', views.membership_renew, name='membership_renew'),
    path('membership/status/', views.membership_status, name='membership_status'),
    
    # ============================================================
    # ACTIVITY LOGS
    # ============================================================
    path('activity/log/', views.activity_log, name='activity_log'),
    
    # ============================================================
    # ROLE CHANGE REQUEST
    # ============================================================
    path('role-change-request/', views.request_role_change, name='request_role_change'),
    
    # ============================================================
    # ADMIN - Registration & User Management
    # ============================================================
    path('admin/applications/', views.manage_applications, name='manage_applications'),
    path('admin/applications/<int:application_id>/review/', views.review_application, name='review_application'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/role-requests/', views.manage_role_requests, name='manage_role_requests'),
    path('admin/role-requests/<int:request_id>/review/', views.review_role_request, name='review_role_request'),
    path('admin/activity-logs/', views.activity_logs, name='activity_logs'),
    
    # ============================================================
    # EMAIL VERIFICATION
    # ============================================================
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # ============================================================
    # PASSWORD RESET
    # ============================================================
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # ============================================================
    # AJAX ENDPOINTS
    # ============================================================
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),
    path('api/stats/', views.get_user_stats, name='get_user_stats'),
]