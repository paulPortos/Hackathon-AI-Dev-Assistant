from projects.models import Project


def project_list_for_user(user):
    return Project.objects.select_related('creator').filter(members__user=user).distinct()
