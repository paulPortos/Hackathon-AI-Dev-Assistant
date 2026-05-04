from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils import timezone

from users.models import EmailVerificationCode


def email_verification_confirm_for_user(*, user, code):
    error_message = None

    with transaction.atomic():
        try:
            verification_code = EmailVerificationCode.objects.select_for_update().get(user=user)
        except ObjectDoesNotExist as exc:
            raise ValidationError('Verification code does not exist') from exc

        now = timezone.now()
        if verification_code.consumed_at:
            raise ValidationError('Verification code has already been used')
        if verification_code.expires_at <= now:
            raise ValidationError('Verification code has expired')
        if verification_code.attempt_count >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
            raise ValidationError('Too many verification attempts')

        verification_code.attempt_count += 1
        if not check_password(code, verification_code.code_hash):
            verification_code.save(update_fields=['attempt_count', 'updated_at'])
            error_message = 'Verification code is invalid'
        else:
            verification_code.consumed_at = now
            verification_code.save(update_fields=['attempt_count', 'consumed_at', 'updated_at'])
            user.email_verified_at = now
            user.save(update_fields=['email_verified_at', 'updated_at'])

    if error_message:
        raise ValidationError(error_message)

    return user
