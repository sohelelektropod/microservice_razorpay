import json
import razorpay
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TransactionSerializer
from .utils import process_razorpay_payment

import stripe
from .utils import process_stripe_payment


class ProcessRazorpayView(APIView):

    def post(self, request):
        try:
            amount = request.POST['amount']
            razorpay_id = request.POST['razorpay_payment_id']
            content = process_razorpay_payment(razorpay_id)
            transaction_data = {
                'amount': amount,
                'payment_id': razorpay_id,
                'payment_method': 'razorpay',
                'transaction_info1': content.get('transaction_info1') if content else None,
                'transaction_info2': content.get('transaction_info2') if content else None,
            }
            serializer = TransactionSerializer(data=transaction_data)
            if serializer.is_valid():
                serializer.save(status='completed')
                print("Successfully processed payment")
                return render(request, "Txn_complete.html")
            else:
                return Response({'success': False, 'message': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RazorpayWebhookView(APIView):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            signature = request.headers.get('X-Razorpay-Signature')
            payload = request.body
            razorpay_secret_key = 'TksSZT7DG7VOE7tdoY2wINOl'

            if not verify_razorpay_signature(payload, signature, razorpay_secret_key):
                return Response({'success': False, 'message': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

            payload_data = json.loads(payload)
            event_type = payload_data.get('event', {})

            if event_type == 'payment.authorized':
                handle_payment_authorized(payload_data)
            elif event_type == 'payment.failed':
                handle_payment_failed(payload_data)
            elif event_type == 'payment.captured':
                handle_payment_captured(payload_data)
            elif event_type == 'refund.failed':
                handle_payment_refunded(payload_data)
            print("Webhook processed successfully")
            return Response({'success': True, 'message': 'Webhook processed successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CapturePaymentView(APIView):

    def capture_payment(self, payment_id, amount):
        try:
            client = razorpay.Client(auth=("rzp_test_7GdoiyFlxJuVO4", "TksSZT7DG7VOE7tdoY2wINOl"))
            response = client.payment.capture(payment_id, amount)
            print("Payment captured successfully")

            return {'success': True, 'message': 'Payment captured successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def post(self, request):
        try:
            payload_data = json.loads(request.body)
            payment_id = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
            amount = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('amount')

            if payment_id:
                capture_result = self.capture_payment(payment_id, amount)
                if capture_result['success']:
                    return Response(capture_result, status=status.HTTP_200_OK)
                else:
                    return Response(capture_result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({'success': False, 'error': 'Payment ID not found in the payload'},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def verify_razorpay_signature(payload, signature, secret_key):
    import hmac
    import hashlib

    secret_key = bytes(secret_key, 'utf-8')
    calculated_signature = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
    return calculated_signature == signature


def handle_payment_captured(payload_data):
    payment_id = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
    amount_captured = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('amount_captured')
    print(f"Payment captured - Payment ID: {payment_id}, Amount Captured: {amount_captured}")


def handle_payment_authorized(payload_data):
    payment_id = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
    amount_authorized = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('amount')
    amount_currency = int(amount_authorized / 100)
    print(f"Payment authorized - Payment ID: {payment_id}, Amount Authorized: {amount_currency}")

    capture_view = CapturePaymentView()
    capture_result = capture_view.capture_payment(payment_id, amount_authorized)

    if capture_result['success']:
        print("Capture Call Payment successful")
    else:
        print("Capture Payment failed: ", capture_result['error'])


def handle_payment_failed(payload_data):
    payment_id = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
    error_message = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('error_reason')
    print(f"Payment failed - Payment ID: {payment_id}, Error Message: {error_message}")


def handle_payment_refunded(payload_data):
    payment_id = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id')
    refunded_amount = payload_data.get('payload', {}).get('payment', {}).get('entity', {}).get('amount_refunded')
    print(f"Payment failed - Payment ID: {payment_id}, Error Message: {refunded_amount}")


def show_payment_options(request):
    return render(request, 'payment_option.html')


def show_razorpay_page(request):
    return render(request, 'razorpay_page.html')


# -------------------------------------- Checkout stripe------------------------------------------------------


stripe.api_key = settings.STRIPE_SECRET_KEY


def product_page(request):
    return render(request, 'stripe_checkout.html')


@require_POST
@csrf_exempt
def create_stripe_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    data = json.loads(request.body.decode('utf-8'))

    amount_in_rupees = float(data.get('amount'))
    amount_in_paise = int(amount_in_rupees * 100)

    currency = 'INR'

    description = data.get('description')
    shipping = data.get('shipping', {})

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {
                    'name': 'Elektropod',
                    'description': description,
                },
                'unit_amount': int(amount_in_paise),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/api/success/'),
        cancel_url=request.build_absolute_uri('/api/cancel/'),
        shipping_address_collection={
            'allowed_countries': ['US', 'CA'],
        },
        shipping=shipping,
    )

    # session = stripe.checkout.Session.create(
    #     payment_method_types=['card'],
    #     line_items=[{
    #         'price_data': {
    #             'currency': currency,
    #             'product_data': {
    #                 'name': 'Elektropod',
    #                 'description': description,
    #             },
    #             'unit_amount': int(amount_in_paise),
    #         },
    #         'quantity': 1,
    #     }],
    #     mode='payment',
    #     success_url=request.build_absolute_uri('/api/success/'),
    #     cancel_url=request.build_absolute_uri('/api/cancel/'),
    #     shipping_address_collection={},  # Set it as an empty dictionary
    #     shipping=shipping,
    # )

    return JsonResponse({'id': session.id})


def success_page(request):
    return render(request, 'success.html')


def cancel_page(request):
    return render(request, 'cancel.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers['Stripe-Signature']
    endpoint_secret = 'whsec_uNjtt0OW3II2ZMHJrMFFDpmj9cwKCqRr'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print("event-----------", event)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    print("before type-----------")
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_intent_id = payment_intent.get('id', None)
        print("after type--------------")

        if payment_intent_id:
            print("Transaction saved successfully")
            save_transaction(payment_intent)
            if payment_intent['status'] != 'succeeded':
                capture_payment(payment_intent_id)

    return HttpResponse(status=200)


def capture_payment(payment_intent_id):
    try:
        captured_payment_intent = stripe.PaymentIntent.capture(payment_intent_id)
        print(f"PaymentIntent {captured_payment_intent['id']} was captured.")
    except stripe.error.StripeError as e:
        print(f"Error capturing payment: {e}")


def save_transaction(payment_intent):
    try:
        amount = payment_intent.get('amount') / 100
        transaction_data = {
            'amount': amount,
            'payment_id': payment_intent['id'],
            'payment_method': 'stripe',
            'transaction_info1': None,
            'transaction_info2': None,
        }

        serializer = TransactionSerializer(data=transaction_data)
        if serializer.is_valid():
            serializer.save(status='completed')
        else:
            print("Invalid data for transaction")
    except Exception as e:
        print(f"Error saving transaction: {e}")