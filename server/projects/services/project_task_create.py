from projects.models import ProjectAuditLog, ProjectTask
from projects.services.project_audit_log_create import project_audit_log_create


def project_task_create(*, project, data, actor_user=None, actor_agent=''):
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
    project_task = ProjectTask.objects.create(project=project, **create_data)
    project_audit_log_create(
        project=project,
        actor_user=actor_user,
        actor_agent=actor_agent or project_task.created_by_agent,
        event_type=ProjectAuditLog.EventType.TASK_CREATED,
        target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
        target_id=project_task.id,
        summary=f'Task created: {project_task.title}',
        after={
            'id': project_task.id,
            'title': project_task.title,
            'assigned_to_id': project_task.assigned_to_id,
            'related_finding_id': project_task.related_finding_id,
            'category': project_task.category,
            'priority': project_task.priority,
            'status': project_task.status,
            'due_date': project_task.due_date.isoformat() if project_task.due_date else None,
        },
    )
    return project_task
