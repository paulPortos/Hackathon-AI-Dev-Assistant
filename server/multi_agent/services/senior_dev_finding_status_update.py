from multi_agent.models import SeniorDevFinding


def senior_dev_finding_status_update(*, finding, status):
    if status not in SeniorDevFinding.Status.values:
        raise ValueError('Invalid finding status')
    finding.status = status
    finding.save(update_fields=['status', 'updated_at'])
    return finding
