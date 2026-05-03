import secrets

from django.http import HttpResponseRedirect
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed as JWTAuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from users.github import (
    GitHubOAuthError,
    build_github_authorization_url,
    exchange_code_for_access_token,
    fetch_github_emails,
    fetch_github_user,
    select_email,
)
from users.serializers import UserSerializer
from users.services import user_create_or_update_from_github


GITHUB_OAUTH_STATE_SESSION_KEY = 'github_oauth_state'


class GitHubLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        state = secrets.token_urlsafe(32)
        request.session[GITHUB_OAUTH_STATE_SESSION_KEY] = state
        request.session.modified = True
        return HttpResponseRedirect(build_github_authorization_url(state=state))


class GitHubCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        expected_state = request.session.pop(GITHUB_OAUTH_STATE_SESSION_KEY, None)
        request.session.modified = True

        if not expected_state or not state or not secrets.compare_digest(expected_state, state):
            raise AuthenticationFailed('Invalid GitHub OAuth state')
        if request.query_params.get('error'):
            detail = request.query_params.get('error_description') or request.query_params['error']
            raise ValidationError({'detail': detail})
        if not code:
            raise ValidationError({'detail': 'Missing GitHub OAuth code'})

        try:
            access_token = exchange_code_for_access_token(code=code)
            github_user = fetch_github_user(access_token=access_token)
            github_emails = fetch_github_emails(access_token=access_token)
            email = select_email(github_user=github_user, github_emails=github_emails)
            user = user_create_or_update_from_github(
                github_user=github_user,
                access_token=access_token,
                email=email,
            )
        except GitHubOAuthError as exc:
            raise AuthenticationFailed(str(exc)) from exc
        except ValueError as exc:
            raise ValidationError({'detail': str(exc)}) from exc

        tokens = get_tokens_for_user(user)
        return Response({'access': tokens['access'], 'refresh': tokens['refresh'], 'user': UserSerializer(user).data})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, version=None):
        return Response(UserSerializer(request.user).data)


def get_tokens_for_user(user):
    if not user.is_active:
        raise JWTAuthenticationFailed('User is not active')

    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
