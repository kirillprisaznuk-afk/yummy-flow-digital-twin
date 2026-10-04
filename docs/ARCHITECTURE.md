# Architecture

Yummy Flow Digital Twin is a local, single-user application. The six product views share one backend calculation model. No external service is required.

## Responsibilities

| Location | Responsibility |
| --- | --- |
| `frontend/app/`, `components/` | Next.js routes, navigation and presentation |
| `frontend/features/scenarios/` | Independent baseline/alternative drafts, editing, comparison and saved-state workflow |
| `frontend/features/risk/` | Analysis controls, result attribution and rendering |
| `frontend/api/`, `types/` | API client and generated OpenAPI contracts |
| `backend/app/api/`, `schemas/` | FastAPI transport, validated requests and responses |
| `backend/app/domain/` | Assumptions, capacity, economics, break-even, cash, comparisons and reporting allocations |
| `backend/app/analytics/` | Sensitivity and Monte Carlo through the domain evaluator |
| `backend/app/services/` | Saved-scenario workflows and version checks |
| `backend/app/models/`, `database/` | SQLAlchemy persistence, sessions and Alembic revisions |
| `backend/tests/`, `frontend/tests/` | Independent arithmetic, API/database integration and browser workflows |

## One calculation boundary

`evaluate(Assumptions(...))` works without HTTP, a database or React. Capacity limits fulfilled orders before revenue and costs are computed. Comparison evaluates each scenario independently. `reporting.py` allocates the resulting monthly amounts per fulfilled order and reports resource gaps.

Keeping these rules in Python avoids inconsistent spreadsheet-like formulas across pages. The API transports results; React formats currency, converts percentage inputs and scales chart geometry. It does not calculate profitability, sample distributions, rank sensitivity or infer probabilities.

Assumptions are immutable validated Pydantic models. Decimal rates and exact rational throughput preserve boundary decisions; outputs use a local 28-significant-digit, half-even Decimal context. Decimal API values are strings. Undefined ratios and no-burn runway use null with accompanying status fields. Model version 1.1 identifies calculation semantics, separately from database revisions and analytics version 1.0.

## Analytics

Sensitivity evaluates six individual inputs at −20%, −10%, baseline, +10% and +20%, ranking valid operating-result ranges. Invalid perturbations are reported rather than clipped.

Monte Carlo draws five independent bounded triangular inputs using a request-local standard-library random generator. Every draw calls the same domain evaluator. The backend returns bins, percentiles, conditional frequencies, seed and sample digest. Runs are limited to 1,000–10,000 with one active simulation per API process. This is synchronous local analysis; navigating away does not cancel computation.

## Frontend state and transport

A shared React provider retains drafts across navigation. Numeric edits invalidate calculated results. Explicit saves persist assumptions; local storage remembers saved UUIDs and the active slot, then reloads actual records from the API after refresh. Unsaved edits are not durable. Replacement and deletion require confirmation; saving one slot never silently changes the other's assumptions.

Risk results are keyed to the selected slot, assumptions and settings, including late responses. Risk settings/results are page-local, not saved with scenarios. Existing assumptions CSV exchange is retained and validates complete fields/units before replacing a draft; it is not a data-ingestion pipeline.

The Next.js server proxy forwards only known API paths, rejects cross-origin writes, and keeps `BACKEND_URL` server-only. Browser cookies and database credentials are not forwarded. The local servers bind to loopback. There is no authentication or multi-user conflict resolution.

## Persistence and schema

PostgreSQL stores UUID-keyed scenario records: name, description, complete JSON assumption snapshot, model version and UTC timestamps. Decimal assumptions remain strings in JSON. Results are recalculated, not cached. A request owns its SQLAlchemy session; writes commit explicitly and unsuccessful work rolls back on closure.

Alembic upgrades run explicitly before API startup. Startup checks the revision instead of creating tables. Existing unversioned tables are not overwritten. Valid old-model records remain readable; incompatible replacements/recalculations return a clear conflict and require an explicit new scenario. Schema revisions do not change calculation versions.

SQLite supports isolated tests and a fallback, while real PostgreSQL tests verify migrated schemas and records across API/database restarts. [Database instructions](DATABASE.md) explain configuration and existing-data precautions.

## Local runtime

Compose runs PostgreSQL 17 with a health check, loopback port and persistent named volume. Development and test databases are separate. Ignored `.env` supplies local credentials; `.env.example` contains placeholders.

Windows START checks Docker, waits for PostgreSQL, applies migrations and launches the existing FastAPI and Next.js development servers. Named Windows Job Objects own each process tree; STOP closes those trees and stops the project's database service without removing its volume. Logs and process records are ignored under `.yummy-flow-runtime/`.

Financial data, credentials and calculations do not depend on a hosted service. Forecasting, dynamic cash paths, routing and multi-store modelling are outside the final scope.
