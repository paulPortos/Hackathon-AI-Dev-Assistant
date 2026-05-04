from projects.models import ProjectTask


def project_task_create(*, project, data):
    assigned_to = data.get('assigned_to')
    related_finding = data.get('related_finding')
    if assigned_to and assigned_to.project_id != project.id:
        raise ValueError('Assigned project member must belong to project')
    if related_finding and related_finding.project_id != project.id:
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
    create_data = {field: value for field, value in data.items() if field in allowed_fields}
    return ProjectTask.objects.create(project=project, **create_data)
