def project_task_confidence_normalize(value):
    if value in (None, ''):
        return None

    try:
        confidence_score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Task confidence_score must be an integer from 0 to 100') from exc

    if confidence_score < 0 or confidence_score > 100:
        raise ValueError('Task confidence_score must be from 0 to 100')

    return confidence_score
