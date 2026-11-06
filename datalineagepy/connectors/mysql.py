"""MySQL connector with lineage tracking."""

from urllib.parse import urlparse

import pandas as pd

from datalineagepy.connectors._engine import SQLALCHEMY_INSTALLED
from datalineagepy.connectors._engine import create_engine as _default_create_engine
from datalineagepy.connectors.base import DatabaseConnector
from datalineagepy.connectors.sql_lineage import create_lineage_dataframe
from datalineagepy.connectors.sql_lineage import track_sql_lineage
from datalineagepy.connectors.sql_parser import SQLLineageParser
from datalineagepy.core.tracker import LineageTracker

try:
    import pymysql  # noqa: F401
    PYMYSQL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional driver
    PYMYSQL_AVAILABLE = False

SQLALCHEMY_AVAILABLE = SQLALCHEMY_INSTALLED
create_engine = _default_create_engine


class MySQLConnector(DatabaseConnector):
    """Read a MySQL database while recording lineage."""

    def __init__(self, connection_string, use_sqlalchemy=None, tracker=None):
        if (
            use_sqlalchemy is None
            and not SQLALCHEMY_AVAILABLE
            and not PYMYSQL_AVAILABLE
        ):
            raise ImportError("MySQL connector requires SQLAlchemy or PyMySQL")

        self.connection_string = connection_string
        if use_sqlalchemy is None:
            use_sqlalchemy = bool(SQLALCHEMY_AVAILABLE)
        self.use_sqlalchemy = bool(use_sqlalchemy)
        self.connection = None
        self.engine = None
        self.tracker = tracker or LineageTracker.get_global_instance()
        self.sql_parser = SQLLineageParser()

    def _parse_connection_string(self):
        """Return PyMySQL connection keyword arguments."""
        parsed = urlparse(self.connection_string)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/"),
            "charset": "utf8mb4",
            "autocommit": True,
        }

    def connect(self):
        """Open the database and return the connection."""
        if self.use_sqlalchemy:
            self.engine = create_engine(self.connection_string)
            self.connection = self.engine.connect()
            return self.connection

        import pymysql
        self.connection = pymysql.connect(**self._parse_connection_string())
        return self.connection

    def read_table(self, table_name, schema=None):
        """Read a table into a LineageDataFrame."""
        query = "SELECT * FROM {}".format(
            self.quote_identifier(table_name, quote="`")
        )
        frame = pd.read_sql(query, self.connection)
        return self._create_lineage_dataframe(frame, table_name)

    def execute_query(self, query):
        """Run a SQL query and record the source tables."""
        frame = pd.read_sql(query, self.connection)
        result = self._create_lineage_dataframe(frame, "query_result")
        self._track_sql_lineage(self.sql_parser.parse_query(query), result)
        return result

    def get_schema(self, table_name, schema=None):
        """Return a mapping of column name to MySQL data type."""
        statement = "SHOW COLUMNS FROM {}".format(
            self.quote_identifier(table_name, quote="`")
        )
        rows = self.connection.execute(statement).fetchall()
        return {row[0]: row[1] for row in rows}

    def list_tables(self, schema=None):
        """Return table names visible to the connection."""
        rows = self.connection.execute("SHOW TABLES").fetchall()
        return [row[0] for row in rows]

    def _create_lineage_dataframe(self, frame, name):
        return create_lineage_dataframe(frame, name, self.tracker)

    def _track_sql_lineage(self, lineage_info, result_df):
        track_sql_lineage(self, lineage_info, result_df)
