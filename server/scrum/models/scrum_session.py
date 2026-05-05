from django.conf import settings
from django.db import models


class ScrumSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='scrum_sessions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scrum_sessions')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-created_at', 'id']
        indexes = [
            models.Index(fields=['user', 'status'], name='scrum_user_status_idx'),
            models.Index(fields=['project', 'status'], name='scrum_project_status_idx'),
        ]

    def __str__(self):
        return f'Scrum session {self.id} for {self.project_id}'
