from django.core.exceptions import ObjectDoesNotExist

from projects.selectors import project_get_for_member, project_meeting_settings_get_for_project
from users.selectors import user_get_by_id


def scrum_get_meeting_settings(project_id, current_user_id):
    try:
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
        'project_id': project.id,
        'meeting_settings': {
            'id': meeting_settings.id,
            'meeting_days': meeting_settings.meeting_days,
            'meeting_time': meeting_settings.meeting_time.isoformat(),
            'timezone': meeting_settings.timezone,
            'google_meet_link': meeting_settings.google_meet_link,
            'weekly_goals': meeting_settings.weekly_goals,
            'monthly_goals': meeting_settings.monthly_goals,
            'alert_minutes_before': meeting_settings.alert_minutes_before,
            'is_active': meeting_settings.is_active,
            'last_reminder_sent_at': meeting_settings.last_reminder_sent_at.isoformat()
            if meeting_settings.last_reminder_sent_at
            else None,
        },
    }
