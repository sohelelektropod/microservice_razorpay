from django.http import request
from django.urls import path
from .views import (ProcessRazorpayView, show_razorpay_page, RazorpayWebhookView, CapturePaymentView, product_page, success_page, cancel_page, create_stripe_checkout_session, stripe_webhook)


urlpatterns = [
    path('razorpay', show_razorpay_page, name='razorpay_page'),
    path('process_payment/', ProcessRazorpayView.as_view(), name='process_payment'),
    path('razorpay-webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    path('razorpay-payment-captured/', CapturePaymentView.as_view(), name='razorpay_payment_captured'),

    path('product_page/', product_page, name='product_page'),
    path('create_stripe_checkout_session/', create_stripe_checkout_session, name='create_stripe_checkout_session'),
    path('success/', success_page, name='success_page'),
    path('cancel/', cancel_page, name='cancel_page'),
    path('stripe_webhook/', stripe_webhook, name='stripe_webhook'),

]
