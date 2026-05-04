from projects.models import ProjectTask


def project_task_get_for_project(*, project, task_id):
    return ProjectTask.objects.select_related('project', 'assigned_to__user', 'related_finding').get(project=project, id=task_id)
