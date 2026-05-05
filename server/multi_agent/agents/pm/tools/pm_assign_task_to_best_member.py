from django.core.exceptions import ObjectDoesNotExist

from multi_agent.agents.pm.tools.constants import ROLE_CATEGORY_KEYWORDS
from projects.models import ProjectTask
from projects.selectors import project_get_agent_context, project_get_for_member
from users.selectors import user_get_by_id


def pm_assign_task_to_best_member(project_id, current_user_id, task_context):
    def terms_from_task():
        if not isinstance(task_context, dict):
            return set()
        raw_text = ' '.join(
            str(task_context.get(field) or '')
            for field in ('title', 'description', 'category', 'affected_area', 'business_impact', 'scalability_impact')
        )
        for value in task_context.get('required_skills') or []:
            raw_text = f'{raw_text} {value}'
        return {term.strip().lower() for term in raw_text.replace('_', ' ').replace('-', ' ').split() if term.strip()}

    def member_text(member_context):
        description = member_context.get('user_description') or {}
        skill_names = [str(skill.get('name') or '') for skill in description.get('skills') or [] if isinstance(skill, dict)]
        return ' '.join(
            [
                str(member_context.get('display_role') or ''),
                ' '.join(str(role) for role in member_context.get('roles') or []),
                str(description.get('primary_role') or ''),
                str(description.get('summary') or ''),
                ' '.join(skill_names),
                str(description.get('agent_notes') or ''),
            ]
        ).lower()

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    if not isinstance(task_context, dict):
        return {'ok': False, 'code': 'validation_error', 'detail': 'task_context must be an object'}

    project_context = project_get_agent_context(project)
    task_terms = terms_from_task()
    category = str(task_context.get('category') or 'other').strip().lower()
    category_terms = ROLE_CATEGORY_KEYWORDS.get(category, ROLE_CATEGORY_KEYWORDS['other'])
    scores = []

    for member_context in project_context['members']:
        text = member_text(member_context)
        description = member_context.get('user_description') or {}
        open_task_count = ProjectTask.objects.filter(project=project, assigned_to_id=member_context['id']).exclude(
            status__in=[ProjectTask.Status.COMPLETED, ProjectTask.Status.CANCELED]
        ).count()
        score = 50
        reasons = []

        matched_category_terms = sorted(term for term in category_terms if term in text)
        if matched_category_terms:
            score += 25
            reasons.append(f'Role fits category via {", ".join(matched_category_terms)}')

        matched_task_terms = sorted(term for term in task_terms if len(term) > 2 and term in text)
        if matched_task_terms:
            score += min(len(matched_task_terms) * 6, 24)
            reasons.append(f'Matches task terms: {", ".join(matched_task_terms[:5])}')

        for skill in description.get('skills') or []:
            if not isinstance(skill, dict):
                continue
            skill_name = str(skill.get('name') or '').lower()
            if skill_name and any(term in skill_name for term in task_terms):
                score += int(skill.get('level') or 1) * 3

        preferred_tasks = ' '.join(str(value).lower() for value in description.get('preferred_tasks') or [])
        avoided_tasks = ' '.join(str(value).lower() for value in description.get('avoided_tasks') or [])
        if category and category in preferred_tasks:
            score += 12
            reasons.append('Category is preferred by member')
        if category and category in avoided_tasks:
            score -= 25
            reasons.append('Category is avoided by member')

        availability_notes = str(description.get('availability_notes') or '').lower()
        if any(term in availability_notes for term in ('unavailable', 'busy', 'vacation', 'weekends only')):
            score -= 10
            reasons.append('Availability notes reduce fit')

        score -= min(open_task_count * 3, 24)
        if open_task_count:
            reasons.append(f'Currently has {open_task_count} open tasks')

        scores.append(
            {
                'member_id': member_context['id'],
                'display_role': member_context['display_role'],
                'score': score,
                'reasoning': '; '.join(reasons) or 'General project member fit',
            }
        )

    if not scores:
        return {'ok': False, 'code': 'no_project_members', 'detail': 'Project has no members to assign'}

    scores.sort(key=lambda item: item['score'], reverse=True)
    best = scores[0]
    return {
        'ok': True,
        'member': {
            'id': best['member_id'],
            'display_role': best['display_role'],
        },
        'score': best['score'],
        'reasoning': best['reasoning'],
        'scores': scores,
    }
