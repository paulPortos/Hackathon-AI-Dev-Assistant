from multi_agent.models import SeniorDevClaim, SeniorDevFinding, SeniorDevToolCall
from projects.services import project_task_evidence_normalize


def senior_dev_tool_evidence_filter(*, parser_payload, tool_call_summary, commit_sha):
    def successful_tool_calls(tool_name):
        return [
            tool_call
            for tool_call in tool_call_summary
            if isinstance(tool_call, dict)
            and tool_call.get('tool_name') == tool_name
            and tool_call.get('status') == SeniorDevToolCall.Status.SUCCESS
            and (tool_call.get('safe_result_summary') or {}).get('ok') is not False
        ]

    def line_matches(evidence_item, result):
        evidence_lines = [
            value
            for value in (evidence_item.get('start_line'), evidence_item.get('end_line'))
            if isinstance(value, int)
        ]
        if not evidence_lines:
            return True
        return result.get('line_number') in evidence_lines

    def snippet_matches(evidence_item, result):
        evidence_snippet = str(evidence_item.get('snippet') or '').strip().lower()
        result_snippet = str(result.get('snippet') or '').strip().lower()
        if not evidence_snippet or not result_snippet:
            return True
        return evidence_snippet in result_snippet or result_snippet in evidence_snippet

    def code_item_has_tool_proof(evidence_item):
        path = str(evidence_item.get('path') or '').strip()
        if not path:
            return False
        for tool_call in tool_call_summary:
            if not isinstance(tool_call, dict):
                continue
            if tool_call.get('status') != SeniorDevToolCall.Status.SUCCESS:
                continue
            if tool_call.get('commit_sha') != commit_sha:
                continue
            result_summary = tool_call.get('safe_result_summary') or {}
            if tool_call.get('tool_name') == 'read_file' and result_summary.get('path') == path:
                return True
            if tool_call.get('tool_name') == 'search_code':
                for result in result_summary.get('results') or []:
                    if not isinstance(result, dict) or result.get('path') != path:
                        continue
                    if line_matches(evidence_item, result) and snippet_matches(evidence_item, result):
                        return True
        return False

    def evidence_has_valid_code_proof(evidence):
        normalized_evidence = project_task_evidence_normalize(evidence)
        code_items = [
            item
            for item in normalized_evidence
            if item.get('type') in ('code', 'github_file') or item.get('path')
        ]
        proven_items = [item for item in code_items if code_item_has_tool_proof(item)]
        return {
            'evidence': normalized_evidence,
            'has_code_or_file_evidence': bool(code_items),
            'has_valid_code_or_file_evidence': bool(proven_items),
            'validated_code_or_file_evidence': proven_items,
            'invalid_code_or_file_evidence': [item for item in code_items if item not in proven_items],
        }

    def finding_requires_code_proof(finding):
        finding_type = str(finding.get('type') or finding.get('finding_type') or SeniorDevFinding.FindingType.OTHER).strip().lower()
        if finding_type == SeniorDevFinding.FindingType.QUESTION:
            return bool(project_task_evidence_normalize(finding.get('evidence')))
        return finding_type in {
            SeniorDevFinding.FindingType.VULNERABILITY,
            SeniorDevFinding.FindingType.GAP,
            SeniorDevFinding.FindingType.SCALABILITY,
            SeniorDevFinding.FindingType.OTHER,
        }

    claims = parser_payload.get('claims') if isinstance(parser_payload.get('claims'), list) else []
    findings = parser_payload.get('findings') if isinstance(parser_payload.get('findings'), list) else []
    has_context = bool(successful_tool_calls('get_context'))
    verification_status = {
        'has_context_tool_call': has_context,
        'has_code_tool_call': bool(successful_tool_calls('search_code') or successful_tool_calls('read_file')),
        'rejected_finding_count': 0,
        'downgraded_claim_count': 0,
    }

    filtered_claims = []
    for claim in claims:
        if not isinstance(claim, dict):
            filtered_claims.append(claim)
            continue
        normalized_claim = dict(claim)
        status = str(normalized_claim.get('status') or '').strip().lower()
        if status in (SeniorDevClaim.Status.VERIFIED, SeniorDevClaim.Status.REFUTED):
            evidence_validation = evidence_has_valid_code_proof(normalized_claim.get('evidence'))
            if not has_context or not evidence_validation['has_valid_code_or_file_evidence']:
                normalized_claim['status'] = SeniorDevClaim.Status.UNVERIFIED
                normalized_claim['verification_note'] = 'Downgraded because matching repository tool proof was not found.'
                verification_status['downgraded_claim_count'] += 1
        filtered_claims.append(normalized_claim)

    accepted_findings = []
    rejected_findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            rejected_findings.append({'finding': finding, 'reason': 'finding_payload_must_be_object'})
            continue
        evidence_validation = evidence_has_valid_code_proof(finding.get('evidence'))
        if not has_context:
            rejected_findings.append({'finding': finding, 'reason': 'missing_get_context_tool_call'})
            continue
        if finding_requires_code_proof(finding) and not evidence_validation['has_valid_code_or_file_evidence']:
            reason = 'missing_code_evidence' if not evidence_validation['has_code_or_file_evidence'] else 'missing_matching_tool_proof'
            rejected_findings.append({'finding': finding, 'reason': reason, 'evidence_validation': evidence_validation})
            continue
        accepted_findings.append(finding)

    verification_status['rejected_finding_count'] = len(rejected_findings)
    return {
        'claims': filtered_claims,
        'findings': accepted_findings,
        'rejected_findings': rejected_findings,
        'verification_status': verification_status,
    }
