"""
Core integration framework for DataLineagePy enterprise platform connectors.
"""

from .base_connector import BaseConnector, ConnectorConfig, ConnectionStatus
from .connector_manager import ConnectorManager, ConnectorRegistry
from .auth_manager import AuthenticationManager, AuthConfig, create_auth_manager
from .connection_pool import ConnectionPool, PoolConfig, create_connection_pool
from .retry_handler import RetryHandler, RetryConfig, create_retry_handler
from .event_handler import EventHandler, IntegrationEvent, EventType, EventPriority, create_event_handler
from .metadata_extractor import MetadataExtractor, MetadataSchema, MetadataType, create_metadata_extractor
from .data_flow_mapper import DataFlowMapper, DataFlow, FlowType, create_data_flow_mapper

__all__ = [
    # Base classes
    'BaseConnector',
    'ConnectorConfig', 
    'ConnectionStatus',
    
    # Management
    'ConnectorManager',
    'ConnectorRegistry',
    'AuthenticationManager',
    'AuthConfig',
    
    # Connection handling
    'ConnectionPool',
    'PoolConfig',
    'RetryHandler',
    'RetryConfig',
    
    # Event handling
    'EventHandler',
    'IntegrationEvent',
    'EventType',
    'EventPriority',
    
    # Metadata and lineage
    'MetadataExtractor',
    'MetadataSchema',
    'MetadataType',
    'DataFlowMapper',
    'DataFlow',
    'FlowType'
]

# Default configurations
DEFAULT_CONNECTOR_CONFIG = {
    'timeout': 30,
    'max_retries': 3,
    'retry_delay': 1.0,
    'connection_pool_size': 10,
    'enable_ssl': True,
    'verify_ssl': True,
    'enable_logging': True,
    'log_level': 'INFO'
}

DEFAULT_AUTH_CONFIG = {
    'auth_type': 'basic',
    'token_refresh_threshold': 300,  # 5 minutes
    'cache_credentials': True,
    'encrypt_credentials': True
}

DEFAULT_POOL_CONFIG = {
    'min_connections': 1,
    'max_connections': 10,
    'connection_timeout': 30,
    'idle_timeout': 300,
    'max_lifetime': 3600
}

DEFAULT_RETRY_CONFIG = {
    'max_attempts': 3,
    'base_delay': 1.0,
    'max_delay': 60.0,
    'exponential_base': 2.0,
    'jitter': True
}

# Supported integration types
INTEGRATION_TYPES = {
    'DATA_PLATFORMS': [
        'snowflake', 'databricks', 'bigquery', 'redshift', 'synapse',
        'postgres', 'mysql', 'oracle', 'mongodb', 'cassandra'
    ],
    'CLOUD_PROVIDERS': [
        'aws', 'azure', 'gcp', 'aws_s3', 'azure_blob', 'gcs'
    ],
    'BI_TOOLS': [
        'tableau', 'powerbi', 'looker', 'qlik', 'sisense', 'domo'
    ],
    'DATA_CATALOGS': [
        'atlas', 'collibra', 'alation', 'purview', 'datahub'
    ],
    'ORCHESTRATION': [
        'airflow', 'prefect', 'dagster', 'adf', 'glue', 'dataflow'
    ],
    'MESSAGE_QUEUES': [
        'kafka', 'rabbitmq', 'sqs', 'servicebus', 'pubsub'
    ],
    'MONITORING': [
        'prometheus', 'grafana', 'datadog', 'newrelic', 'splunk'
    ],
    'AUTHENTICATION': [
        'ldap', 'saml', 'oauth', 'azure_ad', 'okta', 'auth0'
    ]
}

# Factory functions
def create_connector_manager(config: dict = None):
    """Create a connector manager with default configuration."""
    if config is None:
        config = DEFAULT_CONNECTOR_CONFIG.copy()
    return ConnectorManager(config)

def create_auth_manager(config: dict = None):
    """Create an authentication manager with default configuration."""
    if config is None:
        config = DEFAULT_AUTH_CONFIG.copy()
    return AuthenticationManager(config)

def create_connection_pool(config: dict = None):
    """Create a connection pool with default configuration."""
    if config is None:
        config = DEFAULT_POOL_CONFIG.copy()
    return ConnectionPool(config)

def get_supported_integrations():
    """Get list of all supported integration types."""
    return INTEGRATION_TYPES

def get_integration_types():
    """Get list of integration categories."""
    return list(INTEGRATION_TYPES.keys())
