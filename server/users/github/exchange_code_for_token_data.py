from django.conf import settings

from users.github._parse_response import _parse_response
from users.github.constants import GITHUB_TOKEN_URL
from users.github.github_oauth_error import GitHubOAuthError


def exchange_code_for_token_data(*, code):
    import requests

    response = requests.post(
        GITHUB_TOKEN_URL,
        data={
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.GITHUB_CALLBACK_URL,
        },
        headers={'Accept': 'application/json'},
        timeout=10,
    )
    data = _parse_response(response, 'GitHub token exchange failed')
    if not isinstance(data, dict):
        raise GitHubOAuthError('GitHub token exchange returned an invalid response')
    if not data.get('access_token'):
        error = data.get('error_description') or data.get('error') or 'GitHub did not return an access token'
        raise GitHubOAuthError(error)

    return data
