from projects.providers.constants import GITHUB_API_VERSION, GITHUB_REPOS_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def fetch_github_repository_tree(*, access_token, repository, ref):
    import requests

    response = requests.get(
        f'{GITHUB_REPOS_URL}/{repository}/git/trees/{ref}',
        headers={
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
            'X-GitHub-Api-Version': GITHUB_API_VERSION,
        },
        params={'recursive': '1'},
        timeout=10,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubRepositoryError('GitHub repository tree fetch returned an invalid response', status_code=response.status_code) from exc

    if response.status_code == 401:
        raise GitHubRepositoryError('GitHub token is invalid or expired', status_code=response.status_code)
    if response.status_code == 403:
        raise GitHubRepositoryError('GitHub repository tree access was denied or rate limited', status_code=response.status_code)
    if response.status_code == 404:
        raise GitHubRepositoryError('GitHub repository ref does not exist or is not accessible', status_code=response.status_code)
    if response.status_code >= 400:
        raise GitHubRepositoryError('GitHub repository tree fetch failed', status_code=response.status_code)
    if not isinstance(data, dict) or not isinstance(data.get('tree'), list):
        raise GitHubRepositoryError('GitHub repository tree fetch returned an invalid response', status_code=response.status_code)

    return data
