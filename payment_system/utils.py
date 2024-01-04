import json
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth


def process_razorpay_payment(razorpay_id):
    from requests.auth import HTTPBasicAuth
    try:
        response = requests.get(settings.RAZOR_API.format(razorpay_id),
                                auth=HTTPBasicAuth(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        content = json.loads(response.content)
        print(content)

        transaction_info1 = None
        transaction_info2 = None

        if content.get('status') not in ['captured', 'authorized']:
            transaction_info1 = "FAILED"
            transaction_info2 = "FAILED"
        else:
            if content['method'] == 'card':
                transaction_info1 = "{} {} card".format(content['card']['network'], content['card']['type'])
                transaction_info2 = "{} card ending with {}".format(content['card']['issuer'], content['card']['last4'])
            elif content['method'] == 'netbanking':
                transaction_info1 = "{} netbanking".format(content['bank'])
            elif content['method'] == 'wallet':
                transaction_info1 = "{} wallet".format(content['wallet'])
            elif content['method'] == 'paylater':
                transaction_info1 = "{} paylater".format(content['wallet'])
            elif content['method'] == 'upi':
                transaction_info1 = "{}".format(content['vpa'])

        return {'transaction_info1': transaction_info1, 'transaction_info2': transaction_info2}

    except json.JSONDecodeError as e:
        return {'transaction_info1': "FAILED", 'transaction_info2': "FAILED", 'error': f'JSON decoding error: {e}'}


import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def process_stripe_payment(payment_intent_id):
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        transaction_info1 = None
        transaction_info2 = None

        if payment_intent.status not in ['succeeded']:
            transaction_info1 = "FAILED"
            transaction_info2 = "FAILED"
        else:
            payment_method = stripe.PaymentMethod.retrieve(payment_intent.payment_method)

            if payment_method.type == 'card':
                card_info = payment_method.card
                transaction_info1 = "{} {} card".format(card_info.brand, card_info.funding)
                transaction_info2 = "{} card ending with {}".format(card_info.brand, card_info.last4)
            elif payment_method.type == 'card_present':
                transaction_info1 = "Card present"
            elif payment_method.type == 'sepa_debit':
                transaction_info1 = "SEPA debit"

        return {'transaction_info1': transaction_info1, 'transaction_info2': transaction_info2}

    except stripe.error.StripeError as e:
        return {'transaction_info1': "FAILED", 'transaction_info2': "FAILED", 'error': str(e)}

#
# def process_stripe_payment(stripe_payment_intent_id):
#     print("payment_idiiiiiiiiiiiiiiiiiiiii", stripe_payment_intent_id)
#     response = requests.get(
#         settings.API_URL.format(stripe_payment_intent_id),
#         auth=(settings.STRIPE_SECRET_KEY, '')
#     )
#     print("Response------",response)
#     content = json.loads(response.content)
#     print("content-------", content)
#     print("Stripe Status:", content)
#     transaction_info1 = None
#     transaction_info2 = None
#
#     if content.get('status') != 'succeeded':
#         return "FAILED", "FAILED", content
#
#     charges = content.get('charges', {}).get('data', [])
#
#     if not charges:
#         return "FAILED", "FAILED", {'error': {'message': 'No charge associated with the payment intent'}}
#
#     card = charges[0].get('payment_method_details', {}).get('card', {})
#
#     if card:
#         transaction_info1 = "{} {} card".format(card.get('network', ''), card.get('brand', ''))
#         transaction_info2 = "{} card ending with {}".format(card.get('issuer', ''), card.get('last4', ''))
#
#     return transaction_info1, transaction_info2, None