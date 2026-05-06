from django.core.exceptions import ObjectDoesNotExist

from projects.models import Project
from projects.selectors import project_get_for_member
from scrum.selectors import project_meeting_settings_get_for_project
from scrum.services import project_scrum_summary_build
from users.selectors import user_get_by_id


def scrum_generate_meeting_summary(project_id, current_user_id=None):
    try:
        if current_user_id is None:
            project = Project.objects.get(id=project_id)
        else:
            current_user = user_get_by_id(current_user_id)
            project = project_get_for_member(project_id=project_id, user=current_user)
        meeting_settings = project_meeting_settings_get_for_project(project)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'meeting_settings_not_found',
            'detail': 'Meeting settings do not exist or current user cannot access this project',
        }

    return {
        'ok': True,
        'summary': project_scrum_summary_build(meeting_settings=meeting_settings),
    }
