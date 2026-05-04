from projects.models import ProjectTask


def project_task_list(project):
    return ProjectTask.objects.select_related('project', 'assigned_to__user', 'related_finding').filter(project=project)
