import re


def sr_dev_sensitive_text_redact(text):
    value = str(text or '')
    redacted = False

    key_value_patterns = [
        r'(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASS|PRIVATE_KEY|API_KEY|ACCESS_KEY|CLIENT_SECRET)[A-Z0-9_]*)\s*[:=]\s*([^\s#,\]}]+)',
        r'(?i)\b(authorization)\s*[:=]\s*(bearer\s+)?([A-Za-z0-9._\-+/=]{12,})',
    ]

    for pattern in key_value_patterns:
        new_value = re.sub(pattern, lambda match: f'{match.group(1)}=[REDACTED]', value, flags=re.DOTALL)
        if new_value != value:
            redacted = True
            value = new_value

    new_value = re.sub(
        r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----',
        '[REDACTED_PRIVATE_KEY]',
        value,
        flags=re.DOTALL,
    )
    if new_value != value:
        redacted = True
        value = new_value

    return value, redacted
