"""
Resource Manager for DataLineagePy Multi-Tenancy

Provides resource quota management, monitoring, and enforcement for multi-tenant environments.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from threading import Lock
import psutil

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Resource type enumeration."""
    STORAGE = "storage"
    COMPUTE = "compute"
    MEMORY = "memory"
    NETWORK = "network"
    API_REQUESTS = "api_requests"
    CONCURRENT_JOBS = "concurrent_jobs"
    USERS = "users"
    PIPELINES = "pipelines"
    DATASETS = "datasets"

class QuotaStatus(Enum):
    """Quota status enumeration."""
    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    SUSPENDED = "suspended"

@dataclass
class ResourceQuota:
    """Represents a resource quota for a tenant."""
    tenant_id: str
    resource_type: ResourceType
    limit: float
    used: float = 0.0
    reserved: float = 0.0
    unit: str = ""
    warning_threshold: float = 0.8
    status: QuotaStatus = QuotaStatus.OK
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def available(self) -> float:
        """Get available quota."""
        return max(0, self.limit - self.used - self.reserved)
    
    @property
    def usage_percentage(self) -> float:
        """Get usage percentage."""
        if self.limit == 0:
            return 0.0
        return (self.used / self.limit) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quota to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "resource_type": self.resource_type.value,
            "limit": self.limit,
            "used": self.used,
            "reserved": self.reserved,
            "available": self.available,
            "unit": self.unit,
            "warning_threshold": self.warning_threshold,
            "status": self.status.value,
            "usage_percentage": self.usage_percentage,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class ResourceUsage:
    """Represents resource usage data."""
    tenant_id: str
    resource_type: ResourceType
    amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceManager:
    """Manages resource quotas and usage for multi-tenant environments."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.quotas: Dict[str, Dict[ResourceType, ResourceQuota]] = {}  # tenant_id -> resource_type -> quota
        self.usage_history: List[ResourceUsage] = []
        self.lock = Lock()
        self.monitoring_enabled = self.config.get("monitoring_enabled", True)
        self.enforcement_enabled = self.config.get("enforcement_enabled", True)
        self.warning_callbacks: List[Callable] = []
        self.exceeded_callbacks: List[Callable] = []
        self.stats = {
            "total_quotas": 0,
            "quotas_exceeded": 0,
            "quotas_warning": 0,
            "total_usage_records": 0,
            "last_cleanup": None
        }
        
    async def start(self):
        """Start the resource manager."""
        logger.info("Starting resource manager")
        if self.monitoring_enabled:
            asyncio.create_task(self._monitor_system_resources())
            asyncio.create_task(self._cleanup_usage_history())
        
    async def stop(self):
        """Stop the resource manager."""
        logger.info("Stopping resource manager")
        
    async def set_quota(self, tenant_id: str, resource_type: ResourceType, 
                       limit: float, unit: str = "", warning_threshold: float = 0.8) -> bool:
        """Set resource quota for a tenant."""
        with self.lock:
            if tenant_id not in self.quotas:
                self.quotas[tenant_id] = {}
            
            quota = ResourceQuota(
                tenant_id=tenant_id,
                resource_type=resource_type,
                limit=limit,
                unit=unit,
                warning_threshold=warning_threshold
            )
            
            self.quotas[tenant_id][resource_type] = quota
            self.stats["total_quotas"] += 1
            
            logger.info(f"Set quota for tenant {tenant_id}: {resource_type.value} = {limit} {unit}")
            return True
    
    async def get_quota(self, tenant_id: str, resource_type: ResourceType) -> Optional[ResourceQuota]:
        """Get resource quota for a tenant."""
        tenant_quotas = self.quotas.get(tenant_id, {})
        return tenant_quotas.get(resource_type)
    
    async def get_all_quotas(self, tenant_id: str) -> Dict[ResourceType, ResourceQuota]:
        """Get all resource quotas for a tenant."""
        return self.quotas.get(tenant_id, {}).copy()
    
    async def update_usage(self, tenant_id: str, resource_type: ResourceType, 
                          amount: float, operation: str = "", metadata: Dict[str, Any] = None) -> bool:
        """Update resource usage for a tenant."""
        with self.lock:
            quota = await self.get_quota(tenant_id, resource_type)
            if not quota:
                logger.warning(f"No quota found for tenant {tenant_id}, resource {resource_type.value}")
                return False
            
            # Check if usage would exceed quota
            new_usage = quota.used + amount
            if self.enforcement_enabled and new_usage > quota.limit:
                logger.warning(f"Usage would exceed quota for tenant {tenant_id}: {resource_type.value}")
                return False
            
            # Update usage
            quota.used = max(0, new_usage)  # Prevent negative usage
            quota.last_updated = datetime.now()
            
            # Update status
            old_status = quota.status
            quota.status = self._calculate_quota_status(quota)
            
            # Record usage
            usage = ResourceUsage(
                tenant_id=tenant_id,
                resource_type=resource_type,
                amount=amount,
                operation=operation,
                metadata=metadata or {}
            )
            self.usage_history.append(usage)
            self.stats["total_usage_records"] += 1
            
            # Trigger callbacks if status changed
            if old_status != quota.status:
                await self._trigger_status_callbacks(quota, old_status)
            
            logger.debug(f"Updated usage for tenant {tenant_id}: {resource_type.value} = {quota.used}/{quota.limit}")
            return True
    
    async def reserve_resources(self, tenant_id: str, resource_type: ResourceType, 
                               amount: float) -> bool:
        """Reserve resources for a tenant."""
        with self.lock:
            quota = await self.get_quota(tenant_id, resource_type)
            if not quota:
                return False
            
            # Check if reservation would exceed available quota
            if quota.used + quota.reserved + amount > quota.limit:
                return False
            
            quota.reserved += amount
            quota.last_updated = datetime.now()
            
            logger.debug(f"Reserved {amount} {quota.unit} for tenant {tenant_id}: {resource_type.value}")
            return True
    
    async def release_reservation(self, tenant_id: str, resource_type: ResourceType, 
                                 amount: float) -> bool:
        """Release reserved resources for a tenant."""
        with self.lock:
            quota = await self.get_quota(tenant_id, resource_type)
            if not quota:
                return False
            
            quota.reserved = max(0, quota.reserved - amount)
            quota.last_updated = datetime.now()
            
            logger.debug(f"Released {amount} {quota.unit} reservation for tenant {tenant_id}: {resource_type.value}")
            return True
    
    async def check_quota_availability(self, tenant_id: str, resource_type: ResourceType, 
                                     amount: float) -> bool:
        """Check if resources are available within quota."""
        quota = await self.get_quota(tenant_id, resource_type)
        if not quota:
            return False
        
        return quota.available >= amount
    
    async def get_usage_history(self, tenant_id: str = None, resource_type: ResourceType = None, 
                               hours: int = 24) -> List[ResourceUsage]:
        """Get usage history with optional filtering."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_history = []
        for usage in self.usage_history:
            if usage.timestamp < cutoff_time:
                continue
            
            if tenant_id and usage.tenant_id != tenant_id:
                continue
            
            if resource_type and usage.resource_type != resource_type:
                continue
            
            filtered_history.append(usage)
        
        return filtered_history
    
    async def get_tenant_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get resource usage summary for a tenant."""
        quotas = await self.get_all_quotas(tenant_id)
        
        summary = {
            "tenant_id": tenant_id,
            "quotas": {},
            "total_usage_percentage": 0.0,
            "status": "ok",
            "warnings": [],
            "exceeded": []
        }
        
        total_percentage = 0.0
        quota_count = 0
        
        for resource_type, quota in quotas.items():
            summary["quotas"][resource_type.value] = quota.to_dict()
            total_percentage += quota.usage_percentage
            quota_count += 1
            
            if quota.status == QuotaStatus.WARNING:
                summary["warnings"].append(resource_type.value)
            elif quota.status == QuotaStatus.EXCEEDED:
                summary["exceeded"].append(resource_type.value)
        
        if quota_count > 0:
            summary["total_usage_percentage"] = total_percentage / quota_count
        
        # Determine overall status
        if summary["exceeded"]:
            summary["status"] = "exceeded"
        elif summary["warnings"]:
            summary["status"] = "warning"
        
        return summary
    
    async def get_system_summary(self) -> Dict[str, Any]:
        """Get system-wide resource usage summary."""
        tenant_summaries = {}
        total_quotas = 0
        exceeded_quotas = 0
        warning_quotas = 0
        
        for tenant_id in self.quotas.keys():
            summary = await self.get_tenant_summary(tenant_id)
            tenant_summaries[tenant_id] = summary
            
            total_quotas += len(summary["quotas"])
            exceeded_quotas += len(summary["exceeded"])
            warning_quotas += len(summary["warnings"])
        
        return {
            "total_tenants": len(self.quotas),
            "total_quotas": total_quotas,
            "exceeded_quotas": exceeded_quotas,
            "warning_quotas": warning_quotas,
            "system_resources": await self._get_system_resources(),
            "tenant_summaries": tenant_summaries,
            "statistics": self.stats
        }
    
    async def reset_usage(self, tenant_id: str, resource_type: ResourceType = None) -> bool:
        """Reset usage for a tenant (admin operation)."""
        with self.lock:
            tenant_quotas = self.quotas.get(tenant_id, {})
            
            if resource_type:
                quota = tenant_quotas.get(resource_type)
                if quota:
                    quota.used = 0.0
                    quota.reserved = 0.0
                    quota.status = QuotaStatus.OK
                    quota.last_updated = datetime.now()
                    logger.info(f"Reset usage for tenant {tenant_id}: {resource_type.value}")
                    return True
            else:
                for quota in tenant_quotas.values():
                    quota.used = 0.0
                    quota.reserved = 0.0
                    quota.status = QuotaStatus.OK
                    quota.last_updated = datetime.now()
                logger.info(f"Reset all usage for tenant {tenant_id}")
                return True
        
        return False
    
    async def add_warning_callback(self, callback: Callable):
        """Add callback for quota warnings."""
        self.warning_callbacks.append(callback)
    
    async def add_exceeded_callback(self, callback: Callable):
        """Add callback for quota exceeded events."""
        self.exceeded_callbacks.append(callback)
    
    def _calculate_quota_status(self, quota: ResourceQuota) -> QuotaStatus:
        """Calculate quota status based on usage."""
        usage_percentage = quota.usage_percentage / 100
        
        if usage_percentage >= 1.0:
            return QuotaStatus.EXCEEDED
        elif usage_percentage >= quota.warning_threshold:
            return QuotaStatus.WARNING
        else:
            return QuotaStatus.OK
    
    async def _trigger_status_callbacks(self, quota: ResourceQuota, old_status: QuotaStatus):
        """Trigger callbacks when quota status changes."""
        try:
            if quota.status == QuotaStatus.WARNING and old_status != QuotaStatus.WARNING:
                for callback in self.warning_callbacks:
                    await callback(quota)
                self.stats["quotas_warning"] += 1
            
            elif quota.status == QuotaStatus.EXCEEDED and old_status != QuotaStatus.EXCEEDED:
                for callback in self.exceeded_callbacks:
                    await callback(quota)
                self.stats["quotas_exceeded"] += 1
        
        except Exception as e:
            logger.error(f"Error triggering quota callbacks: {e}")
    
    async def _get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_io": psutil.net_io_counters()._asdict(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {}
    
    async def _monitor_system_resources(self):
        """Background task to monitor system resources."""
        while True:
            try:
                # Update system resource usage for all tenants
                # This is a simplified implementation - in production, you'd want
                # more sophisticated resource attribution
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _cleanup_usage_history(self):
        """Background task to cleanup old usage history."""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(days=7)  # Keep 7 days of history
                
                with self.lock:
                    original_count = len(self.usage_history)
                    self.usage_history = [
                        usage for usage in self.usage_history 
                        if usage.timestamp > cutoff_time
                    ]
                    cleaned_count = original_count - len(self.usage_history)
                    
                    if cleaned_count > 0:
                        logger.info(f"Cleaned up {cleaned_count} old usage records")
                
                self.stats["last_cleanup"] = datetime.now().isoformat()
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in usage history cleanup: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
