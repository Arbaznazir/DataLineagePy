"""SQLAlchemy engine loader with a SQLite fallback for local use."""

import sqlite3

try:
    from sqlalchemy import create_engine as _sqlalchemy_create_engine
except ImportError:  # pragma: no cover - depends on the optional extra
    _sqlalchemy_create_engine = None

SQLALCHEMY_INSTALLED = _sqlalchemy_create_engine is not None


class _SQLiteEngine:
    """Enough of a SQLAlchemy engine for pandas to read a local SQLite file."""

    def __init__(self, database_path):
        self.database_path = database_path or ":memory:"
        self._connection = None

    def connect(self):
        self._connection = sqlite3.connect(self.database_path)
        return self._connection

    def dispose(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None


def create_engine(url, *args, **kwargs):
    """Create a SQLAlchemy engine, or a SQLite stand-in when SQLAlchemy is absent."""
    if _sqlalchemy_create_engine is not None:
        return _sqlalchemy_create_engine(url, *args, **kwargs)

    text = str(url)
    if text.startswith("sqlite:///"):
        path = text[len("sqlite:///"):] or ":memory:"
        return _SQLiteEngine(path)
    if text.startswith("sqlite://"):
        return _SQLiteEngine(":memory:")
    raise ImportError("SQLAlchemy is required to connect to {!r}".format(text))
