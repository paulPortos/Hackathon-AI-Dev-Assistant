def project_member_delete(*, project_member):
    if project_member.user_id == project_member.project.creator_id:
        raise ValueError('Project creator membership cannot be removed')

    project_member.delete()
