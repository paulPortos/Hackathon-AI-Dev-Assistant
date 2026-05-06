from django.db import transaction
from django.utils import timezone

from multi_agent.models import SeniorDevFinding, SeniorDevMessage
from multi_agent.agents.sr_dev.agno import senior_dev_agent_run, senior_dev_parser_run
from multi_agent.agents.sr_dev.tools.senior_dev_scoped_tools_create import senior_dev_scoped_tools_create
from multi_agent.agents.sr_dev.tools.senior_dev_tool_call_summary_for_message import senior_dev_tool_call_summary_for_message
from multi_agent.agents.sr_dev.tools.sr_dev_prepare_pm_handoff import sr_dev_prepare_pm_handoff
from multi_agent.agents.sr_dev.validators import senior_dev_tool_evidence_filter
from multi_agent.agents.sr_dev.workflows.senior_dev_claim_create_from_payload import senior_dev_claim_create_from_payload
from multi_agent.agents.sr_dev.workflows.senior_dev_finding_create_from_payload import senior_dev_finding_create_from_payload
from multi_agent.agents.pm.workflows import project_manager_agent_process_handoff


def senior_dev_message_process(*, session, user, input_type, text='', choice='', choice_payload=None, audio_file=None):
    def resolve_text_and_payload():
        payload = {}
        if input_type == SeniorDevMessage.InputType.AUDIO:
            raise ValueError('audio input is not supported by the Ollama-only agent stack')
        if input_type == SeniorDevMessage.InputType.CHOICE:
            payload['choice_payload'] = choice_payload or {}
            return str(choice or text or '').strip(), payload
        return str(text or '').strip(), payload

    if session.user_id != user.id:
        raise ValueError('Senior Dev session does not belong to current user')

    message_text, structured_payload = resolve_text_and_payload()
    if not message_text:
        raise ValueError('message text is required')

    with transaction.atomic():
        user_message = SeniorDevMessage.objects.create(
            session=session,
            role=SeniorDevMessage.Role.USER,
            input_type=input_type,
            text_content=message_text,
            structured_payload=structured_payload,
        )

    tools = senior_dev_scoped_tools_create(session=session, message=user_message)
    agent_error = None
    try:
        assistant_text = senior_dev_agent_run(session=session, user_message=user_message, tools=tools)
    except Exception as exc:
        assistant_text = (
            'I could not complete the repository review because the Senior Dev agent provider failed '
            'or was temporarily unavailable. Please try again in a moment.'
        )
        agent_error = {'code': 'agent_error', 'detail': str(exc)}
    if not assistant_text:
        assistant_text = 'I reviewed your message, but I need one more detail before I can verify it against the repository.'

    tool_call_summary = senior_dev_tool_call_summary_for_message(user_message)
    if agent_error:
        parser_payload = {
            'assistant_message': assistant_text,
            'check_in_question': '',
            'choices': [],
            'allow_free_text': True,
            'conversation_summary': assistant_text,
            'claims': [],
            'findings': [],
            'parser_error': '',
        }
    else:
        try:
            parser_payload = senior_dev_parser_run(
                session=session,
                user_message=user_message,
                assistant_text=assistant_text,
                tool_call_summary=tool_call_summary,
            )
        except Exception as exc:
            parser_payload = {
                'assistant_message': assistant_text,
                'check_in_question': '',
                'choices': [],
                'allow_free_text': True,
                'conversation_summary': assistant_text,
                'claims': [],
                'findings': [],
                'parser_error': str(exc),
            }

    assistant_text = str(parser_payload.get('assistant_message') or assistant_text).strip()
    verification_payload = senior_dev_tool_evidence_filter(
        parser_payload=parser_payload,
        tool_call_summary=tool_call_summary,
        commit_sha=session.commit_sha,
    )
    claims_payload = verification_payload['claims']
    findings_payload = [] if agent_error else verification_payload['findings']
    rejected_findings = verification_payload['rejected_findings']
    verification_status = verification_payload['verification_status']
    handoff = None
    if findings_payload and not agent_error:
        handoff = sr_dev_prepare_pm_handoff(
            project_id=session.project_id,
            current_user_id=session.user_id,
            conversation_summary=parser_payload.get('conversation_summary') or assistant_text,
            findings=findings_payload,
        )

    with transaction.atomic():
        assistant_message = SeniorDevMessage.objects.create(
            session=session,
            source_user_message=user_message,
            role=SeniorDevMessage.Role.ASSISTANT,
            input_type=SeniorDevMessage.InputType.TEXT,
            text_content=assistant_text,
            structured_payload={
                'check_in_question': parser_payload.get('check_in_question') or '',
                'choices': parser_payload.get('choices') or [],
                'allow_free_text': bool(parser_payload.get('allow_free_text', True)),
                'claims': claims_payload,
                'findings': findings_payload,
                'rejected_findings': rejected_findings,
                'verification_status': verification_status,
                'handoff': handoff,
                'pm_handoff_result': None,
                'agent_error': agent_error or {},
                'tool_call_summary': tool_call_summary,
                'parser_error': parser_payload.get('parser_error', ''),
            },
        )
        claims = [
            claim
            for claim in [
                senior_dev_claim_create_from_payload(session=session, message=user_message, payload=claim_payload)
                for claim_payload in claims_payload
            ]
            if claim is not None
        ]
        findings = [
            finding
            for finding in [
                senior_dev_finding_create_from_payload(
                    session=session,
                    message=assistant_message,
                    payload=finding_payload,
                    claim=claims[finding_payload.get('claim_index')]
                    if isinstance(finding_payload, dict)
                    and isinstance(finding_payload.get('claim_index'), int)
                    and finding_payload.get('claim_index') < len(claims)
                    else None,
                )
                for finding_payload in findings_payload
            ]
            if finding is not None
        ]
        session.save(update_fields=['updated_at'])

    pm_handoff_result = None
    if handoff and findings and not agent_error:
        try:
            pm_handoff_result = project_manager_agent_process_handoff(
                session.project_id,
                session.user_id,
                assistant_message.id,
            )
        except Exception as exc:
            pm_handoff_result = {'ok': False, 'code': 'pm_handoff_error', 'detail': str(exc)}

        if isinstance(pm_handoff_result, dict) and pm_handoff_result.get('ok'):
            SeniorDevFinding.objects.filter(id__in=[finding.id for finding in findings]).update(
                status=SeniorDevFinding.Status.HANDED_OFF,
                updated_at=timezone.now(),
            )
            for finding in findings:
                finding.status = SeniorDevFinding.Status.HANDED_OFF

        structured_payload = dict(assistant_message.structured_payload or {})
        structured_payload['pm_handoff_result'] = pm_handoff_result
        assistant_message.structured_payload = structured_payload
        assistant_message.save(update_fields=['structured_payload'])

    return {
        'ok': True,
        'session_id': session.id,
        'user_message_id': user_message.id,
        'assistant_message_id': assistant_message.id,
        'assistant_message': assistant_text,
        'check_in_question': parser_payload.get('check_in_question') or '',
        'choices': parser_payload.get('choices') or [],
        'allow_free_text': bool(parser_payload.get('allow_free_text', True)),
        'claims': claims_payload,
        'claim_ids': [claim.id for claim in claims],
        'findings': findings_payload,
        'finding_ids': [finding.id for finding in findings],
        'handoff': handoff,
        'pm_handoff_result': pm_handoff_result,
        'agent_error': agent_error or {},
        'rejected_findings': rejected_findings,
        'verification_status': verification_status,
        'tool_call_summary': tool_call_summary,
    }
