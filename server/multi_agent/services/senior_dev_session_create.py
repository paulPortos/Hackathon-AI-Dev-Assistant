from multi_agent.models import SeniorDevSession
from projects.selectors import project_get_for_member
from projects.services.project_repository_branch_list import project_repository_branch_list


def senior_dev_session_create(*, user, project_id, commit_sha, branch_name='', name=''):
    """Creates a Senior Dev session, resolving 'latest' commit_sha to the actual HEAD SHA."""
    commit_sha = str(commit_sha or '').strip()
    branch_name = str(branch_name or '').strip()
    name = str(name or '').strip()
    if not commit_sha:
        raise ValueError('commit_sha is required')

    project = project_get_for_member(project_id=project_id, user=user)

    # Resolve 'latest' to the actual HEAD SHA of the target branch
    if commit_sha.lower() == 'latest':
        try:
            branch_data = project_repository_branch_list(project)
            target_branch = branch_name or branch_data.get('default_branch', 'main')
            for branch in branch_data.get('branches', []):
                if branch['name'] == target_branch:
                    commit_sha = branch['commit_sha']
                    branch_name = branch_name or target_branch
                    break
            else:
                # Fallback: use the default branch SHA
                for branch in branch_data.get('branches', []):
                    if branch.get('is_default'):
                        commit_sha = branch['commit_sha']
                        branch_name = branch_name or branch['name']
                        break
        except Exception:
            raise ValueError(
                'Could not resolve "latest" to a commit SHA. '
                'Please provide a specific commit SHA or ensure the repository is accessible.'
            )

    if commit_sha.lower() == 'latest':
        raise ValueError('Could not resolve "latest" to a real commit SHA.')

    return SeniorDevSession.objects.create(
        project=project,
        user=user,
        commit_sha=commit_sha,
        branch_name=branch_name,
        name=name,
    )
