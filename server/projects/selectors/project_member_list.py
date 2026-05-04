from projects.models import ProjectMember


def project_member_list(project):
    return ProjectMember.objects.select_related('project', 'user', 'invited_by').filter(project=project)
