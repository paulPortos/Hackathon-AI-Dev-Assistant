from datetime import date

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from multi_agent.agents.pm.agno import project_manager_agent_run
from multi_agent.agents.pm.validators import pm_handoff_evidence_validate
from multi_agent.models import ProjectManagerAgentRun, SeniorDevMessage, SeniorDevToolCall
from multi_agent.agents.pm.tools.constants import PM_AGENT_NAME, TASK_CATEGORY_KEYWORDS
from multi_agent.agents.pm.tools.pm_assign_task_to_best_member import pm_assign_task_to_best_member
from multi_agent.agents.pm.tools.pm_prioritize_work_item import pm_prioritize_work_item
from projects.models import ProjectMember, ProjectTask, ProjectVulnerability
from projects.selectors import project_get_agent_context, project_get_for_member
from projects.services import (
    project_task_confidence_normalize,
    project_task_create_or_get_from_agent,
    project_vulnerability_create,
)
from users.selectors import user_get_by_id


def project_manager_agent_process_handoff(project_id, current_user_id, senior_dev_message_id, handoff_payload=None):
    def error(code, detail):
        return {'ok': False, 'code': code, 'detail': detail}

    def compact_record(record):
        return {key: value for key, value in record.items() if value not in (None, '', [], {})}

    def resolve_index(candidate, key, default_index, source_items):
        value = candidate.get(key, default_index) if isinstance(candidate, dict) else default_index
        try:
            index = int(value)
        except (TypeError, ValueError):
            index = default_index
        if index < 0 or index >= len(source_items):
            return None
        return index

    def merged_candidate(candidate, source_items, source_key, default_index):
        if not isinstance(candidate, dict):
            candidate = {'title': str(candidate or '').strip()}
        source_index = resolve_index(candidate, source_key, default_index, source_items)
        source_item = source_items[source_index] if source_index is not None and isinstance(source_items[source_index], dict) else {}
        return source_index, source_item, {**source_item, **candidate}

    def normalize_confidence(item):
        return project_task_confidence_normalize(item.get('confidence_score', item.get('confidence')))

    def reject(rejected_items, item_type, item, code, detail, source_index=None):
        rejected_items.append(
            compact_record(
                {
                    'type': item_type,
                    'source_index': source_index,
                    'title': item.get('title') if isinstance(item, dict) else '',
                    'code': code,
                    'detail': detail,
                }
            )
        )

    def infer_task_category(task):
        category = str(task.get('category') or '').strip().lower()
        if category in ProjectTask.Category.values:
            return category
        text = ' '.join(str(task.get(field) or '').lower() for field in ('title', 'description', 'reasoning', 'summary'))
        for candidate, keywords in TASK_CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return candidate
        return ProjectTask.Category.OTHER

    def parse_due_date(value):
        if value in (None, ''):
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError('Task due_date must use YYYY-MM-DD format') from exc

    def is_file_missing_finding(item):
        def normalize(value):
            return str(value or '').strip().lower().replace(' ', '').replace('_', '')

        category = normalize(item.get('category'))
        finding_type = normalize(item.get('type') or item.get('finding_type'))
        return category in {'filemissing', 'missingfile'} or finding_type in {'filemissing', 'missingfile'}

    def normalize_vulnerability(candidate, source_item, source_index, source_validations, rejected_items):
        if source_index is None or not source_item:
            reject(rejected_items, 'vulnerability', candidate, 'missing_source_finding', 'Vulnerability must map to a Senior Dev finding', source_index)
            return None

        if is_file_missing_finding(source_item):
            reject(
                rejected_items,
                'vulnerability',
                candidate,
                'non_vulnerability_finding',
                'File-missing findings are informational and do not create vulnerability records',
                source_index,
            )
            return None

        title = str(candidate.get('title') or candidate.get('summary') or '').strip()
        if not title:
            reject(rejected_items, 'vulnerability', candidate, 'invalid_payload', 'Vulnerability title is required', source_index)
            return None
        try:
            confidence_score = normalize_confidence(source_item)
        except ValueError as exc:
            reject(rejected_items, 'vulnerability', candidate, 'invalid_confidence', str(exc), source_index)
            return None
        if confidence_score is None or confidence_score < confidence_threshold:
            reject(rejected_items, 'vulnerability', candidate, 'low_confidence', 'Vulnerability confidence is below threshold', source_index)
            return None
        evidence_validation = source_validations.get(source_index) or pm_handoff_evidence_validate(
            evidence=source_item.get('evidence'),
            tool_calls=tool_calls,
            commit_sha=source_message.session.commit_sha,
        )
        if evidence_validation['invalid_code_or_file_evidence'] or not evidence_validation['has_valid_code_or_file_evidence']:
            reject(rejected_items, 'vulnerability', candidate, 'insufficient_tool_proof', 'Vulnerability requires matching Senior Dev code proof', source_index)
            return None

        severity = str(candidate.get('severity') or ProjectVulnerability.Severity.MEDIUM).strip().lower()
        if severity not in ProjectVulnerability.Severity.values:
            severity = ProjectVulnerability.Severity.MEDIUM
        status = str(candidate.get('status') or ProjectVulnerability.Status.OPEN).strip().lower()
        if status not in ProjectVulnerability.Status.values:
            status = ProjectVulnerability.Status.OPEN

        return {
            'agent_name': PM_AGENT_NAME,
            'source': 'pm_agent_sr_dev_handoff',
            'title': title,
            'summary': str(candidate.get('summary') or candidate.get('description') or '').strip(),
            'severity': severity,
            'status': status,
            'category': str(candidate.get('category') or '').strip(),
            'affected_area': str(candidate.get('affected_area') or '').strip(),
            'affected_path': str(candidate.get('affected_path') or candidate.get('path') or '').strip(),
            'evidence': evidence_validation['evidence'],
            'recommendation': str(candidate.get('recommendation') or '').strip(),
            'confidence_score': confidence_score,
            'confidence_reason': str(source_item.get('confidence_reason') or '').strip(),
        }

    def normalize_task(candidate, source_item, source_index, source_validations, accepted_vulnerabilities_by_index, rejected_items):
        if source_index is None or not source_item:
            reject(rejected_items, 'task', candidate, 'missing_source_finding', 'Task must map to a Senior Dev finding', source_index)
            return None

        title = str(candidate.get('title') or '').strip()
        if not title:
            reject(rejected_items, 'task', candidate, 'invalid_payload', 'Task title is required', source_index)
            return None
        try:
            confidence_score = normalize_confidence(source_item)
        except ValueError as exc:
            reject(rejected_items, 'task', candidate, 'invalid_confidence', str(exc), source_index)
            return None
        if confidence_score is None or confidence_score < confidence_threshold:
            reject(rejected_items, 'task', candidate, 'low_confidence', 'Task confidence is below threshold', source_index)
            return None

        evidence_validation = source_validations.get(source_index) or pm_handoff_evidence_validate(
            evidence=source_item.get('evidence'),
            tool_calls=tool_calls,
            commit_sha=source_message.session.commit_sha,
        )
        category = infer_task_category(candidate)
        if evidence_validation['invalid_code_or_file_evidence']:
            reject(rejected_items, 'task', candidate, 'insufficient_tool_proof', 'Task code evidence does not match Senior Dev proof', source_index)
            return None
        has_supporting_evidence = (
            evidence_validation['has_valid_code_or_file_evidence']
            or evidence_validation['has_conversation_or_project_context']
        )
        related_finding = None
        related_index = candidate.get('related_finding_index', candidate.get('finding_index', source_index))
        if related_index in (None, ''):
            related_index = candidate.get('related_vulnerability_source_index', source_index)
        if related_index not in (None, ''):
            try:
                related_finding = accepted_vulnerabilities_by_index.get(int(related_index))
            except (TypeError, ValueError):
                related_finding = None
        elif category == ProjectTask.Category.VULNERABILITY_FIX and len(accepted_vulnerabilities_by_index) == 1:
            related_finding = next(iter(accepted_vulnerabilities_by_index.values()))

        if category == ProjectTask.Category.VULNERABILITY_FIX and not related_finding and not evidence_validation['has_valid_code_or_file_evidence']:
            reject(rejected_items, 'task', candidate, 'insufficient_tool_proof', 'Vulnerability-fix task requires matching code proof or an accepted vulnerability', source_index)
            return None
        if category != ProjectTask.Category.VULNERABILITY_FIX and not has_supporting_evidence:
            reject(rejected_items, 'task', candidate, 'insufficient_evidence', 'Task requires supporting evidence', source_index)
            return None

        priority_payload = pm_prioritize_work_item(
            severity=candidate.get('severity') or candidate.get('priority') or '',
            business_impact=candidate.get('business_impact') or '',
            scalability_impact=candidate.get('scalability_impact') or '',
            deadline=candidate.get('due_date') or '',
            reasoning=candidate.get('reasoning') or '',
        )
        priority = str(candidate.get('priority') or priority_payload['priority']).strip().lower()
        if priority not in ProjectTask.Priority.values:
            priority = priority_payload['priority']
        status = str(candidate.get('status') or ProjectTask.Status.TODO).strip().lower()
        if status not in ProjectTask.Status.values:
            status = ProjectTask.Status.TODO

        assignment_payload = pm_assign_task_to_best_member(project.id, current_user.id, {**candidate, 'category': category, 'priority': priority})
        if not assignment_payload.get('ok'):
            reject(rejected_items, 'task', candidate, assignment_payload.get('code') or 'assignment_failed', assignment_payload.get('detail') or 'Task assignment failed', source_index)
            return None
        assigned_to = ProjectMember.objects.get(project=project, id=assignment_payload['member']['id'])
        reasoning_parts = [
            str(candidate.get('reasoning') or '').strip(),
            f"Priority: {priority_payload['reasoning']}",
            f"Assignment: {assignment_payload['reasoning']}",
        ]

        return {
            'assigned_to': assigned_to,
            'related_finding': related_finding,
            'title': title,
            'description': str(candidate.get('description') or candidate.get('summary') or '').strip(),
            'category': category,
            'priority': priority,
            'status': status,
            'created_by_agent': PM_AGENT_NAME,
            'reasoning': '\n'.join(part for part in reasoning_parts if part),
            'confidence_score': confidence_score,
            'confidence_reason': str(source_item.get('confidence_reason') or '').strip(),
            'evidence': evidence_validation['evidence'],
            'due_date': parse_due_date(candidate.get('due_date')),
            'source_item_id': candidate.get('source_item_id') or source_item.get('source_item_id') or '',
        }

    if not isinstance(handoff_payload, dict) and handoff_payload is not None:
        return error('validation_error', 'handoff_payload must be an object')

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return error('not_project_member', 'Current user is not a member of the project or the project does not exist')

    try:
        source_message = SeniorDevMessage.objects.select_related('session', 'source_user_message').get(
            id=senior_dev_message_id,
            role=SeniorDevMessage.Role.ASSISTANT,
        )
    except ObjectDoesNotExist:
        return error('not_found', 'Source Senior Dev assistant message was not found')

    if source_message.session.project_id != project.id:
        return error('project_mismatch', 'Source Senior Dev message does not belong to the requested project')

    if handoff_payload is None:
        handoff_payload = (source_message.structured_payload or {}).get('handoff')
    if not isinstance(handoff_payload, dict):
        return error('validation_error', 'Senior Dev handoff payload was not found')
    if not handoff_payload.get('ok'):
        return error('validation_error', 'Senior Dev handoff is not successful')
    if handoff_payload.get('handoff_version') != 'sr_dev_to_pm.v1':
        return error('validation_error', 'Unsupported Senior Dev handoff version')

    handoff_id = str(handoff_payload.get('handoff_id') or '').strip()
    if not handoff_id:
        return error('validation_error', 'Senior Dev handoff_id is required')
    payload_project_id = (handoff_payload.get('project') or {}).get('id')
    try:
        if int(payload_project_id) != project.id:
            return error('project_mismatch', 'Handoff payload project does not match requested project')
    except (TypeError, ValueError):
        return error('project_mismatch', 'Handoff payload project does not match requested project')

    existing_run = ProjectManagerAgentRun.objects.filter(project=project, handoff_id=handoff_id).first()
    if existing_run:
        payload = dict(existing_run.output_payload or {})
        payload['idempotent_replay'] = True
        return payload

    if not source_message.source_user_message_id:
        return error('missing_source_message', 'Senior Dev assistant message is missing its source user message')

    tool_calls = list(
        SeniorDevToolCall.objects.filter(
            session=source_message.session,
            message=source_message.source_user_message,
        )
    )
    if not tool_calls:
        return error('missing_tool_proof', 'Senior Dev tool-call proof rows are required before PM processing')

    findings = handoff_payload.get('findings') or []
    if not isinstance(findings, list):
        return error('validation_error', 'handoff findings must be a list')

    confidence_threshold = settings.PROJECT_MANAGER_CONFIDENCE_THRESHOLD
    finding_validations = {
        index: pm_handoff_evidence_validate(
            evidence=finding.get('evidence') if isinstance(finding, dict) else None,
            tool_calls=tool_calls,
            commit_sha=source_message.session.commit_sha,
        )
        for index, finding in enumerate(findings)
    }
    agent_context = {
        'project_context': project_get_agent_context(project),
        'handoff': handoff_payload,
        'confidence_threshold': confidence_threshold,
        'tool_proof': [
            {
                'tool_name': tool_call.tool_name,
                'status': tool_call.status,
                'commit_sha': tool_call.commit_sha,
                'safe_input_summary': tool_call.safe_input_summary,
                'safe_result_summary': tool_call.safe_result_summary,
            }
            for tool_call in tool_calls
        ],
        'evidence_validation': {
            'findings': finding_validations,
        },
    }

    try:
        agent_payload = project_manager_agent_run(context=agent_context)
    except Exception as exc:
        ProjectManagerAgentRun.objects.create(
            project=project,
            requested_by=current_user,
            source_senior_dev_message=source_message,
            handoff_id=handoff_id,
            status=ProjectManagerAgentRun.Status.FAILED,
            confidence_threshold=confidence_threshold,
            input_payload=handoff_payload,
            output_payload={'ok': False, 'code': 'agent_error', 'detail': str(exc)},
            rejected_items=[],
        )
        return error('agent_error', str(exc))

    if not isinstance(agent_payload, dict):
        return error('agent_error', 'Project Manager Agent returned invalid JSON')

    rejected_items = []
    created_vulnerabilities = []
    accepted_vulnerabilities_by_index = {}
    vulnerability_candidates = agent_payload.get('vulnerabilities') or []
    task_candidates = agent_payload.get('tasks') or []
    if not isinstance(vulnerability_candidates, list) or not isinstance(task_candidates, list):
        return error('agent_error', 'Project Manager Agent output must contain vulnerabilities and tasks lists')

    with transaction.atomic():
        for default_index, candidate in enumerate(vulnerability_candidates):
            source_index, source_item, vulnerability_candidate = merged_candidate(candidate, findings, 'source_finding_index', default_index)
            data = normalize_vulnerability(vulnerability_candidate, source_item, source_index, finding_validations, rejected_items)
            if data is None:
                continue
            vulnerability = project_vulnerability_create(
                project=project,
                data=data,
                actor_user=current_user,
                actor_agent=PM_AGENT_NAME,
            )
            created_vulnerabilities.append(vulnerability)
            if source_index is not None:
                accepted_vulnerabilities_by_index[source_index] = vulnerability

        task_results = []
        for default_index, candidate in enumerate(task_candidates):
            source_index, source_item, task_candidate = merged_candidate(candidate, findings, 'source_finding_index', default_index)
            try:
                data = normalize_task(task_candidate, source_item, source_index, finding_validations, accepted_vulnerabilities_by_index, rejected_items)
            except ValueError as exc:
                reject(rejected_items, 'task', task_candidate, 'validation_error', str(exc), source_index)
                continue
            if data is None:
                continue
            project_task, created = project_task_create_or_get_from_agent(
                project=project,
                data=data,
                handoff_id=handoff_id,
                actor_user=current_user,
                actor_agent=PM_AGENT_NAME,
            )
            task_results.append((project_task, created))

        status = ProjectManagerAgentRun.Status.COMPLETED if created_vulnerabilities or task_results else ProjectManagerAgentRun.Status.REJECTED
        output_payload = {
            'ok': True,
            'handoff_id': handoff_id,
            'project_id': project.id,
            'status': status,
            'created_vulnerabilities': [
                {
                    'id': vulnerability.id,
                    'title': vulnerability.title,
                    'severity': vulnerability.severity,
                    'status': vulnerability.status,
                    'confidence_score': vulnerability.confidence_score,
                }
                for vulnerability in created_vulnerabilities
            ],
            'created_tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'priority': task.priority,
                    'status': task.status,
                    'assigned_to_id': task.assigned_to_id,
                    'related_finding_id': task.related_finding_id,
                    'confidence_score': task.confidence_score,
                }
                for task, created in task_results
                if created
            ],
            'reused_tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'priority': task.priority,
                    'status': task.status,
                    'assigned_to_id': task.assigned_to_id,
                    'related_finding_id': task.related_finding_id,
                    'confidence_score': task.confidence_score,
                }
                for task, created in task_results
                if not created
            ],
            'rejected_items': rejected_items,
            'summary': str(agent_payload.get('summary') or '').strip(),
            'idempotent_replay': False,
        }
        run = ProjectManagerAgentRun.objects.create(
            project=project,
            requested_by=current_user,
            source_senior_dev_message=source_message,
            handoff_id=handoff_id,
            status=status,
            confidence_threshold=confidence_threshold,
            input_payload=handoff_payload,
            output_payload=output_payload,
            rejected_items=rejected_items,
            created_vulnerability_ids=[vulnerability.id for vulnerability in created_vulnerabilities],
            created_task_ids=[task.id for task, created in task_results if created],
            reused_task_ids=[task.id for task, created in task_results if not created],
        )
        output_payload['run_id'] = run.id
        run.output_payload = output_payload
        run.save(update_fields=['output_payload', 'updated_at'])

    return output_payload
