from django.db import models


class SeniorDevMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        TOOL = 'tool', 'Tool'

    class InputType(models.TextChoices):
        TEXT = 'text', 'Text'
        CHOICE = 'choice', 'Choice'
        OPEN_TEXT = 'open_text', 'Open text'
        AUDIO = 'audio', 'Audio'
        SYSTEM = 'system', 'System'

    session = models.ForeignKey('multi_agent.SeniorDevSession', on_delete=models.CASCADE, related_name='messages')
    source_user_message = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='assistant_responses',
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    input_type = models.CharField(max_length=32, choices=InputType.choices, default=InputType.TEXT)
    text_content = models.TextField(blank=True)
    structured_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['session', 'created_at'], name='multi_agent_session_180039_idx'),
            models.Index(fields=['session', 'role'], name='multi_agent_session_f644dd_idx'),
        ]

    def __str__(self):
        return f'{self.role} message {self.id}'
