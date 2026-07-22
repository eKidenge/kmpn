from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.member_dashboard, name='dashboard'),
    
    # Verification
    path('verification/', views.member_verification_request, name='verification_request'),
    path('verification/status/', views.verification_status, name='verification_status'),
    path('manage-verifications/', views.manage_verifications, name='manage_verifications'),
    path('review-verification/<int:verification_id>/', views.review_verification, name='review_verification'),
    
    # Digital Card
    path('card/', views.digital_card, name='digital_card'),
    path('card/download/', views.download_digital_card, name='download_card'),
    path('qr/download/', views.download_qr_code, name='download_qr'),
    
    # Directory
    path('directory/', views.member_directory, name='directory'),
    path('search/', views.member_search, name='search'),
    
    # Profile
    path('<int:member_id>/', views.member_detail, name='detail'),
    path('<int:member_id>/follow/', views.follow_member, name='follow'),
    path('<int:member_id>/message/', views.message_member, name='message'),
    
    # Settings
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('settings/', views.member_settings, name='settings'),
    
    # Activities
    path('activities/', views.member_activities, name='activities'),
    
    # Admin
    path('statistics/', views.member_statistics, name='statistics'),
    path('export/', views.export_members, name='export'),
    
    # AJAX
    path('api/members-json/', views.get_members_json, name='get_members_json'),
    path('api/verify-documents/', views.verify_documents, name='verify_documents'),
    path('api/check-membership/', views.check_membership, name='check_membership'),
]
