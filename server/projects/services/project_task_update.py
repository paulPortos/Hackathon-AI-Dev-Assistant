def project_task_update(*, project_task, data):
    assigned_to = data.get('assigned_to')
    related_finding = data.get('related_finding')
    if assigned_to and assigned_to.project_id != project_task.project_id:
        raise ValueError('Assigned project member must belong to project')
    if related_finding and related_finding.project_id != project_task.project_id:
        raise ValueError('Related finding must belong to project')

    allowed_fields = {
        'assigned_to',
        'related_finding',
        'title',
        'description',
        'category',
        'priority',
        'status',
        'created_by_agent',
        'reasoning',
        'due_date',
    }
    update_fields = []

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(project_task, field, value)
        update_fields.append(field)

    if update_fields:
        project_task.save(update_fields=[*update_fields, 'updated_at'])

    return project_task
