from django.db import models

class GitHubIssue(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='github_issues')
    github_number = models.IntegerField()
    title = models.CharField(max_length=512)
    body = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=16) # open / closed
    labels = models.JSONField(default=list, blank=True)
    assignees = models.JSONField(default=list, blank=True)
    github_url = models.URLField(max_length=500)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-github_number']
        constraints = [
            models.UniqueConstraint(fields=['project', 'github_number'], name='unique_project_github_issue')
        ]
        indexes = [
            models.Index(fields=['project', 'state']),
        ]

    def __str__(self):
        return f"#{self.github_number}: {self.title}"
