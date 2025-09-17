"""
Enterprise Integrations Example for DataLineagePy

This example demonstrates how to use the enterprise integration framework
to connect to various data platforms, cloud providers, and BI tools.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import integration components
try:
    from datalineagepy.integrations.core import (
        ConnectorManager,
        ConnectorRegistry,
        create_connector_manager,
        get_supported_integration_types
    )
    
    # Import specific connectors
    from datalineagepy.integrations.data_platforms import (
        SnowflakeConnector,
        SnowflakeConfig,
        get_supported_platforms as get_data_platforms
    )
    
    from datalineagepy.integrations.cloud_providers import (
        get_supported_cloud_providers,
        get_cloud_storage_services
    )
    
    from datalineagepy.integrations.bi_tools import (
        TableauConnector,
        TableauConfig,
        get_supported_bi_tools
    )
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Running in demo mode with mock implementations")
    
    # Mock implementations for demo
    class MockConnectorManager:
        def __init__(self, config=None):
            self.registry = MockConnectorRegistry()
            self.config = config or {}
            
        async def register_connector(self, connector):
            logger.info(f"Registered connector: {connector.config.name}")
            
        async def get_health_status(self):
            return {
                'overall_status': 'healthy',
                'total_connectors': 2,
                'healthy_connectors': 2,
                'unhealthy_connectors': 0,
                'connector_status': {
                    'demo_snowflake': {'status': 'healthy', 'last_check': '2024-01-15T10:30:00Z'},
                    'demo_tableau': {'status': 'healthy', 'last_check': '2024-01-15T10:30:00Z'}
                }
            }
            
        async def disconnect_all(self):
            logger.info("Disconnected all connectors")
            
        async def shutdown(self):
            logger.info("Connector manager shutdown")
    
    class MockConnectorRegistry:
        def __init__(self):
            self.connectors = {}
            
        def get_all_connectors(self):
            return self.connectors
    
    def create_connector_manager(config=None):
        return MockConnectorManager(config)
        
    def get_supported_integration_types():
        return ['database', 'cloud_storage', 'bi_tool', 'message_queue']
        
    def get_data_platforms():
        return {
            'snowflake': {'name': 'Snowflake', 'features': ['sql', 'streaming', 'time_travel']},
            'databricks': {'name': 'Databricks', 'features': ['spark', 'ml', 'streaming']},
            'bigquery': {'name': 'Google BigQuery', 'features': ['sql', 'ml', 'federated_queries']}
        }
        
    def get_supported_cloud_providers():
        return {
            'aws': {'name': 'Amazon Web Services', 'services': {'s3': 'S3Connector', 'redshift': 'RedshiftConnector'}},
            'azure': {'name': 'Microsoft Azure', 'services': {'blob_storage': 'AzureBlobConnector'}},
            'gcp': {'name': 'Google Cloud Platform', 'services': {'gcs': 'GCSConnector'}}
        }
        
    def get_supported_bi_tools():
        return {
            'tableau': {'name': 'Tableau', 'lineage_capabilities': ['workbook', 'datasource', 'dashboard']},
            'powerbi': {'name': 'Microsoft Power BI', 'lineage_capabilities': ['report', 'dataset', 'dashboard']}
        }
        
    def get_cloud_storage_services():
        return {
            's3': {'provider': 'aws', 'name': 'Amazon S3'},
            'azure_blob': {'provider': 'azure', 'name': 'Azure Blob Storage'}
        }
    
    # Mock connector classes
    class MockConnectorConfig:
        def __init__(self, name, **kwargs):
            self.name = name
            self.connector_type = type('ConnectorType', (), {'value': 'database'})()
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class MockConnector:
        def __init__(self, config):
            self.config = config
            
    class SnowflakeConfig(MockConnectorConfig):
        pass
        
    class SnowflakeConnector(MockConnector):
        pass
        
    class TableauConfig(MockConnectorConfig):
        pass
        
    class TableauConnector(MockConnector):
        pass


class EnterpriseIntegrationsDemo:
    """Demonstration of enterprise integrations capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.connector_manager = None
        self.connected_systems = {}
        
    async def run_demo(self):
        """Run the complete enterprise integrations demo."""
        logger.info("=== DataLineagePy Enterprise Integrations Demo ===")
        
        try:
            # 1. Initialize connector manager
            await self.initialize_connector_manager()
            
            # 2. Show supported integrations
            await self.show_supported_integrations()
            
            # 3. Configure and test data platform connections
            await self.demo_data_platform_integrations()
            
            # 4. Configure and test BI tool connections
            await self.demo_bi_tool_integrations()
            
            # 5. Extract metadata and lineage
            await self.demo_metadata_extraction()
            
            # 6. Show integration health and metrics
            await self.show_integration_health()
            
            # 7. Demonstrate unified lineage across platforms
            await self.demo_cross_platform_lineage()
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
        finally:
            # Cleanup
            await self.cleanup()
    
    async def initialize_connector_manager(self):
        """Initialize the connector manager."""
        logger.info("Initializing connector manager...")
        
        # Create connector manager with custom configuration
        config = {
            'max_connections': 10,
            'health_check_interval': 30,
            'retry_attempts': 3,
            'connection_timeout': 30
        }
        
        self.connector_manager = create_connector_manager(config)
        
        logger.info(f"Connector manager initialized with {len(self.connector_manager.registry.connectors)} connectors")
    
    async def show_supported_integrations(self):
        """Display all supported integration types."""
        logger.info("\n=== Supported Integration Types ===")
        
        # Show core integration types
        integration_types = get_supported_integration_types()
        logger.info(f"Core integration types: {integration_types}")
        
        # Show data platforms
        data_platforms = get_data_platforms()
        logger.info(f"\nSupported Data Platforms ({len(data_platforms)}):")
        for platform, info in data_platforms.items():
            logger.info(f"  - {info['name']} ({platform}): {', '.join(info['features'])}")
        
        # Show cloud providers
        cloud_providers = get_supported_cloud_providers()
        logger.info(f"\nSupported Cloud Providers ({len(cloud_providers)}):")
        for provider, info in cloud_providers.items():
            services = ', '.join(info['services'].keys())
            logger.info(f"  - {info['name']} ({provider}): {services}")
        
        # Show BI tools
        bi_tools = get_supported_bi_tools()
        logger.info(f"\nSupported BI Tools ({len(bi_tools)}):")
        for tool, info in bi_tools.items():
            capabilities = ', '.join(info['lineage_capabilities'])
            logger.info(f"  - {info['name']} ({tool}): {capabilities}")
    
    async def demo_data_platform_integrations(self):
        """Demonstrate data platform integrations."""
        logger.info("\n=== Data Platform Integrations Demo ===")
        
        # Example Snowflake configuration (using mock credentials)
        snowflake_config = SnowflakeConfig(
            name="demo_snowflake",
            account="demo_account",
            username="demo_user",
            password="demo_password",
            warehouse="DEMO_WH",
            database="DEMO_DB",
            schema="PUBLIC",
            role="DEMO_ROLE"
        )
        
        logger.info("Configured Snowflake connector (demo mode)")
        logger.info(f"  Account: {snowflake_config.account}")
        logger.info(f"  Warehouse: {snowflake_config.warehouse}")
        logger.info(f"  Database: {snowflake_config.database}")
        
        # Create and register connector
        snowflake_connector = SnowflakeConnector(snowflake_config)
        
        # Register with manager
        await self.connector_manager.register_connector(snowflake_connector)
        
        logger.info("Snowflake connector registered with manager")
        
        # Note: In a real scenario, you would call connect() here
        # For demo purposes, we'll simulate the connection
        logger.info("Note: In production, connector.connect() would establish actual connection")
    
    async def demo_bi_tool_integrations(self):
        """Demonstrate BI tool integrations."""
        logger.info("\n=== BI Tool Integrations Demo ===")
        
        # Example Tableau configuration (using mock credentials)
        tableau_config = TableauConfig(
            name="demo_tableau",
            server_url="https://demo-tableau-server.com",
            username="demo_user",
            password="demo_password",
            site_id="demo_site"
        )
        
        logger.info("Configured Tableau connector (demo mode)")
        logger.info(f"  Server: {tableau_config.server_url}")
        logger.info(f"  Site: {tableau_config.site_id}")
        logger.info(f"  API Version: {tableau_config.api_version}")
        
        # Create and register connector
        tableau_connector = TableauConnector(tableau_config)
        
        # Register with manager
        await self.connector_manager.register_connector(tableau_connector)
        
        logger.info("Tableau connector registered with manager")
        
        # Note: In a real scenario, you would call connect() here
        logger.info("Note: In production, connector.connect() would establish actual connection")
    
    async def demo_metadata_extraction(self):
        """Demonstrate metadata extraction from connected systems."""
        logger.info("\n=== Metadata Extraction Demo ===")
        
        # Get all registered connectors
        connectors = self.connector_manager.registry.get_all_connectors()
        
        for connector_name, connector in connectors.items():
            logger.info(f"\nExtracting metadata from {connector_name}...")
            
            try:
                # In a real scenario, this would extract actual metadata
                # For demo, we'll show what would be extracted
                
                if isinstance(connector, SnowflakeConnector):
                    logger.info("  Snowflake metadata would include:")
                    logger.info("    - Databases, schemas, tables, views")
                    logger.info("    - Warehouses, roles, users")
                    logger.info("    - Functions, procedures")
                    logger.info("    - Access history, query history")
                
                elif isinstance(connector, TableauConnector):
                    logger.info("  Tableau metadata would include:")
                    logger.info("    - Workbooks, datasources, projects")
                    logger.info("    - Users, groups, schedules")
                    logger.info("    - Flows, metrics")
                    logger.info("    - Server and site information")
                
                # Simulate metadata extraction
                mock_metadata = {
                    'connector_type': connector.config.connector_type.value,
                    'extraction_time': datetime.now().isoformat(),
                    'entities_count': 42,  # Mock count
                    'status': 'success'
                }
                
                logger.info(f"  Extracted metadata: {json.dumps(mock_metadata, indent=2)}")
                
            except Exception as e:
                logger.error(f"  Failed to extract metadata: {e}")
    
    async def show_integration_health(self):
        """Show health status of all integrations."""
        logger.info("\n=== Integration Health Status ===")
        
        # Get health status from connector manager
        health_status = await self.connector_manager.get_health_status()
        
        logger.info(f"Overall health: {health_status['overall_status']}")
        logger.info(f"Total connectors: {health_status['total_connectors']}")
        logger.info(f"Healthy connectors: {health_status['healthy_connectors']}")
        logger.info(f"Unhealthy connectors: {health_status['unhealthy_connectors']}")
        
        # Show individual connector status
        logger.info("\nIndividual connector status:")
        for connector_name, status in health_status['connector_status'].items():
            logger.info(f"  {connector_name}: {status['status']} (last check: {status['last_check']})")
    
    async def demo_cross_platform_lineage(self):
        """Demonstrate cross-platform lineage tracking."""
        logger.info("\n=== Cross-Platform Lineage Demo ===")
        
        # Simulate a data flow across multiple platforms
        logger.info("Simulating data flow: Snowflake → Tableau")
        
        # Mock lineage data
        lineage_flow = {
            'flow_id': 'cross_platform_flow_001',
            'source_system': 'snowflake',
            'target_system': 'tableau',
            'entities': [
                {
                    'system': 'snowflake',
                    'type': 'table',
                    'identifier': 'DEMO_DB.PUBLIC.SALES_DATA',
                    'role': 'source'
                },
                {
                    'system': 'tableau',
                    'type': 'datasource',
                    'identifier': 'sales_analysis_datasource',
                    'role': 'intermediate'
                },
                {
                    'system': 'tableau',
                    'type': 'workbook',
                    'identifier': 'sales_dashboard',
                    'role': 'target'
                }
            ],
            'transformations': [
                {
                    'type': 'aggregation',
                    'description': 'Group by region and sum sales amount'
                },
                {
                    'type': 'filtering',
                    'description': 'Filter for current year data'
                }
            ]
        }
        
        logger.info("Cross-platform lineage flow:")
        logger.info(json.dumps(lineage_flow, indent=2))
        
        # In a real implementation, this would:
        # 1. Extract lineage from each system
        # 2. Correlate entities across systems
        # 3. Build unified lineage graph
        # 4. Track data transformations
        # 5. Provide impact analysis
        
        logger.info("\nCross-platform capabilities:")
        logger.info("  ✓ Unified lineage graph across all connected systems")
        logger.info("  ✓ Impact analysis for changes")
        logger.info("  ✓ Data flow visualization")
        logger.info("  ✓ Compliance tracking across platforms")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("\n=== Cleanup ===")
        
        if self.connector_manager:
            # Disconnect all connectors
            await self.connector_manager.disconnect_all()
            
            # Shutdown manager
            await self.connector_manager.shutdown()
            
            logger.info("All connectors disconnected and manager shutdown")


async def run_integration_capabilities_overview():
    """Show overview of integration capabilities."""
    logger.info("\n=== Enterprise Integration Capabilities Overview ===")
    
    capabilities = {
        'Data Platform Connectors': [
            'Snowflake - Cloud data warehouse with lineage extraction',
            'Databricks - Unified analytics platform integration',
            'BigQuery - Google Cloud data warehouse connector',
            'Redshift - Amazon data warehouse integration',
            'Azure Synapse - Microsoft analytics platform',
            'PostgreSQL, MySQL, Oracle - Traditional databases',
            'MongoDB - Document database connector'
        ],
        'Cloud Provider Integrations': [
            'AWS - S3, Glue, Athena, EMR, Kinesis, Lambda',
            'Azure - Blob Storage, Data Factory, Event Hubs',
            'GCP - Cloud Storage, Dataflow, Dataproc, Pub/Sub'
        ],
        'BI Tool Connectors': [
            'Tableau - Server API integration with lineage',
            'Power BI - REST API and admin API access',
            'Looker - API 4.0 with LookML parsing',
            'Qlik Sense - Engine and Repository API'
        ],
        'Enterprise Features': [
            'Unified connector management and health monitoring',
            'Cross-platform lineage correlation and tracking',
            'Enterprise authentication (LDAP, SAML, OAuth)',
            'Async/sync operation support with connection pooling',
            'Comprehensive logging and error handling',
            'Configuration-driven setup with retry logic',
            'Event-driven architecture with callbacks',
            'Metadata extraction and transformation mapping'
        ]
    }
    
    for category, items in capabilities.items():
        logger.info(f"\n{category}:")
        for item in items:
            logger.info(f"  • {item}")


async def main():
    """Main function to run the enterprise integrations demo."""
    try:
        # Show capabilities overview
        await run_integration_capabilities_overview()
        
        # Run the main demo
        demo = EnterpriseIntegrationsDemo()
        await demo.run_demo()
        
        logger.info("\n=== Demo Complete ===")
        logger.info("Enterprise integrations framework is ready for production use!")
        logger.info("Next steps:")
        logger.info("  1. Configure actual connection credentials")
        logger.info("  2. Test connections to your enterprise systems")
        logger.info("  3. Set up monitoring and alerting")
        logger.info("  4. Implement custom connectors as needed")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
