from datetime import timedelta
from html import escape

from django.utils import timezone

from projects.models import ProjectTask, ProjectVulnerability


def project_meeting_reminder_build_email_message(meeting_settings):
    project = meeting_settings.project
    members = list(project.members.select_related('user').all())
    member_lines = []
    assigned_task_lines = []

    for member in members:
        member_name = member.user.name or member.user.username
        member_lines.append(f'- {member_name} ({member.display_role})')
        member_tasks = ProjectTask.objects.filter(
            project=project,
            assigned_to=member,
        ).exclude(status__in=[ProjectTask.Status.COMPLETED, ProjectTask.Status.CANCELED])
        for task in member_tasks:
            assigned_task_lines.append(f'- {member_name}: [{task.priority}] {task.title} ({task.status})')

    open_task_lines = [
        f'- [{task.priority}] {task.title} ({task.status})'
        for task in ProjectTask.objects.filter(project=project).exclude(
            status__in=[ProjectTask.Status.COMPLETED, ProjectTask.Status.CANCELED]
        )[:20]
    ]
    blocked_task_lines = [
        f'- {task.title}'
        for task in ProjectTask.objects.filter(project=project, status=ProjectTask.Status.BLOCKED)[:20]
    ]
    recent_cutoff = timezone.now() - timedelta(days=7)
    completed_task_lines = [
        f'- {task.title}'
        for task in ProjectTask.objects.filter(
            project=project,
            status=ProjectTask.Status.COMPLETED,
            updated_at__gte=recent_cutoff,
        )[:20]
    ]
    critical_vulnerability_lines = [
        f'- {vulnerability.title}'
        for vulnerability in ProjectVulnerability.objects.filter(
            project=project,
            severity=ProjectVulnerability.Severity.CRITICAL,
        ).exclude(status__in=[ProjectVulnerability.Status.RESOLVED, ProjectVulnerability.Status.DISMISSED])[:20]
    ]

    sections = [
        f'Scrum reminder for {project.github_full_name}',
        '',
        f'Google Meet: {meeting_settings.google_meet_link}',
        '',
        'Weekly goals:',
        meeting_settings.weekly_goals or 'No weekly goals set.',
        '',
        'Monthly goals:',
        meeting_settings.monthly_goals or 'No monthly goals set.',
        '',
        'Project members:',
        '\n'.join(member_lines) or 'No project members found.',
        '',
        'Open tasks:',
        '\n'.join(open_task_lines) or 'No open tasks.',
        '',
        'Assigned tasks per member:',
        '\n'.join(assigned_task_lines) or 'No assigned open tasks.',
        '',
        'Critical vulnerabilities:',
        '\n'.join(critical_vulnerability_lines) or 'No critical vulnerabilities.',
        '',
        'Blocked tasks:',
        '\n'.join(blocked_task_lines) or 'No blocked tasks.',
        '',
        'Recently completed tasks:',
        '\n'.join(completed_task_lines) or 'No recently completed tasks.',
    ]
    text_content = '\n'.join(sections)
    html_content = '<br>'.join(escape(line) for line in text_content.splitlines())

    return {
        'subject': f'Scrum reminder: {project.github_full_name}',
        'text_content': text_content,
        'html_content': html_content,
        'to_emails': [member.user.email for member in members if member.user.email],
    }
