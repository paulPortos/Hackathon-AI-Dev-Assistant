from users.github._github_get import _github_get
from users.github.constants import GITHUB_USER_URL
from users.github.github_oauth_error import GitHubOAuthError


def fetch_github_user(*, access_token):
    data = _github_get(GITHUB_USER_URL, access_token=access_token, message='GitHub user fetch failed')
    if not isinstance(data, dict):
        raise GitHubOAuthError('GitHub user fetch returned an invalid response')
    return data
