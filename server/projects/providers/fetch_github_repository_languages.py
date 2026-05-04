from projects.providers.constants import GITHUB_API_VERSION, GITHUB_REPOS_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def fetch_github_repository_languages(*, access_token, repository):
    import requests

    response = requests.get(
        f'{GITHUB_REPOS_URL}/{repository}/languages',
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
        raise GitHubRepositoryError('GitHub repository languages fetch returned an invalid response') from exc

    if response.status_code >= 400:
        raise GitHubRepositoryError('GitHub repository languages fetch failed', status_code=response.status_code)
    if not isinstance(data, dict):
        raise GitHubRepositoryError('GitHub repository languages fetch returned an invalid response')

    return data
