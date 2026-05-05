def project_task_evidence_normalize(evidence):
    allowed_types = {'code', 'github_file', 'conversation', 'vulnerability', 'project_context', 'other'}

    def compact_text(value, max_length=1200):
        text = str(value or '').strip()
        if len(text) > max_length:
            return f'{text[:max_length]}...'
        return text

    def compact_int(value):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def normalize_item(item):
        if not isinstance(item, dict):
            summary = compact_text(item)
            return {'type': 'other', 'summary': summary or 'Evidence item'}

        evidence_type = compact_text(item.get('type')).lower()
        if evidence_type not in allowed_types:
            evidence_type = 'other'

        normalized = {
            'type': evidence_type,
            'summary': compact_text(item.get('summary')),
        }

        for field in ('path', 'snippet', 'url', 'source_tool'):
            value = compact_text(item.get(field))
            if value:
                normalized[field] = value

        start_line = compact_int(item.get('start_line'))
        end_line = compact_int(item.get('end_line'))
        if start_line is not None and start_line > 0:
            normalized['start_line'] = start_line
        if end_line is not None and end_line > 0:
            normalized['end_line'] = end_line

        metadata = item.get('metadata')
        if isinstance(metadata, dict):
            normalized['metadata'] = metadata

        if not normalized['summary']:
            normalized['summary'] = (
                normalized.get('path')
                or normalized.get('url')
                or compact_text(normalized.get('snippet'), max_length=160)
                or 'Evidence item'
            )

        return normalized

    if evidence in (None, ''):
        return []
    if isinstance(evidence, list):
        return [normalize_item(item) for item in evidence]
    return [normalize_item(evidence)]
