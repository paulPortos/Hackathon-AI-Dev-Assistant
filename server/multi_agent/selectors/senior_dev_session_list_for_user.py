from multi_agent.models import SeniorDevSession


def senior_dev_session_list_for_user(user):
    return SeniorDevSession.objects.select_related('project', 'user').filter(user=user)
