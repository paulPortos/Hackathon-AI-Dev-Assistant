from projects.providers.constants import GITHUB_API_VERSION, GITHUB_REPOS_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def fetch_github_repository_content(*, access_token, repository, path, ref):
    import requests

    response = requests.get(
        f'{GITHUB_REPOS_URL}/{repository}/contents/{path}',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        params={'ref': ref},
        timeout=10,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubRepositoryError('GitHub repository content fetch returned an invalid response', status_code=response.status_code) from exc

    if response.status_code == 401:
        raise GitHubRepositoryError('GitHub token is invalid or expired', status_code=response.status_code)
    if response.status_code == 403:
        raise GitHubRepositoryError('GitHub repository content access was denied or rate limited', status_code=response.status_code)
    if response.status_code == 404:
        raise GitHubRepositoryError('GitHub repository file does not exist or is not accessible', status_code=response.status_code)
    if response.status_code >= 400:
        raise GitHubRepositoryError('GitHub repository content fetch failed', status_code=response.status_code)
    if not isinstance(data, dict):
        raise GitHubRepositoryError('GitHub repository content fetch returned an invalid response', status_code=response.status_code)

    return data
