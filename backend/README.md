# VNStockLab Backend

This directory provides the minimal FastAPI foundation for the VNStockLab API. It includes the application entry point, health endpoints, and endpoint tests without database, authentication, or business-domain components.

## Requirements

- Python 3.13 (`>=3.13,<3.14`)
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

Install and synchronize dependencies with:

```shell
uv sync
```

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
