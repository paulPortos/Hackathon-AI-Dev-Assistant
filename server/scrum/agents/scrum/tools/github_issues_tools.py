import uuid
from channels.db import database_sync_to_async
from scrum.models.github_issue import GitHubIssue
from projects.models.project import Project
from users.models.user import User
from projects.providers.github_issues import fetch_github_issues
from projects.services.github_issues_sync import github_issues_sync
from users.services import github_access_token_get_valid
from django.utils.dateparse import parse_datetime

@database_sync_to_async
def github_list_issues(project_id: int, state: str = 'open'):
    """Returns list of issues from local DB cache."""
    issues_qs = GitHubIssue.objects.filter(project_id=project_id, state=state).order_by('-github_number')
    
    issues = []
    for i in issues_qs:
        issues.append({
            'github_number': i.github_number,
            'title': i.title,
            'state': i.state,
            'labels': i.labels,
            'assignees': i.assignees,
            'created_at': i.created_at.isoformat() if i.created_at else None
        })
        
    return {
        'ok': True,
        'issues': issues
    }

@database_sync_to_async
def github_get_issue(project_id: int, issue_number: int):
    """Returns details of a specific issue from local DB cache."""
    try:
        issue = GitHubIssue.objects.get(project_id=project_id, github_number=issue_number)
        return {
            'ok': True,
            'issue': {
                'github_number': issue.github_number,
                'title': issue.title,
                'body': issue.body,
                'state': issue.state,
                'labels': issue.labels,
                'assignees': issue.assignees,
                'github_url': issue.github_url,
                'created_at': issue.created_at.isoformat(),
            }
        }
    except GitHubIssue.DoesNotExist:
        return {'ok': False, 'error': f'Issue #{issue_number} not found in local cache.'}

async def github_sync_issues_tool(project_id: int, user: User):
    """Triggers a sync of issues from GitHub to local cache."""
    try:
        project = await database_sync_to_async(Project.objects.get)(id=project_id)
        # Sync issues (synchronous provider/service called via sync_to_async)
        await database_sync_to_async(github_issues_sync)(project, user)
        return {'ok': True, 'message': 'Successfully synced GitHub issues.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
