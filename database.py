from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config


class Base(DeclarativeBase):
    pass


_is_sqlite = config.DATABASE_URI.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(config.DATABASE_URI, echo=config.SQL_ECHO, connect_args=_connect_args)

if _is_sqlite:
    # SQLite ignores FOREIGN KEY constraints (and ON DELETE CASCADE) unless this
    # pragma is set on every connection, so ORM-level relationship cascades are
    # backed by real DB-level cascades too.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    import models  # noqa: F401  (register models on Base.metadata before create_all)

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
