from pathlib import PurePosixPath

from multi_agent.agents.sr_dev.tools.constants import DEPENDENCY_MANIFEST_FILENAMES
from multi_agent.agents.sr_dev.tools.sr_dev_repository_context_resolve import sr_dev_repository_context_resolve
from multi_agent.agents.sr_dev.tools.sr_dev_sensitive_path_is_blocked import sr_dev_sensitive_path_is_blocked
from projects.providers import GitHubRepositoryError, fetch_github_repository_tree


def sr_dev_find_dependency_manifests(project_id, current_user_id, commit_sha, path_prefix=''):
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
    manifests = []
    for entry in tree_data.get('tree') or []:
        path = str(entry.get('path') or '')
        if entry.get('type') != 'blob' or not path:
            continue
        if prefix and not path.startswith(prefix):
            continue
        if sr_dev_sensitive_path_is_blocked(path):
            continue
        filename = PurePosixPath(path).name
        if filename not in DEPENDENCY_MANIFEST_FILENAMES:
            continue
        manifests.append(
            {
                'path': path,
                'filename': filename,
                'size': entry.get('size'),
            }
        )

    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'commit_sha': commit_sha,
        'path_prefix': prefix,
        'manifests': manifests,
        'manifest_count': len(manifests),
    }
