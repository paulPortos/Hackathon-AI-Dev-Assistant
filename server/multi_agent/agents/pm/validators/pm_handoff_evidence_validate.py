from projects.services import project_task_evidence_normalize


def pm_handoff_evidence_validate(*, evidence, tool_calls, commit_sha):
    def line_matches(evidence_item, result):
        evidence_lines = [
            value
            for value in (evidence_item.get('start_line'), evidence_item.get('end_line'))
            if isinstance(value, int)
        ]
        if not evidence_lines:
            return True
        result_line = result.get('line_number')
        return result_line in evidence_lines

    def snippet_matches(evidence_item, result):
        evidence_snippet = str(evidence_item.get('snippet') or '').strip().lower()
        result_snippet = str(result.get('snippet') or '').strip().lower()
        if not evidence_snippet:
            return True
        if not result_snippet:
            return True
        return evidence_snippet in result_snippet or result_snippet in evidence_snippet

    def code_item_has_tool_proof(evidence_item):
        path = str(evidence_item.get('path') or '').strip()
        if not path:
            return False
        for tool_call in tool_calls:
            if tool_call.status != tool_call.Status.SUCCESS:
                continue
            if tool_call.commit_sha != commit_sha:
                continue
            result_summary = tool_call.safe_result_summary or {}
            if tool_call.tool_name == 'read_file' and result_summary.get('path') == path:
                return True
            if tool_call.tool_name == 'search_code':
                for result in result_summary.get('results') or []:
                    if not isinstance(result, dict) or result.get('path') != path:
                        continue
                    if line_matches(evidence_item, result) and snippet_matches(evidence_item, result):
                        return True
        return False

    normalized_evidence = project_task_evidence_normalize(evidence)
    code_items = [
        item
        for item in normalized_evidence
        if item.get('type') in ('code', 'github_file')
    ]
    proven_code_items = [item for item in code_items if code_item_has_tool_proof(item)]
    invalid_code_items = [item for item in code_items if item not in proven_code_items]
    conversation_items = [
        item
        for item in normalized_evidence
        if item.get('type') in ('conversation', 'project_context')
    ]

    return {
        'evidence': normalized_evidence,
        'has_code_or_file_evidence': bool(code_items),
        'has_valid_code_or_file_evidence': bool(proven_code_items),
        'has_conversation_or_project_context': bool(conversation_items),
        'invalid_code_or_file_evidence': invalid_code_items,
        'validated_code_or_file_evidence': proven_code_items,
    }
