# Enterprise Integrations Guide

## Overview

DataLineagePy's Enterprise Integrations framework provides comprehensive connectivity to major enterprise data platforms, cloud providers, BI tools, and other systems. This guide covers setup, configuration, and usage of the integration framework.

## Table of Contents

1. [Architecture](#architecture)
2. [Supported Integrations](#supported-integrations)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Data Platform Connectors](#data-platform-connectors)
6. [Cloud Provider Integrations](#cloud-provider-integrations)
7. [BI Tool Connectors](#bi-tool-connectors)
8. [Authentication](#authentication)
9. [Lineage Extraction](#lineage-extraction)
10. [Monitoring and Health Checks](#monitoring-and-health-checks)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)
13. [API Reference](#api-reference)

## Architecture

The Enterprise Integrations framework follows a modular, plugin-based architecture:

```
datalineagepy/integrations/
├── core/                    # Core integration framework
│   ├── base_connector.py    # Abstract base connector
│   ├── connector_manager.py # Connector lifecycle management
│   └── __init__.py         # Framework initialization
├── data_platforms/         # Data platform connectors
│   ├── snowflake_connector.py
│   ├── databricks_connector.py
│   └── ...
├── cloud_providers/        # Cloud provider integrations
│   ├── aws_connector.py
│   ├── azure_connector.py
│   └── ...
├── bi_tools/              # BI tool connectors
│   ├── tableau_connector.py
│   ├── powerbi_connector.py
│   └── ...
└── examples/              # Integration examples
```

### Key Components

- **BaseConnector**: Abstract base class for all connectors
- **ConnectorManager**: Manages connector lifecycle and health
- **ConnectorRegistry**: Registry for connector discovery
- **Authentication Manager**: Handles enterprise authentication
- **Connection Pool**: Manages connection pooling and reuse

## Supported Integrations

### Data Platforms (10 connectors)
- **Snowflake** - Cloud data warehouse
- **Databricks** - Unified analytics platform
- **Google BigQuery** - Cloud data warehouse
- **Amazon Redshift** - Cloud data warehouse
- **Azure Synapse** - Analytics platform
- **PostgreSQL** - Open source database
- **MySQL** - Popular database
- **Oracle Database** - Enterprise database
- **MongoDB** - Document database
- **Apache Cassandra** - NoSQL database

### Cloud Providers (3 major providers)
- **Amazon Web Services (AWS)** - S3, Glue, Athena, EMR, Kinesis
- **Microsoft Azure** - Blob Storage, Data Factory, Event Hubs
- **Google Cloud Platform (GCP)** - Cloud Storage, Dataflow, Pub/Sub

### BI Tools (4 major platforms)
- **Tableau** - Enterprise visualization platform
- **Microsoft Power BI** - Business intelligence platform
- **Looker** - Modern BI platform
- **Qlik Sense** - Associative analytics platform

### Additional Categories
- **Data Catalogs**: Apache Atlas, Collibra, Alation, Microsoft Purview
- **Workflow Orchestration**: Apache Airflow, Prefect, Dagster
- **Message Queues**: Apache Kafka, RabbitMQ, AWS SQS
- **Authentication**: LDAP, SAML, OAuth, Azure AD
- **Monitoring**: Prometheus, Grafana, Datadog

## Quick Start

### 1. Installation

```bash
# Install core integrations
pip install -r requirements-integrations.txt

# Or install specific connector dependencies
pip install snowflake-connector-python  # For Snowflake
pip install tableauserverclient         # For Tableau
```

### 2. Basic Usage

```python
import asyncio
from datalineagepy.integrations.core import create_connector_manager
from datalineagepy.integrations.data_platforms import SnowflakeConnector, SnowflakeConfig

async def main():
    # Create connector manager
    manager = create_connector_manager()
    
    # Configure Snowflake connector
    config = SnowflakeConfig(
        name="prod_snowflake",
        account="your_account",
        username="your_username",
        password="your_password",
        warehouse="COMPUTE_WH",
        database="ANALYTICS_DB"
    )
    
    # Create and register connector
    connector = SnowflakeConnector(config)
    await manager.register_connector(connector)
    
    # Connect and extract metadata
    await connector.connect()
    metadata = await connector.get_metadata()
    
    print(f"Extracted metadata: {len(metadata)} entities")
    
    # Cleanup
    await manager.shutdown()

# Run the example
asyncio.run(main())
```

## Configuration

### Environment Variables

```bash
# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USERNAME=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# Tableau
TABLEAU_SERVER_URL=https://your-tableau-server.com
TABLEAU_USERNAME=your_username
TABLEAU_PASSWORD=your_password
TABLEAU_SITE_ID=your_site

# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

### Configuration Files

```yaml
# config/integrations.yaml
connectors:
  snowflake:
    account: "${SNOWFLAKE_ACCOUNT}"
    username: "${SNOWFLAKE_USERNAME}"
    password: "${SNOWFLAKE_PASSWORD}"
    warehouse: "COMPUTE_WH"
    database: "ANALYTICS_DB"
    
  tableau:
    server_url: "${TABLEAU_SERVER_URL}"
    username: "${TABLEAU_USERNAME}"
    password: "${TABLEAU_PASSWORD}"
    site_id: "default"
    
  aws:
    access_key_id: "${AWS_ACCESS_KEY_ID}"
    secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
    region: "us-east-1"
```

## Data Platform Connectors

### Snowflake Connector

```python
from datalineagepy.integrations.data_platforms import SnowflakeConnector, SnowflakeConfig

# Configuration
config = SnowflakeConfig(
    name="snowflake_prod",
    account="xy12345.us-east-1",
    username="data_engineer",
    password="secure_password",
    warehouse="COMPUTE_WH",
    database="ANALYTICS_DB",
    schema="PUBLIC",
    role="DATA_ENGINEER_ROLE"
)

# Create connector
connector = SnowflakeConnector(config)

# Connect and use
await connector.connect()
metadata = await connector.get_metadata()
lineage = await connector.get_lineage("ANALYTICS_DB.PUBLIC.SALES_DATA")
```

### Databricks Connector

```python
from datalineagepy.integrations.data_platforms import DatabricksConnector, DatabricksConfig

config = DatabricksConfig(
    name="databricks_prod",
    server_hostname="your-workspace.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/your-warehouse-id",
    access_token="your_access_token"
)

connector = DatabricksConnector(config)
```

### BigQuery Connector

```python
from datalineagepy.integrations.data_platforms import BigQueryConnector, BigQueryConfig

config = BigQueryConfig(
    name="bigquery_prod",
    project_id="your-gcp-project",
    credentials_path="/path/to/service-account.json",
    location="US"
)

connector = BigQueryConnector(config)
```

## Cloud Provider Integrations

### AWS Integration

```python
from datalineagepy.integrations.cloud_providers import AWSConnector, AWSConfig

config = AWSConfig(
    name="aws_prod",
    access_key_id="your_access_key",
    secret_access_key="your_secret_key",
    region="us-east-1"
)

connector = AWSConnector(config)
```

### S3 Connector

```python
from datalineagepy.integrations.cloud_providers import S3Connector, S3Config

config = S3Config(
    name="s3_data_lake",
    bucket_name="your-data-lake-bucket",
    access_key_id="your_access_key",
    secret_access_key="your_secret_key",
    region="us-east-1"
)

connector = S3Connector(config)
```

## BI Tool Connectors

### Tableau Connector

```python
from datalineagepy.integrations.bi_tools import TableauConnector, TableauConfig

# Username/Password Authentication
config = TableauConfig(
    name="tableau_prod",
    server_url="https://your-tableau-server.com",
    username="your_username",
    password="your_password",
    site_id="your_site"
)

# Personal Access Token Authentication
config = TableauConfig(
    name="tableau_prod",
    server_url="https://your-tableau-server.com",
    personal_access_token_name="your_token_name",
    personal_access_token_secret="your_token_secret",
    site_id="your_site"
)

connector = TableauConnector(config)
await connector.connect()

# Extract workbook lineage
lineage = await connector.get_lineage("workbook:your-workbook-id")
```

### Power BI Connector

```python
from datalineagepy.integrations.bi_tools import PowerBIConnector, PowerBIConfig

config = PowerBIConfig(
    name="powerbi_prod",
    tenant_id="your_tenant_id",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

connector = PowerBIConnector(config)
```

## Authentication

### Supported Authentication Methods

1. **Username/Password** - Basic authentication
2. **Personal Access Tokens** - Token-based authentication
3. **OAuth 2.0** - Modern OAuth flow
4. **Service Principal** - Azure AD service accounts
5. **Private Key** - Certificate-based authentication
6. **SAML** - Enterprise SSO
7. **LDAP** - Directory-based authentication

### Authentication Configuration

```python
# OAuth Configuration
from datalineagepy.integrations.core import AuthManager, OAuthConfig

oauth_config = OAuthConfig(
    client_id="your_client_id",
    client_secret="your_client_secret",
    authorization_url="https://auth.provider.com/oauth/authorize",
    token_url="https://auth.provider.com/oauth/token",
    scope="read:data"
)

auth_manager = AuthManager()
token = await auth_manager.get_oauth_token(oauth_config)
```

## Lineage Extraction

### Cross-Platform Lineage

```python
async def extract_cross_platform_lineage():
    # Extract from Snowflake
    snowflake_lineage = await snowflake_connector.get_lineage("DB.SCHEMA.TABLE")
    
    # Extract from Tableau
    tableau_lineage = await tableau_connector.get_lineage("workbook:wb-id")
    
    # Correlate lineage across platforms
    unified_lineage = correlate_lineage([snowflake_lineage, tableau_lineage])
    
    return unified_lineage
```

### Lineage Data Structure

```python
lineage = {
    'entity_id': 'ANALYTICS_DB.PUBLIC.SALES_DATA',
    'entity_type': 'table',
    'system': 'snowflake',
    'upstream_dependencies': [
        {
            'entity_id': 'RAW_DB.STAGING.SALES_RAW',
            'entity_type': 'table',
            'relationship_type': 'derives_from'
        }
    ],
    'downstream_dependencies': [
        {
            'entity_id': 'sales_dashboard',
            'entity_type': 'workbook',
            'system': 'tableau',
            'relationship_type': 'consumed_by'
        }
    ],
    'column_lineage': [
        {
            'source_column': 'sales_amount',
            'target_column': 'total_sales',
            'transformation': 'SUM(sales_amount)'
        }
    ]
}
```

## Monitoring and Health Checks

### Health Check Configuration

```python
from datalineagepy.integrations.core import ConnectorManager

manager = ConnectorManager(
    health_check_interval=30,  # Check every 30 seconds
    retry_attempts=3,
    connection_timeout=30
)

# Get health status
health_status = await manager.get_health_status()
print(f"Overall health: {health_status['overall_status']}")
```

### Metrics and Monitoring

```python
# Get connector metrics
metrics = await connector.get_metrics()
print(f"Query count: {metrics['query_count']}")
print(f"Average response time: {metrics['avg_response_time']}")
print(f"Error rate: {metrics['error_rate']}")
```

## Best Practices

### 1. Connection Management

```python
# Use connection pooling
config = SnowflakeConfig(
    # ... other config
    connection_pool_size=10,
    max_overflow=20,
    pool_timeout=30
)

# Always use context managers
async with connector:
    metadata = await connector.get_metadata()
```

### 2. Error Handling

```python
from datalineagepy.integrations.core import ConnectorError, AuthenticationError

try:
    await connector.connect()
except AuthenticationError as e:
    logger.error(f"Authentication failed: {e}")
    # Handle authentication error
except ConnectorError as e:
    logger.error(f"Connector error: {e}")
    # Handle general connector error
```

### 3. Async Operations

```python
# Use async/await for all operations
async def extract_all_metadata():
    tasks = []
    for connector in connectors:
        task = asyncio.create_task(connector.get_metadata())
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 4. Configuration Management

```python
# Use environment-specific configurations
import os
from datalineagepy.integrations.core import load_config

config = load_config(
    config_file=f"config/{os.getenv('ENVIRONMENT', 'dev')}.yaml"
)
```

## Troubleshooting

### Common Issues

#### 1. Connection Timeouts

```python
# Increase timeout values
config = SnowflakeConfig(
    # ... other config
    connection_timeout=60,
    request_timeout=120
)
```

#### 2. Authentication Failures

```bash
# Check credentials
export SNOWFLAKE_ACCOUNT=your_account
export SNOWFLAKE_USERNAME=your_username
export SNOWFLAKE_PASSWORD=your_password

# Test connection
python -c "
from datalineagepy.integrations.data_platforms import SnowflakeConnector, SnowflakeConfig
import asyncio

async def test():
    config = SnowflakeConfig(account='your_account', username='user', password='pass')
    connector = SnowflakeConnector(config)
    result = await connector.test_connection()
    print(f'Connection test: {result}')

asyncio.run(test())
"
```

#### 3. SSL/TLS Issues

```python
# Disable SSL verification (not recommended for production)
config = SnowflakeConfig(
    # ... other config
    ssl_verify=False
)
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('datalineagepy.integrations')
logger.setLevel(logging.DEBUG)
```

## API Reference

### BaseConnector

```python
class BaseConnector:
    async def connect(self) -> bool
    async def disconnect(self) -> bool
    async def test_connection(self) -> bool
    async def get_metadata(self) -> Dict[str, Any]
    async def get_lineage(self, entity_id: str) -> Dict[str, Any]
    async def execute_query(self, query: str, parameters: Dict = None) -> Any
    async def health_check(self) -> bool
```

### ConnectorManager

```python
class ConnectorManager:
    async def register_connector(self, connector: BaseConnector)
    async def unregister_connector(self, name: str)
    async def get_connector(self, name: str) -> BaseConnector
    async def get_all_connectors(self) -> Dict[str, BaseConnector]
    async def connect_all(self) -> Dict[str, bool]
    async def disconnect_all(self) -> Dict[str, bool]
    async def get_health_status(self) -> Dict[str, Any]
    async def shutdown(self)
```

### Factory Functions

```python
# Create connector manager
manager = create_connector_manager(config: Dict = None)

# Create specific connectors
snowflake_connector = create_connector('snowflake', config)
tableau_connector = create_connector('tableau', config)
```

## Integration Examples

### Multi-Platform Data Pipeline

```python
async def track_data_pipeline():
    """Track data flow across multiple platforms."""
    
    # 1. Extract from source (Snowflake)
    source_lineage = await snowflake_connector.get_lineage("RAW_DB.STAGING.ORDERS")
    
    # 2. Process in Databricks
    processing_lineage = await databricks_connector.get_lineage("analytics.processed_orders")
    
    # 3. Visualize in Tableau
    viz_lineage = await tableau_connector.get_lineage("workbook:orders-dashboard")
    
    # 4. Build unified lineage
    pipeline_lineage = {
        'pipeline_id': 'orders_pipeline',
        'stages': [
            {'system': 'snowflake', 'entity': 'RAW_DB.STAGING.ORDERS', 'role': 'source'},
            {'system': 'databricks', 'entity': 'analytics.processed_orders', 'role': 'transform'},
            {'system': 'tableau', 'entity': 'orders-dashboard', 'role': 'visualize'}
        ],
        'lineage_graph': build_lineage_graph([source_lineage, processing_lineage, viz_lineage])
    }
    
    return pipeline_lineage
```

### Compliance Tracking

```python
async def track_compliance_across_platforms():
    """Track data compliance across all connected systems."""
    
    compliance_report = {}
    
    for connector_name, connector in manager.get_all_connectors().items():
        # Extract metadata
        metadata = await connector.get_metadata()
        
        # Check for PII/sensitive data
        sensitive_entities = identify_sensitive_data(metadata)
        
        # Track access patterns
        access_patterns = await connector.get_access_history()
        
        compliance_report[connector_name] = {
            'sensitive_entities': sensitive_entities,
            'access_patterns': access_patterns,
            'compliance_score': calculate_compliance_score(sensitive_entities, access_patterns)
        }
    
    return compliance_report
```

## Performance Optimization

### Connection Pooling

```python
# Configure connection pooling
config = SnowflakeConfig(
    connection_pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600  # Recycle connections every hour
)
```

### Async Batch Operations

```python
async def batch_metadata_extraction():
    """Extract metadata from multiple systems in parallel."""
    
    tasks = []
    for connector in connectors:
        task = asyncio.create_task(connector.get_metadata())
        tasks.append(task)
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    metadata_collection = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to extract metadata from {connectors[i].name}: {result}")
        else:
            metadata_collection[connectors[i].name] = result
    
    return metadata_collection
```

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-integrations.txt .
RUN pip install -r requirements-integrations.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "-m", "datalineagepy.integrations"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datalineage-integrations
spec:
  replicas: 3
  selector:
    matchLabels:
      app: datalineage-integrations
  template:
    metadata:
      labels:
        app: datalineage-integrations
    spec:
      containers:
      - name: integrations
        image: datalineagepy/integrations:latest
        env:
        - name: SNOWFLAKE_ACCOUNT
          valueFrom:
            secretKeyRef:
              name: integration-secrets
              key: snowflake-account
        - name: TABLEAU_SERVER_URL
          valueFrom:
            configMapKeyRef:
              name: integration-config
              key: tableau-server-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Support and Resources

### Documentation
- [API Documentation](api-docs.md)
- [Connector Development Guide](connector-development.md)
- [Authentication Guide](authentication.md)

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share experiences
- Contributing: Guidelines for contributing to the project

### Enterprise Support
- Professional Services: Implementation and consulting
- Training: Workshops and certification programs
- Priority Support: Dedicated support channels

---

This guide provides comprehensive coverage of DataLineagePy's Enterprise Integrations framework. For specific connector documentation, refer to the individual connector guides in the `docs/connectors/` directory.
