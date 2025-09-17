"""
Edge Computing Module for DataLineagePy

Provides edge node support, offline lineage tracking, IoT device integration,
and distributed edge computing capabilities.
"""

from .edge_node import EdgeNode, EdgeNodeConfig, EdgeNodeStatus
from .offline_tracker import OfflineTracker, OfflineEvent, SyncManager
from .iot_integration import IoTIntegration, IoTDevice, IoTDataProcessor
from .edge_coordinator import EdgeCoordinator, EdgeCluster, EdgeTopology
from .edge_storage import EdgeStorage, EdgeCache, EdgeDatabase
from .edge_sync import EdgeSyncManager, SyncPolicy, ConflictResolver

# Factory functions
def create_edge_node(config=None):
    """Create a new edge node instance."""
    return EdgeNode(config or EdgeNodeConfig())

def create_offline_tracker(config=None):
    """Create a new offline tracker instance."""
    return OfflineTracker(config)

def create_iot_integration(config=None):
    """Create a new IoT integration instance."""
    return IoTIntegration(config)

def create_edge_coordinator(config=None):
    """Create a new edge coordinator instance."""
    return EdgeCoordinator(config)

def create_edge_storage(config=None):
    """Create a new edge storage instance."""
    return EdgeStorage(config)

def create_edge_sync_manager(config=None):
    """Create a new edge sync manager instance."""
    return EdgeSyncManager(config)

# Default configurations
DEFAULT_EDGE_NODE_CONFIG = {
    "node_id": None,  # Auto-generated if not provided
    "node_name": "edge-node",
    "location": "unknown",
    "capabilities": ["lineage_tracking", "data_processing", "storage"],
    "max_storage_mb": 1024,  # 1GB
    "max_memory_mb": 512,    # 512MB
    "heartbeat_interval": 30,
    "sync_interval": 300,    # 5 minutes
    "offline_mode": True,
    "compression_enabled": True,
    "encryption_enabled": True
}

DEFAULT_OFFLINE_CONFIG = {
    "max_events": 10000,
    "max_storage_mb": 500,
    "compression_enabled": True,
    "encryption_enabled": True,
    "sync_on_connect": True,
    "conflict_resolution": "timestamp",
    "batch_size": 100
}

DEFAULT_IOT_CONFIG = {
    "supported_protocols": ["mqtt", "http", "coap"],
    "device_discovery": True,
    "auto_registration": True,
    "data_validation": True,
    "rate_limiting": True,
    "max_devices": 1000,
    "heartbeat_timeout": 60
}

DEFAULT_SYNC_CONFIG = {
    "sync_strategy": "incremental",
    "conflict_resolution": "last_write_wins",
    "batch_size": 100,
    "retry_attempts": 3,
    "compression": True,
    "encryption": True,
    "priority_sync": True
}

# Supported features
SUPPORTED_EDGE_CAPABILITIES = [
    "lineage_tracking", "data_processing", "storage", "analytics", 
    "monitoring", "alerting", "caching", "transformation"
]

SUPPORTED_IOT_PROTOCOLS = ["mqtt", "http", "https", "coap", "websocket", "tcp", "udp"]

SUPPORTED_SYNC_STRATEGIES = ["full", "incremental", "delta", "priority"]

SUPPORTED_CONFLICT_RESOLUTIONS = ["last_write_wins", "timestamp", "manual", "merge"]

__all__ = [
    "EdgeNode",
    "EdgeNodeConfig",
    "EdgeNodeStatus",
    "OfflineTracker",
    "OfflineEvent",
    "SyncManager",
    "IoTIntegration",
    "IoTDevice",
    "IoTDataProcessor",
    "EdgeCoordinator",
    "EdgeCluster",
    "EdgeTopology",
    "EdgeStorage",
    "EdgeCache",
    "EdgeDatabase",
    "EdgeSyncManager",
    "SyncPolicy",
    "ConflictResolver",
    "create_edge_node",
    "create_offline_tracker",
    "create_iot_integration",
    "create_edge_coordinator",
    "create_edge_storage",
    "create_edge_sync_manager",
    "DEFAULT_EDGE_NODE_CONFIG",
    "DEFAULT_OFFLINE_CONFIG",
    "DEFAULT_IOT_CONFIG",
    "DEFAULT_SYNC_CONFIG",
    "SUPPORTED_EDGE_CAPABILITIES",
    "SUPPORTED_IOT_PROTOCOLS",
    "SUPPORTED_SYNC_STRATEGIES",
    "SUPPORTED_CONFLICT_RESOLUTIONS"
]
