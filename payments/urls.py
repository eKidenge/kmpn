from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payments
    path('', views.payment_list, name='list'),
    path('initiate/', views.initiate_payment, name='initiate'),
    path('<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('<int:payment_id>/receipt/', views.payment_receipt, name='receipt'),
    
    # M-Pesa
    path('mpesa/<int:payment_id>/', views.mpesa_payment, name='mpesa_pay'),
    path('mpesa/webhook/', views.mpesa_webhook, name='mpesa_webhook'),
    
    # Subscription
    path('subscription/', views.subscription_view, name='subscription'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
]
