from projects.models import ProjectMember


def project_member_invite(*, project, user, invited_by, display_role, roles):
    if ProjectMember.objects.filter(project=project, user=user).exists():
        raise ValueError('User is already a project member')

    return ProjectMember.objects.create(
        project=project,
        user=user,
        invited_by=invited_by,
        display_role=display_role,
        roles=roles,
    )
