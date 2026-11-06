"""
Comprehensive tests for SQLite connector.
"""

import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch
from lineagepy.connectors.sqlite import SQLiteConnector


class TestSQLiteConnector:
    """Test suite for SQLite connector functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        # Cleanup
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.fixture
    def sample_dataframe(self):
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'score': [95.5, 87.2, 92.1]
        })

    def test_connector_initialization_file_path(self, temp_db_path):
        """Test SQLite connector initialization with file path."""
        connector = SQLiteConnector(temp_db_path)

        assert connector.database_path == temp_db_path
        assert f'sqlite:///{os.path.abspath(temp_db_path)}' in connector.connection_string
        assert connector.connection is None

    def test_connector_initialization_memory(self):
        """Test SQLite connector initialization with in-memory database."""
        connector = SQLiteConnector(':memory:')

        assert connector.database_path == ':memory:'
        assert connector.connection_string == 'sqlite:///:memory:'
        assert connector.connection is None

    @patch('lineagepy.connectors.sqlite.create_engine')
    def test_sqlalchemy_connection_file(self, mock_create_engine, temp_db_path):
        """Test SQLAlchemy connection to file database."""
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        mock_create_engine.return_value = mock_engine

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connect()

            assert connector.engine == mock_engine
            assert connector.connection == mock_connection

    @patch('lineagepy.connectors.sqlite.sqlite3.connect')
    def test_sqlite3_connection_memory(self, mock_sqlite_connect):
        """Test sqlite3 connection to memory database."""
        mock_connection = Mock()
        mock_sqlite_connect.return_value = mock_connection

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            connector = SQLiteConnector(':memory:', use_sqlalchemy=False)
            connector.connect()

            assert connector.connection == mock_connection
            mock_sqlite_connect.assert_called_once_with(':memory:')

    @patch('lineagepy.connectors.sqlite.pd.read_sql')
    def test_read_table_sqlalchemy(self, mock_read_sql, temp_db_path, sample_dataframe):
        """Test reading table with SQLAlchemy."""
        mock_read_sql.return_value = sample_dataframe

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()

            with patch.object(connector, '_create_lineage_dataframe') as mock_create_lineage:
                mock_lineage_df = Mock()
                mock_create_lineage.return_value = mock_lineage_df

                result = connector.read_table('test_table')

                assert result == mock_lineage_df
                mock_read_sql.assert_called_once_with(
                    'SELECT * FROM "test_table"',
                    connector.connection
                )

    @patch('lineagepy.connectors.sqlite.pd.read_sql_query')
    def test_read_table_sqlite3(self, mock_read_sql_query, temp_db_path, sample_dataframe):
        """Test reading table with sqlite3."""
        mock_read_sql_query.return_value = sample_dataframe

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            connector = SQLiteConnector(temp_db_path, use_sqlalchemy=False)
            connector.connection = Mock()

            with patch.object(connector, '_create_lineage_dataframe') as mock_create_lineage:
                mock_lineage_df = Mock()
                mock_create_lineage.return_value = mock_lineage_df

                result = connector.read_table('test_table')

                assert result == mock_lineage_df
                mock_read_sql_query.assert_called_once_with(
                    'SELECT * FROM "test_table"',
                    connector.connection
                )

    @patch('lineagepy.connectors.sqlite.pd.read_sql')
    def test_execute_query(self, mock_read_sql, temp_db_path, sample_dataframe):
        """Test executing custom SQL query."""
        mock_read_sql.return_value = sample_dataframe

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()

            with patch.object(connector, '_create_lineage_dataframe') as mock_create_lineage:
                with patch.object(connector, '_track_sql_lineage') as mock_track_lineage:
                    mock_lineage_df = Mock()
                    mock_lineage_df._lineage_node_id = 'test_node'
                    mock_create_lineage.return_value = mock_lineage_df

                    query = "SELECT * FROM test_table WHERE score > 90"
                    result = connector.execute_query(query)

                    assert result == mock_lineage_df
                    mock_read_sql.assert_called_once_with(
                        query, connector.connection)
                    mock_track_lineage.assert_called_once()

    def test_get_schema_sqlalchemy(self, temp_db_path):
        """Test getting table schema with SQLAlchemy."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            # SQLAlchemy PRAGMA result format
            (0, 'id', 'INTEGER', 0, None, 1),
            (1, 'name', 'TEXT', 0, None, 0),
            (2, 'score', 'REAL', 0, None, 0)
        ]

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            schema = connector.get_schema('test_table')

            expected = {
                'id': 'INTEGER',
                'name': 'TEXT',
                'score': 'REAL'
            }
            assert schema == expected

    def test_get_schema_sqlite3(self, temp_db_path):
        """Test getting table schema with sqlite3."""
        # Mock sqlite3.Row objects
        mock_row1 = Mock()
        mock_row1.__getitem__ = Mock(side_effect=lambda key: {
                                     'name': 'id', 'type': 'INTEGER'}[key])
        mock_row2 = Mock()
        mock_row2.__getitem__ = Mock(side_effect=lambda key: {
                                     'name': 'name', 'type': 'TEXT'}[key])

        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [mock_row1, mock_row2]

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            with patch('lineagepy.connectors.sqlite.sqlite3.Row'):
                connector = SQLiteConnector(temp_db_path, use_sqlalchemy=False)
                connector.connection = Mock()
                connector.connection.cursor.return_value = mock_cursor

                schema = connector.get_schema('test_table')

                expected = {'id': 'INTEGER', 'name': 'TEXT'}
                assert schema == expected
                mock_cursor.execute.assert_called_once()
                mock_cursor.close.assert_called_once()

    def test_list_tables_sqlalchemy(self, temp_db_path):
        """Test listing tables with SQLAlchemy."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('users',), ('orders',), ('products',)]

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            tables = connector.list_tables()

            expected = ['users', 'orders', 'products']
            assert tables == expected

    def test_list_tables_sqlite3(self, temp_db_path):
        """Test listing tables with sqlite3."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('users',), ('orders',)]

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            connector = SQLiteConnector(temp_db_path, use_sqlalchemy=False)
            connector.connection = Mock()
            connector.connection.cursor.return_value = mock_cursor

            tables = connector.list_tables()

            expected = ['users', 'orders']
            assert tables == expected
            mock_cursor.execute.assert_called_once()
            mock_cursor.close.assert_called_once()

    def test_write_dataframe_sqlalchemy(self, temp_db_path, sample_dataframe):
        """Test writing DataFrame to table with SQLAlchemy."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()

            with patch.object(sample_dataframe, 'to_sql') as mock_to_sql:
                connector._write_dataframe(
                    sample_dataframe, 'test_table', None, 'replace')

                mock_to_sql.assert_called_once_with(
                    'test_table',
                    connector.connection,
                    if_exists='replace',
                    index=False
                )

    @patch('lineagepy.connectors.sqlite.create_engine')
    def test_write_dataframe_sqlite3(self, mock_create_engine, temp_db_path, sample_dataframe):
        """Test writing DataFrame to table with sqlite3."""
        mock_temp_engine = Mock()
        mock_create_engine.return_value = mock_temp_engine

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            connector = SQLiteConnector(temp_db_path, use_sqlalchemy=False)
            connector.connection = Mock()

            with patch.object(sample_dataframe, 'to_sql') as mock_to_sql:
                connector._write_dataframe(
                    sample_dataframe, 'test_table', None, 'append')

                mock_to_sql.assert_called_once_with(
                    'test_table',
                    mock_temp_engine,
                    if_exists='append',
                    index=False
                )
                mock_temp_engine.dispose.assert_called_once()

    def test_get_connection_info_sqlalchemy(self, temp_db_path):
        """Test getting connection info with SQLAlchemy."""
        mock_result = Mock()
        mock_result.fetchone.return_value = ['3.39.4']

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1024000):  # 1MB
                    connector = SQLiteConnector(temp_db_path)
                    connector.connection = Mock()
                    connector.connection.execute.return_value = mock_result

                    info = connector.get_connection_info()

                    assert info['status'] == 'connected'
                    assert info['backend'] == 'sqlalchemy'
                    assert info['sqlite_version'] == '3.39.4'
                    # 1024000 bytes ~ 0.98 MB
                    assert info['file_size_mb'] == 0.98

    def test_get_connection_info_memory(self):
        """Test getting connection info for in-memory database."""
        mock_result = Mock()
        mock_result.fetchone.return_value = ['3.39.4']

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(':memory:')
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            info = connector.get_connection_info()

            assert info['status'] == 'connected'
            assert info['backend'] == 'sqlalchemy'
            assert info['sqlite_version'] == '3.39.4'
            assert 'file_size_mb' not in info  # Memory database doesn't have file size

    def test_get_connection_info_disconnected(self, temp_db_path):
        """Test getting connection info when disconnected."""
        connector = SQLiteConnector(temp_db_path)

        info = connector.get_connection_info()

        assert info['status'] == 'disconnected'

    def test_test_connection_success(self, temp_db_path):
        """Test successful connection test."""
        mock_result = Mock()
        mock_result.fetchone.return_value = [1]

        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()
            connector.connection.execute.return_value = mock_result

            assert connector.test_connection() == True

    def test_test_connection_failure(self, temp_db_path):
        """Test failed connection test."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.connection = Mock()
            connector.connection.execute.side_effect = Exception(
                "Connection failed")

            assert connector.test_connection() == False

    def test_disconnect_sqlalchemy(self, temp_db_path):
        """Test disconnection with SQLAlchemy."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connection = Mock()
            engine = Mock()
            connector.connection = connection
            connector.engine = engine

            connector.disconnect()

            connection.close.assert_called_once()
            engine.dispose.assert_called_once()
            assert connector.connection is None
            assert connector.engine is None

    def test_disconnect_sqlite3(self, temp_db_path):
        """Test disconnection with sqlite3."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
            connector = SQLiteConnector(temp_db_path, use_sqlalchemy=False)
            connection = Mock()
            connector.connection = connection

            connector.disconnect()

            connection.close.assert_called_once()
            assert connector.connection is None

    def test_directory_creation(self):
        """Test that parent directory is created for database file."""
        test_path = "/tmp/nested/path/test.db"

        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs') as mock_makedirs:
                with patch('lineagepy.connectors.sqlite.sqlite3.connect') as mock_connect:
                    with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', False):
                        connector = SQLiteConnector(
                            test_path, use_sqlalchemy=False)
                        connector.connect()

                        mock_makedirs.assert_called_once_with(
                            "/tmp/nested/path")

    def test_sql_lineage_tracking(self, temp_db_path, sample_dataframe):
        """Test SQL lineage tracking functionality."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)
            connector.tracker = Mock()
            connector.tracker.nodes = {}

            # Mock lineage info
            mock_lineage_info = Mock()
            mock_table_ref = Mock()
            mock_table_ref.full_name = 'test_table'
            mock_table_ref.name = 'test_table'
            mock_lineage_info.source_tables = [mock_table_ref]
            mock_lineage_info.query_type = 'SELECT'
            mock_lineage_info.raw_query = 'SELECT * FROM test_table'
            mock_lineage_info.operations = []

            # Mock result DataFrame
            mock_result_df = Mock()
            mock_result_df._lineage_node_id = 'result_node'
            mock_result_df.columns = ['id', 'name', 'score']

            with patch.object(connector, 'get_schema') as mock_get_schema:
                mock_get_schema.return_value = {
                    'id': 'INTEGER', 'name': 'TEXT', 'score': 'REAL'}

                # Test lineage tracking
                connector._track_sql_lineage(mock_lineage_info, mock_result_df)

                # Verify calls were made
                connector.tracker.add_node.assert_called_once()
                connector.tracker.add_edge.assert_called_once()

    def test_error_handling_connection_failure(self, temp_db_path):
        """Test error handling during connection failure."""
        with patch('lineagepy.connectors.sqlite.create_engine') as mock_create_engine:
            mock_create_engine.side_effect = Exception("Connection failed")

            with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
                connector = SQLiteConnector(temp_db_path)

                with pytest.raises(Exception):
                    connector.connect()

    def test_error_handling_read_table_failure(self, temp_db_path):
        """Test error handling during table read failure."""
        with patch('lineagepy.connectors.sqlite.pd.read_sql') as mock_read_sql:
            mock_read_sql.side_effect = Exception("Table not found")

            with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
                connector = SQLiteConnector(temp_db_path)
                connector.connection = Mock()

                with pytest.raises(Exception):
                    connector.read_table('nonexistent_table')

    def test_table_reference_formatting(self, temp_db_path):
        """Test SQLite-specific table reference formatting."""
        with patch('lineagepy.connectors.sqlite.SQLALCHEMY_AVAILABLE', True):
            connector = SQLiteConnector(temp_db_path)

            # Test table name quoting
            with patch.object(connector, 'connect'):
                with patch('lineagepy.connectors.sqlite.pd.read_sql') as mock_read_sql:
                    mock_read_sql.return_value = pd.DataFrame()
                    connector.connection = Mock()

                    with patch.object(connector, '_create_lineage_dataframe') as mock_create:
                        mock_create.return_value = Mock()
                        connector.read_table('test_table')

                        mock_read_sql.assert_called_with(
                            'SELECT * FROM "test_table"',
                            connector.connection
                        )
