from django.core.exceptions import ObjectDoesNotExist

from projects.models import ProjectMember
from projects.selectors import project_get_agent_context, project_get_for_member
from user_descriptions.selectors import user_description_get_agent_context, user_description_get_for_user
from users.selectors import user_get_by_id


def sr_dev_get_context(project_id, current_user_id):
    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
        current_member = ProjectMember.objects.get(project=project, user=current_user)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    try:
        current_user_description = user_description_get_agent_context(user_description_get_for_user(current_user))
    except ObjectDoesNotExist:
        current_user_description = None

    return {
        'ok': True,
        'project_context': project_get_agent_context(project),
        'current_user': {
            'id': current_user.id,
            'username': current_user.username,
            'name': current_user.name,
            'email': current_user.email,
            'avatar_url': current_user.avatar_url,
        },
        'current_user_description': current_user_description,
        'current_user_project_role': {
            'member_id': current_member.id,
            'display_role': current_member.display_role,
            'roles': current_member.roles,
        },
    }
