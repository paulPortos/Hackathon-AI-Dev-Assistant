from html import escape

from scrum.services import project_scrum_summary_build


def project_meeting_reminder_build_email_message(meeting_settings, current_datetime=None):
    summary = project_scrum_summary_build(meeting_settings=meeting_settings, current_datetime=current_datetime)
    project = meeting_settings.project
    member_lines = [f"- {member['name']} ({member['display_role']})" for member in summary['members']]
    assigned_task_lines = [
        f"- {member['name']}: [{task['priority']}] {task['title']} ({task['status']})"
        for member in summary['assigned_tasks_by_member']
        for task in member['tasks']
    ]
    open_task_lines = [f"- [{task['priority']}] {task['title']} ({task['status']})" for task in summary['open_tasks'][:20]]
    blocked_task_lines = [f"- {task['title']}" for task in summary['blockers'][:20]]
    completed_task_lines = [f"- {task['title']}" for task in summary['recently_completed_tasks'][:20]]
    vulnerability_lines = [
        f"- [{vulnerability['severity']}] {vulnerability['title']}"
        for vulnerability in summary['unresolved_vulnerabilities'][:20]
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
        'Unresolved vulnerabilities:',
        '\n'.join(vulnerability_lines) or 'No unresolved vulnerabilities.',
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
        'to_emails': [member['email'] for member in summary['members'] if member['email']],
    }
