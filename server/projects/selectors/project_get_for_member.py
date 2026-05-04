from projects.models import Project


def project_get_for_member(*, project_id, user):
    return Project.objects.select_related('creator').get(id=project_id, members__user=user)
