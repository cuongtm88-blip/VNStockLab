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
