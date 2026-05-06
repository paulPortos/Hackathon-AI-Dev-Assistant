from projects.models.project import Project
from users.models.user import User
from projects.providers.github_issues import fetch_github_issues
from users.services import github_access_token_get_valid
from scrum.models.github_issue import GitHubIssue
from django.utils.dateparse import parse_datetime

def github_issues_sync(project: Project, user: User) -> dict:
    """Fetch all open issues from GitHub and upsert into GitHubIssue cache."""
    access_token = github_access_token_get_valid(
        user,
        missing_message='GitHub account must be connected before syncing issues',
    )
    
    # We sync both open and closed issues or just open? 
    # Plan says "Fetch all open issues". Let's stick to open for now as context.
    # But maybe we want both for completeness. Let's do open for speed.
    issues_data = fetch_github_issues(
        access_token=access_token, 
        repo_full_name=project.github_full_name,
        state='open'
    )
    
    synced_count = 0
    for issue in issues_data:
        # Normalize labels and assignees
        labels = [{"name": l.get("name"), "color": l.get("color")} for l in issue.get("labels", [])]
        assignees = [{"login": a.get("login"), "avatar_url": a.get("avatar_url")} for a in issue.get("assignees", [])]
        
        GitHubIssue.objects.update_or_create(
            project=project,
            github_number=issue['number'],
            defaults={
                'title': issue['title'],
                'body': issue.get('body') or '',
                'state': issue['state'],
                'labels': labels,
                'assignees': assignees,
                'github_url': issue['html_url'],
                'created_at': parse_datetime(issue['created_at']),
                'updated_at': parse_datetime(issue['updated_at']),
            }
        )
        synced_count += 1
        
    return {
        "ok": True,
        "synced": synced_count,
        "repo": project.github_full_name
    }
