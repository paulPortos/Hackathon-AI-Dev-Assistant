from django.conf import settings
from django.db import models


class Project(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_projects')
    github_repo_id = models.BigIntegerField()
    github_full_name = models.CharField(max_length=255)
    github_html_url = models.URLField(max_length=500)
    github_clone_url = models.URLField(max_length=500, blank=True)
    github_default_branch = models.CharField(max_length=255, blank=True)
    github_visibility = models.CharField(max_length=32, blank=True)
    github_primary_language = models.CharField(max_length=100, blank=True)
    github_languages = models.JSONField(default=dict, blank=True)
    github_description = models.TextField(blank=True)
    github_is_private = models.BooleanField(default=False)
    overview = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    tech_stack = models.JSONField(default=list, blank=True)
    business_context = models.TextField(blank=True)
    agent_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', 'id']
        constraints = [
            models.UniqueConstraint(fields=['creator', 'github_repo_id'], name='unique_project_creator_github_repo_id'),
        ]

    def __str__(self):
        return self.github_full_name
