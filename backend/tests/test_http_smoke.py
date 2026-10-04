"""Real loopback HTTP and separate API process restarts, with an isolated database."""

import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from decimal import Decimal
from urllib.error import URLError
from urllib.request import Request, urlopen


def request_json(base_url, path, payload=None, method=None):
    request = Request(
        base_url + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request, timeout=3) as response:
        return json.load(response)


@contextmanager
def running_api(database_url, log_path):
    with socket.socket() as available_port:
        available_port.bind(("127.0.0.1", 0))
        port = available_port.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    with log_path.open("w+") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env={**os.environ, "DATABASE_URL": database_url},
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 15
            ready = False
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    request_json(base_url, "/health")
                except (URLError, TimeoutError):
                    time.sleep(0.1)
                else:
                    ready = True
                    break
            if not ready:
                log.seek(0)
                raise AssertionError("Local API failed to start: " + log.read())
            yield base_url
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_real_http_scenario_survives_process_restart(tmp_path, database_url):
    with running_api(database_url, tmp_path / "first.log") as base_url:
        defaults = request_json(base_url, "/api/v1/defaults")
        defaults["orders_per_day"] = "0"
        record = request_json(
            base_url, "/api/v1/scenarios", {"name": "HTTP smoke", "assumptions": defaults}
        )
        path = f"/api/v1/scenarios/{record['id']}"
        assert request_json(base_url, path) == record
        result = request_json(base_url, path + "/evaluation")["evaluation"]
        assert Decimal(result["economics"]["total_revenue"]) == 0
        assert Decimal(result["economics"]["operating_profit"]) == -109660
        defaults["monthly_rent"] = "7000"
        updated = request_json(base_url, path, {"name": "Updated", "assumptions": defaults}, "PUT")
    with running_api(database_url, tmp_path / "second.log") as base_url:
        assert request_json(base_url, path) == updated
        assert (
            Decimal(
                request_json(base_url, path + "/evaluation")["evaluation"]["economics"][
                    "operating_profit"
                ]
            )
            == -110160
        )
