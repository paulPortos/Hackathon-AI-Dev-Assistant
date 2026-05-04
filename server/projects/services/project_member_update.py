def project_member_update(*, project_member, data):
    allowed_fields = {'display_role', 'roles'}
    update_fields = []

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(project_member, field, value)
        update_fields.append(field)

    if update_fields:
        project_member.save(update_fields=[*update_fields, 'updated_at'])

    return project_member
