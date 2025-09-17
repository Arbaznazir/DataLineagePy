"""
Data platform integrations for DataLineagePy.
Supports major enterprise data platforms and databases.
"""

from .snowflake_connector import SnowflakeConnector, SnowflakeConfig
from .databricks_connector import DatabricksConnector, DatabricksConfig
from .bigquery_connector import BigQueryConnector, BigQueryConfig
from .redshift_connector import RedshiftConnector, RedshiftConfig
from .synapse_connector import SynapseConnector, SynapseConfig
from .postgres_connector import PostgresConnector, PostgresConfig
from .mysql_connector import MySQLConnector, MySQLConfig
from .oracle_connector import OracleConnector, OracleConfig
from .mongodb_connector import MongoDBConnector, MongoDBConfig

__all__ = [
    # Snowflake
    'SnowflakeConnector',
    'SnowflakeConfig',
    
    # Databricks
    'DatabricksConnector', 
    'DatabricksConfig',
    
    # BigQuery
    'BigQueryConnector',
    'BigQueryConfig',
    
    # Redshift
    'RedshiftConnector',
    'RedshiftConfig',
    
    # Synapse
    'SynapseConnector',
    'SynapseConfig',
    
    # PostgreSQL
    'PostgresConnector',
    'PostgresConfig',
    
    # MySQL
    'MySQLConnector',
    'MySQLConfig',
    
    # Oracle
    'OracleConnector',
    'OracleConfig',
    
    # MongoDB
    'MongoDBConnector',
    'MongoDBConfig'
]

# Supported data platforms
SUPPORTED_PLATFORMS = {
    'snowflake': {
        'name': 'Snowflake',
        'connector_class': 'SnowflakeConnector',
        'config_class': 'SnowflakeConfig',
        'type': 'cloud_data_warehouse',
        'features': ['sql', 'streaming', 'semi_structured', 'time_travel']
    },
    'databricks': {
        'name': 'Databricks',
        'connector_class': 'DatabricksConnector', 
        'config_class': 'DatabricksConfig',
        'type': 'unified_analytics',
        'features': ['spark', 'ml', 'streaming', 'delta_lake']
    },
    'bigquery': {
        'name': 'Google BigQuery',
        'connector_class': 'BigQueryConnector',
        'config_class': 'BigQueryConfig', 
        'type': 'cloud_data_warehouse',
        'features': ['sql', 'ml', 'streaming', 'federated_queries']
    },
    'redshift': {
        'name': 'Amazon Redshift',
        'connector_class': 'RedshiftConnector',
        'config_class': 'RedshiftConfig',
        'type': 'cloud_data_warehouse', 
        'features': ['sql', 'columnar', 'spectrum', 'concurrency_scaling']
    },
    'synapse': {
        'name': 'Azure Synapse Analytics',
        'connector_class': 'SynapseConnector',
        'config_class': 'SynapseConfig',
        'type': 'cloud_data_warehouse',
        'features': ['sql', 'spark', 'pipelines', 'power_bi']
    },
    'postgres': {
        'name': 'PostgreSQL',
        'connector_class': 'PostgresConnector',
        'config_class': 'PostgresConfig',
        'type': 'relational_database',
        'features': ['sql', 'json', 'full_text_search', 'extensions']
    },
    'mysql': {
        'name': 'MySQL',
        'connector_class': 'MySQLConnector',
        'config_class': 'MySQLConfig',
        'type': 'relational_database',
        'features': ['sql', 'json', 'replication', 'clustering']
    },
    'oracle': {
        'name': 'Oracle Database',
        'connector_class': 'OracleConnector',
        'config_class': 'OracleConfig',
        'type': 'relational_database',
        'features': ['sql', 'plsql', 'partitioning', 'rac']
    },
    'mongodb': {
        'name': 'MongoDB',
        'connector_class': 'MongoDBConnector',
        'config_class': 'MongoDBConfig',
        'type': 'document_database',
        'features': ['nosql', 'aggregation', 'sharding', 'atlas']
    }
}

def get_supported_platforms():
    """Get list of supported data platforms."""
    return SUPPORTED_PLATFORMS

def get_platform_info(platform_name: str):
    """Get information about a specific platform."""
    return SUPPORTED_PLATFORMS.get(platform_name.lower())

def create_connector(platform_name: str, config: dict):
    """Factory function to create a connector for a specific platform."""
    platform_info = get_platform_info(platform_name)
    if not platform_info:
        raise ValueError(f"Unsupported platform: {platform_name}")
    
    # Import the connector class dynamically
    connector_class_name = platform_info['connector_class']
    connector_class = globals().get(connector_class_name)
    
    if not connector_class:
        raise ImportError(f"Connector class {connector_class_name} not found")
    
    # Create config object
    config_class_name = platform_info['config_class']
    config_class = globals().get(config_class_name)
    
    if config_class:
        config_obj = config_class(**config)
    else:
        # Fallback to basic config
        from ..core.base_connector import ConnectorConfig, ConnectorType
        config_obj = ConnectorConfig(
            name=config.get('name', platform_name),
            connector_type=ConnectorType.DATABASE,
            **config
        )
    
    return connector_class(config_obj)
