from projects.models import ProjectAuditLog
from projects.services.project_audit_log_create import project_audit_log_create


def project_task_delete(*, project_task, actor_user=None, actor_agent=''):
    project = project_task.project
    target_id = project_task.id
    before = {
        'id': project_task.id,
        'title': project_task.title,
        'assigned_to_id': project_task.assigned_to_id,
        'related_finding_id': project_task.related_finding_id,
        'category': project_task.category,
        'priority': project_task.priority,
        'status': project_task.status,
        'due_date': project_task.due_date.isoformat() if project_task.due_date else None,
    }
    summary = f'Task deleted: {project_task.title}'
    project_task.delete()
    project_audit_log_create(
        project=project,
        actor_user=actor_user,
        actor_agent=actor_agent,
        event_type=ProjectAuditLog.EventType.TASK_DELETED,
        target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
        target_id=target_id,
        summary=summary,
        before=before,
    )
