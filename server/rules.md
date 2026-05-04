# Server Rules

These rules apply only to the Django backend under `server/`. Do not use this file to define client, design, or repository-wide conventions.

## Stack

- Use Django, Django REST Framework, PostgreSQL, and JWT authentication unless a task explicitly changes the backend stack.
- Use Argon2id through Django's `Argon2PasswordHasher` as the first password hasher.
- Keep runtime configuration in `.env` or environment variables. Never hardcode secrets, credentials, callback URLs, private key paths, or machine-specific absolute paths.
- PostgreSQL is the only supported database for runtime and tests.

## App Structure

Every Django app should use this structure unless the app genuinely does not need a layer:

```text
app_name/
  __init__.py
  apps.py
  urls.py
  models/
    __init__.py
    model_name.py
  views/
    __init__.py
    action_or_resource_view.py
  services/
    __init__.py
    create_resource.py
    update_resource.py
    delete_resource.py
  selectors/
    __init__.py
    get_resource.py
    list_resources.py
  serializers/
    __init__.py
    resource_serializer.py
  providers/
    __init__.py
    external_service_action.py
  tests/
    __init__.py
    test_resource.py
  migrations/
    __init__.py
```

- Do not add `admin.py`. Administration belongs in the dedicated client admin UI, not Django admin.
- Use one top-level class or function per file for app domain code.
- Methods inside classes, tests, migrations, and small settings helpers are exempt from the one-class/function rule.
- Package `__init__.py` files may re-export public classes and functions to keep imports stable.
- Name files after the class or function they contain, using snake_case.

## Layer Rules

- Views orchestrate HTTP request and response handling only. They should validate request flow, call selectors/services/providers, and return serialized responses.
- Services own create, update, delete, and other mutation workflows.
- Selectors own reads, queries, filters, and list retrieval.
- Serializers own API representation and basic validation. Do not put business logic in serializers.
- Providers or clients own external API calls, such as GitHub OAuth requests.
- Models define persistence and small model-local behavior only. Keep cross-resource workflows out of models.
- Keep errors explicit and clean. Convert external provider failures and invalid workflow states into consistent API errors at the view boundary.

## API Rules

- Version API endpoints. Use `/api/v1/` as the canonical prefix unless a task explicitly introduces another version.
- Keep compatibility aliases only when they are intentionally required.
- Use JWT as the backend auth token format unless explicitly changed.
- List `GET` endpoints must be paginated by default.
- Detail `GET` endpoints return a single resource and are not paginated.
- Keep pagination metadata consistent across list responses.
- Do not expose sensitive fields such as access tokens, secrets, private keys, or internal credentials in API responses.

## Data And Configuration

- Read GitHub OAuth settings from environment variables: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_CALLBACK_URL`, and optional `GITHUB_PRIVATE_KEY_PATH`.
- Read Django and database settings from environment variables, including `DJANGO_SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`.
- Store user-linked external identifiers as stable provider IDs, not usernames or display names.
- Create migrations for model changes and keep migrations committed with the app.

## Testing Rules

- Add focused tests for new services, selectors, views, serializers, models, auth flows, and provider integrations.
- Mock external APIs in tests. Do not call GitHub or other third-party services from unit tests.
- Before delivery, run:

```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test <app_name>
```

- For server-wide changes, run the full backend test suite.
- Tests must run against PostgreSQL. Do not add alternate database fallbacks or test-only database settings.
