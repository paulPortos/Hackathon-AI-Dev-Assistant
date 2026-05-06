import base64
import binascii

from django.core.exceptions import ObjectDoesNotExist

from multi_agent.agents.sr_dev.tools.constants import MAX_READ_FILE_BYTES
from multi_agent.agents.sr_dev.tools.sr_dev_sensitive_path_is_blocked import sr_dev_sensitive_path_is_blocked
from multi_agent.agents.sr_dev.tools.sr_dev_sensitive_text_redact import sr_dev_sensitive_text_redact
from projects.providers import GitHubRepositoryError, fetch_github_repository_content
from projects.selectors import project_get_for_member
from users.selectors import user_get_by_id
from users.services import GitHubTokenError, github_access_token_get_valid


def sr_dev_read_repository_file(project_id, current_user_id, commit_sha, path):
    if not commit_sha:
        return {'ok': False, 'code': 'validation_error', 'detail': 'commit_sha is required'}
    if not path or path.startswith('/') or '..' in path.split('/'):
        return {'ok': False, 'code': 'validation_error', 'detail': 'path must be a relative repository file path'}
    if sr_dev_sensitive_path_is_blocked(path):
        return {'ok': False, 'code': 'sensitive_file_blocked', 'detail': 'Sensitive repository files cannot be read by the agent'}

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    try:
        access_token = github_access_token_get_valid(project.creator)
        github_file = fetch_github_repository_content(
            access_token=access_token,
            repository=project.github_full_name,
            path=path,
            ref=commit_sha,
        )
    except GitHubTokenError as exc:
        return {'ok': False, 'code': exc.code, 'detail': str(exc)}
    except GitHubRepositoryError as exc:
        if exc.status_code == 404:
            return {'ok': False, 'code': 'file_not_found', 'detail': str(exc)}
        if exc.status_code == 401:
            return {'ok': False, 'code': 'github_reconnect_required', 'detail': 'GitHub token is invalid or expired'}
        return {'ok': False, 'code': 'github_provider_error', 'detail': str(exc)}

    if github_file.get('type') != 'file' or github_file.get('encoding') != 'base64' or not github_file.get('content'):
        return {'ok': False, 'code': 'file_not_found', 'detail': 'Repository path is not a readable file'}
    if github_file.get('size', 0) > MAX_READ_FILE_BYTES:
        return {
            'ok': False,
            'code': 'file_too_large',
            'detail': f'File is larger than {MAX_READ_FILE_BYTES} bytes',
        }

    try:
        content = base64.b64decode(github_file['content']).decode('utf-8')
    except (binascii.Error, UnicodeDecodeError):
        return {'ok': False, 'code': 'unsupported_file', 'detail': 'File content is not UTF-8 text'}
    content, sensitive_content_redacted = sr_dev_sensitive_text_redact(content)

    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'commit_sha': commit_sha,
        'path': github_file.get('path') or path,
        'size': github_file.get('size', len(content.encode())),
        'line_count': len(content.splitlines()),
        'sensitive_content_redacted': sensitive_content_redacted,
        'content': content,
    }
