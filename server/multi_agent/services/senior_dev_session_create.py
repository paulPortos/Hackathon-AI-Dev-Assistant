from multi_agent.models import SeniorDevSession
from projects.selectors import project_get_for_member


def senior_dev_session_create(*, user, project_id, commit_sha, branch_name=''):
    commit_sha = str(commit_sha or '').strip()
    if not commit_sha:
        raise ValueError('commit_sha is required')

    project = project_get_for_member(project_id=project_id, user=user)
    return SeniorDevSession.objects.create(
        project=project,
        user=user,
        commit_sha=commit_sha,
        branch_name=str(branch_name or '').strip(),
    )
