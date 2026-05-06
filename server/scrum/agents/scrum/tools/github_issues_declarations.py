GITHUB_ISSUES_FUNCTION_DECLARATIONS = [
    {
        "name": "github_list_issues",
        "description": "List GitHub issues for the current project from the local cache. Use this to see what issues are currently open or closed.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["open", "closed"], "description": "Filter by issue state (default: open)"}
            }
        }
    },
    {
        "name": "github_get_issue",
        "description": "Get details of a specific GitHub issue by its number.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "The GitHub issue number"}
            },
            "required": ["issue_number"]
        }
    },
    {
        "name": "github_sync_issues",
        "description": "Trigger a synchronization of GitHub issues from the live GitHub API into the local cache. Use this if the user says there are issues you can't see, or if the data feels stale.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
