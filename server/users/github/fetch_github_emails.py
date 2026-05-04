from users.github._github_get import _github_get
from users.github.constants import GITHUB_EMAILS_URL
from users.github.github_oauth_error import GitHubOAuthError


def fetch_github_emails(*, access_token):
    data = _github_get(GITHUB_EMAILS_URL, access_token=access_token, message='GitHub email fetch failed')
    if not isinstance(data, list):
        raise GitHubOAuthError('GitHub email fetch returned an invalid response')
    return data
