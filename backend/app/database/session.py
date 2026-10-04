"""PostgreSQL target, SQLite local convenience; no connection at module import."""

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.migrate import require_current_schema, upgrade_database


class Database:
    def __init__(self, url: str) -> None:
        parsed = make_url(url)
        options = {"pool_pre_ping": True}
        if parsed.get_backend_name() == "sqlite":
            options["connect_args"] = {"check_same_thread": False}
            if parsed.database in (None, "", ":memory:"):
                options["poolclass"] = StaticPool
        elif parsed.get_backend_name() == "postgresql":
            if parsed.drivername == "postgresql":
                parsed = parsed.set(drivername="postgresql+psycopg")
        else:
            raise ValueError("DATABASE_URL must use PostgreSQL or SQLite")
        self.engine = create_engine(parsed, **options)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    def initialize(self) -> None:
        """Explicitly apply versioned migrations (not called by API startup)."""
        upgrade_database(self.engine)

    def require_current_schema(self) -> None:
        require_current_schema(self.engine)

    def close(self) -> None:
        self.engine.dispose()
