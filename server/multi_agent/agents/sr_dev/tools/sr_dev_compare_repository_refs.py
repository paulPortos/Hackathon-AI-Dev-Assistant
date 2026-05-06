from multi_agent.agents.sr_dev.tools.constants import MAX_COMPARE_COMMITS, MAX_COMPARE_FILES
from multi_agent.agents.sr_dev.tools.sr_dev_repository_context_resolve import sr_dev_repository_context_resolve
from multi_agent.agents.sr_dev.tools.sr_dev_sensitive_path_is_blocked import sr_dev_sensitive_path_is_blocked
from projects.providers import GitHubRepositoryError, fetch_github_repository_compare


def sr_dev_compare_repository_refs(project_id, current_user_id, base_ref, head_ref):
    base_ref = str(base_ref or '').strip()
    head_ref = str(head_ref or '').strip()
    if not base_ref or not head_ref:
        return {'ok': False, 'code': 'validation_error', 'detail': 'base_ref and head_ref are required'}

    project, access_token, error = sr_dev_repository_context_resolve(project_id, current_user_id)
    if error:
        return error

    try:
        compare = fetch_github_repository_compare(
            access_token=access_token,
            repository=project.github_full_name,
            base_ref=base_ref,
            head_ref=head_ref,
        )
    except GitHubRepositoryError as exc:
        if exc.status_code == 401:
            return {'ok': False, 'code': 'github_reconnect_required', 'detail': 'GitHub token is invalid or expired'}
        if exc.status_code == 404:
            return {'ok': False, 'code': 'invalid_ref', 'detail': str(exc)}
        return {'ok': False, 'code': 'github_provider_error', 'detail': str(exc)}

    files = [
        {
            'filename': file_item.get('filename'),
            'status': file_item.get('status'),
            'additions': file_item.get('additions'),
            'deletions': file_item.get('deletions'),
            'changes': file_item.get('changes'),
        }
        for file_item in (compare.get('files') or [])
        if isinstance(file_item, dict) and not sr_dev_sensitive_path_is_blocked(file_item.get('filename'))
    ][:MAX_COMPARE_FILES]
    commits = [
        {
            'sha': commit.get('sha'),
            'message': ((commit.get('commit') or {}).get('message') or '').split('\n', 1)[0],
            'author_date': (((commit.get('commit') or {}).get('author') or {}).get('date')),
        }
        for commit in (compare.get('commits') or [])[:MAX_COMPARE_COMMITS]
        if isinstance(commit, dict)
    ]

    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'base_ref': base_ref,
        'head_ref': head_ref,
        'status': compare.get('status'),
        'ahead_by': compare.get('ahead_by'),
        'behind_by': compare.get('behind_by'),
        'total_commits': compare.get('total_commits'),
        'commits': commits,
        'files': files,
        'file_count': len(files),
        'truncated_files': len(compare.get('files') or []) > len(files),
        'truncated_commits': len(compare.get('commits') or []) > len(commits),
    }
