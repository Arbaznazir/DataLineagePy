"""
Business Intelligence tools integrations for DataLineagePy.
Supports major BI platforms for lineage extraction.
"""

from .tableau_connector import TableauConnector, TableauConfig
from .powerbi_connector import PowerBIConnector, PowerBIConfig
from .looker_connector import LookerConnector, LookerConfig
from .qlik_connector import QlikConnector, QlikConfig

__all__ = [
    # Tableau
    'TableauConnector',
    'TableauConfig',
    
    # Power BI
    'PowerBIConnector',
    'PowerBIConfig',
    
    # Looker
    'LookerConnector', 
    'LookerConfig',
    
    # Qlik
    'QlikConnector',
    'QlikConfig'
]

# Supported BI tools
SUPPORTED_BI_TOOLS = {
    'tableau': {
        'name': 'Tableau',
        'connector_class': 'TableauConnector',
        'config_class': 'TableauConfig',
        'type': 'visualization_platform',
        'features': ['server_api', 'rest_api', 'metadata_api', 'hyper_api'],
        'lineage_capabilities': ['workbook', 'datasource', 'dashboard', 'worksheet'],
        'authentication': ['username_password', 'personal_access_token', 'trusted_ticket']
    },
    'powerbi': {
        'name': 'Microsoft Power BI',
        'connector_class': 'PowerBIConnector',
        'config_class': 'PowerBIConfig',
        'type': 'visualization_platform',
        'features': ['rest_api', 'admin_api', 'xmla_endpoint', 'power_query'],
        'lineage_capabilities': ['report', 'dataset', 'dashboard', 'dataflow'],
        'authentication': ['service_principal', 'master_user', 'azure_ad']
    },
    'looker': {
        'name': 'Looker',
        'connector_class': 'LookerConnector',
        'config_class': 'LookerConfig',
        'type': 'modern_bi_platform',
        'features': ['api_4_0', 'lookml', 'system_activity', 'git_integration'],
        'lineage_capabilities': ['look', 'dashboard', 'explore', 'model'],
        'authentication': ['api_credentials', 'oauth', 'embed_sso']
    },
    'qlik': {
        'name': 'Qlik Sense',
        'connector_class': 'QlikConnector',
        'config_class': 'QlikConfig',
        'type': 'associative_platform',
        'features': ['engine_api', 'repository_api', 'qrs_api', 'associative_model'],
        'lineage_capabilities': ['app', 'sheet', 'object', 'connection'],
        'authentication': ['windows_auth', 'certificate', 'jwt', 'saml']
    }
}

# BI tool categories
BI_TOOL_CATEGORIES = {
    'traditional': ['tableau', 'qlik'],
    'modern': ['looker'],
    'cloud_native': ['powerbi'],
    'self_service': ['tableau', 'powerbi', 'qlik'],
    'governed': ['looker']
}

def get_supported_bi_tools():
    """Get list of supported BI tools."""
    return SUPPORTED_BI_TOOLS

def get_bi_tool_categories():
    """Get BI tool categories."""
    return BI_TOOL_CATEGORIES

def get_bi_tool_info(tool_name: str):
    """Get information about a specific BI tool."""
    return SUPPORTED_BI_TOOLS.get(tool_name.lower())

def get_tools_by_category(category: str):
    """Get BI tools by category."""
    return BI_TOOL_CATEGORIES.get(category.lower(), [])

def create_bi_connector(tool_name: str, config: dict):
    """Factory function to create a BI tool connector."""
    tool_info = get_bi_tool_info(tool_name)
    if not tool_info:
        raise ValueError(f"Unsupported BI tool: {tool_name}")
    
    # Import the connector class dynamically
    connector_class_name = tool_info['connector_class']
    connector_class = globals().get(connector_class_name)
    
    if not connector_class:
        raise ImportError(f"Connector class {connector_class_name} not found")
    
    # Create config object
    config_class_name = tool_info['config_class']
    config_class = globals().get(config_class_name)
    
    if config_class:
        config_obj = config_class(**config)
    else:
        # Fallback to basic config
        from ..core.base_connector import ConnectorConfig, ConnectorType
        config_obj = ConnectorConfig(
            name=config.get('name', tool_name),
            connector_type=ConnectorType.BI_TOOL,
            **config
        )
    
    return connector_class(config_obj)

def get_lineage_capabilities(tool_name: str):
    """Get lineage extraction capabilities for a BI tool."""
    tool_info = get_bi_tool_info(tool_name)
    return tool_info.get('lineage_capabilities', []) if tool_info else []

def get_authentication_methods(tool_name: str):
    """Get supported authentication methods for a BI tool."""
    tool_info = get_bi_tool_info(tool_name)
    return tool_info.get('authentication', []) if tool_info else []
