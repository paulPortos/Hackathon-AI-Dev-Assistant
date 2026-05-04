import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from users.models import EmailVerificationCode
from users.providers import send_email_verification_code


@transaction.atomic
def email_verification_request_for_user(*, user):
    if not user.email:
        raise ValidationError('User does not have an email address')

    now = timezone.now()
    verification_code = EmailVerificationCode.objects.select_for_update().filter(user=user).first()
    cooldown_until = None
    if verification_code:
        cooldown_until = verification_code.last_sent_at + timedelta(seconds=settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS)
    if cooldown_until and cooldown_until > now:
        raise ValidationError('Please wait before requesting another verification code')

    code = f'{secrets.randbelow(1000000):06d}'
    ttl_minutes = settings.EMAIL_VERIFICATION_CODE_TTL_MINUTES
    send_email_verification_code(to_email=user.email, code=code, ttl_minutes=ttl_minutes)

    defaults = {
        'sent_to_email': user.email,
        'code_hash': make_password(code),
        'expires_at': now + timedelta(minutes=ttl_minutes),
        'attempt_count': 0,
        'consumed_at': None,
        'last_sent_at': now,
    }
    if verification_code:
        for field, value in defaults.items():
            setattr(verification_code, field, value)
        verification_code.save(update_fields=[*defaults.keys(), 'updated_at'])
        return verification_code

    return EmailVerificationCode.objects.create(user=user, **defaults)
