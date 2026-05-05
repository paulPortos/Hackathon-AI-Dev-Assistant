from django.conf import settings

from users.github._parse_response import _parse_response
from users.github.constants import GITHUB_TOKEN_URL
from users.github.github_oauth_error import GitHubOAuthError


def refresh_github_access_token(*, refresh_token):
    import requests

    response = requests.post(
        GITHUB_TOKEN_URL,
        data={
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        },
        headers={'Accept': 'application/json'},
        timeout=10,
    )
    data = _parse_response(response, 'GitHub token refresh failed')
    if not isinstance(data, dict) or not data.get('access_token'):
        raise GitHubOAuthError('GitHub token refresh returned an invalid response')

    return data
