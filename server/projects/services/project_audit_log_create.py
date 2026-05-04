from projects.models import ProjectAuditLog


def project_audit_log_create(*, project, event_type, target_type, target_id, summary='', before=None, after=None, actor_user=None, actor_agent=''):
    return ProjectAuditLog.objects.create(
        project=project,
        actor_user=actor_user,
        actor_agent=actor_agent or '',
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
        before=before or {},
        after=after or {},
    )
