from multi_agent.models import SeniorDevToolCall


def senior_dev_tool_call_summary_for_message(message):
    return [
        {
            'id': tool_call.id,
            'tool_name': tool_call.tool_name,
            'status': tool_call.status,
            'duration_ms': tool_call.duration_ms,
            'error_code': tool_call.error_code,
            'commit_sha': tool_call.commit_sha,
            'safe_input_summary': tool_call.safe_input_summary,
            'safe_result_summary': tool_call.safe_result_summary,
        }
        for tool_call in SeniorDevToolCall.objects.filter(message=message)
    ]
