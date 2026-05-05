# GitHub Callback

## URL
`/auth/github/callback/`

## Method
`GET`

## Query Parameters
| Name | Type | Description |
| :--- | :--- | :--- |
| `code` | string | GitHub OAuth code |
| `state` | string | GitHub OAuth state for CSRF protection |

## Request Body
None

## Response Body
```json
{
    "access": "string (JWT Access Token)",
    "refresh": "string (JWT Refresh Token)",
    "user": {
        "id": 1,
        "github_id": 12345,
        "username": "johndoe",
        "name": "John Doe",
        "email": "john@example.com",
        "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        "created_at": "2024-05-05T00:00:00Z",
        "updated_at": "2024-05-05T00:00:00Z"
    }
}
```
