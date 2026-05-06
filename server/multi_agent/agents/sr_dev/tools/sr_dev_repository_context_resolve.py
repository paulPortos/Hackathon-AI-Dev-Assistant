from django.core.exceptions import ObjectDoesNotExist

from projects.selectors import project_get_for_member
from users.selectors import user_get_by_id
from users.services import GitHubTokenError, github_access_token_get_valid


def sr_dev_repository_context_resolve(project_id, current_user_id):
    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return None, None, {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    try:
        return project, github_access_token_get_valid(project.creator), None
    except GitHubTokenError as exc:
        return project, None, {'ok': False, 'code': exc.code, 'detail': str(exc)}
