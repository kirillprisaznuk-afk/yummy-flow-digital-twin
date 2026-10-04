"""Alembic environment supporting shared test connections and DATABASE_URL."""

import os

from alembic import context
from sqlalchemy.engine import Connection

from app.database.session import Database
from app.models.scenario import Base

config = context.config


def run_with_connection(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=os.getenv("DATABASE_URL", "sqlite:///./yummy_flow.db"),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    run_with_connection(config.attributes["connection"])
else:
    database = Database(os.getenv("DATABASE_URL", "sqlite:///./yummy_flow.db"))
    try:
        with database.engine.begin() as connection:
            run_with_connection(connection)
    finally:
        database.close()
