from django.db import models


class SeniorDevClaim(models.Model):
    class Status(models.TextChoices):
        UNVERIFIED = 'unverified', 'Unverified'
        VERIFIED = 'verified', 'Verified'
        REFUTED = 'refuted', 'Refuted'
        NEEDS_FOLLOWUP = 'needs_followup', 'Needs follow-up'

    session = models.ForeignKey('multi_agent.SeniorDevSession', on_delete=models.CASCADE, related_name='claims')
    message = models.ForeignKey('multi_agent.SeniorDevMessage', blank=True, null=True, on_delete=models.SET_NULL, related_name='claims')
    text = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.UNVERIFIED)
    evidence = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'id']

    def __str__(self):
        return self.text[:80]
