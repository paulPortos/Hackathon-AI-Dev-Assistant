from django.db import transaction

from projects.models import Project, ProjectMember
from projects.providers import fetch_github_repository, fetch_github_repository_languages
from projects.services.project_update_github_metadata import project_update_github_metadata
from users.services import github_access_token_get_valid


@transaction.atomic
def project_import_from_github(*, creator, repository):
    access_token = github_access_token_get_valid(creator)

    github_repo = fetch_github_repository(access_token=access_token, repository=repository)
    github_languages = fetch_github_repository_languages(access_token=access_token, repository=repository)

    github_repo_id = github_repo.get('id')
    github_full_name = github_repo.get('full_name')
    github_html_url = github_repo.get('html_url')
    if not github_repo_id or not github_full_name or not github_html_url:
        raise ValueError('GitHub repository response did not include required fields')

    metadata = {
        'github_repo_id': github_repo_id,
        'github_full_name': github_full_name,
        'github_html_url': github_html_url,
        'github_clone_url': github_repo.get('clone_url') or '',
        'github_default_branch': github_repo.get('default_branch') or '',
        'github_visibility': github_repo.get('visibility') or ('private' if github_repo.get('private') else 'public'),
        'github_primary_language': github_repo.get('language') or '',
        'github_languages': github_languages,
        'github_description': github_repo.get('description') or '',
        'github_is_private': bool(github_repo.get('private')),
    }

    project, created = Project.objects.select_for_update().get_or_create(
        creator=creator,
        github_repo_id=github_repo_id,
        defaults=metadata,
    )
    if not created:
        project_update_github_metadata(project=project, data=metadata)

    ProjectMember.objects.get_or_create(
        project=project,
        user=creator,
        defaults={'invited_by': creator, 'display_role': 'Owner', 'roles': ['owner']},
    )
    return project
