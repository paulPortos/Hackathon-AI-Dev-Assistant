from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from projects.models import ProjectMeetingSettings


def project_meeting_settings_due_for_reminder(*, current_datetime=None):
    now = current_datetime or timezone.now()
    due_settings = []

    for settings in ProjectMeetingSettings.objects.select_related('project').filter(is_active=True):
        local_now = now.astimezone(ZoneInfo(settings.timezone))
        for day_offset in (0, 1):
            meeting_date = local_now.date() + timedelta(days=day_offset)
            meeting_day = meeting_date.strftime('%A').lower()
            if meeting_day not in settings.meeting_days:
                continue

            meeting_at = datetime.combine(meeting_date, settings.meeting_time, tzinfo=ZoneInfo(settings.timezone))
            alert_at = meeting_at - timedelta(minutes=settings.alert_minutes_before)
            if not alert_at <= local_now < meeting_at:
                continue

            last_sent_at = settings.last_reminder_sent_at
            if last_sent_at and last_sent_at.astimezone(ZoneInfo(settings.timezone)) >= alert_at:
                continue

            due_settings.append(settings)
            break

    return due_settings
