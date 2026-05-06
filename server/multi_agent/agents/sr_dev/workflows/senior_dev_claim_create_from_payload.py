from multi_agent.models import SeniorDevClaim
from projects.services import project_task_evidence_normalize


def senior_dev_claim_create_from_payload(*, session, message, payload):
    if not isinstance(payload, dict):
        payload = {'text': str(payload or '').strip()}

    text = str(payload.get('text') or payload.get('claim') or '').strip()
    if not text:
        return None

    status = str(payload.get('status') or SeniorDevClaim.Status.UNVERIFIED).strip().lower()
    if status not in SeniorDevClaim.Status.values:
        status = SeniorDevClaim.Status.UNVERIFIED

    evidence = project_task_evidence_normalize(payload.get('evidence'))
    if status == SeniorDevClaim.Status.VERIFIED and not evidence:
        status = SeniorDevClaim.Status.UNVERIFIED

    return SeniorDevClaim.objects.create(
        session=session,
        message=message,
        text=text,
        category=str(payload.get('category') or '').strip(),
        status=status,
        evidence=evidence,
    )
