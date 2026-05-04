from projects.models import ProjectMember


def project_member_get_for_project(*, project, member_id):
    return ProjectMember.objects.select_related('project', 'user', 'invited_by').get(project=project, id=member_id)
