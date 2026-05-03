from urllib.parse import urlencode

from django.conf import settings


GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_URL = 'https://api.github.com/user'
GITHUB_EMAILS_URL = 'https://api.github.com/user/emails'
GITHUB_SCOPE = 'read:user user:email'


class GitHubOAuthError(Exception):
    pass


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


def exchange_code_for_access_token(*, code):
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

    access_token = data.get('access_token')
    if not access_token:
        error = data.get('error_description') or data.get('error') or 'GitHub did not return an access token'
        raise GitHubOAuthError(error)
    return access_token


def fetch_github_user(*, access_token):
    data = _github_get(GITHUB_USER_URL, access_token=access_token, message='GitHub user fetch failed')
    if not isinstance(data, dict):
        raise GitHubOAuthError('GitHub user fetch returned an invalid response')
    return data


def fetch_github_emails(*, access_token):
    data = _github_get(GITHUB_EMAILS_URL, access_token=access_token, message='GitHub email fetch failed')
    if not isinstance(data, list):
        raise GitHubOAuthError('GitHub email fetch returned an invalid response')
    return data


def select_email(*, github_user, github_emails):
    if github_user.get('email'):
        return github_user['email']

    for email in github_emails:
        if email.get('primary') and email.get('verified') and email.get('email'):
            return email['email']

    return ''


def _github_get(url, *, access_token, message):
    import requests

    response = requests.get(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': '2022-11-28',
        },
        timeout=10,
    )
    return _parse_response(response, message)


def _parse_response(response, message):
    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubOAuthError(message) from exc

    if response.status_code >= 400:
        detail = message
        if isinstance(data, dict):
            detail = data.get('error_description') or data.get('message') or message
        raise GitHubOAuthError(detail)

    return data
