from multi_agent.models import SeniorDevClaim


def senior_dev_claim_create_from_payload(*, session, message, payload):
    if not isinstance(payload, dict):
        payload = {'text': str(payload or '').strip()}

    text = str(payload.get('text') or payload.get('claim') or '').strip()
    if not text:
        return None

    status = str(payload.get('status') or SeniorDevClaim.Status.UNVERIFIED).strip().lower()
    if status not in SeniorDevClaim.Status.values:
        status = SeniorDevClaim.Status.UNVERIFIED

    evidence = payload.get('evidence') or []
    if isinstance(evidence, dict):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = [{'type': 'other', 'summary': str(evidence)}]

    return SeniorDevClaim.objects.create(
        session=session,
        message=message,
        text=text,
        category=str(payload.get('category') or '').strip(),
        status=status,
        evidence=evidence,
    )
