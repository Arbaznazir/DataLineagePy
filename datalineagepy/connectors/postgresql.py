"""PostgreSQL connector with lineage tracking."""

import pandas as pd

from datalineagepy.connectors._engine import SQLALCHEMY_INSTALLED
from datalineagepy.connectors._engine import create_engine as _default_create_engine
from datalineagepy.connectors.base import DatabaseConnector
from datalineagepy.connectors.query_tracking import create_lineage_dataframe
from datalineagepy.connectors.query_tracking import track_sql_lineage
from datalineagepy.connectors.sql_parser import SQLLineageParser
from datalineagepy.core.tracker import LineageTracker

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional driver
    psycopg2 = None

SQLALCHEMY_AVAILABLE = SQLALCHEMY_INSTALLED
create_engine = _default_create_engine


class PostgreSQLConnector(DatabaseConnector):
    """Read a PostgreSQL database while recording lineage.

    A ``sqlite://`` URL also works, which lets the connector be exercised
    without a PostgreSQL server.
    """

    def __init__(self, connection_string=None, use_sqlalchemy=True, tracker=None,
                 lineage_tracker=None, host=None, user=None, password=None,
                 database=None, port=None):
        if connection_string is None:
            if not host or not database:
                raise TypeError(
                    "PostgreSQLConnector requires a connection string or host and database"
                )
            connection_string = "postgresql://{}:{}@{}:{}/{}".format(
                user or "", password or "", host, port or 5432, database
            )
        self.connection_string = connection_string
        self.use_sqlalchemy = bool(use_sqlalchemy)
        self.connection = None
        self.engine = None
        self.tracker = tracker or lineage_tracker or LineageTracker.get_global_instance()
        self.lineage_tracker = self.tracker
        self.sql_parser = SQLLineageParser()

    def connect(self):
        """Open the database and return the connection."""
        if self.use_sqlalchemy:
            self.engine = create_engine(self.connection_string)
            self.connection = self.engine.connect()
            return self.connection
        if psycopg2 is None:
            raise ImportError("psycopg2 is required when use_sqlalchemy is False")
        self.connection = psycopg2.connect(self.connection_string)
        return self.connection

    def read_table(self, table_name, schema="public"):
        """Read a schema-qualified table into a LineageDataFrame."""
        query = "SELECT * FROM {}.{}".format(
            self.quote_identifier(schema),
            self.quote_identifier(table_name),
        )
        frame = pd.read_sql(query, self.connection)
        return self._create_lineage_dataframe(frame, table_name)

    def execute_query(self, query, params=None):
        """Run a SQL query and record the source tables."""
        if params is None:
            frame = pd.read_sql(query, self.connection)
        else:
            frame = pd.read_sql(query, self.connection, params=params)
        result = self._create_lineage_dataframe(frame, "query_result")
        self._track_sql_lineage(self.sql_parser.parse_query(query), result)
        return result

    def get_schema(self, table_name, schema="public"):
        """Return a mapping of column name to PostgreSQL data type."""
        statement = (
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = '{}' AND table_name = '{}' "
            "ORDER BY ordinal_position"
        ).format(schema, table_name)
        rows = self.connection.execute(statement).fetchall()
        return {row[0]: row[1] for row in rows}

    def list_tables(self, schema="public"):
        """Return table names in one schema."""
        statement = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = '{}' AND table_type = 'BASE TABLE'"
        ).format(schema)
        rows = self.connection.execute(statement).fetchall()
        return [row[0] for row in rows]

    def get_connection_info(self):
        """Describe the open connection and server version."""
        if self.connection is None:
            return {"status": "disconnected"}
        version = self.connection.execute("SELECT version()").fetchone()[0]
        return {
            "status": "connected",
            "backend": "sqlalchemy" if self.use_sqlalchemy else "psycopg2",
            "postgresql_version": version,
        }

    def _create_lineage_dataframe(self, frame, name):
        return create_lineage_dataframe(frame, name, self.tracker)

    def _track_sql_lineage(self, lineage_info, result_df):
        track_sql_lineage(self, lineage_info, result_df)
