from django.db import models


class ScrumMessage(models.Model):
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

    session = models.ForeignKey('scrum.ScrumSession', on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=32, choices=Role.choices)
    input_type = models.CharField(max_length=32, choices=InputType.choices, default=InputType.TEXT)
    text_content = models.TextField(blank=True)
    structured_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['session', 'created_at'], name='scrum_msg_session_date_idx'),
            models.Index(fields=['session', 'role'], name='scrum_msg_session_role_idx'),
        ]

    def __str__(self):
        return f'Scrum message {self.id} ({self.role})'
