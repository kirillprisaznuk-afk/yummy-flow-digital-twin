"""Migrations are tested against disposable SQLite; PostgreSQL has its own opt-in test."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select

from app.database.migrate import migration_config
from app.database.session import Database
from app.domain.assumptions import Assumptions
from app.main import create_app
from app.models.scenario import Base, Scenario


def test_upgrade_matches_orm_and_repeated_upgrade_preserves_data(database_url):
    database = Database(database_url)
    try:
        with database.sessions() as session:
            record = Scenario(name="Keep me", assumptions=Assumptions().model_dump(mode="json"))
            session.add(record)
            session.commit()
            identifier = record.id
        database.initialize()
        database.require_current_schema()
        with database.sessions() as session:
            assert session.get(Scenario, identifier).name == "Keep me"
        with database.engine.connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
            assert MigrationContext.configure(connection).get_current_revision() == "0001_scenarios"
    finally:
        database.close()


def test_api_refuses_unmigrated_database_without_creating_tables(tmp_path):
    url = f"sqlite:///{(tmp_path / 'unmigrated.db').as_posix()}"
    with pytest.raises(RuntimeError, match="python -m app.database.migrate"):
        with TestClient(create_app(url)):
            pass
    database = Database(url)
    try:
        assert inspect(database.engine).get_table_names() == []
    finally:
        database.close()


def test_unversioned_existing_database_is_not_overwritten(tmp_path):
    database = Database(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    try:
        Base.metadata.create_all(database.engine)  # Simulate the previous unversioned schema.
        identifier = uuid4()
        with database.sessions() as session:
            session.add(Scenario(id=identifier, name="Legacy", assumptions={}, model_version="1.0"))
            session.commit()
        with pytest.raises(RuntimeError, match="Unversioned scenarios"):
            database.initialize()
        with database.sessions() as session:
            assert session.get(Scenario, identifier).model_version == "1.0"
        assert not inspect(database.engine).has_table("alembic_version")
    finally:
        database.close()


def test_downgrade_and_upgrade_disposable_empty_database(database_url):
    database = Database(database_url)
    try:
        with database.engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
        assert not inspect(database.engine).has_table("scenarios")
        database.initialize()
        with database.sessions() as session:
            assert session.scalars(select(Scenario)).all() == []
    finally:
        database.close()


def test_migration_cli_and_alembic_ini_use_environment_url(tmp_path):
    url = f"sqlite:///{(tmp_path / 'cli.db').as_posix()}"
    env = {**os.environ, "DATABASE_URL": url}
    result = subprocess.run(
        [sys.executable, "-m", "app.database.migrate"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "upgraded" in result.stdout
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    database = Database(url)
    try:
        database.require_current_schema()
    finally:
        database.close()


def test_initial_migration_compiles_to_postgresql_sql_offline():
    # SQL compilation is intentionally not described as live PostgreSQL verification.
    env = {**os.environ, "DATABASE_URL": "postgresql+psycopg://localhost/unused"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "CREATE TABLE scenarios" in result.stdout
    assert "UUID" in result.stdout
    assert "0001_scenarios" in result.stdout
