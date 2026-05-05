from multi_agent.models import SeniorDevToolCall


def senior_dev_tool_call_list_for_message(message):
    return SeniorDevToolCall.objects.filter(message=message)
