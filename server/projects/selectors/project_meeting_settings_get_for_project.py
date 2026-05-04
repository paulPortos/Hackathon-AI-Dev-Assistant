from projects.models import ProjectMeetingSettings


def project_meeting_settings_get_for_project(project):
    return ProjectMeetingSettings.objects.select_related('project').get(project=project)
