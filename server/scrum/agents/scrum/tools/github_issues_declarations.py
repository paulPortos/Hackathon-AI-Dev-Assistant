GITHUB_ISSUES_FUNCTION_DECLARATIONS = [
    {
        "name": "github_list_issues",
        "description": "List GitHub issues for the current project directly from the GitHub API. Use this to see the most up-to-date issues.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["open", "closed"], "description": "Filter by issue state (default: open)"}
            }
        }
    },
    {
        "name": "github_get_issue",
        "description": "Get live details of a specific GitHub issue by its number directly from GitHub.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "The GitHub issue number"}
            },
            "required": ["issue_number"]
        }
    }
]
