"""
Snowflake connector for DataLineagePy enterprise integrations.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..core.base_connector import BaseConnector, ConnectorConfig, ConnectorType, ConnectionStatus

logger = logging.getLogger(__name__)


@dataclass
class SnowflakeConfig(ConnectorConfig):
    """Snowflake-specific configuration."""
    account: str = None
    warehouse: str = None
    schema: str = None
    role: str = None
    region: str = None
    authenticator: str = 'snowflake'  # snowflake, externalbrowser, oauth
    private_key_path: str = None
    private_key_passphrase: str = None
    session_parameters: Dict[str, Any] = None
    client_session_keep_alive: bool = True
    
    def __post_init__(self):
        """Validate Snowflake configuration."""
        super().__post_init__()
        
        if not self.account:
            raise ValueError("Snowflake account is required")
        
        if not self.warehouse:
            raise ValueError("Snowflake warehouse is required")
        
        # Set connector type
        self.connector_type = ConnectorType.DATABASE
        
        # Build connection string if not provided
        if not self.connection_string:
            self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build Snowflake connection string."""
        parts = [f"account={self.account}"]
        
        if self.username:
            parts.append(f"user={self.username}")
        if self.password:
            parts.append(f"password={self.password}")
        if self.database:
            parts.append(f"database={self.database}")
        if self.schema:
            parts.append(f"schema={self.schema}")
        if self.warehouse:
            parts.append(f"warehouse={self.warehouse}")
        if self.role:
            parts.append(f"role={self.role}")
        if self.region:
            parts.append(f"region={self.region}")
        
        return "&".join(parts)


class SnowflakeConnector(BaseConnector):
    """Snowflake connector for data lineage extraction."""
    
    def __init__(self, config: SnowflakeConfig):
        """Initialize Snowflake connector."""
        super().__init__(config)
        self.snowflake_config = config
        self._connection = None
        self._cursor = None
        
        # Snowflake-specific attributes
        self.current_warehouse = None
        self.current_database = None
        self.current_schema = None
        self.current_role = None
        
        self.logger.info(f"Initialized Snowflake connector for account: {config.account}")
    
    async def connect(self) -> bool:
        """Connect to Snowflake."""
        try:
            self._update_status(ConnectionStatus.CONNECTING)
            
            # Import snowflake-connector-python
            try:
                import snowflake.connector
                from snowflake.connector import DictCursor
            except ImportError:
                raise ImportError("snowflake-connector-python is required for Snowflake integration")
            
            # Prepare connection parameters
            conn_params = {
                'account': self.snowflake_config.account,
                'user': self.snowflake_config.username,
                'password': self.snowflake_config.password,
                'warehouse': self.snowflake_config.warehouse,
                'client_session_keep_alive': self.snowflake_config.client_session_keep_alive
            }
            
            # Optional parameters
            if self.snowflake_config.database:
                conn_params['database'] = self.snowflake_config.database
            if self.snowflake_config.schema:
                conn_params['schema'] = self.snowflake_config.schema
            if self.snowflake_config.role:
                conn_params['role'] = self.snowflake_config.role
            if self.snowflake_config.region:
                conn_params['region'] = self.snowflake_config.region
            if self.snowflake_config.authenticator:
                conn_params['authenticator'] = self.snowflake_config.authenticator
            
            # Private key authentication
            if self.snowflake_config.private_key_path:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                
                with open(self.snowflake_config.private_key_path, 'rb') as key_file:
                    private_key = load_pem_private_key(
                        key_file.read(),
                        password=self.snowflake_config.private_key_passphrase.encode() if self.snowflake_config.private_key_passphrase else None
                    )
                
                pkb = private_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                conn_params['private_key'] = pkb
                del conn_params['password']  # Remove password when using private key
            
            # Session parameters
            if self.snowflake_config.session_parameters:
                conn_params['session_parameters'] = self.snowflake_config.session_parameters
            
            # Create connection
            self._connection = snowflake.connector.connect(**conn_params)
            self._cursor = self._connection.cursor(DictCursor)
            
            # Get current context
            await self._update_current_context()
            
            self._update_status(ConnectionStatus.CONNECTED)
            self.logger.info(f"Connected to Snowflake account: {self.snowflake_config.account}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Snowflake: {e}")
            self._update_status(ConnectionStatus.ERROR)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Snowflake."""
        try:
            if self._cursor:
                self._cursor.close()
                self._cursor = None
            
            if self._connection:
                self._connection.close()
                self._connection = None
            
            self._update_status(ConnectionStatus.DISCONNECTED)
            self.logger.info("Disconnected from Snowflake")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Snowflake: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Snowflake connection."""
        try:
            if not self._connection:
                return False
            
            # Simple test query
            result = await self.execute_query("SELECT CURRENT_VERSION()")
            return result is not None
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute query against Snowflake."""
        if not self._cursor:
            raise RuntimeError("Not connected to Snowflake")
        
        start_time = time.time()
        
        try:
            # Execute query
            if parameters:
                self._cursor.execute(query, parameters)
            else:
                self._cursor.execute(query)
            
            # Fetch results
            results = self._cursor.fetchall()
            
            response_time = time.time() - start_time
            self._log_query(query, True, response_time)
            
            return results
            
        except Exception as e:
            response_time = time.time() - start_time
            self._log_query(query, False, response_time, str(e))
            raise
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Extract metadata from Snowflake."""
        try:
            metadata = {
                'account': self.snowflake_config.account,
                'current_warehouse': self.current_warehouse,
                'current_database': self.current_database,
                'current_schema': self.current_schema,
                'current_role': self.current_role,
                'databases': await self._get_databases(),
                'warehouses': await self._get_warehouses(),
                'roles': await self._get_roles(),
                'users': await self._get_users(),
                'schemas': await self._get_schemas(),
                'tables': await self._get_tables(),
                'views': await self._get_views(),
                'functions': await self._get_functions(),
                'procedures': await self._get_procedures()
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}
    
    async def get_lineage(self, entity_id: str) -> Dict[str, Any]:
        """Extract lineage information for a Snowflake entity."""
        try:
            # Parse entity ID (format: database.schema.table)
            parts = entity_id.split('.')
            if len(parts) != 3:
                raise ValueError("Entity ID must be in format: database.schema.table")
            
            database, schema, table = parts
            
            lineage = {
                'entity_id': entity_id,
                'entity_type': 'table',
                'database': database,
                'schema': schema,
                'table': table,
                'upstream_dependencies': await self._get_upstream_dependencies(database, schema, table),
                'downstream_dependencies': await self._get_downstream_dependencies(database, schema, table),
                'column_lineage': await self._get_column_lineage(database, schema, table),
                'access_history': await self._get_access_history(database, schema, table),
                'query_history': await self._get_query_history(database, schema, table)
            }
            
            return lineage
            
        except Exception as e:
            self.logger.error(f"Failed to extract lineage for {entity_id}: {e}")
            return {}
    
    async def _update_current_context(self):
        """Update current Snowflake context."""
        try:
            # Get current warehouse
            result = await self.execute_query("SELECT CURRENT_WAREHOUSE()")
            self.current_warehouse = result[0]['CURRENT_WAREHOUSE()'] if result else None
            
            # Get current database
            result = await self.execute_query("SELECT CURRENT_DATABASE()")
            self.current_database = result[0]['CURRENT_DATABASE()'] if result else None
            
            # Get current schema
            result = await self.execute_query("SELECT CURRENT_SCHEMA()")
            self.current_schema = result[0]['CURRENT_SCHEMA()'] if result else None
            
            # Get current role
            result = await self.execute_query("SELECT CURRENT_ROLE()")
            self.current_role = result[0]['CURRENT_ROLE()'] if result else None
            
        except Exception as e:
            self.logger.warning(f"Failed to update current context: {e}")
    
    async def _get_databases(self) -> List[Dict[str, Any]]:
        """Get list of databases."""
        try:
            query = "SHOW DATABASES"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get databases: {e}")
            return []
    
    async def _get_warehouses(self) -> List[Dict[str, Any]]:
        """Get list of warehouses."""
        try:
            query = "SHOW WAREHOUSES"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get warehouses: {e}")
            return []
    
    async def _get_roles(self) -> List[Dict[str, Any]]:
        """Get list of roles."""
        try:
            query = "SHOW ROLES"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get roles: {e}")
            return []
    
    async def _get_users(self) -> List[Dict[str, Any]]:
        """Get list of users."""
        try:
            query = "SHOW USERS"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get users: {e}")
            return []
    
    async def _get_schemas(self) -> List[Dict[str, Any]]:
        """Get list of schemas."""
        try:
            query = "SHOW SCHEMAS"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get schemas: {e}")
            return []
    
    async def _get_tables(self) -> List[Dict[str, Any]]:
        """Get list of tables."""
        try:
            query = "SHOW TABLES"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get tables: {e}")
            return []
    
    async def _get_views(self) -> List[Dict[str, Any]]:
        """Get list of views."""
        try:
            query = "SHOW VIEWS"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get views: {e}")
            return []
    
    async def _get_functions(self) -> List[Dict[str, Any]]:
        """Get list of functions."""
        try:
            query = "SHOW FUNCTIONS"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get functions: {e}")
            return []
    
    async def _get_procedures(self) -> List[Dict[str, Any]]:
        """Get list of procedures."""
        try:
            query = "SHOW PROCEDURES"
            results = await self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Failed to get procedures: {e}")
            return []
    
    async def _get_upstream_dependencies(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get upstream dependencies for a table."""
        try:
            # Query information schema for table dependencies
            query = """
            SELECT 
                referenced_database,
                referenced_schema,
                referenced_object_name,
                referenced_object_domain
            FROM information_schema.object_dependencies
            WHERE referencing_database = %s
              AND referencing_schema = %s
              AND referencing_object_name = %s
            """
            
            results = await self.execute_query(query, {
                'database': database,
                'schema': schema,
                'table': table
            })
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.error(f"Failed to get upstream dependencies: {e}")
            return []
    
    async def _get_downstream_dependencies(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get downstream dependencies for a table."""
        try:
            # Query information schema for objects that depend on this table
            query = """
            SELECT 
                referencing_database,
                referencing_schema,
                referencing_object_name,
                referencing_object_domain
            FROM information_schema.object_dependencies
            WHERE referenced_database = %s
              AND referenced_schema = %s
              AND referenced_object_name = %s
            """
            
            results = await self.execute_query(query, {
                'database': database,
                'schema': schema,
                'table': table
            })
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.error(f"Failed to get downstream dependencies: {e}")
            return []
    
    async def _get_column_lineage(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get column-level lineage for a table."""
        try:
            # Query information schema for column lineage
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                comment
            FROM information_schema.columns
            WHERE table_catalog = %s
              AND table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """
            
            results = await self.execute_query(query, {
                'database': database,
                'schema': schema,
                'table': table
            })
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.error(f"Failed to get column lineage: {e}")
            return []
    
    async def _get_access_history(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get access history for a table."""
        try:
            # Query access history (requires ACCOUNTADMIN role)
            query = """
            SELECT 
                query_start_time,
                user_name,
                role_name,
                query_type,
                objects_accessed
            FROM snowflake.account_usage.access_history
            WHERE array_contains(%s::variant, objects_accessed)
            ORDER BY query_start_time DESC
            LIMIT 100
            """
            
            table_identifier = f"{database}.{schema}.{table}"
            results = await self.execute_query(query, {'table_identifier': table_identifier})
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.warning(f"Failed to get access history (may require ACCOUNTADMIN role): {e}")
            return []
    
    async def _get_query_history(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get query history for a table."""
        try:
            # Query query history
            query = """
            SELECT 
                start_time,
                end_time,
                query_text,
                user_name,
                role_name,
                warehouse_name,
                execution_status,
                total_elapsed_time
            FROM snowflake.account_usage.query_history
            WHERE query_text ILIKE %s
            ORDER BY start_time DESC
            LIMIT 50
            """
            
            table_pattern = f"%{database}.{schema}.{table}%"
            results = await self.execute_query(query, {'table_pattern': table_pattern})
            
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            self.logger.warning(f"Failed to get query history: {e}")
            return []
