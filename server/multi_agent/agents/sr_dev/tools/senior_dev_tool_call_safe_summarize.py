def senior_dev_tool_call_safe_summarize(*, tool_name, payload):
    sensitive_keys = {'access_token', 'refresh_token', 'authorization', 'token', 'secret', 'password', 'private_key', 'content'}

    def compact_string(value, max_length=500):
        text = str(value or '')
        if len(text) > max_length:
            return f'{text[:max_length]}...'
        return text

    def scrub(value, depth=0):
        if depth > 3:
            return '...'
        if isinstance(value, dict):
            return {
                str(key): scrub(item, depth + 1)
                for key, item in value.items()
                if str(key).lower() not in sensitive_keys
            }
        if isinstance(value, list):
            return [scrub(item, depth + 1) for item in value[:5]]
        if isinstance(value, str):
            return compact_string(value)
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        return compact_string(value)

    payload = payload or {}
    if tool_name == 'read_file':
        return {
            'ok': payload.get('ok'),
            'code': payload.get('code', ''),
            'path': payload.get('path') or payload.get('detail', ''),
            'size': payload.get('size'),
            'line_count': payload.get('line_count'),
            'commit_sha': payload.get('commit_sha'),
        }
    if tool_name == 'search_code':
        return {
            'ok': payload.get('ok'),
            'code': payload.get('code', ''),
            'query': payload.get('query'),
            'result_count': payload.get('result_count'),
            'scanned_files': payload.get('scanned_files'),
            'truncated': payload.get('truncated'),
            'results': [
                {
                    'path': item.get('path'),
                    'line_number': item.get('line_number'),
                    'snippet': compact_string(item.get('snippet'), max_length=260),
                }
                for item in payload.get('results', [])[:5]
                if isinstance(item, dict)
            ],
        }
    if tool_name == 'get_context':
        project_context = payload.get('project_context') or {}
        project = project_context.get('project') or {}
        return {
            'ok': payload.get('ok'),
            'code': payload.get('code', ''),
            'project_id': project.get('id'),
            'github_full_name': project.get('github_full_name'),
            'member_count': len(project_context.get('members') or []),
        }
    if tool_name == 'prepare_pm_handoff':
        return {
            'ok': payload.get('ok'),
            'code': payload.get('code', ''),
            'handoff_id': payload.get('handoff_id'),
            'finding_count': len(payload.get('findings') or []),
        }
    return scrub(payload)
