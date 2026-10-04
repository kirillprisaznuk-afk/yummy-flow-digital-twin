# Running Yummy Flow

## START

Double-click **START_YUMMY_FLOW.bat**.

Wait for the success message. Your browser opens at **http://localhost:3000**.
You can close the launcher window. VS Code does not need to be open.

## STOP

Double-click **STOP_YUMMY_FLOW.bat**.

Wait for the completion message. Your saved scenarios remain in the database.
The browser tab may stay open; you can close it yourself.

## First-time setup

Requires Python 3.12+, Node.js 22+, pnpm 11.25.0 and Docker Desktop with a reachable engine. From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c backend/requirements.lock -e './backend[dev,api]'
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd frontend
pnpm install --frozen-lockfile
cd ..
```

In `.env`, replace the placeholder password and keep the database URLs consistent. Keep this file private. START uses the existing environment, starts PostgreSQL, checks migrations and launches both servers. It does not install software.

For separate terminals, from the project root:

```powershell
docker compose up -d --wait
./scripts/backend.ps1 -m app.database.migrate
./scripts/backend.ps1 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, run `pnpm dev` from `frontend/`. The Windows helper loads the root `.env`; direct Python commands require exported environment variables. See [database configuration](docs/DATABASE.md) and [frontend configuration](frontend/README.md).

## If something does not start

- Follow the message in the launcher window. Docker Desktop may need a Windows approval.
- If a port is already in use, close the previously started development server and try again.
- This launcher uses the project's existing setup. A fresh checkout first needs the Python environment, frontend dependencies, local `.env`, Node.js and Docker Desktop described above. It does not install software or change Windows settings.
- Diagnostic logs are in the ignored `.yummy-flow-runtime` folder. Do not share logs without checking for local configuration details.
- Leave `.yummy-flow-runtime` in place while the app is running; STOP uses its process records.

The first page may take longer while Next.js prepares its development build. Repeated START clicks reuse launcher-owned servers. STOP only closes those servers and this project's PostgreSQL service; it does not stop Docker Desktop or delete database volumes.
