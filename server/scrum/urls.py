from django.urls import path
from scrum.views import ProjectMeetingSettingsView

app_name = 'scrum'

urlpatterns = [
    path(
        'projects/<int:project_id>/meeting-settings/',
        ProjectMeetingSettingsView.as_view(),
        name='project-meeting-settings-detail'
    ),
]
