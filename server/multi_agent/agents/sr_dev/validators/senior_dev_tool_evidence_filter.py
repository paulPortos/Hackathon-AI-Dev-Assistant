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

    def build_tool_evidence():
        def add_item(path, item, evidence_map, seen):
            if not path:
                return
            key = (
                path,
                item.get('start_line'),
                item.get('end_line'),
                item.get('snippet'),
                item.get('summary'),
            )
            if key in seen:
                return
            seen.add(key)
            evidence_map.setdefault(path, []).append(item)

        evidence_map = {}
        seen = set()

        read_file_calls = successful_tool_calls('read_file')
        read_paths = []
        for call in read_file_calls:
            path = (call.get('safe_result_summary') or {}).get('path')
            if path:
                read_paths.append(path)
                add_item(
                    path,
                    {'type': 'code', 'summary': 'Read file via tool', 'path': path},
                    evidence_map,
                    seen,
                )

        search_calls = successful_tool_calls('search_code')
        search_paths = set()
        for call in search_calls:
            for result in (call.get('safe_result_summary') or {}).get('results') or []:
                if not isinstance(result, dict):
                    continue
                path = result.get('path')
                if not path:
                    continue
                search_paths.add(path)
                add_item(
                    path,
                    {
                        'type': 'code',
                        'summary': 'Search match via tool',
                        'path': path,
                        'start_line': result.get('line_number'),
                        'snippet': result.get('snippet'),
                    },
                    evidence_map,
                    seen,
                )

        return {
            'evidence_by_path': evidence_map,
            'read_paths': read_paths,
            'search_paths': search_paths,
            'last_read_path': read_paths[-1] if read_paths else '',
        }

    def finding_has_code_evidence(evidence):
        normalized_evidence = project_task_evidence_normalize(evidence)
        return any(
            item.get('type') in ('code', 'github_file') and item.get('path')
            for item in normalized_evidence
        )

    def normalize_finding_classification(finding):
        if not isinstance(finding, dict):
            return finding
        title = str(finding.get('title') or '').strip().lower()
        category = str(finding.get('category') or '').strip().lower()

        if 'csv response wrapped as json' in title:
            finding['finding_type'] = SeniorDevFinding.FindingType.GAP
            if not category:
                finding['category'] = 'bug'
        return finding

    def attach_tool_evidence(finding, tool_evidence):
        if not isinstance(finding, dict):
            return finding
        if finding_has_code_evidence(finding.get('evidence')):
            return finding

        evidence_by_path = tool_evidence['evidence_by_path']
        read_paths = tool_evidence['read_paths']
        search_paths = tool_evidence['search_paths']
        last_read_path = tool_evidence['last_read_path']

        hinted_paths = []
        for key in ('path', 'affected_path'):
            value = str(finding.get(key) or '').strip()
            if value:
                hinted_paths.append(value)

        for path in hinted_paths:
            if path in evidence_by_path:
                existing = list(finding.get('evidence') or [])
                finding['evidence'] = existing + evidence_by_path[path]
                return finding

        if last_read_path and last_read_path in evidence_by_path:
            existing = list(finding.get('evidence') or [])
            finding['evidence'] = existing + evidence_by_path[last_read_path]
            return finding

        if len(search_paths) == 1:
            path = next(iter(search_paths))
            if path in evidence_by_path:
                existing = list(finding.get('evidence') or [])
                finding['evidence'] = existing + evidence_by_path[path]
        return finding

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
    tool_evidence = build_tool_evidence()
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
        normalized_finding = normalize_finding_classification(dict(finding))
        normalized_finding = attach_tool_evidence(normalized_finding, tool_evidence)
        evidence_validation = evidence_has_valid_code_proof(normalized_finding.get('evidence'))
        if not has_context:
            rejected_findings.append({'finding': normalized_finding, 'reason': 'missing_get_context_tool_call'})
            continue
        if finding_requires_code_proof(normalized_finding) and not evidence_validation['has_valid_code_or_file_evidence']:
            reason = 'missing_code_evidence' if not evidence_validation['has_code_or_file_evidence'] else 'missing_matching_tool_proof'
            rejected_findings.append({'finding': normalized_finding, 'reason': reason, 'evidence_validation': evidence_validation})
            continue
        accepted_findings.append(normalized_finding)

    verification_status['rejected_finding_count'] = len(rejected_findings)
    return {
        'claims': filtered_claims,
        'findings': accepted_findings,
        'rejected_findings': rejected_findings,
        'verification_status': verification_status,
    }
