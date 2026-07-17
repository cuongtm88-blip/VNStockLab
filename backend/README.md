# VNStockLab Backend

This directory provides the FastAPI foundation for the VNStockLab API. It includes the
application entry point, health endpoints, asynchronous PostgreSQL connectivity, and endpoint
tests without authentication or business-domain components.

## Requirements

- Python 3.13 (`>=3.13,<3.14`)
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

Install and synchronize dependencies with:

```shell
uv sync
```

For local development, copy `.env.example` to `.env` and adjust its non-secret settings.
Keep `.env` local and do not commit it.

## Development

Start the development server with:

```shell
uv run fastapi dev app/main.py
```

## Tests

Run the test suite with:

```shell
uv run pytest
```

Run linting, formatting checks, and static type checking with:

```shell
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
```

## Database and migrations

Verify the local database connection from this directory with:

```shell
uv run python -m app.db.check
```

Run Alembic commands from this directory:

```shell
uv run alembic current
uv run alembic history
uv run alembic upgrade head
uv run alembic downgrade -1
```

In a future task, create a migration with:

```shell
uv run alembic revision --autogenerate -m "description"
```

Task 5A introduces no business tables or migration revisions. The engine opens connections
lazily, so application startup does not require PostgreSQL to be immediately available.
Sessions do not auto-commit; services own transaction boundaries. Database credentials must
remain in environment variables and must never be committed.

## Application structure

- `app/api/router.py` is the central API router registry.
- `app/api/routes` contains HTTP route modules.
- `app/core` contains configuration and logging.
- `app/db` contains asynchronous engine, session, and connectivity helpers.
- `app/common` contains stable shared constants.
- `app/schemas` contains API request and response schemas.

## Request and response conventions

Every request receives an `X-Request-ID` response header. Clients may supply a UUID in
`X-Correlation-ID`; valid UUIDs are preserved as the request ID, while missing or invalid
values are replaced with a generated UUID. Successful response envelopes include the same
identifier as `meta.request_id`.

Errors use a standardized `error` envelope containing a stable code, a safe message,
structured details, and the request ID. Internal exceptions are logged with their request ID
but their messages and tracebacks are not exposed to clients.

`app/api/dependencies.py` contains explicit FastAPI dependency aliases. No authentication
dependencies exist yet.

Business modules will be introduced only in later roadmap tasks.

## Pre-commit hooks

Pre-commit runs lightweight quality checks before commits. Install the hooks from the
`backend` directory with:

```shell
uv run pre-commit install
```

From the repository root, the preferred command for manually running all hooks is:

```shell
uv --project backend run pre-commit run --all-files
```

When invoking the backend project directly, run the uv command from the `backend`
directory:

```shell
uv run pre-commit run --all-files
```

Pre-commit does not run the test suite. Continue to run pytest explicitly with
`uv run pytest` from the `backend` directory.

## Docker development

Run the following commands from the repository root.

Copy the development environment template:

```shell
cp .env.example .env
```

Validate the Compose configuration:

```shell
docker compose config
```

Build the backend image:

```shell
docker compose build backend
```

Start all services:

```shell
docker compose up -d
```

View service status:

```shell
docker compose ps
```

Follow backend logs:

```shell
docker compose logs -f backend
```

Run tests inside the backend container:

```shell
docker compose exec backend uv run pytest
```

Verify the Docker database connection:

```shell
docker compose exec backend uv run python -m app.db.check
```

Stop services without deleting data:

```shell
docker compose down
```

Stop services and delete local database and Redis volumes:

```shell
docker compose down -v
```

**Warning:** `docker compose down -v` permanently deletes the local PostgreSQL
and Redis data stored in the named volumes.

Local endpoints:

- <http://127.0.0.1:8000/>
- <http://127.0.0.1:8000/api/v1/health>
- <http://127.0.0.1:8000/docs>

PostgreSQL and Redis are provisioned for local development. PostgreSQL connectivity is wired
into the application lifecycle; Redis application integration remains for a later roadmap task.
