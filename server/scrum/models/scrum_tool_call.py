from django.db import models


class ScrumToolCall(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        ERROR = 'error', 'Error'

    session = models.ForeignKey('scrum.ScrumSession', on_delete=models.CASCADE, related_name='tool_calls')
    message = models.ForeignKey(
        'scrum.ScrumMessage',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='tool_calls',
    )
    tool_name = models.CharField(max_length=100)
    safe_input_summary = models.JSONField(default=dict, blank=True)
    safe_result_summary = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices)
    duration_ms = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['session', 'tool_name'], name='scrum_tool_session_name_idx'),
            models.Index(fields=['session', 'status'], name='scrum_tool_session_status_idx'),
        ]

    def __str__(self):
        return f'Scrum tool call {self.tool_name} ({self.status})'
