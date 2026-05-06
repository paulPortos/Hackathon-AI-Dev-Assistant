from pathlib import PurePosixPath

from multi_agent.agents.sr_dev.tools.constants import MAX_TREE_RESULTS
from multi_agent.agents.sr_dev.tools.sr_dev_repository_context_resolve import sr_dev_repository_context_resolve
from multi_agent.agents.sr_dev.tools.sr_dev_sensitive_path_is_blocked import sr_dev_sensitive_path_is_blocked
from projects.providers import GitHubRepositoryError, fetch_github_repository_tree


def sr_dev_list_repository_tree(project_id, current_user_id, commit_sha, path_prefix='', file_extensions=None, max_results=MAX_TREE_RESULTS):
    if not commit_sha:
        return {'ok': False, 'code': 'validation_error', 'detail': 'commit_sha is required'}

    project, access_token, error = sr_dev_repository_context_resolve(project_id, current_user_id)
    if error:
        return error

    try:
        tree_data = fetch_github_repository_tree(
            access_token=access_token,
            repository=project.github_full_name,
            ref=commit_sha,
        )
    except GitHubRepositoryError as exc:
        if exc.status_code == 401:
            return {'ok': False, 'code': 'github_reconnect_required', 'detail': 'GitHub token is invalid or expired'}
        return {'ok': False, 'code': 'github_provider_error', 'detail': str(exc)}

    prefix = str(path_prefix or '').strip().strip('/')
    extensions = None
    if file_extensions:
        extensions = {
            value if str(value).startswith('.') else f'.{value}'
            for value in [str(item).strip().lower() for item in file_extensions]
            if value
        }
    limit = min(max(int(max_results or MAX_TREE_RESULTS), 1), MAX_TREE_RESULTS)
    entries = []
    skipped_sensitive = 0

    for entry in tree_data.get('tree') or []:
        path = str(entry.get('path') or '')
        if not path:
            continue
        if prefix and not path.startswith(prefix):
            continue
        if sr_dev_sensitive_path_is_blocked(path):
            skipped_sensitive += 1
            continue
        if extensions and entry.get('type') == 'blob' and PurePosixPath(path).suffix.lower() not in extensions:
            continue
        entries.append(
            {
                'path': path,
                'type': entry.get('type'),
                'size': entry.get('size'),
            }
        )
        if len(entries) >= limit:
            break

    total_candidates = len(tree_data.get('tree') or [])
    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'commit_sha': commit_sha,
        'path_prefix': prefix,
        'entries': entries,
        'result_count': len(entries),
        'skipped_sensitive_files': skipped_sensitive,
        'truncated': len(entries) >= limit and total_candidates > limit,
    }
