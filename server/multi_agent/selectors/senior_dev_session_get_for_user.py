from multi_agent.models import SeniorDevSession


def senior_dev_session_get_for_user(*, session_id, user):
    return SeniorDevSession.objects.select_related('project', 'user').get(id=session_id, user=user)
