# User Search

## URL
`/api/<version>/users/search/`

## Method
`GET`

## Query Parameters
`q`: Searches user usernames and emails case-insensitively.

## Request Body
None

## Response Body
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "johndoe",
            "name": "John Doe",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345"
        }
    ]
}
```
