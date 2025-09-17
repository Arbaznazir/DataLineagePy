"""
Multi-Tenancy Module for DataLineagePy

Provides comprehensive multi-tenant support with tenant isolation, resource quotas,
cross-tenant data sharing controls, and tenant management capabilities.
"""

# Import available modules with error handling
try:
    from .tenant_manager import TenantManager, Tenant, TenantConfig
except ImportError as e:
    print(f"Warning: Could not import tenant_manager: {e}")
    TenantManager = Tenant = TenantConfig = None

try:
    from .resource_manager import ResourceManager, ResourceQuota, ResourceType
except ImportError as e:
    print(f"Warning: Could not import resource_manager: {e}")
    ResourceManager = ResourceQuota = ResourceType = None

from .isolation_manager import IsolationManager, IsolationLevel
from .sharing_manager import SharingManager, SharingPolicy, SharingPermission
from .tenant_auth import TenantAuthenticator, TenantContext
from .tenant_storage import TenantStorage, TenantDatabase

# Factory functions
def create_tenant_manager(config=None):
    """Create a new tenant manager instance."""
    return TenantManager(config or TenantConfig())

def create_resource_manager(config=None):
    """Create a new resource manager instance."""
    return ResourceManager(config)

def create_isolation_manager(level=IsolationLevel.STRICT):
    """Create a new isolation manager instance."""
    return IsolationManager(level)

def create_sharing_manager(config=None):
    """Create a new sharing manager instance."""
    return SharingManager(config)

# Default configurations
DEFAULT_TENANT_CONFIG = {
    "max_tenants": 1000,
    "default_storage_quota": "10GB",
    "default_compute_quota": "100 CPU hours",
    "isolation_level": "strict",
    "enable_cross_tenant_sharing": True,
    "tenant_prefix": "tenant_",
    "auto_provisioning": True
}

DEFAULT_RESOURCE_QUOTAS = {
    "storage": "10GB",
    "compute_hours": 100,
    "api_requests": 10000,
    "concurrent_jobs": 5,
    "max_users": 50,
    "max_pipelines": 100,
    "max_datasets": 1000
}

DEFAULT_ISOLATION_CONFIG = {
    "level": "strict",
    "network_isolation": True,
    "storage_isolation": True,
    "compute_isolation": True,
    "logging_isolation": True,
    "monitoring_isolation": True
}

# Supported features
SUPPORTED_ISOLATION_LEVELS = ["strict", "moderate", "basic"]
SUPPORTED_RESOURCE_TYPES = ["storage", "compute", "network", "api", "users", "pipelines", "datasets"]
SUPPORTED_SHARING_PERMISSIONS = ["read", "write", "admin", "share"]

__all__ = [
    "TenantManager",
    "Tenant", 
    "TenantConfig",
    "ResourceManager",
    "ResourceQuota",
    "ResourceType",
    "IsolationManager",
    "IsolationLevel",
    "SharingManager",
    "SharingPolicy",
    "SharingPermission",
    "TenantAuthenticator",
    "TenantContext",
    "TenantStorage",
    "TenantDatabase",
    "create_tenant_manager",
    "create_resource_manager",
    "create_isolation_manager",
    "create_sharing_manager",
    "DEFAULT_TENANT_CONFIG",
    "DEFAULT_RESOURCE_QUOTAS",
    "DEFAULT_ISOLATION_CONFIG",
    "SUPPORTED_ISOLATION_LEVELS",
    "SUPPORTED_RESOURCE_TYPES",
    "SUPPORTED_SHARING_PERMISSIONS"
]
