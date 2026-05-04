from email_verifications.models import EmailVerificationCode


def email_verification_code_get_for_user(user):
    return EmailVerificationCode.objects.get(user=user)
