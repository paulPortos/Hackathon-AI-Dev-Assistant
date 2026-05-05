from datetime import timedelta

from django.utils import timezone

from projects.models import ProjectTask, ProjectVulnerability


def project_scrum_summary_build(*, meeting_settings, current_datetime=None):
    def task_payload(task):
        return {
            'id': task.id,
            'title': task.title,
            'category': task.category,
            'priority': task.priority,
            'status': task.status,
            'assigned_to_id': task.assigned_to_id,
            'assigned_to_name': task.assigned_to.user.name if task.assigned_to else '',
            'due_date': task.due_date.isoformat() if task.due_date else None,
        }

    def vulnerability_payload(vulnerability):
        return {
            'id': vulnerability.id,
            'title': vulnerability.title,
            'severity': vulnerability.severity,
            'status': vulnerability.status,
            'category': vulnerability.category,
            'affected_area': vulnerability.affected_area,
            'affected_path': vulnerability.affected_path,
        }

    def sort_key(item):
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        due_date = item.due_date or timezone.localdate() + timedelta(days=3650)
        return priority_order.get(getattr(item, 'priority', getattr(item, 'severity', 'medium')), 2), due_date, item.created_at

    project = meeting_settings.project
    generated_at = current_datetime or timezone.now()
    member_list = list(project.members.select_related('user').all())
    normal_excluded_statuses = [ProjectTask.Status.BLOCKED, ProjectTask.Status.COMPLETED, ProjectTask.Status.CANCELED]
    open_tasks = sorted(
        ProjectTask.objects.select_related('assigned_to__user').filter(project=project).exclude(status__in=normal_excluded_statuses),
        key=sort_key,
    )
    blocked_tasks = sorted(
        ProjectTask.objects.select_related('assigned_to__user').filter(project=project, status=ProjectTask.Status.BLOCKED),
        key=sort_key,
    )
    recent_cutoff = generated_at - timedelta(days=7)
    recently_completed_tasks = sorted(
        ProjectTask.objects.select_related('assigned_to__user').filter(
            project=project,
            status=ProjectTask.Status.COMPLETED,
            updated_at__gte=recent_cutoff,
        ),
        key=sort_key,
    )
    unresolved_vulnerabilities = sorted(
        ProjectVulnerability.objects.filter(project=project).exclude(
            status__in=[ProjectVulnerability.Status.RESOLVED, ProjectVulnerability.Status.DISMISSED]
        ),
        key=lambda vulnerability: ({'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}.get(vulnerability.severity, 2), vulnerability.created_at),
    )

    assigned_tasks_by_member = []
    for member in member_list:
        assigned_tasks_by_member.append(
            {
                'member_id': member.id,
                'user_id': member.user_id,
                'name': member.user.name or member.user.username,
                'email': member.user.email,
                'display_role': member.display_role,
                'tasks': [task_payload(task) for task in open_tasks if task.assigned_to_id == member.id],
            }
        )

    return {
        'project': {
            'id': project.id,
            'github_full_name': project.github_full_name,
        },
        'meeting': {
            'google_meet_link': meeting_settings.google_meet_link,
            'meeting_days': meeting_settings.meeting_days,
            'meeting_time': meeting_settings.meeting_time.isoformat(),
            'timezone': meeting_settings.timezone,
            'alert_minutes_before': meeting_settings.alert_minutes_before,
        },
        'goals': {
            'weekly': meeting_settings.weekly_goals,
            'monthly': meeting_settings.monthly_goals,
        },
        'members': [
            {
                'member_id': member.id,
                'user_id': member.user_id,
                'name': member.user.name or member.user.username,
                'email': member.user.email,
                'display_role': member.display_role,
            }
            for member in member_list
        ],
        'open_tasks': [task_payload(task) for task in open_tasks],
        'assigned_tasks_by_member': assigned_tasks_by_member,
        'blockers': [task_payload(task) for task in blocked_tasks],
        'unresolved_vulnerabilities': [vulnerability_payload(vulnerability) for vulnerability in unresolved_vulnerabilities],
        'recently_completed_tasks': [task_payload(task) for task in recently_completed_tasks],
        'generated_at': generated_at.isoformat(),
    }
