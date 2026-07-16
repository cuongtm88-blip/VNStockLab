# VNStockLab Backend

This directory provides the minimal FastAPI foundation for the VNStockLab API. It includes the application entry point, health endpoints, and endpoint tests without database, authentication, or business-domain components.

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

## Application structure

- `app/api/router.py` is the central API router registry.
- `app/api/routes` contains HTTP route modules.
- `app/core` contains configuration and logging.
- `app/common` contains stable shared constants.
- `app/schemas` contains API request and response schemas.

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

PostgreSQL and Redis are provisioned for local development, but application
integration will be implemented in later frozen roadmap tasks.
