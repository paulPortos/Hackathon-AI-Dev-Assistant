from django.conf import settings
from django.db import models


class UserDescription(models.Model):
    class PrimaryRole(models.TextChoices):
        FRONTEND = 'frontend', 'Frontend'
        BACKEND = 'backend', 'Backend'
        FULLSTACK = 'fullstack', 'Fullstack'
        MOBILE = 'mobile', 'Mobile'
        DEVOPS = 'devops', 'DevOps'
        QA = 'qa', 'QA'
        SECURITY = 'security', 'Security'
        AI_DATA = 'ai_data', 'AI/Data'
        PRODUCT_PM = 'product_pm', 'Product/PM'
        DESIGN = 'design', 'Design'
        NON_TECHNICAL = 'non_technical', 'Non-technical'
        OTHER = 'other', 'Other'

    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        JUNIOR = 'junior', 'Junior'
        MID = 'mid', 'Mid'
        SENIOR = 'senior', 'Senior'
        LEAD = 'lead', 'Lead'
        NON_TECHNICAL = 'non_technical', 'Non-technical'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='description')
    primary_role = models.CharField(max_length=32, choices=PrimaryRole.choices, default=PrimaryRole.OTHER)
    experience_level = models.CharField(max_length=32, choices=ExperienceLevel.choices, default=ExperienceLevel.BEGINNER)
    summary = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    preferred_tasks = models.JSONField(default=list, blank=True)
    avoided_tasks = models.JSONField(default=list, blank=True)
    availability_notes = models.TextField(blank=True)
    agent_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.user.username} description'
