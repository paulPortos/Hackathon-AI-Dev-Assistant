from django.conf import settings

from users.providers.email_delivery_error import EmailDeliveryError


def send_email_verification_code(*, to_email, code, ttl_minutes):
    if not settings.TWILLIO_SENDGRID_API_KEY or not settings.TWILLIO_SENDGRID_FROM_EMAIL:
        raise EmailDeliveryError('Email provider is not configured')

    import requests

    response = requests.post(
        'https://api.sendgrid.com/v3/mail/send',
        json={
            'personalizations': [{'to': [{'email': to_email}]}],
            'from': {
                'email': settings.TWILLIO_SENDGRID_FROM_EMAIL,
                'name': settings.TWILLIO_SENDGRID_FROM_NAME,
            },
            'subject': 'Your email verification code',
            'content': [
                {
                    'type': 'text/plain',
                    'value': f'Your verification code is {code}. It expires in {ttl_minutes} minutes.',
                },
                {
                    'type': 'text/html',
                    'value': f'<p>Your verification code is <strong>{code}</strong>.</p><p>It expires in {ttl_minutes} minutes.</p>',
                },
            ],
        },
        headers={
            'Authorization': f'Bearer {settings.TWILLIO_SENDGRID_API_KEY}',
            'Content-Type': 'application/json',
        },
        timeout=10,
    )
    if response.status_code < 200 or response.status_code >= 300:
        raise EmailDeliveryError('Email provider could not send verification code')
