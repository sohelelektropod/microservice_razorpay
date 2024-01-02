import json
import razorpay
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import TransactionSerializer
from .utils import process_razorpay_payment


class ProcessPaymentView(APIView):

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


def show_stripe_page(request):
    return render(request, 'stripe_page.html')
