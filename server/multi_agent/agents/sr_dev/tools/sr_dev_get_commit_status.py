from multi_agent.agents.sr_dev.tools.sr_dev_repository_context_resolve import sr_dev_repository_context_resolve
from projects.providers import GitHubRepositoryError, fetch_github_repository_commit_status


def sr_dev_get_commit_status(project_id, current_user_id, reference):
    reference = str(reference or '').strip()
    if not reference:
        return {'ok': False, 'code': 'validation_error', 'detail': 'reference is required'}

    project, access_token, error = sr_dev_repository_context_resolve(project_id, current_user_id)
    if error:
        return error

    try:
        status_payload = fetch_github_repository_commit_status(
            access_token=access_token,
            repository=project.github_full_name,
            ref=reference,
        )
    except GitHubRepositoryError as exc:
        if exc.status_code == 401:
            return {'ok': False, 'code': 'github_reconnect_required', 'detail': 'GitHub token is invalid or expired'}
        if exc.status_code == 404:
            return {'ok': False, 'code': 'invalid_ref', 'detail': str(exc)}
        return {'ok': False, 'code': 'github_provider_error', 'detail': str(exc)}

    statuses = [
        {
            'context': item.get('context'),
            'state': item.get('state'),
            'description': item.get('description'),
            'target_url': item.get('target_url'),
        }
        for item in (status_payload.get('statuses') or [])[:20]
        if isinstance(item, dict)
    ]
    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'reference': reference,
        'sha': status_payload.get('sha'),
        'state': status_payload.get('state'),
        'total_count': status_payload.get('total_count'),
        'statuses': statuses,
    }
