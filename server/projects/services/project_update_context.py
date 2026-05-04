def project_update_context(*, project, data):
    allowed_fields = {'overview', 'goals', 'tech_stack', 'business_context', 'agent_notes'}
    update_fields = []

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(project, field, value)
        update_fields.append(field)

    if update_fields:
        project.save(update_fields=[*update_fields, 'updated_at'])

    return project
