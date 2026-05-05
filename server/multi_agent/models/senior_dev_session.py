from django.conf import settings
from django.db import models


class SeniorDevSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='senior_dev_sessions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='senior_dev_sessions')
    commit_sha = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-created_at', 'id']
        indexes = [
            models.Index(fields=['user', 'status'], name='multi_agent_user_id_16489a_idx'),
            models.Index(fields=['project', 'commit_sha'], name='multi_agent_project_b5bcb1_idx'),
        ]

    def __str__(self):
        return f'Sr Dev session {self.id} for {self.project_id}'
