"""Explicit schema upgrades. API startup only checks the revision."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def migration_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).with_name("migrations")))
    return config


def upgrade_database(engine: Engine) -> None:
    with engine.begin() as connection:
        current = MigrationContext.configure(connection).get_current_heads()
        if not current and inspect(connection).has_table("scenarios"):
            raise RuntimeError(
                "Unversioned scenarios table found. Back up and review the schema before "
                "stamping revision 0001_scenarios; existing records were not modified. "
                "See docs/DATABASE.md."
            )
        config = migration_config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def require_current_schema(engine: Engine) -> None:
    with engine.connect() as connection:
        current = set(MigrationContext.configure(connection).get_current_heads())
    expected = set(ScriptDirectory.from_config(migration_config()).get_heads())
    if current != expected:
        raise RuntimeError("Database schema is not current. Run: python -m app.database.migrate")


def main() -> None:
    from app.database.session import Database

    database = Database(os.getenv("DATABASE_URL", "sqlite:///./yummy_flow.db"))
    try:
        database.initialize()
        database.require_current_schema()
        print("Database schema upgraded to the current Alembic revision.")
    finally:
        database.close()


if __name__ == "__main__":
    main()
