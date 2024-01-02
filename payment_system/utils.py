import json
import requests
from django.conf import settings


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
