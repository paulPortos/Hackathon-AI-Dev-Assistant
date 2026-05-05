import base64
import binascii
from pathlib import PurePosixPath

from django.core.exceptions import ObjectDoesNotExist

from multi_agent.agents.sr_dev.tools.constants import (
    DEFAULT_SEARCH_EXTENSIONS,
    MAX_SEARCH_FILE_BYTES,
    MAX_SEARCH_RESULTS,
    MAX_TREE_FILES_TO_SCAN,
    SEARCH_SNIPPET_CONTEXT_LINES,
    SEARCH_SNIPPET_MAX_CHARS,
)
from projects.providers import (
    GitHubRepositoryError,
    fetch_github_repository_content,
    fetch_github_repository_tree,
    search_github_repository_code,
)
from projects.services import project_repository_branch_list
from projects.selectors import project_get_for_member
from users.selectors import user_get_by_id
from users.services import GitHubTokenError, github_access_token_get_valid


def sr_dev_search_repository_code(project_id, current_user_id, commit_sha, query, path_prefix='', file_extensions=None):
    def error(code, detail):
        return {'ok': False, 'code': code, 'detail': detail}

    def normalize_extensions(values):
        if not values:
            return DEFAULT_SEARCH_EXTENSIONS
        normalized_values = set()
        for value in values:
            value = str(value).strip().lower()
            if not value:
                continue
            normalized_values.add(value if value.startswith('.') else f'.{value}')
        return normalized_values or DEFAULT_SEARCH_EXTENSIONS

    def is_searchable_file(entry, extensions):
        path = entry.get('path') or ''
        if entry.get('type') != 'blob':
            return False
        if entry.get('size', 0) > MAX_SEARCH_FILE_BYTES:
            return False
        if path_prefix and not path.startswith(path_prefix.strip('/')):
            return False
        if PurePosixPath(path).suffix.lower() not in extensions:
            return False
        return True

    def decode_github_file(github_file):
        if github_file.get('type') != 'file' or github_file.get('encoding') != 'base64' or not github_file.get('content'):
            return None
        if github_file.get('size', 0) > MAX_SEARCH_FILE_BYTES:
            return None
        try:
            return base64.b64decode(github_file['content']).decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            return None

    def matched_terms_for_line(line, terms):
        lower_line = line.lower()
        return [term for term in terms if term in lower_line]

    def append_snippets(results, path, content, terms):
        lines = content.splitlines()
        for index, line in enumerate(lines):
            matched_terms = matched_terms_for_line(line, terms)
            if not matched_terms:
                continue

            start = max(index - SEARCH_SNIPPET_CONTEXT_LINES, 0)
            end = min(index + SEARCH_SNIPPET_CONTEXT_LINES + 1, len(lines))
            snippet = '\n'.join(lines[start:end])
            if len(snippet) > SEARCH_SNIPPET_MAX_CHARS:
                snippet = f'{snippet[:SEARCH_SNIPPET_MAX_CHARS]}...'

            results.append(
                {
                    'path': path,
                    'line_number': index + 1,
                    'snippet': snippet,
                    'matched_terms': matched_terms,
                }
            )
            if len(results) >= MAX_SEARCH_RESULTS:
                return True
        return False

    def fetch_and_search_file(access_token, repository, path, terms, results):
        try:
            github_file = fetch_github_repository_content(
                access_token=access_token,
                repository=repository,
                path=path,
                ref=commit_sha,
            )
        except GitHubRepositoryError as exc:
            if exc.status_code == 401:
                raise
            return False

        content = decode_github_file(github_file)
        if content is None:
            return False
        return append_snippets(results, github_file.get('path') or path, content, terms)

    if not commit_sha:
        return error('validation_error', 'commit_sha is required')

    query = str(query or '').strip()
    if not query:
        return error('validation_error', 'query is required')

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return error('not_project_member', 'Current user is not a member of the project or the project does not exist')

    try:
        access_token = github_access_token_get_valid(project.creator)
    except GitHubTokenError as exc:
        return error(exc.code, str(exc))

    terms = [term.lower() for term in query.split() if term.strip()]
    extensions = normalize_extensions(file_extensions)
    results = []
    scanned_files = 0
    skipped_files = 0
    truncated = False
    search_mode = 'tree_scan'

    try:
        branch_context = project_repository_branch_list(project)
        default_branch = next((branch for branch in branch_context['branches'] if branch['is_default']), None)
    except (GitHubTokenError, GitHubRepositoryError, ValueError):
        default_branch = None

    if default_branch and default_branch['commit_sha'] == commit_sha:
        try:
            search_mode = 'github_code_search'
            search_data = search_github_repository_code(
                access_token=access_token,
                repository=project.github_full_name,
                query=query,
                per_page=MAX_TREE_FILES_TO_SCAN,
            )
            for item in search_data['items']:
                path = item.get('path')
                if not path:
                    continue
                if path_prefix and not path.startswith(path_prefix.strip('/')):
                    skipped_files += 1
                    continue
                if PurePosixPath(path).suffix.lower() not in extensions:
                    skipped_files += 1
                    continue
                scanned_files += 1
                if fetch_and_search_file(access_token, project.github_full_name, path, terms, results):
                    truncated = True
                    break
        except GitHubRepositoryError as exc:
            if exc.status_code == 401:
                return error('github_reconnect_required', 'GitHub token is invalid or expired')
            results = []
            scanned_files = 0
            skipped_files = 0
            search_mode = 'tree_scan'

    if search_mode == 'tree_scan':
        try:
            tree_data = fetch_github_repository_tree(
                access_token=access_token,
                repository=project.github_full_name,
                ref=commit_sha,
            )
        except GitHubRepositoryError as exc:
            if exc.status_code == 401:
                return error('github_reconnect_required', 'GitHub token is invalid or expired')
            return error('github_provider_error', str(exc))

        for entry in tree_data['tree']:
            if not is_searchable_file(entry, extensions):
                skipped_files += 1
                continue
            if scanned_files >= MAX_TREE_FILES_TO_SCAN:
                truncated = True
                break

            scanned_files += 1
            if fetch_and_search_file(access_token, project.github_full_name, entry['path'], terms, results):
                truncated = True
                break

    return {
        'ok': True,
        'project_id': project.id,
        'repository': project.github_full_name,
        'commit_sha': commit_sha,
        'query': query,
        'search_mode': search_mode,
        'results': results,
        'result_count': len(results),
        'scanned_files': scanned_files,
        'skipped_files': skipped_files,
        'truncated': truncated,
        'truncation_code': 'search_truncated' if truncated else '',
    }
