import requests
import re
from users.github._parse_response import _parse_response
from users.github.constants import GITHUB_API_VERSION

def _get_headers(access_token):
    return {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {access_token}',
        'X-GitHub-Api-Version': GITHUB_API_VERSION,
    }

def _parse_next_link(link_header):
    if not link_header:
        return None
    # Pattern to find the next link: <url>; rel="next"
    links = re.findall(r'<(.*?)>;\s*rel="next"', link_header)
    return links[0] if links else None

def fetch_github_issues(access_token, repo_full_name, state='open', per_page=100):
    url = f"https://api.github.com/repos/{repo_full_name}/issues"
    params = {"state": state, "per_page": per_page, "page": 1, "filter": "all"}
    all_issues = []
    
    headers = _get_headers(access_token)
    
    while url:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        data = _parse_response(response, f"GitHub issues fetch failed for {repo_full_name}")
        
        # GitHub returns PRs mixed with issues — filter them out
        all_issues.extend([i for i in data if "pull_request" not in i])
        
        # Parse Link header: <url>; rel="next"
        link_header = response.headers.get("Link", "")
        url = _parse_next_link(link_header)
        params = {} # next URL already includes query params
        
    return all_issues

def create_github_issue(access_token, repo_full_name, title, body, labels=None, assignees=None):
    url = f"https://api.github.com/repos/{repo_full_name}/issues"
    headers = _get_headers(access_token)
    payload = {
        "title": title,
        "body": body,
    }
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees
        
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    return _parse_response(response, f"Failed to create issue in {repo_full_name}")

def update_github_issue(access_token, repo_full_name, issue_number, **fields):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}"
    headers = _get_headers(access_token)
    
    response = requests.patch(url, json=fields, headers=headers, timeout=15)
    return _parse_response(response, f"Failed to update issue #{issue_number} in {repo_full_name}")
