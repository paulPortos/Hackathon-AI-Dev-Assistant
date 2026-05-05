from multi_agent.models import SeniorDevMessage


def senior_dev_message_list(session):
    return SeniorDevMessage.objects.filter(session=session)
