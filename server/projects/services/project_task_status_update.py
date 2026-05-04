from projects.models import ProjectAuditLog
from projects.services.project_audit_log_create import project_audit_log_create


def project_task_status_update(*, project_task, status, actor_user=None, actor_agent=''):
    previous_status = project_task.status
    project_task.status = status
    project_task.save(update_fields=['status', 'updated_at'])
    if previous_status != project_task.status:
        project_audit_log_create(
            project=project_task.project,
            actor_user=actor_user,
            actor_agent=actor_agent,
            event_type=ProjectAuditLog.EventType.TASK_STATUS_CHANGED,
            target_type=ProjectAuditLog.TargetType.PROJECT_TASK,
            target_id=project_task.id,
            summary=f'Task status changed: {project_task.title}',
            before={'status': previous_status},
            after={'status': project_task.status},
        )
    return project_task
