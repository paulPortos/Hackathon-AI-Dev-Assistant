from django.core.exceptions import ObjectDoesNotExist

from projects.models import ProjectTask, ProjectVulnerability
from projects.selectors import project_get_agent_context, project_get_for_member
from users.selectors import user_get_by_id


def pm_get_project_context(project_id, current_user_id):
    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    open_tasks = [
        {
            'id': task.id,
            'title': task.title,
            'category': task.category,
            'priority': task.priority,
            'status': task.status,
            'assigned_to_id': task.assigned_to_id,
            'assigned_to_user_id': task.assigned_to.user_id if task.assigned_to else None,
            'due_date': task.due_date.isoformat() if task.due_date else None,
        }
        for task in ProjectTask.objects.select_related('assigned_to').filter(project=project).exclude(
            status__in=[ProjectTask.Status.COMPLETED, ProjectTask.Status.CANCELED]
        )
    ]
    unresolved_vulnerabilities = [
        {
            'id': vulnerability.id,
            'title': vulnerability.title,
            'severity': vulnerability.severity,
            'status': vulnerability.status,
            'category': vulnerability.category,
            'affected_area': vulnerability.affected_area,
            'affected_path': vulnerability.affected_path,
        }
        for vulnerability in ProjectVulnerability.objects.filter(project=project).exclude(
            status__in=[ProjectVulnerability.Status.RESOLVED, ProjectVulnerability.Status.DISMISSED]
        )
    ]

    return {
        'ok': True,
        'project_context': project_get_agent_context(project),
        'open_tasks': open_tasks,
        'unresolved_vulnerabilities': unresolved_vulnerabilities,
    }
