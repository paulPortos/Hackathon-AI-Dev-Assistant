from django.utils import timezone


def github_token_expiry_from_seconds(seconds):
    if seconds in (None, ''):
        return None

    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None

    if seconds <= 0:
        return None

    return timezone.now() + timezone.timedelta(seconds=seconds)
