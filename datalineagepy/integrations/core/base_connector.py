"""
Base connector class for all DataLineagePy integrations.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import threading
import uuid

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class ConnectorType(Enum):
    """Connector type enumeration."""
    DATABASE = "database"
    CLOUD_STORAGE = "cloud_storage"
    BI_TOOL = "bi_tool"
    DATA_CATALOG = "data_catalog"
    ORCHESTRATION = "orchestration"
    MESSAGE_QUEUE = "message_queue"
    API = "api"
    FILE_SYSTEM = "file_system"
    STREAMING = "streaming"


@dataclass
class ConnectorConfig:
    """Configuration for connectors."""
    name: str
    connector_type: ConnectorType
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    ssl_config: Optional[Dict[str, Any]] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 10
    enable_ssl: bool = True
    verify_ssl: bool = True
    enable_logging: bool = True
    log_level: str = 'INFO'
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Connector name is required")
        
        if not self.connection_string and not self.host:
            raise ValueError("Either connection_string or host must be provided")


@dataclass
class ConnectionMetrics:
    """Connection metrics and statistics."""
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_response_time: float = 0.0
    average_response_time: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    def update_query_stats(self, success: bool, response_time: float, error: str = None):
        """Update query statistics."""
        self.last_used = datetime.now()
        self.total_queries += 1
        self.total_response_time += response_time
        self.average_response_time = self.total_response_time / self.total_queries
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
            self.last_error = error
            self.last_error_time = datetime.now()


class BaseConnector(ABC):
    """Base class for all DataLineagePy connectors."""
    
    def __init__(self, config: ConnectorConfig):
        """Initialize the connector."""
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.connection = None
        self.metrics = ConnectionMetrics()
        self.lock = threading.RLock()
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
        # Set up logging
        if config.enable_logging:
            self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        self.logger.info(f"Initialized {config.connector_type.value} connector: {config.name}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the target system."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the target system."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the target system."""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the target system."""
        pass
    
    @abstractmethod
    async def get_lineage(self, entity_id: str) -> Dict[str, Any]:
        """Extract lineage information for a specific entity."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute a query against the target system."""
        pass
    
    def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self.status
    
    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return self.metrics
    
    def get_config(self) -> ConnectorConfig:
        """Get connector configuration."""
        return self.config
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connector."""
        try:
            start_time = time.time()
            is_healthy = await self.test_connection()
            response_time = time.time() - start_time
            
            return {
                'connector_name': self.config.name,
                'connector_type': self.config.connector_type.value,
                'status': self.status.value,
                'healthy': is_healthy,
                'response_time_ms': round(response_time * 1000, 2),
                'last_check': datetime.now().isoformat(),
                'metrics': {
                    'total_queries': self.metrics.total_queries,
                    'successful_queries': self.metrics.successful_queries,
                    'failed_queries': self.metrics.failed_queries,
                    'average_response_time_ms': round(self.metrics.average_response_time * 1000, 2),
                    'last_error': self.metrics.last_error
                }
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'connector_name': self.config.name,
                'connector_type': self.config.connector_type.value,
                'status': ConnectionStatus.ERROR.value,
                'healthy': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def reconnect(self) -> bool:
        """Reconnect to the target system."""
        try:
            self.status = ConnectionStatus.RECONNECTING
            self.logger.info(f"Reconnecting to {self.config.name}")
            
            # Disconnect first
            await self.disconnect()
            
            # Wait before reconnecting
            await asyncio.sleep(self.config.retry_delay)
            
            # Reconnect
            success = await self.connect()
            
            if success:
                self.logger.info(f"Successfully reconnected to {self.config.name}")
            else:
                self.logger.error(f"Failed to reconnect to {self.config.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            self.status = ConnectionStatus.ERROR
            return False
    
    def _update_status(self, status: ConnectionStatus):
        """Update connection status thread-safely."""
        with self.lock:
            old_status = self.status
            self.status = status
            if old_status != status:
                self.logger.info(f"Status changed from {old_status.value} to {status.value}")
    
    def _log_query(self, query: str, success: bool, response_time: float, error: str = None):
        """Log query execution."""
        self.metrics.update_query_stats(success, response_time, error)
        
        if success:
            self.logger.debug(f"Query executed successfully in {response_time:.3f}s: {query[:100]}...")
        else:
            self.logger.error(f"Query failed after {response_time:.3f}s: {error}")
    
    def __str__(self) -> str:
        """String representation of the connector."""
        return f"{self.config.connector_type.value}:{self.config.name}({self.status.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the connector."""
        return (f"BaseConnector(name='{self.config.name}', "
                f"type='{self.config.connector_type.value}', "
                f"status='{self.status.value}', "
                f"queries={self.metrics.total_queries})")


# Import asyncio at the end to avoid circular imports
import asyncio
