"""
Sharing Manager for Multi-Tenant DataLineagePy

Manages cross-tenant data sharing policies, permissions, and access controls.
"""

import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)


class SharingPermission(Enum):
    """Types of sharing permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    SHARE = "share"


class SharingScope(Enum):
    """Scope of sharing permissions."""
    RESOURCE = "resource"
    DATASET = "dataset"
    LINEAGE = "lineage"
    METADATA = "metadata"
    ALL = "all"


@dataclass
class SharingPolicy:
    """Defines a sharing policy between tenants."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_tenant: str = ""
    target_tenant: str = ""
    permissions: Set[SharingPermission] = field(default_factory=set)
    scope: SharingScope = SharingScope.RESOURCE
    resource_patterns: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    active: bool = True


@dataclass
class SharingRequest:
    """Represents a sharing request between tenants."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_tenant: str = ""
    target_tenant: str = ""
    resource_id: str = ""
    requested_permissions: Set[SharingPermission] = field(default_factory=set)
    justification: str = ""
    status: str = "pending"  # pending, approved, rejected, expired
    requested_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class SharingManager:
    """Manages cross-tenant sharing policies and permissions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.policies: Dict[str, SharingPolicy] = {}
        self.requests: Dict[str, SharingRequest] = {}
        self.tenant_shares: Dict[str, Set[str]] = {}  # tenant_id -> shared_with_tenants
        self.resource_shares: Dict[str, Dict[str, Set[SharingPermission]]] = {}  # resource_id -> {tenant_id: permissions}
        self._lock = threading.RLock()
        
        # Configuration
        self.auto_approve_read = self.config.get('auto_approve_read', False)
        self.default_expiry_days = self.config.get('default_expiry_days', 30)
        self.max_sharing_policies = self.config.get('max_sharing_policies', 1000)
        
        logger.info("SharingManager initialized")
    
    def create_sharing_policy(self, policy: SharingPolicy) -> str:
        """Create a new sharing policy."""
        with self._lock:
            if len(self.policies) >= self.max_sharing_policies:
                raise ValueError("Maximum number of sharing policies reached")
            
            # Set default expiry if not specified
            if not policy.expires_at and self.default_expiry_days > 0:
                policy.expires_at = datetime.now() + timedelta(days=self.default_expiry_days)
            
            self.policies[policy.id] = policy
            
            # Update tenant sharing relationships
            if policy.source_tenant not in self.tenant_shares:
                self.tenant_shares[policy.source_tenant] = set()
            self.tenant_shares[policy.source_tenant].add(policy.target_tenant)
            
            logger.info(f"Created sharing policy {policy.id}: {policy.source_tenant} -> {policy.target_tenant}")
            return policy.id
    
    def get_sharing_policy(self, policy_id: str) -> Optional[SharingPolicy]:
        """Get a sharing policy by ID."""
        with self._lock:
            return self.policies.get(policy_id)
    
    def update_sharing_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing sharing policy."""
        with self._lock:
            if policy_id not in self.policies:
                return False
            
            policy = self.policies[policy_id]
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            
            logger.info(f"Updated sharing policy {policy_id}")
            return True
    
    def delete_sharing_policy(self, policy_id: str) -> bool:
        """Delete a sharing policy."""
        with self._lock:
            if policy_id not in self.policies:
                return False
            
            policy = self.policies.pop(policy_id)
            
            # Update tenant sharing relationships
            if policy.source_tenant in self.tenant_shares:
                self.tenant_shares[policy.source_tenant].discard(policy.target_tenant)
                if not self.tenant_shares[policy.source_tenant]:
                    del self.tenant_shares[policy.source_tenant]
            
            logger.info(f"Deleted sharing policy {policy_id}")
            return True
    
    def request_sharing_access(self, request: SharingRequest) -> str:
        """Request sharing access to a resource."""
        with self._lock:
            # Set default expiry
            if not request.expires_at:
                request.expires_at = datetime.now() + timedelta(days=self.default_expiry_days)
            
            self.requests[request.id] = request
            
            # Auto-approve read-only requests if configured
            if (self.auto_approve_read and 
                request.requested_permissions == {SharingPermission.READ}):
                self.approve_sharing_request(request.id, "system", "Auto-approved read request")
            
            logger.info(f"Created sharing request {request.id}: {request.source_tenant} -> {request.target_tenant}")
            return request.id
    
    def approve_sharing_request(self, request_id: str, reviewer: str, notes: str = "") -> bool:
        """Approve a sharing request."""
        with self._lock:
            if request_id not in self.requests:
                return False
            
            request = self.requests[request_id]
            if request.status != "pending":
                return False
            
            request.status = "approved"
            request.reviewed_at = datetime.now()
            request.reviewed_by = reviewer
            
            # Create sharing policy from approved request
            policy = SharingPolicy(
                name=f"Auto-generated from request {request_id}",
                source_tenant=request.source_tenant,
                target_tenant=request.target_tenant,
                permissions=request.requested_permissions,
                resource_patterns=[request.resource_id],
                expires_at=request.expires_at,
                created_by=reviewer
            )
            
            self.create_sharing_policy(policy)
            
            # Update resource sharing
            if request.resource_id not in self.resource_shares:
                self.resource_shares[request.resource_id] = {}
            self.resource_shares[request.resource_id][request.target_tenant] = request.requested_permissions
            
            logger.info(f"Approved sharing request {request_id} by {reviewer}")
            return True
    
    def reject_sharing_request(self, request_id: str, reviewer: str, reason: str = "") -> bool:
        """Reject a sharing request."""
        with self._lock:
            if request_id not in self.requests:
                return False
            
            request = self.requests[request_id]
            if request.status != "pending":
                return False
            
            request.status = "rejected"
            request.reviewed_at = datetime.now()
            request.reviewed_by = reviewer
            
            logger.info(f"Rejected sharing request {request_id} by {reviewer}: {reason}")
            return True
    
    def check_sharing_permission(self, tenant_id: str, resource_id: str, permission: SharingPermission) -> bool:
        """Check if a tenant has sharing permission for a resource."""
        with self._lock:
            # Check direct resource sharing
            if resource_id in self.resource_shares:
                tenant_permissions = self.resource_shares[resource_id].get(tenant_id, set())
                if permission in tenant_permissions:
                    return True
            
            # Check policy-based sharing
            for policy in self.policies.values():
                if not policy.active:
                    continue
                
                if policy.expires_at and policy.expires_at < datetime.now():
                    continue
                
                if policy.target_tenant != tenant_id:
                    continue
                
                if permission not in policy.permissions:
                    continue
                
                # Check resource patterns
                if self._matches_resource_pattern(resource_id, policy.resource_patterns):
                    return True
            
            return False
    
    def _matches_resource_pattern(self, resource_id: str, patterns: List[str]) -> bool:
        """Check if a resource ID matches any of the patterns."""
        if not patterns:
            return True  # Empty patterns match all
        
        for pattern in patterns:
            if pattern == "*" or resource_id.startswith(pattern):
                return True
        
        return False
    
    def get_tenant_shared_resources(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get resources shared with a tenant."""
        with self._lock:
            shared_resources = []
            
            # From direct resource sharing
            for resource_id, tenant_permissions in self.resource_shares.items():
                if tenant_id in tenant_permissions:
                    shared_resources.append({
                        'resource_id': resource_id,
                        'permissions': list(tenant_permissions[tenant_id]),
                        'source': 'direct'
                    })
            
            # From policy-based sharing
            for policy in self.policies.values():
                if (policy.active and 
                    policy.target_tenant == tenant_id and
                    (not policy.expires_at or policy.expires_at > datetime.now())):
                    
                    for pattern in policy.resource_patterns:
                        shared_resources.append({
                            'resource_pattern': pattern,
                            'permissions': list(policy.permissions),
                            'source': 'policy',
                            'policy_id': policy.id
                        })
            
            return shared_resources
    
    def get_tenant_sharing_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get sharing statistics for a tenant."""
        with self._lock:
            outgoing_policies = [p for p in self.policies.values() if p.source_tenant == tenant_id]
            incoming_policies = [p for p in self.policies.values() if p.target_tenant == tenant_id]
            
            outgoing_requests = [r for r in self.requests.values() if r.source_tenant == tenant_id]
            incoming_requests = [r for r in self.requests.values() if r.target_tenant == tenant_id]
            
            return {
                'outgoing_policies': len(outgoing_policies),
                'incoming_policies': len(incoming_policies),
                'outgoing_requests': len(outgoing_requests),
                'incoming_requests': len(incoming_requests),
                'shared_with_tenants': len(self.tenant_shares.get(tenant_id, set())),
                'shared_resources': len([r for r in self.resource_shares.values() if tenant_id in r])
            }
    
    def cleanup_expired_policies(self) -> int:
        """Clean up expired sharing policies."""
        with self._lock:
            expired_policies = []
            now = datetime.now()
            
            for policy_id, policy in self.policies.items():
                if policy.expires_at and policy.expires_at < now:
                    expired_policies.append(policy_id)
            
            for policy_id in expired_policies:
                self.delete_sharing_policy(policy_id)
            
            logger.info(f"Cleaned up {len(expired_policies)} expired sharing policies")
            return len(expired_policies)
    
    def cleanup_expired_requests(self) -> int:
        """Clean up expired sharing requests."""
        with self._lock:
            expired_requests = []
            now = datetime.now()
            
            for request_id, request in self.requests.items():
                if request.expires_at and request.expires_at < now:
                    expired_requests.append(request_id)
            
            for request_id in expired_requests:
                self.requests[request_id].status = "expired"
            
            logger.info(f"Marked {len(expired_requests)} sharing requests as expired")
            return len(expired_requests)
    
    def get_sharing_stats(self) -> Dict[str, Any]:
        """Get overall sharing statistics."""
        with self._lock:
            active_policies = sum(1 for p in self.policies.values() if p.active)
            pending_requests = sum(1 for r in self.requests.values() if r.status == "pending")
            
            return {
                'total_policies': len(self.policies),
                'active_policies': active_policies,
                'total_requests': len(self.requests),
                'pending_requests': pending_requests,
                'tenant_relationships': len(self.tenant_shares),
                'shared_resources': len(self.resource_shares)
            }


def create_sharing_manager(config: Optional[Dict[str, Any]] = None) -> SharingManager:
    """Factory function to create a sharing manager."""
    return SharingManager(config)
