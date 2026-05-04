from rest_framework_simplejwt.exceptions import AuthenticationFailed as JWTAuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    if not user.is_active:
        raise JWTAuthenticationFailed('User is not active')

    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
