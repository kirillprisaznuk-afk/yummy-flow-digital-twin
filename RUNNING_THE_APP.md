# Running Yummy Flow

## START

Double-click **START_YUMMY_FLOW.bat**.

Wait for the success message. Your browser opens at **http://localhost:3000**.
You can close the launcher window. VS Code does not need to be open.

## STOP

Double-click **STOP_YUMMY_FLOW.bat**.

Wait for the completion message. Your saved scenarios remain in the database.
The browser tab may stay open; you can close it yourself.

## If something does not start

- Follow the message in the launcher window. Docker Desktop may need a Windows approval.
- If a port is already in use, close the previously started development server and try again.
- This launcher uses the project's existing setup. A fresh checkout first needs the Python environment, frontend dependencies, local `.env`, Node.js and Docker Desktop described in README.md. It does not install software or change Windows settings.
- Diagnostic logs are in the ignored `.yummy-flow-runtime` folder. Do not share logs without checking for local configuration details.
- Leave `.yummy-flow-runtime` in place while the app is running; STOP uses its process records.

The first page may take longer while Next.js prepares its development build. Repeated START clicks reuse launcher-owned servers. STOP only closes those servers and this project's PostgreSQL service; it does not stop Docker Desktop or delete database volumes.
