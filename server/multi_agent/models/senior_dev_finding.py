from django.db import models
from django.db.models import Q


class SeniorDevFinding(models.Model):
    class FindingType(models.TextChoices):
        VULNERABILITY = 'vulnerability', 'Vulnerability'
        GAP = 'gap', 'Gap'
        SCALABILITY = 'scalability', 'Scalability'
        QUESTION = 'question', 'Question'
        OTHER = 'other', 'Other'

    class Severity(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'
        INFO = 'info', 'Info'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        DISMISSED = 'dismissed', 'Dismissed'
        HANDED_OFF = 'handed_off', 'Handed off'

    session = models.ForeignKey('multi_agent.SeniorDevSession', on_delete=models.CASCADE, related_name='findings')
    message = models.ForeignKey('multi_agent.SeniorDevMessage', blank=True, null=True, on_delete=models.SET_NULL, related_name='findings')
    claim = models.ForeignKey('multi_agent.SeniorDevClaim', blank=True, null=True, on_delete=models.SET_NULL, related_name='findings')
    finding_type = models.CharField(max_length=32, choices=FindingType.choices, default=FindingType.OTHER)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=32, choices=Severity.choices, default=Severity.MEDIUM)
    confidence_score = models.PositiveSmallIntegerField(blank=True, null=True)
    confidence_reason = models.TextField(blank=True)
    evidence = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'id']
        constraints = [
            models.CheckConstraint(
                check=Q(confidence_score__isnull=True) | (Q(confidence_score__gte=0) & Q(confidence_score__lte=100)),
                name='senior_dev_finding_confidence_score_0_100',
            ),
        ]

    def __str__(self):
        return self.title
