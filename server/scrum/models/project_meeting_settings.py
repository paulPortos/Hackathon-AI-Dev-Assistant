from django.db import models


class ProjectMeetingSettings(models.Model):
    project = models.OneToOneField('projects.Project', on_delete=models.CASCADE, related_name='meeting_settings')
    meeting_days = models.JSONField(default=list, blank=True)
    meeting_time = models.TimeField()
    timezone = models.CharField(max_length=100)
    google_meet_link = models.URLField(max_length=500)
    weekly_goals = models.TextField(blank=True)
    monthly_goals = models.TextField(blank=True)
    alert_minutes_before = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    last_reminder_sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        db_table = 'projects_projectmeetingsettings'  # Keep original table name to avoid data loss if any

    def __str__(self):
        return f'{self.project.github_full_name} meeting settings'
