from django.conf import settings
from django.db import models


class ProjectAuditLog(models.Model):
    class EventType(models.TextChoices):
        TASK_CREATED = 'task_created', 'Task created'
        TASK_ASSIGNED = 'task_assigned', 'Task assigned'
        TASK_REASSIGNED = 'task_reassigned', 'Task reassigned'
        TASK_UPDATED = 'task_updated', 'Task updated'
        TASK_PRIORITY_CHANGED = 'task_priority_changed', 'Task priority changed'
        TASK_STATUS_CHANGED = 'task_status_changed', 'Task status changed'
        TASK_DUE_DATE_CHANGED = 'task_due_date_changed', 'Task due date changed'
        TASK_DELETED = 'task_deleted', 'Task deleted'
        VULNERABILITY_RESOLVED = 'vulnerability_resolved', 'Vulnerability resolved'

    class TargetType(models.TextChoices):
        PROJECT_TASK = 'project_task', 'Project task'
        PROJECT_VULNERABILITY = 'project_vulnerability', 'Project vulnerability'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='audit_logs')
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='project_audit_logs',
    )
    actor_agent = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=64, choices=EventType.choices)
    target_type = models.CharField(max_length=64, choices=TargetType.choices)
    target_id = models.PositiveBigIntegerField()
    summary = models.TextField(blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'id']

    def __str__(self):
        return f'{self.event_type} on {self.target_type}:{self.target_id}'
