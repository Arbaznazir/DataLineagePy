"""Shared connection lifecycle for SQL connectors."""

import re


class DatabaseConnector:
    """Connection lifecycle shared by the SQL connectors."""

    connection = None
    engine = None

    def disconnect(self):
        """Close the connection and dispose of the engine."""
        connection = self.connection
        engine = self.engine
        self.connection = None
        self.engine = None
        if connection is not None:
            connection.close()
        if engine is not None:
            engine.dispose()

    def test_connection(self) -> bool:
        """Return whether a trivial query succeeds on the open connection."""
        try:
            result = self.connection.execute("SELECT 1")
            return result.fetchone() is not None
        except Exception:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.disconnect()
        return False

    @staticmethod
    def quote_identifier(name: str, quote: str = '"') -> str:
        """Quote a plain SQL identifier."""
        if not re.match(r"^[A-Za-z_][\w]*$", name or ""):
            raise ValueError("Unsupported identifier: {!r}".format(name))
        return "{quote}{name}{quote}".format(quote=quote, name=name)
