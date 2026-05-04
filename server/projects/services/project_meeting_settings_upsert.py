from projects.models import ProjectMeetingSettings


def project_meeting_settings_upsert(*, project, data):
    meeting_settings, _ = ProjectMeetingSettings.objects.get_or_create(project=project, defaults=data)
    update_fields = []

    for field, value in data.items():
        setattr(meeting_settings, field, value)
        update_fields.append(field)

    if update_fields:
        meeting_settings.save(update_fields=[*update_fields, 'updated_at'])

    return meeting_settings
