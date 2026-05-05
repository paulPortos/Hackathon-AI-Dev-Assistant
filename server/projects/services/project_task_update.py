from projects.models import ProjectAuditLog
from projects.services.project_audit_log_create import project_audit_log_create


def project_task_update(*, project_task, data, actor_user=None, actor_agent=''):
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
        'confidence_score',
        'confidence_reason',
        'evidence',
        'agent_source_key',
        'due_date',
    }
    update_fields = []
    previous_values = {
        'assigned_to': project_task.assigned_to_id,
        'related_finding': project_task.related_finding_id,
        'title': project_task.title,
        'description': project_task.description,
        'category': project_task.category,
        'priority': project_task.priority,
        'status': project_task.status,
        'created_by_agent': project_task.created_by_agent,
        'reasoning': project_task.reasoning,
        'confidence_score': project_task.confidence_score,
        'confidence_reason': project_task.confidence_reason,
        'evidence': project_task.evidence,
        'agent_source_key': project_task.agent_source_key,
        'due_date': project_task.due_date.isoformat() if project_task.due_date else None,
    }

    for field, value in data.items():
        if field not in allowed_fields:
            continue
        setattr(project_task, field, value)
        update_fields.append(field)

    if update_fields:
        project_task.save(update_fields=[*update_fields, 'updated_at'])
        current_values = {
            'assigned_to': project_task.assigned_to_id,
            'related_finding': project_task.related_finding_id,
            'title': project_task.title,
            'description': project_task.description,
            'category': project_task.category,
            'priority': project_task.priority,
            'status': project_task.status,
            'created_by_agent': project_task.created_by_agent,
            'reasoning': project_task.reasoning,
            'confidence_score': project_task.confidence_score,
            'confidence_reason': project_task.confidence_reason,
            'evidence': project_task.evidence,
            'agent_source_key': project_task.agent_source_key,
            'due_date': project_task.due_date.isoformat() if project_task.due_date else None,
        }
        changed_fields = [field for field in previous_values if previous_values[field] != current_values[field]]

        if 'assigned_to' in changed_fields:
            event_type = ProjectAuditLog.EventType.TASK_ASSIGNED if previous_values['assigned_to'] is None else ProjectAuditLog.EventType.TASK_REASSIGNED
            project_audit_log_create(
                project=project_task.project,
                actor_user=actor_user,
                actor_agent=actor_agent,
                event_type=event_type,
                target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
                target_id=project_task.id,
                summary=f'Task assignment changed: {project_task.title}',
                before={'assigned_to_id': previous_values['assigned_to']},
                after={'assigned_to_id': current_values['assigned_to']},
            )
        if 'priority' in changed_fields:
            project_audit_log_create(
                project=project_task.project,
                actor_user=actor_user,
                actor_agent=actor_agent,
                event_type=ProjectAuditLog.EventType.TASK_PRIORITY_CHANGED,
                target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
                target_id=project_task.id,
                summary=f'Task priority changed: {project_task.title}',
                before={'priority': previous_values['priority']},
                after={'priority': current_values['priority']},
            )
        if 'status' in changed_fields:
            project_audit_log_create(
                project=project_task.project,
                actor_user=actor_user,
                actor_agent=actor_agent,
                event_type=ProjectAuditLog.EventType.TASK_STATUS_CHANGED,
                target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
                target_id=project_task.id,
                summary=f'Task status changed: {project_task.title}',
                before={'status': previous_values['status']},
                after={'status': current_values['status']},
            )
        if 'due_date' in changed_fields:
            project_audit_log_create(
                project=project_task.project,
                actor_user=actor_user,
                actor_agent=actor_agent,
                event_type=ProjectAuditLog.EventType.TASK_DUE_DATE_CHANGED,
                target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
                target_id=project_task.id,
                summary=f'Task due date changed: {project_task.title}',
                before={'due_date': previous_values['due_date']},
                after={'due_date': current_values['due_date']},
            )

        generic_fields = [
            field
            for field in changed_fields
            if field not in {'assigned_to', 'priority', 'status', 'due_date'}
        ]
        if generic_fields:
            project_audit_log_create(
                project=project_task.project,
                actor_user=actor_user,
                actor_agent=actor_agent,
                event_type=ProjectAuditLog.EventType.TASK_UPDATED,
                target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
                target_id=project_task.id,
                summary=f'Task updated: {project_task.title}',
                before={field: previous_values[field] for field in generic_fields},
                after={field: current_values[field] for field in generic_fields},
            )

    return project_task
