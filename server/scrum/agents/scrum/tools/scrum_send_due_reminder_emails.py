from django.utils import timezone
from django.utils.dateparse import parse_datetime

from scrum.selectors import project_meeting_settings_due_for_reminder
from scrum.services import project_meeting_reminder_send


def scrum_send_due_reminder_emails(current_datetime=None):
    def normalize_datetime(value):
        if value in (None, ''):
            return None
        if hasattr(value, 'isoformat'):
            return value
        parsed_datetime = parse_datetime(str(value))
        if parsed_datetime and timezone.is_naive(parsed_datetime):
            return timezone.make_aware(parsed_datetime)
        return parsed_datetime

    normalized_datetime = normalize_datetime(current_datetime)
    if current_datetime not in (None, '') and normalized_datetime is None:
        return {
            'ok': False,
            'code': 'validation_error',
            'detail': 'current_datetime must be an ISO 8601 datetime',
        }

    sent = []
    failed = []

    for meeting_settings in project_meeting_settings_due_for_reminder(current_datetime=normalized_datetime):
        try:
            project_meeting_reminder_send(meeting_settings=meeting_settings, current_datetime=normalized_datetime)
            sent.append(
                {
                    'project_id': meeting_settings.project_id,
                    'meeting_settings_id': meeting_settings.id,
                }
            )
        except Exception as exc:
            failed.append(
                {
                    'project_id': meeting_settings.project_id,
                    'meeting_settings_id': meeting_settings.id,
                    'code': 'scrum_email_send_failed',
                    'detail': str(exc),
                }
            )

    return {
        'ok': not failed,
        'sent_count': len(sent),
        'failed_count': len(failed),
        'sent': sent,
        'failed': failed,
    }
