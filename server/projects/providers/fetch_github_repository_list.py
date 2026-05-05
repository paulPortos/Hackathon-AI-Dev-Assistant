from projects.providers.constants import GITHUB_API_VERSION, GITHUB_USER_REPOS_URL
from projects.providers.github_repository_error import GitHubRepositoryError


def fetch_github_repository_list(*, access_token):
    import requests

    repositories = []
    page = 1
    per_page = 100

    while True:
        response = requests.get(
            GITHUB_USER_REPOS_URL,
            headers={
                'Accept': 'application/vnd.github+json',
                'Authorization': f'Bearer {access_token}',
                'X-GitHub-Api-Version': GITHUB_API_VERSION,
            },
            params={
                'affiliation': 'owner,collaborator,organization_member',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': per_page,
                'page': page,
            },
            timeout=10,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise GitHubRepositoryError('GitHub repository list fetch returned an invalid response') from exc

        if response.status_code == 401:
            raise GitHubRepositoryError('GitHub token is invalid or expired', status_code=response.status_code)
        if response.status_code == 403:
            raise GitHubRepositoryError(
                'GitHub repository list access was denied or rate limited',
                status_code=response.status_code,
            )
        if response.status_code >= 400:
            raise GitHubRepositoryError('GitHub repository list fetch failed', status_code=response.status_code)
        if not isinstance(data, list):
            raise GitHubRepositoryError('GitHub repository list fetch returned an invalid response')

        repositories.extend(data)
        if len(data) < per_page:
            break
        page += 1

    return repositories
