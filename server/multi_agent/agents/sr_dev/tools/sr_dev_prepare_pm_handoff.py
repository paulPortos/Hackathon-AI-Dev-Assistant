import hashlib
import json

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from projects.selectors import project_get_for_member
from users.selectors import user_get_by_id


def sr_dev_prepare_pm_handoff(project_id, current_user_id, conversation_summary, findings):
    def build_handoff_id(project, current_user):
        handoff_payload = {
            'project_id': project.id,
            'current_user_id': current_user.id,
            'conversation_summary': str(conversation_summary or '').strip(),
            'findings': findings,
        }
        encoded_payload = json.dumps(handoff_payload, sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(encoded_payload.encode()).hexdigest()

    if not isinstance(findings, list):
        return {'ok': False, 'code': 'validation_error', 'detail': 'findings must be a list'}

    try:
        current_user = user_get_by_id(current_user_id)
        project = project_get_for_member(project_id=project_id, user=current_user)
    except ObjectDoesNotExist:
        return {
            'ok': False,
            'code': 'not_project_member',
            'detail': 'Current user is not a member of the project or the project does not exist',
        }

    return {
        'ok': True,
        'handoff_version': 'sr_dev_to_pm.v1',
        'handoff_id': build_handoff_id(project, current_user),
        'project': {
            'id': project.id,
            'github_full_name': project.github_full_name,
            'github_default_branch': project.github_default_branch,
        },
        'source_agent': 'sr_dev',
        'requested_by': {
            'id': current_user.id,
            'username': current_user.username,
        },
        'conversation_summary': str(conversation_summary or '').strip(),
        'findings': findings,
        'created_at': timezone.now().isoformat(),
    }
