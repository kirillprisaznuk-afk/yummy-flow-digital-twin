# Local database and migrations

## Current verification status

Real PostgreSQL migrations, schema-drift checks and API/database restart persistence are verified. See [the final validation record](PORTFOLIO_REVIEW.md) for the current results. These checks demonstrate graceful restart persistence, not power-loss recovery or backups.

## Local Compose workflow

From the project root, copy `.env.example` to ignored `.env` on a new checkout and replace its placeholder password consistently. The Windows helper reads simple unquoted `KEY=value` entries; it does not evaluate shell expressions. Do not print or commit the file.

```powershell
docker compose up -d --wait
./scripts/backend.ps1 -m app.database.migrate
./scripts/backend.ps1 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Compose publishes only `127.0.0.1:5433`, uses a persistent named volume and health check, and creates `yummy_flow` and `yummy_flow_test`. The init SQL runs only for a new volume. Never remove a volume to repair a migration. Changing the password in `.env` does not change an existing database role's password. The local bootstrap role is suitable for this isolated workstation, not a shared-database permission model. The image follows PostgreSQL major version 17; it is not digest-pinned.

For full verification, including a brief restart of this project's database service:

```powershell
$env:YUMMY_TEST_COMPOSE_RESTART = '1'
./scripts/backend.ps1 -m pytest --cov=app.domain --cov-branch
./scripts/backend.ps1 -m alembic check
```

Without the restart opt-in, that test skips; without the PostgreSQL URL, the schema-isolated test also skips. `docker compose stop` stops the database while preserving data. Docker CLI must be on PATH (a new terminal picks up a newly installed Docker).

## Why Alembic now

Saved scenarios are now persistent artifacts. SQLAlchemy `create_all` creates missing tables but does not provide reviewed schema evolution. A single initial Alembic revision is sufficient at this stage; no migration framework beyond Alembic is needed. The schema revision `0001_scenarios` is independent of business model version `1.1`.

The initial revision creates the UUID scenario key, name/description, JSON assumption snapshot, calculation version, UTC timestamps, and creation-time index. It contains no business defaults or credentials. Domain formulas and assumption defaults remain unchanged.

## Normal setup

With backend dependencies installed, run from `backend/`:

```sh
# Optional: export DATABASE_URL for an existing local PostgreSQL database.
# Without it, the local file is ./yummy_flow.db (ignored by Git).
python -m app.database.migrate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API checks that the database revision matches the migration head; it no longer executes DDL on startup. Migration is an explicit local setup step. `.env` is not automatically loaded into the Python process; export the chosen `DATABASE_URL` as described in the main README. No configuration duplicates or plaintext credentials are stored in `alembic.ini`.

Standard Alembic commands are also available:

```sh
python -m alembic current
python -m alembic revision --autogenerate -m "Describe schema change"
python -m alembic upgrade head
python -m alembic check
```

Review generated revisions before applying them. Keep old applied revisions unchanged. The initial downgrade removes the scenario table and its data: use downgrade only on a disposable database or with an explicit recovery plan. Normal application startup and upgrade never perform a downgrade.

## Existing unversioned databases

The explicit migration command refuses to overwrite an existing unversioned `scenarios` table. Back up the database first, compare its actual columns, nullability, types, primary key, and indexes with `0001_scenarios.py`, and resolve differences deliberately. Only if the schema already matches, use `python -m alembic stamp 0001_scenarios` to record that baseline without changing records. Then run `python -m alembic check` and the relevant persistence tests. Do not blindly stamp an unknown schema, delete a database, or replace user data to make an upgrade pass.

Tests verify that an unversioned scenario survives a refused upgrade, repeated upgrades preserve data, the migrated schema matches SQLAlchemy metadata, and an unmigrated API refuses startup without creating tables.

## PostgreSQL integration test

Set `YUMMY_TEST_POSTGRES_URL` to a dedicated disposable local test database, with an account allowed to create schemas. From `backend/`:

```sh
python -m pytest -m postgresql -v
python -m pytest --cov=app.domain --cov-branch
```

The integration test creates a uniquely named schema, applies the actual Alembic migration, checks the revision, creates/retrieves/replaces/recalculates a scenario, restarts the application, retrieves the same data, and deletes its record. Cleanup removes only that generated schema. The second explicitly enabled test restarts both the real API process and the Compose PostgreSQL service. Both tests have passed against the local server.

Migration connections follow Alembic's documented [shared-connection pattern](https://alembic.sqlalchemy.org/en/latest/cookbook.html#sharing-a-connection-across-one-or-more-programmatic-migration-commands), so isolated schemas and test transactions use the same migration path as normal setup.
