from projects.models import ProjectAuditLog


def project_audit_log_list(project):
    return ProjectAuditLog.objects.select_related('project', 'actor_user').filter(project=project)
