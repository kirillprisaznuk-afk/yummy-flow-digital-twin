# Repository Guidelines

## Project Structure & Module Organization

`backend/app/domain/` owns validated assumptions, capacity, economics, cash, and comparisons. Keep formulas independent of HTTP and persistence. `api/` handles FastAPI routes, `services/` orchestrates saved scenarios, `schemas/` defines transport contracts, and `models/` plus `database/` own SQLAlchemy persistence. Tests live in `backend/tests/`; model decisions and formulas live in `docs/`.

`frontend/` contains the Next.js UI, generated API types and Playwright tests. `backend/app/analytics/` owns sensitivity and simulation analytics; synthetic historical datasets are not implemented yet. Follow `docs/PLAN.md` milestone gates.

## Build, Test, and Development Commands

Use Python 3.12+ in an isolated `.venv`. From the project root, install with `python -m pip install -c backend/requirements.lock -e './backend[dev,api]'`.

From `backend/`:

- `python -m app`: print the synthetic baseline without a database.
- `python -m app.database.migrate`: apply Alembic revisions before API startup.
- `python -m uvicorn app.main:app --reload`: run the local API.
- `python -m pytest --cov=app.domain --cov-branch`: run tests and enforce 95% domain coverage.
- `python -m ruff check app tests`: lint code.
- `python -m ruff format app tests`: apply formatting.

From `frontend/`, use `pnpm dev`, `pnpm build`, `pnpm lint`, `pnpm typecheck`, and `pnpm test`. Browser tests require both local servers. Regenerate API types with `python scripts/export_api.py` from the root, then `pnpm api:types` from the frontend. Keep business formulas in Python.

## Coding Style & Naming Conventions

Use four-space Python indentation, type hints, `snake_case` functions/modules, and `PascalCase` classes. Ruff enforces imports and a 100-character line limit. Keep monetary rates in Decimal and throughput ratios exact until output conversion. Defaults live in `domain/assumptions.py`. Both `with_changes` and the overridden `model_copy` validate edits.

## Testing Guidelines

Use pytest with `test_*.py` files and descriptive behavior-based names. Include independent arithmetic examples and boundary regressions. PostgreSQL requires `YUMMY_TEST_POSTGRES_URL`; the local Compose restart test additionally requires `YUMMY_TEST_COMPOSE_RESTART=1`. Run `pytest -m postgresql` for both. A skipped test is not verification. Both pass locally. Product scope is frozen. Only demonstrated bug fixes, cleanup and portfolio documentation/presentation work are authorised; forecasting is outside scope. See `docs/DATABASE.md` for setup and limitations.

## Commit & Pull Request Guidelines

This folder is a standalone Git repository. Keep commits scoped to this project and never add local configuration or generated runtime files. Use focused imperative subjects such as `Add capacity-constrained economics engine`. Describe behavioral changes, verification, and limitations; link issues and include screenshots for UI changes.

## Data & Configuration

Label every example synthetic. Never imply this portfolio system existed during the original venture. Document assumptions before changing formulas. Keep `.env`, credentials, local databases, environments, caches, and generated build files out of Git. Compose provides local PostgreSQL development/test databases. `scripts/backend.ps1` loads ignored `.env` for Windows Python commands; direct Python requires exported `DATABASE_URL`. SQLite remains a fallback.
