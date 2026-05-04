from django.conf import settings

from projects.providers.email_delivery_error import EmailDeliveryError


def send_scrum_meeting_email(*, to_emails, subject, text_content, html_content):
    import requests

    if not settings.TWILLIO_SENDGRID_API_KEY or not settings.TWILLIO_SENDGRID_FROM_EMAIL:
        raise EmailDeliveryError('Scrum email provider is not configured')

    response = requests.post(
        'https://api.sendgrid.com/v3/mail/send',
        json={
            'personalizations': [{'to': [{'email': email} for email in to_emails]}],
            'from': {
                'email': settings.TWILLIO_SENDGRID_FROM_EMAIL,
                'name': settings.TWILLIO_SENDGRID_FROM_NAME,
            },
            'subject': subject,
            'content': [
                {'type': 'text/plain', 'value': text_content},
                {'type': 'text/html', 'value': html_content},
            ],
        },
        headers={
            'Authorization': f'Bearer {settings.TWILLIO_SENDGRID_API_KEY}',
            'Content-Type': 'application/json',
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise EmailDeliveryError('Scrum email provider could not send reminder')
