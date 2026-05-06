from urllib.parse import quote

from projects.providers.constants import GITHUB_API_VERSION, GITHUB_REPOS_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def fetch_github_repository_commit_status(*, access_token, repository, ref):
    import requests

    response = requests.get(
        f'{GITHUB_REPOS_URL}/{repository}/commits/{quote(str(ref), safe="")}/status',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        timeout=10,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubRepositoryError('GitHub commit status returned an invalid response', status_code=response.status_code) from exc

    if response.status_code == 401:
        raise GitHubRepositoryError('GitHub token is invalid or expired', status_code=response.status_code)
    if response.status_code == 403:
        raise GitHubRepositoryError('GitHub commit status access was denied or rate limited', status_code=response.status_code)
    if response.status_code == 404:
        raise GitHubRepositoryError('GitHub commit status ref was not found', status_code=response.status_code)
    if response.status_code >= 400:
        raise GitHubRepositoryError('GitHub commit status failed', status_code=response.status_code)
    if not isinstance(data, dict):
        raise GitHubRepositoryError('GitHub commit status returned an invalid response', status_code=response.status_code)

    return data
