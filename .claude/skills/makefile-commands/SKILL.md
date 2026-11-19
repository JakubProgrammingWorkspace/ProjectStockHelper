---
name: makefile-commands
description: "Rules and conventions for running project commands, including package management (uv), migrations, and other Django commands. Always prefer Makefile targets; fall back to docker exec only when no Makefile target exists."
---

# Project Makefile & Docker Conventions

This project runs inside Docker containers. Because of this, **you must never run `uv`, `python`, or `manage.py` directly on the host machine.** Instead, use the pre-configured `make` commands that proxy execution into the correct containers.

## Command Resolution Order

**Always try Makefile first.** Only fall back to `docker exec` when no suitable `make` target exists.

1. Check `Makefile` for an existing target that covers the operation.
2. If no target exists, run the command directly inside the container via `docker exec`:

```bash
# Django / web container
docker exec -it stock_helper_web <command>

# React / frontend container
docker exec -it stock_helper_react <command>

# PostgreSQL container
docker exec -it stock_helper_postgres <command>
```

Container name pattern: `stock_helper_<service>` (where `<service>` is `web`, `react`, `postgres`, or `redis`).

## 1. Core Management

- **Environment**: `make initialize` (setup .env and build), `make up`, `make down`
- **Shell Access**: `make sh` (Backend), `make sh-react` (Frontend), `make sh-db` (Postgres)
- **Package Management**:
  - Backend (`uv`): `make uv [args]` (e.g., `make uv add django`)
  - Frontend (`npm`): `make npm [args]` (e.g., `make npm install axios`)

## 2. Backend (Django)

- **Migrations**: `make create-migrations`, `make execute-migrations`
- **Linting & Formatting**: `make lint`, `make lint-fix`, `make format`
- **Testing**: `make test-backend` (or `make run-tests`), `make test-unit`, `make test-integration`

## 3. Frontend (React)

- **Build**: `make build-frontend`
- **Testing**: `make test-frontend`, `make test-frontend-watch`

## 4. Data Ingestion & Processing

- **Tickers**: `make fetch-tickers` (SEC + Processing)
- **Financial Data**: `make fetch-sec-financial`
- **Prices**: `make fetch-prices` (YFinance), `make fetch-bulk-historical-prices`

## 5. End-to-End Testing

- **Full Suite**: `make test` (Backend + Frontend)
- **E2E (Browser)**: `make test-e2e` (Playwright)

## IMPORTANT: Version Constraints
When adding new dependencies to `pyproject.toml`, you MUST specify version constraints (e.g., `>=X.Y.Z,<(X+1).0.0`) to prevent breaking changes from new major versions. Never add a dependency without a version constraint.
