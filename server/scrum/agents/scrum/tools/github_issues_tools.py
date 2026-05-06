import uuid
from channels.db import database_sync_to_async
from scrum.models.github_issue import GitHubIssue
from projects.models.project import Project
from users.models.user import User
from projects.providers.github_issues import fetch_github_issues, get_github_issue
from users.services import github_access_token_get_valid

async def github_list_issues(project_id: int, user: User, state: str = 'open'):
    """Returns list of issues directly from GitHub API."""
    try:
        project = await database_sync_to_async(Project.objects.get)(id=project_id)
        if not project.github_full_name:
            return {'ok': False, 'error': 'Project is not linked to a GitHub repository.'}
            
        access_token = await database_sync_to_async(github_access_token_get_valid)(user)
        if not access_token:
             return {'ok': False, 'error': 'User does not have a valid GitHub token.'}
             
        # fetch_github_issues is synchronous, wrap in sync_to_async
        issues_data = await database_sync_to_async(fetch_github_issues)(access_token, project.github_full_name, state=state)
        
        issues = []
        for i in issues_data:
            issues.append({
                'github_number': i.get('number'),
                'title': i.get('title'),
                'state': i.get('state'),
                'labels': [l.get('name') for l in i.get('labels', [])],
                'assignees': [a.get('login') for a in i.get('assignees', [])],
                'created_at': i.get('created_at')
            })
            
        return {
            'ok': True,
            'issues': issues
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}

async def github_get_issue(project_id: int, user: User, issue_number: int):
    """Returns details of a specific issue directly from GitHub API."""
    try:
        project = await database_sync_to_async(Project.objects.get)(id=project_id)
        if not project.github_full_name:
            return {'ok': False, 'error': 'Project is not linked to a GitHub repository.'}
            
        access_token = await database_sync_to_async(github_access_token_get_valid)(user)
        if not access_token:
             return {'ok': False, 'error': 'User does not have a valid GitHub token.'}
             
        # get_github_issue is synchronous, wrap in sync_to_async
        issue = await database_sync_to_async(get_github_issue)(access_token, project.github_full_name, issue_number)
        
        return {
            'ok': True,
            'issue': {
                'github_number': issue.get('number'),
                'title': issue.get('title'),
                'body': issue.get('body'),
                'state': issue.get('state'),
                'labels': [l.get('name') for l in issue.get('labels', [])],
                'assignees': [a.get('login') for a in issue.get('assignees', [])],
                'github_url': issue.get('html_url'),
                'created_at': issue.get('created_at'),
            }
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}
