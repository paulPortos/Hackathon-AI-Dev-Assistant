from django.conf import settings
from django.db import models


class ProjectMember(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='project_member_invites',
    )
    display_role = models.CharField(max_length=255)
    roles = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member_user'),
        ]

    def __str__(self):
        return f'{self.user.username} in {self.project.github_full_name}'
