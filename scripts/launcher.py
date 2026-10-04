"""Windows local start/stop orchestration. No installation or system settings changes."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from uuid import UUID, uuid4

import windows_jobs as jobs

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / ".yummy-flow-runtime"
PREFIX = (
    "Local\\YummyFlow-"
    + hashlib.sha256(str(ROOT).lower().encode()).hexdigest()[:16]
    + "-"
)
PYTHON = ROOT / ".venv/Scripts/python.exe"
POWERSHELL = (
    Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
)


def say(message):
    print(message, flush=True)


def executable(name, candidates):
    found = shutil.which(name)
    if found:
        return Path(found)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        f"{name} is not installed or could not be found. See RUNNING_THE_APP.md."
    )


def docker_path():
    return executable(
        "docker.exe",
        [
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "Docker/Docker/resources/bin/docker.exe",
            Path(os.environ["LOCALAPPDATA"])
            / "Programs/DockerDesktop/resources/bin/docker.exe",
        ],
    )


def node_path():
    return executable(
        "node.exe",
        [
            Path(os.environ.get("ProgramFiles", "C:/Program Files"))
            / "nodejs/node.exe",
            Path(os.environ["LOCALAPPDATA"]) / "Programs/nodejs/node.exe",
            *sorted(
                (Path.home() / ".cache/codex-runtimes").glob(
                    "*/dependencies/node/bin/node.exe"
                )
            ),
        ],
    )


def run(command, log, timeout=180):
    with (RUNTIME / log).open("ab") as output:
        result = subprocess.run(
            [str(v) for v in command],
            cwd=ROOT,
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    if result.returncode:
        raise RuntimeError(
            f"A startup command failed. Details: .yummy-flow-runtime/{log}"
        )


def compose(docker, *arguments):
    run(
        [
            docker,
            "compose",
            "--project-directory",
            ROOT,
            "-f",
            ROOT / "compose.yaml",
            *arguments,
        ],
        "postgres.log",
    )


def docker_ready(docker):
    try:
        return (
            subprocess.run(
                [str(docker), "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ).returncode
            == 0
        )
    except subprocess.TimeoutExpired:
        return False


def ensure_docker(docker):
    if docker_ready(docker):
        return
    desktop = docker.parent.parent.parent / "Docker Desktop.exe"
    if not desktop.is_file():
        raise RuntimeError(
            "Docker Engine is not reachable. Open Docker Desktop, then try START again."
        )
    say("Starting Docker Desktop; waiting for its engine...")
    subprocess.Popen(
        [str(desktop)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if docker_ready(docker):
            return
        time.sleep(2)
    raise RuntimeError(
        "Docker is not ready. Check Docker Desktop for a Windows approval or error, then retry."
    )


def record(service):
    path = RUNTIME / f"{service}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    name = data["job"]
    if not name.startswith(PREFIX):
        raise RuntimeError(f"Refusing unfamiliar process record: {path.name}")
    UUID(name[len(PREFIX) :])
    return data


def running(service):
    data = record(service)
    return bool(data and jobs.exists(data["job"]))


def port_busy(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def backend_command(*args):
    return [
        str(POWERSHELL),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT / "scripts/backend.ps1"),
        *args,
    ]


def worker(service, name, node=None):
    command = (
        backend_command(
            "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"
        )
        if service == "backend"
        else [
            node,
            str(ROOT / "frontend/node_modules/next/dist/bin/next"),
            "dev",
            "--hostname",
            "127.0.0.1",
            "--port",
            "3000",
        ]
    )
    path = RUNTIME / f"{service}.json"

    def ready(pid):
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"job": name, "pid": pid}))
        temporary.replace(path)

    try:
        jobs.supervise(
            name,
            command,
            str(ROOT / ("backend" if service == "backend" else "frontend")),
            ready,
        )
    finally:
        if path.exists() and record(service)["job"] == name:
            path.unlink()


def launch(service, node=None):
    if running(service):
        say(f"{service.capitalize()} is already running under this launcher.")
        return False
    name = PREFIX + str(uuid4())
    command = [str(PYTHON), str(Path(__file__).resolve()), "worker", service, name]
    if node:
        command.append(str(node))
    with (RUNTIME / f"{service}.log").open("wb") as output:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        data = record(service)
        if data and data["job"] == name and jobs.exists(name):
            return True
        if process.poll() is not None:
            break
        time.sleep(0.2)
    jobs.stop(name)
    raise RuntimeError(
        f"{service.capitalize()} could not start. See .yummy-flow-runtime/{service}.log"
    )


def stop_service(service):
    data = record(service)
    if data:
        jobs.stop(data["job"])
        deadline = time.monotonic() + 15
        while jobs.exists(data["job"]) and time.monotonic() < deadline:
            time.sleep(0.2)
        if jobs.exists(data["job"]):
            raise RuntimeError(f"{service} is still closing. Retry STOP shortly.")
    say(f"{service.capitalize()} launcher processes stopped.")


def reachable(service, url, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not running(service):
            raise RuntimeError(
                f"{service.capitalize()} exited. See .yummy-flow-runtime/{service}.log"
            )
        try:
            with urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(1)
    raise RuntimeError(
        f"{service.capitalize()} did not become ready. See .yummy-flow-runtime/{service}.log"
    )


def start():
    for path in (
        ROOT / ".env",
        PYTHON,
        ROOT / "frontend/node_modules/next/dist/bin/next",
    ):
        if not path.is_file():
            raise RuntimeError(
                f"Missing {path.relative_to(ROOT)}. See RUNNING_THE_APP.md."
            )
    # Never adopt or terminate a server started by an editor or another application.
    for service, port in (("backend", 8000), ("frontend", 3000)):
        if port_busy(port) and not running(service):
            raise RuntimeError(
                f"Port {port} is already in use outside this launcher. Close that server, then retry."
            )
    docker, node = docker_path(), node_path()
    os.environ["PATH"] = (
        str(docker.parent)
        + os.pathsep
        + str(node.parent)
        + os.pathsep
        + os.environ["PATH"]
    )
    ensure_docker(docker)
    say("Starting PostgreSQL and waiting for its health check...")
    compose(docker, "up", "-d", "--wait", "--wait-timeout", "90", "postgres")
    say("Checking database migrations...")
    run(backend_command("-m", "app.database.migrate"), "migrations.log")
    started = []
    try:
        for service in ("backend", "frontend"):
            say(f"Starting {service} in the background...")
            if launch(service, node):
                started.append(service)
        say("Waiting for the API and application pages...")
        reachable("backend", "http://127.0.0.1:8000/health", 60)
        reachable("backend", "http://127.0.0.1:8000/api/v1/scenarios?limit=1", 30)
        reachable("frontend", "http://localhost:3000", 180)
    except BaseException:
        for service in reversed(started):
            stop_service(service)
        raise
    try:
        os.startfile("http://localhost:3000")
    except OSError:
        say(
            "The app is ready, but Windows could not open a browser. Visit http://localhost:3000."
        )
    say("SUCCESS - Yummy Flow is running at http://localhost:3000")
    say("You can close this window. Double-click STOP_YUMMY_FLOW.bat when finished.")


def stop():
    errors = []
    for service in ("frontend", "backend"):
        try:
            stop_service(service)
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(str(error))
    try:
        docker = docker_path()
        os.environ["PATH"] = str(docker.parent) + os.pathsep + os.environ["PATH"]
        if docker_ready(docker):
            compose(docker, "stop", "postgres")
            say("Project PostgreSQL stopped. Database data is preserved.")
        else:
            errors.append(
                "Docker is unreachable; PostgreSQL stop could not be verified. Open Docker Desktop and retry STOP."
            )
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        errors.append(str(error))
    if errors:
        raise RuntimeError("\n".join(errors))
    say(
        "COMPLETE - Yummy Flow is stopped. Unrelated processes and Docker Desktop were left alone."
    )


if __name__ == "__main__":
    RUNTIME.mkdir(exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        worker(*sys.argv[2:])
    else:
        import msvcrt

        with (RUNTIME / "launcher.lock").open("a+b") as lock:
            lock.seek(0, 2)
            if lock.tell() == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                say("Another START or STOP is in progress. Wait for it to finish.")
                sys.exit(1)
            try:
                {"start": start, "stop": stop}[sys.argv[1]]()
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
                KeyError,
            ) as error:
                say(f"Yummy Flow could not complete this action: {error}")
                say("No database data was deleted. Logs are in .yummy-flow-runtime.")
                sys.exit(1)
