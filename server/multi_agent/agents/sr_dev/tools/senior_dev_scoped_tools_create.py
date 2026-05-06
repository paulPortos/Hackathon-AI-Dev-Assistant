import time

from multi_agent.models import SeniorDevToolCall
from multi_agent.agents.sr_dev.tools.senior_dev_tool_call_create import senior_dev_tool_call_create
from multi_agent.agents.sr_dev.tools.senior_dev_tool_call_safe_summarize import senior_dev_tool_call_safe_summarize
from multi_agent.agents.sr_dev.tools.sr_dev_compare_repository_refs import sr_dev_compare_repository_refs
from multi_agent.agents.sr_dev.tools.sr_dev_find_dependency_manifests import sr_dev_find_dependency_manifests
from multi_agent.agents.sr_dev.tools.sr_dev_get_commit_status import sr_dev_get_commit_status
from multi_agent.agents.sr_dev.tools.sr_dev_get_context import sr_dev_get_context
from multi_agent.agents.sr_dev.tools.sr_dev_list_repository_tree import sr_dev_list_repository_tree
from multi_agent.agents.sr_dev.tools.sr_dev_prepare_pm_handoff import sr_dev_prepare_pm_handoff
from multi_agent.agents.sr_dev.tools.sr_dev_read_repository_file import sr_dev_read_repository_file
from multi_agent.agents.sr_dev.tools.sr_dev_search_repository_code import sr_dev_search_repository_code
from multi_agent.agents.sr_dev.tools.sr_dev_set_repository_ref import sr_dev_set_repository_ref


def senior_dev_scoped_tools_create(*, session, message):
    def record_tool_call(tool_name, input_payload, callback):
        started_at = time.monotonic()
        safe_input = senior_dev_tool_call_safe_summarize(tool_name=tool_name, payload=input_payload)
        try:
            result = callback()
            status = SeniorDevToolCall.Status.SUCCESS if result.get('ok') else SeniorDevToolCall.Status.ERROR
            error_code = result.get('code', '')
            return result
        except Exception as exc:
            result = {'ok': False, 'code': 'tool_error', 'detail': str(exc)}
            status = SeniorDevToolCall.Status.ERROR
            error_code = 'tool_error'
            return result
        finally:
            duration_ms = int((time.monotonic() - started_at) * 1000)
            senior_dev_tool_call_create(
                session=session,
                message=message,
                tool_name=tool_name,
                safe_input_summary=safe_input,
                safe_result_summary=senior_dev_tool_call_safe_summarize(tool_name=tool_name, payload=locals().get('result', {})),
                status=status,
                duration_ms=duration_ms,
                error_code=error_code,
            )

    def get_context():
        """Get project, current user, and project-role context for this Senior Dev review."""
        return record_tool_call(
            'get_context',
            {},
            lambda: sr_dev_get_context(project_id=session.project_id, current_user_id=session.user_id),
        )

    def search_code(query: str, path_prefix: str = '', file_extensions=None):
        """Search code at the selected commit_sha. Returns snippets, not full files."""
        input_payload = {
            'query': query,
            'path_prefix': path_prefix,
            'file_extensions': file_extensions or [],
        }
        return record_tool_call(
            'search_code',
            input_payload,
            lambda: sr_dev_search_repository_code(
                project_id=session.project_id,
                current_user_id=session.user_id,
                commit_sha=session.commit_sha,
                query=query,
                path_prefix=path_prefix,
                file_extensions=file_extensions or [],
            ),
        )

    def set_repository_ref(reference: str):
        """Update the session commit_sha/branch using a branch name, SHA, or 'latest'."""
        input_payload = {'reference': reference}

        def callback():
            result = sr_dev_set_repository_ref(
                project_id=session.project_id,
                current_user_id=session.user_id,
                reference=reference,
            )
            if result.get('ok'):
                session.commit_sha = result.get('commit_sha') or session.commit_sha
                session.branch_name = result.get('branch_name') or ''
                session.save(update_fields=['commit_sha', 'branch_name', 'updated_at'])
            return result

        return record_tool_call('set_repository_ref', input_payload, callback)

    def list_repository_tree(path_prefix: str = '', file_extensions=None, max_results: int = 120):
        """List repository files/directories at the selected commit_sha without reading file contents."""
        input_payload = {
            'path_prefix': path_prefix,
            'file_extensions': file_extensions or [],
            'max_results': max_results,
        }
        return record_tool_call(
            'list_repository_tree',
            input_payload,
            lambda: sr_dev_list_repository_tree(
                project_id=session.project_id,
                current_user_id=session.user_id,
                commit_sha=session.commit_sha,
                path_prefix=path_prefix,
                file_extensions=file_extensions or [],
                max_results=max_results,
            ),
        )

    def compare_repository_refs(base_ref: str, head_ref: str):
        """Compare two GitHub refs and return compact commit/file metadata."""
        input_payload = {'base_ref': base_ref, 'head_ref': head_ref}
        return record_tool_call(
            'compare_repository_refs',
            input_payload,
            lambda: sr_dev_compare_repository_refs(
                project_id=session.project_id,
                current_user_id=session.user_id,
                base_ref=base_ref,
                head_ref=head_ref,
            ),
        )

    def get_commit_status(reference: str = ''):
        """Get combined GitHub commit status for a branch, tag, or commit SHA."""
        ref = reference or session.commit_sha
        return record_tool_call(
            'get_commit_status',
            {'reference': ref},
            lambda: sr_dev_get_commit_status(
                project_id=session.project_id,
                current_user_id=session.user_id,
                reference=ref,
            ),
        )

    def find_dependency_manifests(path_prefix: str = ''):
        """Find dependency and package manifest files at the selected commit_sha."""
        return record_tool_call(
            'find_dependency_manifests',
            {'path_prefix': path_prefix},
            lambda: sr_dev_find_dependency_manifests(
                project_id=session.project_id,
                current_user_id=session.user_id,
                commit_sha=session.commit_sha,
                path_prefix=path_prefix,
            ),
        )

    def read_file(path: str):
        """Read a UTF-8 repository file at the selected commit_sha."""
        return record_tool_call(
            'read_file',
            {'path': path},
            lambda: sr_dev_read_repository_file(
                project_id=session.project_id,
                current_user_id=session.user_id,
                commit_sha=session.commit_sha,
                path=path,
            ),
        )

    def prepare_pm_handoff(conversation_summary: str, findings: list[dict]):
        """Prepare a PM handoff without creating tasks or vulnerabilities.

        Args:
            conversation_summary (str): A detailed summary of the senior dev check-in.
            findings (list[dict]): A list of findings to hand off, each containing 'title' and 'detail'.
        """
        input_payload = {
            'conversation_summary': conversation_summary,
            'finding_count': len(findings or []),
        }
        return record_tool_call(
            'prepare_pm_handoff',
            input_payload,
            lambda: sr_dev_prepare_pm_handoff(
                project_id=session.project_id,
                current_user_id=session.user_id,
                conversation_summary=conversation_summary,
                findings=findings or [],
            ),
        )

    return [
        get_context,
        set_repository_ref,
        list_repository_tree,
        compare_repository_refs,
        get_commit_status,
        find_dependency_manifests,
        search_code,
        read_file,
        prepare_pm_handoff,
    ]
