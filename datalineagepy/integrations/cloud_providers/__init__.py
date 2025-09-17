"""
Cloud provider integrations for DataLineagePy.
Supports AWS, Azure, and Google Cloud Platform services.
"""

from .aws_connector import AWSConnector, AWSConfig
from .azure_connector import AzureConnector, AzureConfig  
from .gcp_connector import GCPConnector, GCPConfig
from .s3_connector import S3Connector, S3Config
from .azure_blob_connector import AzureBlobConnector, AzureBlobConfig
from .gcs_connector import GCSConnector, GCSConfig

__all__ = [
    # AWS
    'AWSConnector',
    'AWSConfig',
    'S3Connector', 
    'S3Config',
    
    # Azure
    'AzureConnector',
    'AzureConfig',
    'AzureBlobConnector',
    'AzureBlobConfig',
    
    # Google Cloud
    'GCPConnector',
    'GCPConfig',
    'GCSConnector',
    'GCSConfig'
]

# Supported cloud providers
SUPPORTED_CLOUD_PROVIDERS = {
    'aws': {
        'name': 'Amazon Web Services',
        'connector_class': 'AWSConnector',
        'config_class': 'AWSConfig',
        'services': {
            's3': 'S3Connector',
            'redshift': 'RedshiftConnector',
            'glue': 'GlueConnector',
            'athena': 'AthenaConnector',
            'emr': 'EMRConnector',
            'kinesis': 'KinesisConnector',
            'lambda': 'LambdaConnector',
            'rds': 'RDSConnector'
        },
        'features': ['iam', 'cloudtrail', 'cloudwatch', 'tags']
    },
    'azure': {
        'name': 'Microsoft Azure',
        'connector_class': 'AzureConnector', 
        'config_class': 'AzureConfig',
        'services': {
            'blob_storage': 'AzureBlobConnector',
            'synapse': 'SynapseConnector',
            'data_factory': 'DataFactoryConnector',
            'databricks': 'DatabricksConnector',
            'sql_database': 'AzureSQLConnector',
            'cosmos_db': 'CosmosDBConnector',
            'event_hubs': 'EventHubsConnector'
        },
        'features': ['azure_ad', 'rbac', 'monitor', 'tags']
    },
    'gcp': {
        'name': 'Google Cloud Platform',
        'connector_class': 'GCPConnector',
        'config_class': 'GCPConfig', 
        'services': {
            'gcs': 'GCSConnector',
            'bigquery': 'BigQueryConnector',
            'dataflow': 'DataflowConnector',
            'dataproc': 'DataprocConnector',
            'cloud_sql': 'CloudSQLConnector',
            'firestore': 'FirestoreConnector',
            'pubsub': 'PubSubConnector'
        },
        'features': ['iam', 'audit_logs', 'monitoring', 'labels']
    }
}

# Cloud storage services
CLOUD_STORAGE_SERVICES = {
    's3': {
        'provider': 'aws',
        'name': 'Amazon S3',
        'connector_class': 'S3Connector',
        'features': ['versioning', 'lifecycle', 'encryption', 'access_logs']
    },
    'azure_blob': {
        'provider': 'azure',
        'name': 'Azure Blob Storage',
        'connector_class': 'AzureBlobConnector',
        'features': ['tiers', 'lifecycle', 'encryption', 'access_logs']
    },
    'gcs': {
        'provider': 'gcp',
        'name': 'Google Cloud Storage',
        'connector_class': 'GCSConnector',
        'features': ['classes', 'lifecycle', 'encryption', 'audit_logs']
    }
}

def get_supported_cloud_providers():
    """Get list of supported cloud providers."""
    return SUPPORTED_CLOUD_PROVIDERS

def get_cloud_storage_services():
    """Get list of supported cloud storage services."""
    return CLOUD_STORAGE_SERVICES

def get_provider_info(provider_name: str):
    """Get information about a specific cloud provider."""
    return SUPPORTED_CLOUD_PROVIDERS.get(provider_name.lower())

def get_storage_service_info(service_name: str):
    """Get information about a specific cloud storage service."""
    return CLOUD_STORAGE_SERVICES.get(service_name.lower())

def create_cloud_connector(provider_name: str, config: dict):
    """Factory function to create a cloud connector."""
    provider_info = get_provider_info(provider_name)
    if not provider_info:
        raise ValueError(f"Unsupported cloud provider: {provider_name}")
    
    # Import the connector class dynamically
    connector_class_name = provider_info['connector_class']
    connector_class = globals().get(connector_class_name)
    
    if not connector_class:
        raise ImportError(f"Connector class {connector_class_name} not found")
    
    # Create config object
    config_class_name = provider_info['config_class']
    config_class = globals().get(config_class_name)
    
    if config_class:
        config_obj = config_class(**config)
    else:
        # Fallback to basic config
        from ..core.base_connector import ConnectorConfig, ConnectorType
        config_obj = ConnectorConfig(
            name=config.get('name', provider_name),
            connector_type=ConnectorType.CLOUD_STORAGE,
            **config
        )
    
    return connector_class(config_obj)

def create_storage_connector(service_name: str, config: dict):
    """Factory function to create a cloud storage connector."""
    service_info = get_storage_service_info(service_name)
    if not service_info:
        raise ValueError(f"Unsupported storage service: {service_name}")
    
    # Import the connector class dynamically
    connector_class_name = service_info['connector_class']
    connector_class = globals().get(connector_class_name)
    
    if not connector_class:
        raise ImportError(f"Connector class {connector_class_name} not found")
    
    # Create appropriate config
    if service_name == 's3':
        config_obj = S3Config(**config)
    elif service_name == 'azure_blob':
        config_obj = AzureBlobConfig(**config)
    elif service_name == 'gcs':
        config_obj = GCSConfig(**config)
    else:
        from ..core.base_connector import ConnectorConfig, ConnectorType
        config_obj = ConnectorConfig(
            name=config.get('name', service_name),
            connector_type=ConnectorType.CLOUD_STORAGE,
            **config
        )
    
    return connector_class(config_obj)
