from projects.providers import fetch_github_repository_branches


def project_repository_branch_list(project):
    if not project.creator.access_token:
        raise ValueError('Project creator does not have a connected GitHub token')

    branches = fetch_github_repository_branches(
        access_token=project.creator.access_token,
        repository=project.github_full_name,
    )

    normalized_branches = []
    for branch in branches:
        name = branch.get('name') if isinstance(branch, dict) else None
        commit = branch.get('commit') if isinstance(branch, dict) else None
        commit_sha = commit.get('sha') if isinstance(commit, dict) else None
        if not name or not commit_sha:
            raise ValueError('GitHub repository branches fetch returned an invalid response')

        normalized_branches.append(
            {
                'name': name,
                'commit_sha': commit_sha,
                'is_default': name == project.github_default_branch,
            }
        )

    return {
        'default_branch': project.github_default_branch,
        'branches': normalized_branches,
    }
