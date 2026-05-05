from multi_agent.models import SeniorDevFinding


def senior_dev_finding_list(session):
    return SeniorDevFinding.objects.filter(session=session)
