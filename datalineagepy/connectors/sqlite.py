"""SQLite connector with lineage tracking."""

import os
import sqlite3

import pandas as pd

from datalineagepy.connectors._engine import SQLALCHEMY_INSTALLED
from datalineagepy.connectors._engine import create_engine as _default_create_engine
from datalineagepy.connectors.base import DatabaseConnector
from datalineagepy.connectors.query_tracking import create_lineage_dataframe
from datalineagepy.connectors.query_tracking import track_sql_lineage
from datalineagepy.connectors.sql_parser import SQLLineageParser
from datalineagepy.core.tracker import LineageTracker

SQLALCHEMY_AVAILABLE = SQLALCHEMY_INSTALLED
create_engine = _default_create_engine


def _is_select(query) -> bool:
    first = str(query).lstrip().split(None, 1)
    if not first:
        return False
    return first[0].upper() in ("SELECT", "WITH", "PRAGMA")


class SQLiteConnector(DatabaseConnector):
    """Read and write a SQLite database while recording lineage."""

    def __init__(self, database_path, use_sqlalchemy=None, tracker=None, lineage_tracker=None):
        self.database_path = database_path
        if database_path == ":memory:":
            self.connection_string = "sqlite:///:memory:"
        else:
            self.connection_string = "sqlite:///{}".format(os.path.abspath(database_path))
        if use_sqlalchemy is None:
            use_sqlalchemy = SQLALCHEMY_AVAILABLE
        self.use_sqlalchemy = bool(use_sqlalchemy)
        self.connection = None
        self.engine = None
        self._memory_connection = None
        self.tracker = tracker or lineage_tracker or LineageTracker.get_global_instance()
        self.lineage_tracker = self.tracker
        self.sql_parser = SQLLineageParser()

    def connect(self):
        """Open the database and return the connection."""
        if self.use_sqlalchemy:
            self.engine = create_engine(self.connection_string)
            self.connection = self.engine.connect()
            return self.connection

        if self.database_path != ":memory:":
            parent = os.path.dirname(self.database_path)
            if parent and not os.path.exists(parent):
                os.makedirs(parent)
        self.connection = sqlite3.connect(self.database_path)
        return self.connection

    def read_table(self, table_name, schema=None):
        """Read a table into a LineageDataFrame."""
        query = "SELECT * FROM {}".format(self.quote_identifier(table_name))
        if self.use_sqlalchemy:
            frame = pd.read_sql(query, self.connection)
        else:
            frame = pd.read_sql_query(query, self.connection)
        return self._create_lineage_dataframe(frame, table_name)

    def execute_query(self, query, params=None):
        """Run a SQL statement and record lineage.

        SELECT statements return a LineageDataFrame. Other statements return
        the affected row count and accept SQLite parameter placeholders.
        """
        if params is not None or not _is_select(query):
            return self._execute_statement(query, params)
        if self.connection is None:
            self.connect()
        if self.use_sqlalchemy:
            frame = pd.read_sql(query, self.connection)
        else:
            frame = pd.read_sql_query(query, self.connection)
        result = self._create_lineage_dataframe(frame, "query_result")
        self._track_sql_lineage(self.sql_parser.parse_query(query), result)
        return result

    def _execute_statement(self, query, params=None):
        """Execute a write, or a parameterized read, on a SQLite connection."""
        own_connection = False
        if isinstance(self.connection, sqlite3.Connection):
            connection = self.connection
        elif self.database_path == ":memory:":
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(":memory:")
            connection = self._memory_connection
        else:
            connection = sqlite3.connect(self.database_path)
            own_connection = True
        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            if _is_select(query):
                columns = [item[0] for item in cursor.description] if cursor.description else []
                frame = pd.DataFrame(cursor.fetchall(), columns=columns)
                result = self._create_lineage_dataframe(frame, "query_result")
                self._track_sql_lineage(self.sql_parser.parse_query(query), result)
                return result
            connection.commit()
            self.tracker.track_operation(
                "sqlite_statement",
                [],
                [],
                {"query": query},
            )
            return cursor.rowcount
        finally:
            if own_connection:
                connection.close()

    def get_schema(self, table_name):
        """Return a mapping of column name to declared SQLite type."""
        statement = 'PRAGMA table_info("{}")'.format(table_name)
        if self.use_sqlalchemy:
            rows = self.connection.execute(statement).fetchall()
            return {row[1]: row[2] for row in rows}

        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        try:
            cursor.execute(statement)
            rows = cursor.fetchall()
            return {row["name"]: row["type"] for row in rows}
        finally:
            cursor.close()

    def list_tables(self):
        """Return user table names in the database."""
        statement = (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        if self.use_sqlalchemy:
            rows = self.connection.execute(statement).fetchall()
            return [row[0] for row in rows]

        cursor = self.connection.cursor()
        try:
            cursor.execute(statement)
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def _write_dataframe(self, frame, table_name, schema, if_exists):
        """Write a DataFrame with either the open connection or a short-lived engine."""
        if self.use_sqlalchemy:
            frame.to_sql(
                table_name,
                self.connection,
                if_exists=if_exists,
                index=False,
            )
            return

        engine = create_engine(self.connection_string)
        try:
            frame.to_sql(table_name, engine, if_exists=if_exists, index=False)
        finally:
            engine.dispose()

    def get_connection_info(self):
        """Describe the open connection, including file size for on-disk databases."""
        if self.connection is None:
            return {"status": "disconnected"}

        version = self.connection.execute("SELECT sqlite_version()").fetchone()[0]
        info = {
            "status": "connected",
            "backend": "sqlalchemy" if self.use_sqlalchemy else "sqlite3",
            "sqlite_version": version,
        }
        if self.database_path != ":memory:" and os.path.exists(self.database_path):
            info["file_size_mb"] = round(
                os.path.getsize(self.database_path) / (1024 * 1024), 2
            )
        return info

    def _create_lineage_dataframe(self, frame, name):
        return create_lineage_dataframe(frame, name, self.tracker)

    def _track_sql_lineage(self, lineage_info, result_df):
        track_sql_lineage(self, lineage_info, result_df)
