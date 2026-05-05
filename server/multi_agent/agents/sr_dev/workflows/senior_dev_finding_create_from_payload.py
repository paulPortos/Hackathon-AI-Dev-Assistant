from multi_agent.models import SeniorDevFinding
from projects.services import project_task_confidence_normalize, project_task_evidence_normalize


def senior_dev_finding_create_from_payload(*, session, message, payload, claim=None):
    if not isinstance(payload, dict):
        payload = {'title': str(payload or '').strip()}

    title = str(payload.get('title') or payload.get('summary') or '').strip()
    if not title:
        return None

    finding_type = str(payload.get('type') or payload.get('finding_type') or SeniorDevFinding.FindingType.OTHER).strip().lower()
    if finding_type not in SeniorDevFinding.FindingType.values:
        finding_type = SeniorDevFinding.FindingType.OTHER

    severity = str(payload.get('severity') or SeniorDevFinding.Severity.MEDIUM).strip().lower()
    if severity not in SeniorDevFinding.Severity.values:
        severity = SeniorDevFinding.Severity.MEDIUM

    status = str(payload.get('status') or SeniorDevFinding.Status.OPEN).strip().lower()
    if status not in SeniorDevFinding.Status.values:
        status = SeniorDevFinding.Status.OPEN

    try:
        confidence_score = project_task_confidence_normalize(payload.get('confidence_score'))
    except ValueError:
        confidence_score = None

    return SeniorDevFinding.objects.create(
        session=session,
        message=message,
        claim=claim,
        finding_type=finding_type,
        title=title,
        category=str(payload.get('category') or '').strip(),
        severity=severity,
        confidence_score=confidence_score,
        confidence_reason=str(payload.get('confidence_reason') or '').strip(),
        evidence=project_task_evidence_normalize(payload.get('evidence')),
        status=status,
    )
