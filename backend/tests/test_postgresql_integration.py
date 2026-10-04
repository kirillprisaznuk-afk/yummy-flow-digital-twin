"""Opt-in PostgreSQL checks using isolated schemas or the dedicated local test database."""

import os
import subprocess
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema
from test_http_smoke import request_json, running_api

from app.database.session import Database
from app.main import create_app


@pytest.mark.postgresql
def test_postgresql_persistence_round_trip_and_application_restart():
    configured_url = os.getenv("YUMMY_TEST_POSTGRES_URL")
    if not configured_url:
        pytest.skip("No PostgreSQL server configured: set YUMMY_TEST_POSTGRES_URL to run")
    url = make_url(configured_url)
    assert url.get_backend_name() == "postgresql", "This test requires real PostgreSQL"
    url = url.set(drivername="postgresql+psycopg")
    schema = "yummy_review_" + uuid4().hex
    engine = create_engine(url)
    created_schema = False
    try:
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
            created_schema = True
        scoped = url.update_query_dict({"options": f"-csearch_path={schema}"})
        scoped_url = scoped.render_as_string(hide_password=False)
        database = Database(scoped_url)
        try:
            database.initialize()
            database.require_current_schema()
        finally:
            database.close()
        with TestClient(create_app(scoped_url)) as client:
            created = client.post(
                "/api/v1/scenarios",
                json={"name": "PostgreSQL smoke", "assumptions": {"orders_per_day": 0}},
            )
            assert created.status_code == 201
            record = created.json()
            path = f"/api/v1/scenarios/{record['id']}"
            assert client.get(path).json() == record
            record["assumptions"]["monthly_rent"] = "7000"
            updated = client.put(
                path, json={"name": "Updated", "assumptions": record["assumptions"]}
            )
            assert updated.status_code == 200
            saved = updated.json()
            evaluated = client.get(path + "/evaluation")
            assert evaluated.status_code == 200
            assert (
                Decimal(evaluated.json()["evaluation"]["economics"]["operating_profit"]) == -110160
            )
        with TestClient(create_app(scoped_url)) as restarted:
            assert restarted.get(path).json() == saved
            assert restarted.delete(path).status_code == 204
            assert restarted.get(path).status_code == 404
    finally:
        if created_schema:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        engine.dispose()


@pytest.mark.postgresql
def test_local_compose_data_survives_api_and_database_process_restarts(tmp_path):
    """Explicit opt-in: briefly restart only this project's local database service."""
    if os.getenv("YUMMY_TEST_COMPOSE_RESTART") != "1":
        pytest.skip("Set YUMMY_TEST_COMPOSE_RESTART=1 to restart the local Compose database")
    database_url = os.environ["YUMMY_TEST_POSTGRES_URL"]
    url = make_url(database_url)
    assert url.get_backend_name() == "postgresql"
    assert url.host in ("127.0.0.1", "localhost")
    assert url.database == "yummy_flow_test", "Restart test is local/test-only"
    database = Database(database_url)
    database.initialize()
    database.require_current_schema()
    with database.engine.connect() as connection:
        started_before = connection.scalar(text("SELECT pg_postmaster_start_time()"))
    database.close()
    project_root = Path(__file__).resolve().parents[2]
    with running_api(database_url, tmp_path / "before.log") as api:
        record = request_json(
            api,
            "/api/v1/scenarios",
            {"name": "Synthetic restart verification", "assumptions": {"orders_per_day": 0}},
        )
        path = f"/api/v1/scenarios/{record['id']}"
        assert request_json(api, path) == record
        assumptions = record["assumptions"]
        assumptions["monthly_rent"] = "7000"
        updated = request_json(
            api, path, {"name": "Synthetic replaced scenario", "assumptions": assumptions}, "PUT"
        )
        before = request_json(api, path + "/evaluation")
        assert Decimal(before["evaluation"]["economics"]["operating_profit"]) == -110160
    subprocess.run(
        ["docker", "compose", "restart", "postgres"],
        cwd=project_root,
        check=True,
        timeout=60,
    )
    subprocess.run(
        ["docker", "compose", "up", "-d", "--wait", "--wait-timeout", "60", "postgres"],
        cwd=project_root,
        check=True,
        timeout=90,
    )
    with running_api(database_url, tmp_path / "after.log") as api:
        assert request_json(api, path) == updated
        assert request_json(api, path + "/evaluation") == before
    database = Database(database_url)
    try:
        with database.engine.connect() as connection:
            assert connection.scalar(text("SELECT pg_postmaster_start_time()")) > started_before
    finally:
        database.close()
    # Preserve other test/development scenarios; remove only this test's UUID.
    with TestClient(create_app(database_url)) as client:
        assert client.delete(path).status_code == 204
