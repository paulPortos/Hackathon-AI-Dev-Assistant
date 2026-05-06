from multi_agent.models import SeniorDevFinding


def senior_dev_finding_get_for_session(*, session, finding_id):
    return SeniorDevFinding.objects.get(id=finding_id, session=session)
