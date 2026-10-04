import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateTable

from app.database.session import Database
from app.main import create_app
from app.models.scenario import Scenario


def test_scenarios_survive_application_restart(database_url):
    url = database_url
    with TestClient(create_app(url)) as first:
        response = first.post("/api/v1/scenarios", json={"name": "Persistent scenario"})
        assert response.status_code == 201
        record = response.json()
    with TestClient(create_app(url)) as second:
        assert second.get(f"/api/v1/scenarios/{record['id']}").json() == record


def test_environment_database_url_is_used(database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database_url)
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        assert client.app.state.database.engine.url == make_url(database_url)


def test_postgresql_schema_compiles_without_a_server():
    ddl = str(CreateTable(Scenario.__table__).compile(dialect=postgresql.dialect()))
    assert "UUID" in ddl
    assert "JSON" in ddl
    assert "TIMESTAMP WITH TIME ZONE" in ddl


def test_postgresql_url_selects_psycopg_without_connecting():
    database = Database("postgresql://example:example@localhost/example")
    try:
        assert database.engine.url.drivername == "postgresql+psycopg"
    finally:
        database.close()


def test_unsupported_database_dialect_fails_early():
    with pytest.raises(ValueError, match="PostgreSQL or SQLite"):
        Database("mysql://example:example@localhost/example")


def test_uncommitted_flush_rolls_back_on_session_close(tmp_path):
    database = Database(f"sqlite:///{(tmp_path / 'rollback.db').as_posix()}")
    try:
        database.initialize()
        with database.sessions() as session:
            session.add(Scenario(name="Not committed", assumptions={}))
            session.flush()
            # Leaving without commit must roll back the flushed row.
        with database.sessions() as session:
            assert session.scalar(select(func.count()).select_from(Scenario)) == 0
    finally:
        database.close()
