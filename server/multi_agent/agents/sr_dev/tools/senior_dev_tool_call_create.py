from multi_agent.models import SeniorDevToolCall


def senior_dev_tool_call_create(*, session, message, tool_name, safe_input_summary, safe_result_summary, status, duration_ms=0, error_code=''):
    return SeniorDevToolCall.objects.create(
        session=session,
        message=message,
        tool_name=tool_name,
        safe_input_summary=safe_input_summary,
        safe_result_summary=safe_result_summary,
        status=status,
        duration_ms=max(int(duration_ms or 0), 0),
        error_code=str(error_code or '').strip(),
        commit_sha=session.commit_sha,
    )
