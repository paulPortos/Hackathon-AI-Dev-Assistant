from projects.providers.constants import GITHUB_API_VERSION, GITHUB_SEARCH_CODE_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def search_github_repository_code(*, access_token, repository, query, per_page=30):
    import requests

    response = requests.get(
        GITHUB_SEARCH_CODE_URL,
        headers={
            'Accept': 'application/vnd.github.text-match+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        params={'q': f'{query} repo:{repository}', 'per_page': per_page},
        timeout=10,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubRepositoryError('GitHub code search returned an invalid response', status_code=response.status_code) from exc

    if response.status_code == 401:
        raise GitHubRepositoryError('GitHub token is invalid or expired', status_code=response.status_code)
    if response.status_code == 403:
        raise GitHubRepositoryError('GitHub code search was denied or rate limited', status_code=response.status_code)
    if response.status_code >= 400:
        raise GitHubRepositoryError('GitHub code search failed', status_code=response.status_code)
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise GitHubRepositoryError('GitHub code search returned an invalid response', status_code=response.status_code)

    return data
