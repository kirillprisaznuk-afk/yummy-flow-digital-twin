# Testing

The suite checks model behaviour with independent arithmetic examples, capacity and break-even boundaries, invalid inputs, persistence, sensitivity and reproducible simulation. Browser tests cover scenario isolation, save/reload, comparison, validation and matching outputs across the decision views. [The worked example](WORKED_EXAMPLE.md) can also be checked by hand.

## Automated checks

One [GitHub Actions workflow](../.github/workflows/ci.yml) runs on pushes and pull requests:

- Backend: Python 3.12, constrained dependencies, Ruff lint/format, pytest and domain/analytics branch coverage. A temporary PostgreSQL 17 service exercises the real schema-isolated persistence test; it uses disposable CI-only credentials, not repository secrets.
- Frontend: Node.js 24, the pinned pnpm version and frozen lockfile, ESLint, Prettier, production build and TypeScript. Building first generates Next.js route types on a fresh checkout.

The workflow has read-only repository permissions and no deployment steps. It excludes only the test that restarts the local Compose service, which does not exist on the CI runner. Browser tests and Windows launcher checks run locally. A green workflow does not claim those checks ran in CI.

## Backend and database checks

After [local setup](../RUNNING_THE_APP.md), run from the project root on Windows:

```powershell
docker compose up -d --wait
$env:YUMMY_TEST_COMPOSE_RESTART = '1'
./scripts/backend.ps1 -m pytest --cov=app.domain --cov=app.analytics --cov-branch
./scripts/backend.ps1 -m alembic check
./scripts/backend.ps1 -m ruff check app tests
./scripts/backend.ps1 -m ruff format --check app tests
./scripts/backend.ps1 -m pip check
```

The helper reads the ignored `.env`. Without `YUMMY_TEST_POSTGRES_URL`, the real PostgreSQL test skips. The restart test also needs `YUMMY_TEST_COMPOSE_RESTART=1` and briefly interrupts this project's database. Run it separately from browser tests. See [Database](DATABASE.md) for isolation and migration safety.

On other systems, activate the Python environment, export the database variables and run the same Python modules from `backend/`. Coverage enforces a 95% floor; independently checked expected outcomes matter more than the percentage. No Python static type checker is configured.

## Frontend and browser checks

Stop any frontend development server before building. From `frontend/`:

```sh
pnpm lint
pnpm format:check
pnpm build
pnpm typecheck
pnpm exec playwright install chromium
pnpm start
```

With the PostgreSQL-backed API and built frontend running, run `pnpm test` in another terminal. Tests create uniquely named scenarios and remove only their own records. Error-recovery tests deliberately simulate failed requests; financial calculations are tested independently in Python.

On Windows, `.venv\Scripts\python.exe scripts/test_launcher.py` checks START/STOP, repeated startup, persistent records across restarts and unrelated-process isolation. It opens the browser and leaves application services stopped. Logs, traces, caches and runtime files remain ignored.

The reviewed local baseline passed 163 backend tests with no skips and 15 browser tests. PostgreSQL restart tests establish graceful-restart persistence, not backup or power-loss recovery. Current automated results are visible in the repository's Actions tab.
