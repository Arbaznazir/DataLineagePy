"""
Isolation Manager for Multi-Tenant DataLineagePy

Provides tenant isolation capabilities to ensure data and operations
are properly separated between tenants.
"""

import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import threading
import logging

logger = logging.getLogger(__name__)


class IsolationLevel(Enum):
    """Isolation levels for tenant separation."""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    COMPLETE = "complete"


@dataclass
class IsolationPolicy:
    """Defines isolation policies for a tenant."""
    level: IsolationLevel
    data_isolation: bool = True
    compute_isolation: bool = True
    network_isolation: bool = False
    storage_isolation: bool = True
    metadata_isolation: bool = True


class IsolationManager:
    """Manages tenant isolation and ensures proper data separation."""
    
    def __init__(self, default_level: IsolationLevel = IsolationLevel.STRICT):
        self.default_level = default_level
        self.tenant_policies: Dict[str, IsolationPolicy] = {}
        self.active_contexts: Dict[str, str] = {}  # thread_id -> tenant_id
        self.isolation_barriers: Dict[str, Set[str]] = {}  # tenant_id -> blocked_tenants
        self._lock = threading.RLock()
        
        logger.info(f"IsolationManager initialized with default level: {default_level}")
    
    def set_tenant_policy(self, tenant_id: str, policy: IsolationPolicy) -> None:
        """Set isolation policy for a tenant."""
        with self._lock:
            self.tenant_policies[tenant_id] = policy
            logger.info(f"Set isolation policy for tenant {tenant_id}: {policy.level}")
    
    def get_tenant_policy(self, tenant_id: str) -> IsolationPolicy:
        """Get isolation policy for a tenant."""
        with self._lock:
            return self.tenant_policies.get(
                tenant_id, 
                IsolationPolicy(self.default_level)
            )
    
    def set_tenant_context(self, tenant_id: str) -> None:
        """Set the current tenant context for this thread."""
        thread_id = str(threading.current_thread().ident)
        with self._lock:
            self.active_contexts[thread_id] = tenant_id
            logger.debug(f"Set tenant context: {tenant_id} for thread {thread_id}")
    
    def get_current_tenant(self) -> Optional[str]:
        """Get the current tenant ID for this thread."""
        thread_id = str(threading.current_thread().ident)
        with self._lock:
            return self.active_contexts.get(thread_id)
    
    def clear_tenant_context(self) -> None:
        """Clear the tenant context for this thread."""
        thread_id = str(threading.current_thread().ident)
        with self._lock:
            self.active_contexts.pop(thread_id, None)
            logger.debug(f"Cleared tenant context for thread {thread_id}")
    
    def can_access_resource(self, tenant_id: str, resource_tenant_id: str) -> bool:
        """Check if a tenant can access a resource owned by another tenant."""
        if tenant_id == resource_tenant_id:
            return True
        
        with self._lock:
            # Check if there's an isolation barrier
            if tenant_id in self.isolation_barriers:
                if resource_tenant_id in self.isolation_barriers[tenant_id]:
                    return False
            
            # Check isolation policies
            policy = self.get_tenant_policy(tenant_id)
            resource_policy = self.get_tenant_policy(resource_tenant_id)
            
            if policy.level == IsolationLevel.COMPLETE:
                return False
            elif policy.level == IsolationLevel.STRICT:
                return False  # No cross-tenant access in strict mode
            elif policy.level == IsolationLevel.BASIC:
                return True  # Allow with basic checks
            else:  # NONE
                return True
    
    def create_isolation_barrier(self, tenant_id: str, blocked_tenants: List[str]) -> None:
        """Create an isolation barrier preventing access between tenants."""
        with self._lock:
            if tenant_id not in self.isolation_barriers:
                self.isolation_barriers[tenant_id] = set()
            self.isolation_barriers[tenant_id].update(blocked_tenants)
            logger.info(f"Created isolation barrier for {tenant_id}: {blocked_tenants}")
    
    def remove_isolation_barrier(self, tenant_id: str, unblocked_tenants: List[str]) -> None:
        """Remove isolation barriers for specific tenants."""
        with self._lock:
            if tenant_id in self.isolation_barriers:
                self.isolation_barriers[tenant_id].difference_update(unblocked_tenants)
                if not self.isolation_barriers[tenant_id]:
                    del self.isolation_barriers[tenant_id]
                logger.info(f"Removed isolation barrier for {tenant_id}: {unblocked_tenants}")
    
    def validate_operation(self, tenant_id: str, operation: str, resource_id: str) -> bool:
        """Validate if a tenant can perform an operation on a resource."""
        current_tenant = self.get_current_tenant()
        
        if current_tenant != tenant_id:
            logger.warning(f"Tenant mismatch: current={current_tenant}, requested={tenant_id}")
            return False
        
        policy = self.get_tenant_policy(tenant_id)
        
        # Apply isolation rules based on policy
        if policy.level == IsolationLevel.COMPLETE:
            # Most restrictive - only allow operations on own resources
            return resource_id.startswith(tenant_id)
        elif policy.level == IsolationLevel.STRICT:
            # Strict isolation with some exceptions
            return self._validate_strict_operation(tenant_id, operation, resource_id)
        elif policy.level == IsolationLevel.BASIC:
            # Basic validation
            return self._validate_basic_operation(tenant_id, operation, resource_id)
        else:  # NONE
            return True
    
    def _validate_strict_operation(self, tenant_id: str, operation: str, resource_id: str) -> bool:
        """Validate operation under strict isolation."""
        # Allow read operations on shared resources
        if operation.startswith('read') and resource_id.startswith('shared_'):
            return True
        
        # Only allow operations on tenant's own resources
        return resource_id.startswith(tenant_id)
    
    def _validate_basic_operation(self, tenant_id: str, operation: str, resource_id: str) -> bool:
        """Validate operation under basic isolation."""
        # More permissive - allow most operations
        forbidden_operations = ['delete_tenant', 'modify_global_config']
        return operation not in forbidden_operations
    
    def get_isolation_stats(self) -> Dict[str, Any]:
        """Get isolation manager statistics."""
        with self._lock:
            return {
                'active_contexts': len(self.active_contexts),
                'tenant_policies': len(self.tenant_policies),
                'isolation_barriers': len(self.isolation_barriers),
                'default_level': self.default_level.value,
                'policy_distribution': {
                    level.value: sum(1 for p in self.tenant_policies.values() if p.level == level)
                    for level in IsolationLevel
                }
            }
    
    def cleanup_tenant(self, tenant_id: str) -> None:
        """Clean up isolation data for a removed tenant."""
        with self._lock:
            # Remove tenant policy
            self.tenant_policies.pop(tenant_id, None)
            
            # Remove isolation barriers
            self.isolation_barriers.pop(tenant_id, None)
            
            # Remove from other tenants' barriers
            for barriers in self.isolation_barriers.values():
                barriers.discard(tenant_id)
            
            # Clear any active contexts for this tenant
            contexts_to_remove = [
                thread_id for thread_id, tid in self.active_contexts.items()
                if tid == tenant_id
            ]
            for thread_id in contexts_to_remove:
                del self.active_contexts[thread_id]
            
            logger.info(f"Cleaned up isolation data for tenant: {tenant_id}")


class IsolationContext:
    """Context manager for tenant isolation."""
    
    def __init__(self, isolation_manager: IsolationManager, tenant_id: str):
        self.isolation_manager = isolation_manager
        self.tenant_id = tenant_id
        self.previous_tenant = None
    
    def __enter__(self):
        self.previous_tenant = self.isolation_manager.get_current_tenant()
        self.isolation_manager.set_tenant_context(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_tenant:
            self.isolation_manager.set_tenant_context(self.previous_tenant)
        else:
            self.isolation_manager.clear_tenant_context()


def create_isolation_manager(level: IsolationLevel = IsolationLevel.STRICT) -> IsolationManager:
    """Factory function to create an isolation manager."""
    return IsolationManager(level)
