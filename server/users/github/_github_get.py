from users.github._parse_response import _parse_response
from users.github.constants import GITHUB_API_VERSION


def _github_get(url, *, access_token, message):
    import requests

    response = requests.get(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        timeout=10,
    )
    return _parse_response(response, message)
