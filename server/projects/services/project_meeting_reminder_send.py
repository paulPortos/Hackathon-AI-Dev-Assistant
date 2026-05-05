from django.utils import timezone

from projects.providers import send_scrum_meeting_email
from projects.services.project_meeting_reminder_build_email_message import project_meeting_reminder_build_email_message


def project_meeting_reminder_send(*, meeting_settings, current_datetime=None):
    message = project_meeting_reminder_build_email_message(meeting_settings, current_datetime=current_datetime)
    if not message['to_emails']:
        raise ValueError('Project has no member emails to notify')

    send_scrum_meeting_email(
        to_emails=message['to_emails'],
        subject=message['subject'],
        text_content=message['text_content'],
        html_content=message['html_content'],
    )
    meeting_settings.last_reminder_sent_at = current_datetime or timezone.now()
    meeting_settings.save(update_fields=['last_reminder_sent_at', 'updated_at'])
    return meeting_settings
