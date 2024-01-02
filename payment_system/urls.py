from django.http import request
from django.urls import path
from .views import ProcessPaymentView, show_razorpay_page, RazorpayWebhookView, CapturePaymentView

urlpatterns = [
    path('razorpay', show_razorpay_page, name='razorpay_page'),
    path('process_payment/', ProcessPaymentView.as_view(), name='process_payment'),
    path('razorpay-webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    path('razorpay-payment-captured/', CapturePaymentView.as_view(), name='razorpay_payment_captured'),
]
