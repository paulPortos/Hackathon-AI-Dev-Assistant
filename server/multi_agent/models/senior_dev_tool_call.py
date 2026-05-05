from django.db import models


class SeniorDevToolCall(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        ERROR = 'error', 'Error'

    session = models.ForeignKey('multi_agent.SeniorDevSession', on_delete=models.CASCADE, related_name='tool_calls')
    message = models.ForeignKey('multi_agent.SeniorDevMessage', blank=True, null=True, on_delete=models.SET_NULL, related_name='tool_calls')
    tool_name = models.CharField(max_length=100)
    safe_input_summary = models.JSONField(default=dict, blank=True)
    safe_result_summary = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices)
    duration_ms = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=100, blank=True)
    commit_sha = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['session', 'tool_name'], name='multi_agent_session_6c60fb_idx'),
            models.Index(fields=['session', 'status'], name='multi_agent_session_e8fdce_idx'),
        ]

    def __str__(self):
        return f'{self.tool_name} {self.status}'
