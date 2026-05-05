from projects.providers import fetch_github_repository_list
from users.services import github_access_token_get_valid


def project_github_repository_list(user):
    access_token = github_access_token_get_valid(
        user,
        missing_message='GitHub account must be connected before listing repositories',
    )
    repositories = fetch_github_repository_list(access_token=access_token)

    normalized_repositories = []
    for repository in repositories:
        if not isinstance(repository, dict):
            raise ValueError('GitHub repository list fetch returned an invalid response')

        owner = repository.get('owner') or {}
        github_repo_id = repository.get('id')
        name = repository.get('name')
        full_name = repository.get('full_name')
        html_url = repository.get('html_url')
        if not github_repo_id or not name or not full_name or not html_url:
            raise ValueError('GitHub repository list fetch returned an invalid response')

        normalized_repositories.append(
            {
                'github_repo_id': github_repo_id,
                'name': name,
                'full_name': full_name,
                'owner_login': owner.get('login') or '',
                'owner_avatar_url': owner.get('avatar_url') or '',
                'html_url': html_url,
                'clone_url': repository.get('clone_url') or '',
                'default_branch': repository.get('default_branch') or '',
                'visibility': repository.get('visibility')
                or ('private' if repository.get('private') else 'public'),
                'primary_language': repository.get('language') or '',
                'description': repository.get('description') or '',
                'is_private': bool(repository.get('private')),
                'is_fork': bool(repository.get('fork')),
                'is_archived': bool(repository.get('archived')),
                'updated_at': repository.get('updated_at'),
            }
        )

    return normalized_repositories
