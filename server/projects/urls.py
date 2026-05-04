from django.urls import path

from projects.views import (
    ProjectAuditLogListView,
    ProjectDetailView,
    ProjectImportFromGitHubView,
    ProjectListView,
    ProjectMeetingSettingsView,
    ProjectMemberDetailView,
    ProjectMemberListView,
    ProjectRepositoryBranchListView,
    ProjectTaskDetailView,
    ProjectTaskListView,
    ProjectVulnerabilityDetailView,
    ProjectVulnerabilityListView,
)


app_name = 'projects'

urlpatterns = [
    path(
        '',
        ProjectListView.as_view(),
        name='project-list'
    ),
    path(
        'import-from-github/',
        ProjectImportFromGitHubView.as_view(),
        name='project-import-from-github'
    ),
    path(
        '<int:project_id>/',
        ProjectDetailView.as_view(),
        name='project-detail'
    ),
    path(
        '<int:project_id>/audit-logs/',
        ProjectAuditLogListView.as_view(),
        name='project-audit-log-list'
    ),
    path(
        '<int:project_id>/meeting-settings/',
        ProjectMeetingSettingsView.as_view(),
        name='project-meeting-settings-detail'
    ),
    path(
        '<int:project_id>/members/',
        ProjectMemberListView.as_view(),
        name='project-member-list'
    ),
    path(
        '<int:project_id>/members/<int:member_id>/',
        ProjectMemberDetailView.as_view(),
        name='project-member-detail'
    ),
    path(
        '<int:project_id>/repository/branches/',
        ProjectRepositoryBranchListView.as_view(),
        name='project-repository-branch-list'
    ),
    path(
        '<int:project_id>/tasks/',
        ProjectTaskListView.as_view(),
        name='project-task-list'
    ),
    path(
        '<int:project_id>/tasks/<int:task_id>/',
        ProjectTaskDetailView.as_view(),
        name='project-task-detail'
    ),
    path(
        '<int:project_id>/vulnerabilities/',
        ProjectVulnerabilityListView.as_view(),
        name='project-vulnerability-list'
    ),
    path(
        '<int:project_id>/vulnerabilities/<int:vulnerability_id>/',
        ProjectVulnerabilityDetailView.as_view(),
        name='project-vulnerability-detail',
    ),
]
