from django.conf import settings
from django.db.models import Q

from multi_agent.models import SeniorDevMessage


def senior_dev_session_memory_context_build(*, session, before_message=None):
    max_messages = int(getattr(settings, 'SR_DEV_SESSION_MEMORY_MAX_MESSAGES', 12))
    max_chars = int(getattr(settings, 'SR_DEV_SESSION_MEMORY_MAX_CHARS', 6000))

    queryset = SeniorDevMessage.objects.filter(session=session)
    if before_message and before_message.id:
        queryset = queryset.filter(
            Q(created_at__lt=before_message.created_at)
            | Q(created_at=before_message.created_at, id__lt=before_message.id)
        )

    messages = list(queryset.order_by('-created_at', '-id')[:max_messages])
    if not messages:
        return 'No prior messages in this Senior Dev session.'

    lines = []
    current_chars = 0
    role_labels = {
        SeniorDevMessage.Role.USER: 'User',
        SeniorDevMessage.Role.ASSISTANT: 'Senior Dev',
        SeniorDevMessage.Role.TOOL: 'Tool',
    }

    for message in reversed(messages):
        text = str(message.text_content or '').strip()
        if not text:
            continue
        if len(text) > 1000:
            text = f'{text[:1000]}...'
        line = f'{role_labels.get(message.role, message.role)}: {text}'
        if current_chars + len(line) > max_chars:
            remaining = max(max_chars - current_chars, 0)
            if remaining > 80:
                lines.append(f'{line[:remaining]}...')
            break
        lines.append(line)
        current_chars += len(line)

    return '\n'.join(lines) or 'No prior messages in this Senior Dev session.'
