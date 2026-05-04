from urllib.parse import urlencode

from django.conf import settings

from users.github.constants import GITHUB_AUTHORIZE_URL, GITHUB_SCOPE


def build_github_authorization_url(*, state):
    query = urlencode(
        {
            'client_id': settings.GITHUB_CLIENT_ID,
            'redirect_uri': settings.GITHUB_CALLBACK_URL,
            'scope': GITHUB_SCOPE,
            'state': state,
        }
    )
    return f'{GITHUB_AUTHORIZE_URL}?{query}'
