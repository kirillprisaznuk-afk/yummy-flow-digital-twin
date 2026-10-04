"""Opt-in Windows integration check; restarts this project's local services.

Run with .venv/Scripts/python.exe scripts/test_launcher.py. Requires the existing
local setup. Opens the browser via START and leaves application services stopped.
"""

import json
import subprocess
import sys
from urllib.request import Request, urlopen
from uuid import uuid4

import launcher


def request(path, payload=None, method=None):
    data = None if payload is None else json.dumps(payload).encode()
    with urlopen(
        Request(
            "http://127.0.0.1:8000/api/v1" + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        ),
        timeout=15,
    ) as response:
        body = response.read()
        return json.loads(body) if body else None


def batch(action):
    subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            str(launcher.ROOT / f"{action}_YUMMY_FLOW.bat"),
            "--no-pause",
        ],
        cwd=launcher.ROOT,
        timeout=360,
        check=True,
    )


def main():
    sentinels = []
    try:
        for command in (
            # Avoid the Windows venv redirector so cleanup owns the actual sleeper.
            [sys._base_executable, "-c", "import time; time.sleep(1200)"],
            [str(launcher.node_path()), "-e", "setTimeout(() => {}, 1200000)"],
        ):
            sentinels.append(
                subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            )
        batch("STOP")
        batch("START")
        with urlopen("http://localhost:3000", timeout=60) as response:
            assert response.status == 200
        assumptions = request("/defaults")
        assumptions["orders_per_day"] = "123"
        saved = request(
            "/scenarios",
            {"name": f"Launcher check {uuid4()}", "assumptions": assumptions},
        )
        path = f"/scenarios/{saved['id']}"
        before = request(path + "/evaluation")
        assert request(path)["assumptions"] == assumptions
        identities = {
            service: launcher.record(service) for service in ("backend", "frontend")
        }
        batch("START")
        assert identities == {
            service: launcher.record(service) for service in identities
        }
        batch("STOP")
        assert not launcher.port_busy(8000) and not launcher.port_busy(3000)
        assert all(process.poll() is None for process in sentinels)
        docker = launcher.docker_path()
        status = subprocess.run(
            [str(docker), "compose", "ps", "--all", "--format", "json", "postgres"],
            cwd=launcher.ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(status.stdout)["State"] == "exited"
        batch("START")
        assert request(path + "/evaluation") == before
        request(path, method="DELETE")
        print(
            "PASS: HTTP readiness, save/retrieve, repeat START, database restart persistence."
        )
    finally:
        try:
            batch("STOP")
            assert not launcher.port_busy(8000) and not launcher.port_busy(3000)
            assert all(process.poll() is None for process in sentinels)
            print(
                "PASS: STOP closes application ports and preserves unrelated Python/Node processes."
            )
        finally:
            for process in sentinels:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
