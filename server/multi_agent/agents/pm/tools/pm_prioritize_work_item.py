from datetime import date

from django.utils import timezone

from multi_agent.agents.pm.tools.constants import PRIORITY_SCORE


def pm_prioritize_work_item(severity='', business_impact='', scalability_impact='', deadline='', reasoning=''):
    score = PRIORITY_SCORE.get(str(severity or '').strip().lower(), 30)
    reasons = []

    if severity:
        reasons.append(f'Severity is {severity}')

    business_text = str(business_impact or '').strip().lower()
    if any(term in business_text for term in ('critical', 'revenue', 'launch', 'customer', 'blocking')):
        score += 20
        reasons.append('Business impact is high')
    elif any(term in business_text for term in ('medium', 'important', 'workflow')):
        score += 10
        reasons.append('Business impact is moderate')

    scalability_text = str(scalability_impact or '').strip().lower()
    if any(term in scalability_text for term in ('critical', 'high', 'scale', 'performance', 'bottleneck')):
        score += 15
        reasons.append('Scalability impact is meaningful')

    if deadline:
        try:
            due_date = deadline if isinstance(deadline, date) else date.fromisoformat(str(deadline))
            days_until_due = (due_date - timezone.localdate()).days
            if days_until_due <= 2:
                score += 25
                reasons.append('Deadline is urgent')
            elif days_until_due <= 7:
                score += 15
                reasons.append('Deadline is within a week')
        except ValueError:
            reasons.append('Deadline could not be parsed')

    if reasoning:
        reasons.append(str(reasoning).strip())

    if score >= 85:
        priority = 'critical'
    elif score >= 60:
        priority = 'high'
    elif score >= 35:
        priority = 'medium'
    else:
        priority = 'low'

    return {
        'ok': True,
        'priority': priority,
        'score': min(score, 100),
        'reasoning': '; '.join(reason for reason in reasons if reason) or 'Priority inferred from available task context',
    }
