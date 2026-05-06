from django.core.exceptions import ObjectDoesNotExist

from projects.providers import GitHubRepositoryError, fetch_github_repository_tree
from projects.services import project_repository_branch_list
from projects.selectors import project_get_for_member
from users.selectors import user_get_by_id
from users.services import GitHubTokenError, github_access_token_get_valid


def sr_dev_set_repository_ref(project_id, current_user_id, reference):
    def error(code, detail):
        return {'ok': False, 'code': code, 'detail': detail}

    ref = str(reference or '').strip()
    if not ref:
        return error('validation_error', 'reference is required')

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return error('not_project_member', 'Current user is not a member of the project or the project does not exist')

    try:
        access_token = github_access_token_get_valid(project.creator)
    except GitHubTokenError as exc:
        return error(exc.code, str(exc))

    try:
        branch_context = project_repository_branch_list(project)
    except (GitHubTokenError, GitHubRepositoryError, ValueError) as exc:
        return error('github_provider_error', str(exc))

    branch_lookup = {
        branch.get('name'): branch.get('commit_sha')
        for branch in branch_context.get('branches') or []
        if isinstance(branch, dict)
    }
    normalized_ref = ref.lower()
    if normalized_ref in {'latest', 'default', 'default_branch'}:
        branch_name = branch_context.get('default_branch') or ''
        commit_sha = branch_lookup.get(branch_name)
        if not commit_sha:
            return error('github_provider_error', 'Default branch commit could not be resolved')
        return {
            'ok': True,
            'project_id': project.id,
            'reference': ref,
            'resolved_type': 'default_branch',
            'commit_sha': commit_sha,
            'branch_name': branch_name,
        }

    if ref in branch_lookup:
        return {
            'ok': True,
            'project_id': project.id,
            'reference': ref,
            'resolved_type': 'branch',
            'commit_sha': branch_lookup[ref],
            'branch_name': ref,
        }

    try:
        fetch_github_repository_tree(
            access_token=access_token,
            repository=project.github_full_name,
            ref=ref,
        )
    except GitHubRepositoryError as exc:
        if exc.status_code == 401:
            return error('github_reconnect_required', 'GitHub token is invalid or expired')
        if exc.status_code == 404:
            return error('invalid_ref', 'Commit SHA or ref was not found')
        return error('github_provider_error', str(exc))

    return {
        'ok': True,
        'project_id': project.id,
        'reference': ref,
        'resolved_type': 'commit',
        'commit_sha': ref,
        'branch_name': '',
    }
