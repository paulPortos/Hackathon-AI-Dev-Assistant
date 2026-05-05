from django.conf import settings
from django.db import models
from django.db.models import Q


class ProjectManagerAgentRun(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'
        FAILED = 'failed', 'Failed'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='project_manager_agent_runs')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='project_manager_agent_runs',
    )
    source_senior_dev_message = models.ForeignKey(
        'multi_agent.SeniorDevMessage',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='project_manager_agent_runs',
    )
    handoff_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.COMPLETED)
    confidence_threshold = models.PositiveSmallIntegerField(default=75)
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    rejected_items = models.JSONField(default=list, blank=True)
    created_vulnerability_ids = models.JSONField(default=list, blank=True)
    created_task_ids = models.JSONField(default=list, blank=True)
    reused_task_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'id']
        constraints = [
            models.CheckConstraint(
                check=Q(confidence_threshold__gte=0) & Q(confidence_threshold__lte=100),
                name='pm_agent_run_confidence_threshold_0_100',
            ),
            models.UniqueConstraint(
                fields=['project', 'handoff_id'],
                condition=~Q(handoff_id=''),
                name='unique_pm_agent_run_project_handoff',
            ),
        ]
        indexes = [
            models.Index(fields=['project', 'status'], name='pm_run_project_status_idx'),
            models.Index(fields=['source_senior_dev_message'], name='pm_run_source_msg_idx'),
        ]

    def __str__(self):
        return f'PM Agent run {self.id}'
