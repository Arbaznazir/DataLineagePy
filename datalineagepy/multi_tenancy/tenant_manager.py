"""
Tenant Manager for DataLineagePy Multi-Tenancy

Provides comprehensive tenant lifecycle management, configuration, and administration.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from threading import Lock
import json

logger = logging.getLogger(__name__)

class TenantStatus(Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    TERMINATED = "terminated"

class TenantTier(Enum):
    """Tenant tier enumeration."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class TenantConfig:
    """Configuration for tenant management."""
    max_tenants: int = 1000
    default_storage_quota: str = "10GB"
    default_compute_quota: str = "100 CPU hours"
    isolation_level: str = "strict"
    enable_cross_tenant_sharing: bool = True
    tenant_prefix: str = "tenant_"
    auto_provisioning: bool = True
    default_tier: TenantTier = TenantTier.STANDARD
    retention_days: int = 30
    backup_enabled: bool = True

@dataclass
class Tenant:
    """Represents a tenant in the multi-tenant system."""
    id: str
    name: str
    tier: TenantTier
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resource_quotas: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    users: Set[str] = field(default_factory=set)
    admin_users: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "resource_quotas": self.resource_quotas,
            "settings": self.settings,
            "users": list(self.users),
            "admin_users": list(self.admin_users)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """Create tenant from dictionary."""
        tenant = cls(
            id=data["id"],
            name=data["name"],
            tier=TenantTier(data["tier"]),
            status=TenantStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            metadata=data.get("metadata", {}),
            resource_quotas=data.get("resource_quotas", {}),
            settings=data.get("settings", {}),
            users=set(data.get("users", [])),
            admin_users=set(data.get("admin_users", []))
        )
        return tenant

class TenantManager:
    """Manages tenant lifecycle and operations."""
    
    def __init__(self, config: TenantConfig):
        self.config = config
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_index: Dict[str, str] = {}  # name -> id mapping
        self.lock = Lock()
        self.stats = {
            "total_tenants": 0,
            "active_tenants": 0,
            "suspended_tenants": 0,
            "terminated_tenants": 0,
            "created_today": 0,
            "last_cleanup": None
        }
        
    async def start(self):
        """Start the tenant manager."""
        logger.info("Starting tenant manager")
        # Start background tasks
        asyncio.create_task(self._cleanup_expired_tenants())
        asyncio.create_task(self._update_statistics())
        
    async def stop(self):
        """Stop the tenant manager."""
        logger.info("Stopping tenant manager")
        
    async def create_tenant(self, name: str, tier: TenantTier = None, 
                          admin_user: str = None, metadata: Dict[str, Any] = None) -> Tenant:
        """Create a new tenant."""
        with self.lock:
            # Check if tenant already exists
            if name in self.tenant_index:
                raise ValueError(f"Tenant '{name}' already exists")
            
            # Check tenant limit
            if len(self.tenants) >= self.config.max_tenants:
                raise ValueError(f"Maximum tenant limit ({self.config.max_tenants}) reached")
            
            # Generate tenant ID
            tenant_id = f"{self.config.tenant_prefix}{uuid.uuid4().hex[:8]}"
            
            # Create tenant
            tenant = Tenant(
                id=tenant_id,
                name=name,
                tier=tier or self.config.default_tier,
                metadata=metadata or {},
                resource_quotas=self._get_default_quotas(tier or self.config.default_tier),
                settings=self._get_default_settings()
            )
            
            if admin_user:
                tenant.admin_users.add(admin_user)
                tenant.users.add(admin_user)
            
            # Store tenant
            self.tenants[tenant_id] = tenant
            self.tenant_index[name] = tenant_id
            
            # Update statistics
            self.stats["total_tenants"] += 1
            self.stats["active_tenants"] += 1
            self.stats["created_today"] += 1
            
            logger.info(f"Created tenant: {name} (ID: {tenant_id})")
            return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)
    
    async def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Get tenant by name."""
        tenant_id = self.tenant_index.get(name)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None
    
    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant configuration."""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            # Update allowed fields
            if "name" in updates and updates["name"] != tenant.name:
                # Update name index
                old_name = tenant.name
                new_name = updates["name"]
                if new_name in self.tenant_index:
                    raise ValueError(f"Tenant name '{new_name}' already exists")
                del self.tenant_index[old_name]
                self.tenant_index[new_name] = tenant_id
                tenant.name = new_name
            
            if "tier" in updates:
                tenant.tier = TenantTier(updates["tier"])
                # Update quotas based on new tier
                tenant.resource_quotas = self._get_default_quotas(tenant.tier)
            
            if "status" in updates:
                old_status = tenant.status
                tenant.status = TenantStatus(updates["status"])
                self._update_status_stats(old_status, tenant.status)
            
            if "metadata" in updates:
                tenant.metadata.update(updates["metadata"])
            
            if "settings" in updates:
                tenant.settings.update(updates["settings"])
            
            if "resource_quotas" in updates:
                tenant.resource_quotas.update(updates["resource_quotas"])
            
            tenant.updated_at = datetime.now()
            
            logger.info(f"Updated tenant: {tenant_id}")
            return True
    
    async def delete_tenant(self, tenant_id: str, force: bool = False) -> bool:
        """Delete a tenant."""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            if not force and tenant.status == TenantStatus.ACTIVE:
                # Suspend first, then schedule for deletion
                tenant.status = TenantStatus.SUSPENDED
                tenant.expires_at = datetime.now() + timedelta(days=self.config.retention_days)
                tenant.updated_at = datetime.now()
                logger.info(f"Suspended tenant for deletion: {tenant_id}")
                return True
            
            # Remove tenant
            del self.tenants[tenant_id]
            del self.tenant_index[tenant.name]
            
            # Update statistics
            self.stats["total_tenants"] -= 1
            if tenant.status == TenantStatus.ACTIVE:
                self.stats["active_tenants"] -= 1
            elif tenant.status == TenantStatus.SUSPENDED:
                self.stats["suspended_tenants"] -= 1
            
            logger.info(f"Deleted tenant: {tenant_id}")
            return True
    
    async def list_tenants(self, status: TenantStatus = None, 
                          tier: TenantTier = None, limit: int = None) -> List[Tenant]:
        """List tenants with optional filtering."""
        tenants = list(self.tenants.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        if tier:
            tenants = [t for t in tenants if t.tier == tier]
        
        # Sort by creation date
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        
        if limit:
            tenants = tenants[:limit]
        
        return tenants
    
    async def add_user_to_tenant(self, tenant_id: str, user_id: str, is_admin: bool = False) -> bool:
        """Add user to tenant."""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            tenant.users.add(user_id)
            if is_admin:
                tenant.admin_users.add(user_id)
            
            tenant.updated_at = datetime.now()
            logger.info(f"Added user {user_id} to tenant {tenant_id}")
            return True
    
    async def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> bool:
        """Remove user from tenant."""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False
            
            tenant.users.discard(user_id)
            tenant.admin_users.discard(user_id)
            
            tenant.updated_at = datetime.now()
            logger.info(f"Removed user {user_id} from tenant {tenant_id}")
            return True
    
    async def get_tenant_statistics(self) -> Dict[str, Any]:
        """Get tenant statistics."""
        return self.stats.copy()
    
    async def export_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Export tenant configuration."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {}
        
        return tenant.to_dict()
    
    async def import_tenant_config(self, config: Dict[str, Any]) -> bool:
        """Import tenant configuration."""
        try:
            tenant = Tenant.from_dict(config)
            
            with self.lock:
                # Check if tenant already exists
                if tenant.id in self.tenants or tenant.name in self.tenant_index:
                    return False
                
                self.tenants[tenant.id] = tenant
                self.tenant_index[tenant.name] = tenant.id
                
                # Update statistics
                self.stats["total_tenants"] += 1
                if tenant.status == TenantStatus.ACTIVE:
                    self.stats["active_tenants"] += 1
                elif tenant.status == TenantStatus.SUSPENDED:
                    self.stats["suspended_tenants"] += 1
                
                logger.info(f"Imported tenant: {tenant.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to import tenant config: {e}")
            return False
    
    def _get_default_quotas(self, tier: TenantTier) -> Dict[str, Any]:
        """Get default resource quotas for tier."""
        base_quotas = {
            "storage": "10GB",
            "compute_hours": 100,
            "api_requests": 10000,
            "concurrent_jobs": 5,
            "max_users": 50,
            "max_pipelines": 100,
            "max_datasets": 1000
        }
        
        # Adjust based on tier
        multipliers = {
            TenantTier.BASIC: 0.5,
            TenantTier.STANDARD: 1.0,
            TenantTier.PREMIUM: 2.0,
            TenantTier.ENTERPRISE: 5.0
        }
        
        multiplier = multipliers.get(tier, 1.0)
        
        return {
            "storage": f"{int(10 * multiplier)}GB",
            "compute_hours": int(100 * multiplier),
            "api_requests": int(10000 * multiplier),
            "concurrent_jobs": int(5 * multiplier),
            "max_users": int(50 * multiplier),
            "max_pipelines": int(100 * multiplier),
            "max_datasets": int(1000 * multiplier)
        }
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default tenant settings."""
        return {
            "isolation_level": self.config.isolation_level,
            "cross_tenant_sharing": self.config.enable_cross_tenant_sharing,
            "backup_enabled": self.config.backup_enabled,
            "monitoring_enabled": True,
            "audit_logging": True,
            "data_retention_days": 365,
            "auto_scaling": True
        }
    
    def _update_status_stats(self, old_status: TenantStatus, new_status: TenantStatus):
        """Update status statistics."""
        if old_status == TenantStatus.ACTIVE:
            self.stats["active_tenants"] -= 1
        elif old_status == TenantStatus.SUSPENDED:
            self.stats["suspended_tenants"] -= 1
        elif old_status == TenantStatus.TERMINATED:
            self.stats["terminated_tenants"] -= 1
        
        if new_status == TenantStatus.ACTIVE:
            self.stats["active_tenants"] += 1
        elif new_status == TenantStatus.SUSPENDED:
            self.stats["suspended_tenants"] += 1
        elif new_status == TenantStatus.TERMINATED:
            self.stats["terminated_tenants"] += 1
    
    async def _cleanup_expired_tenants(self):
        """Background task to cleanup expired tenants."""
        while True:
            try:
                now = datetime.now()
                expired_tenants = []
                
                with self.lock:
                    for tenant_id, tenant in self.tenants.items():
                        if (tenant.expires_at and tenant.expires_at <= now and 
                            tenant.status == TenantStatus.SUSPENDED):
                            expired_tenants.append(tenant_id)
                
                for tenant_id in expired_tenants:
                    await self.delete_tenant(tenant_id, force=True)
                
                self.stats["last_cleanup"] = now.isoformat()
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in tenant cleanup: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _update_statistics(self):
        """Background task to update statistics."""
        while True:
            try:
                # Reset daily counters at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute == 0:
                    self.stats["created_today"] = 0
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(300)
