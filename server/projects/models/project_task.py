from django.db import models


class ProjectTask(models.Model):
    class Category(models.TextChoices):
        VULNERABILITY_FIX = 'vulnerability_fix', 'Vulnerability fix'
        FEATURE = 'feature', 'Feature'
        BUG = 'bug', 'Bug'
        REFACTOR = 'refactor', 'Refactor'
        RESEARCH = 'research', 'Research'
        OTHER = 'other', 'Other'

    class Priority(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    class Status(models.TextChoices):
        TODO = 'todo', 'Todo'
        IN_PROGRESS = 'in_progress', 'In progress'
        BLOCKED = 'blocked', 'Blocked'
        COMPLETED = 'completed', 'Completed'
        CANCELED = 'canceled', 'Canceled'

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(
        'projects.ProjectMember',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
    )
    related_finding = models.ForeignKey(
        'projects.ProjectVulnerability',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='tasks',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
    priority = models.CharField(max_length=32, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.TODO)
    created_by_agent = models.CharField(max_length=255, blank=True)
    reasoning = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'id']

    def __str__(self):
        return self.title
