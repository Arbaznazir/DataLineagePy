"""
Role-Based Access Control (RBAC) Engine
Enterprise-grade authorization system with hierarchical roles and fine-grained permissions.
"""

from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import uuid


class ResourceType(Enum):
    """Types of resources that can be protected."""
    LINEAGE_GRAPH = "lineage_graph"
    DATA_SOURCE = "data_source"
    PIPELINE = "pipeline"
    REPORT = "report"
    USER = "user"
    ROLE = "role"
    SYSTEM = "system"
    API_ENDPOINT = "api_endpoint"


class Action(Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    SHARE = "share"
    EXPORT = "export"
    ADMIN = "admin"


@dataclass
class Permission:
    """Represents a specific permission."""
    id: str
    resource_type: ResourceType
    action: Action
    resource_id: Optional[str] = None  # Specific resource ID, None for all resources of type
    conditions: Dict[str, Any] = field(default_factory=dict)  # Additional conditions
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self):
        resource_str = f"{self.resource_type.value}"
        if self.resource_id:
            resource_str += f":{self.resource_id}"
        return f"{self.action.value}:{resource_str}"


@dataclass
class Role:
    """Represents a role with associated permissions."""
    id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)  # Permission IDs
    parent_roles: Set[str] = field(default_factory=set)  # Inherit from parent roles
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class User:
    """Represents a user with roles and direct permissions."""
    id: str
    email: str
    roles: Set[str] = field(default_factory=set)  # Role IDs
    direct_permissions: Set[str] = field(default_factory=set)  # Direct permission IDs
    attributes: Dict[str, Any] = field(default_factory=dict)  # User attributes for conditions
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class RBACEngine:
    """
    Role-Based Access Control Engine.
    
    Features:
    - Hierarchical roles with inheritance
    - Fine-grained permissions
    - Resource-specific access control
    - Conditional permissions
    - Permission caching for performance
    """
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self._permission_cache: Dict[str, Set[str]] = {}  # User ID -> Permission IDs
        self._cache_ttl = timedelta(minutes=15)
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Initialize system roles
        self._initialize_system_roles()
    
    def _initialize_system_roles(self):
        """Initialize default system roles."""
        # Super Admin - Full system access
        super_admin_perms = set()
        for resource_type in ResourceType:
            for action in Action:
                perm_id = str(uuid.uuid4())
                permission = Permission(
                    id=perm_id,
                    resource_type=resource_type,
                    action=action
                )
                self.permissions[perm_id] = permission
                super_admin_perms.add(perm_id)
        
        super_admin_role = Role(
            id="super_admin",
            name="Super Administrator",
            description="Full system access",
            permissions=super_admin_perms,
            is_system_role=True
        )
        self.roles["super_admin"] = super_admin_role
        
        # Admin - System administration without user management
        admin_perms = set()
        admin_resources = [ResourceType.LINEAGE_GRAPH, ResourceType.DATA_SOURCE, 
                          ResourceType.PIPELINE, ResourceType.REPORT, ResourceType.SYSTEM]
        for resource_type in admin_resources:
            for action in Action:
                if not (resource_type == ResourceType.SYSTEM and action == Action.DELETE):
                    perm_id = str(uuid.uuid4())
                    permission = Permission(
                        id=perm_id,
                        resource_type=resource_type,
                        action=action
                    )
                    self.permissions[perm_id] = permission
                    admin_perms.add(perm_id)
        
        admin_role = Role(
            id="admin",
            name="Administrator",
            description="System administration access",
            permissions=admin_perms,
            is_system_role=True
        )
        self.roles["admin"] = admin_role
        
        # Data Analyst - Read access to data and lineage
        analyst_perms = set()
        analyst_resources = [ResourceType.LINEAGE_GRAPH, ResourceType.DATA_SOURCE, 
                           ResourceType.PIPELINE, ResourceType.REPORT]
        analyst_actions = [Action.READ, Action.EXPORT]
        for resource_type in analyst_resources:
            for action in analyst_actions:
                perm_id = str(uuid.uuid4())
                permission = Permission(
                    id=perm_id,
                    resource_type=resource_type,
                    action=action
                )
                self.permissions[perm_id] = permission
                analyst_perms.add(perm_id)
        
        analyst_role = Role(
            id="data_analyst",
            name="Data Analyst",
            description="Read access to data lineage and reports",
            permissions=analyst_perms,
            is_system_role=True
        )
        self.roles["data_analyst"] = analyst_role
        
        # Data Engineer - Create and manage pipelines
        engineer_perms = set()
        engineer_resources = [ResourceType.LINEAGE_GRAPH, ResourceType.DATA_SOURCE, 
                            ResourceType.PIPELINE]
        engineer_actions = [Action.CREATE, Action.READ, Action.UPDATE, Action.EXECUTE]
        for resource_type in engineer_resources:
            for action in engineer_actions:
                perm_id = str(uuid.uuid4())
                permission = Permission(
                    id=perm_id,
                    resource_type=resource_type,
                    action=action
                )
                self.permissions[perm_id] = permission
                engineer_perms.add(perm_id)
        
        engineer_role = Role(
            id="data_engineer",
            name="Data Engineer",
            description="Create and manage data pipelines",
            permissions=engineer_perms,
            is_system_role=True
        )
        self.roles["data_engineer"] = engineer_role
        
        # Viewer - Read-only access
        viewer_perms = set()
        viewer_resources = [ResourceType.LINEAGE_GRAPH, ResourceType.REPORT]
        for resource_type in viewer_resources:
            perm_id = str(uuid.uuid4())
            permission = Permission(
                id=perm_id,
                resource_type=resource_type,
                action=Action.READ
            )
            self.permissions[perm_id] = permission
            viewer_perms.add(perm_id)
        
        viewer_role = Role(
            id="viewer",
            name="Viewer",
            description="Read-only access to lineage and reports",
            permissions=viewer_perms,
            is_system_role=True
        )
        self.roles["viewer"] = viewer_role
    
    def create_permission(self, resource_type: ResourceType, action: Action, 
                         resource_id: Optional[str] = None, 
                         conditions: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new permission.
        
        Args:
            resource_type: Type of resource
            action: Action to be performed
            resource_id: Specific resource ID (optional)
            conditions: Additional conditions (optional)
            
        Returns:
            Permission ID
        """
        permission_id = str(uuid.uuid4())
        permission = Permission(
            id=permission_id,
            resource_type=resource_type,
            action=action,
            resource_id=resource_id,
            conditions=conditions or {}
        )
        
        self.permissions[permission_id] = permission
        return permission_id
    
    def create_role(self, name: str, description: str, 
                   permission_ids: Optional[List[str]] = None,
                   parent_role_ids: Optional[List[str]] = None) -> str:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            permission_ids: List of permission IDs
            parent_role_ids: List of parent role IDs for inheritance
            
        Returns:
            Role ID
        """
        role_id = str(uuid.uuid4())
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=set(permission_ids or []),
            parent_roles=set(parent_role_ids or [])
        )
        
        self.roles[role_id] = role
        return role_id
    
    def create_user(self, email: str, role_ids: Optional[List[str]] = None,
                   permission_ids: Optional[List[str]] = None,
                   attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new user.
        
        Args:
            email: User email
            role_ids: List of role IDs
            permission_ids: List of direct permission IDs
            attributes: User attributes
            
        Returns:
            User ID
        """
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            roles=set(role_ids or []),
            direct_permissions=set(permission_ids or []),
            attributes=attributes or {}
        )
        
        self.users[user_id] = user
        return user_id
    
    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """Assign role to user."""
        if user_id in self.users and role_id in self.roles:
            self.users[user_id].roles.add(role_id)
            self._invalidate_user_cache(user_id)
            return True
        return False
    
    def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Revoke role from user."""
        if user_id in self.users and role_id in self.users[user_id].roles:
            self.users[user_id].roles.remove(role_id)
            self._invalidate_user_cache(user_id)
            return True
        return False
    
    def grant_permission_to_user(self, user_id: str, permission_id: str) -> bool:
        """Grant direct permission to user."""
        if user_id in self.users and permission_id in self.permissions:
            self.users[user_id].direct_permissions.add(permission_id)
            self._invalidate_user_cache(user_id)
            return True
        return False
    
    def revoke_permission_from_user(self, user_id: str, permission_id: str) -> bool:
        """Revoke direct permission from user."""
        if user_id in self.users and permission_id in self.users[user_id].direct_permissions:
            self.users[user_id].direct_permissions.remove(permission_id)
            self._invalidate_user_cache(user_id)
            return True
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for a user (including inherited from roles).
        
        Args:
            user_id: User ID
            
        Returns:
            Set of permission IDs
        """
        # Check cache first
        if self._is_cache_valid(user_id):
            return self._permission_cache[user_id]
        
        if user_id not in self.users:
            return set()
        
        user = self.users[user_id]
        all_permissions = set(user.direct_permissions)
        
        # Get permissions from roles (including inherited)
        for role_id in user.roles:
            all_permissions.update(self._get_role_permissions(role_id))
        
        # Cache the result
        self._permission_cache[user_id] = all_permissions
        self._cache_timestamps[user_id] = datetime.utcnow()
        
        return all_permissions
    
    def _get_role_permissions(self, role_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Get all permissions for a role (including inherited from parent roles)."""
        if visited is None:
            visited = set()
        
        if role_id not in self.roles or role_id in visited:
            return set()
        
        visited.add(role_id)
        role = self.roles[role_id]
        all_permissions = set(role.permissions)
        
        # Get permissions from parent roles
        for parent_role_id in role.parent_roles:
            all_permissions.update(self._get_role_permissions(parent_role_id, visited))
        
        return all_permissions
    
    def check_permission(self, user_id: str, resource_type: ResourceType, 
                        action: Action, resource_id: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if user has permission to perform action on resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            action: Action to perform
            resource_id: Specific resource ID (optional)
            context: Additional context for condition evaluation
            
        Returns:
            True if user has permission, False otherwise
        """
        if user_id not in self.users or not self.users[user_id].is_active:
            return False
        
        user_permissions = self.get_user_permissions(user_id)
        context = context or {}
        
        # Check each permission
        for perm_id in user_permissions:
            if perm_id not in self.permissions:
                continue
            
            permission = self.permissions[perm_id]
            
            # Check resource type and action
            if (permission.resource_type == resource_type and 
                permission.action == action):
                
                # Check resource ID (if specified)
                if permission.resource_id is None or permission.resource_id == resource_id:
                    
                    # Check conditions
                    if self._evaluate_conditions(permission.conditions, context, user_id):
                        return True
        
        return False
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], 
                           context: Dict[str, Any], user_id: str) -> bool:
        """Evaluate permission conditions."""
        if not conditions:
            return True
        
        user = self.users.get(user_id)
        if not user:
            return False
        
        # Example condition evaluations
        for condition_type, condition_value in conditions.items():
            if condition_type == "department":
                user_dept = user.attributes.get("department")
                if user_dept != condition_value:
                    return False
            
            elif condition_type == "time_range":
                current_hour = datetime.utcnow().hour
                start_hour, end_hour = condition_value
                if not (start_hour <= current_hour <= end_hour):
                    return False
            
            elif condition_type == "ip_range":
                user_ip = context.get("ip_address")
                if not user_ip or not self._ip_in_range(user_ip, condition_value):
                    return False
        
        return True
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range (simplified implementation)."""
        # In production, use proper IP range checking library
        return True  # Placeholder
    
    def _is_cache_valid(self, user_id: str) -> bool:
        """Check if user permission cache is valid."""
        if user_id not in self._cache_timestamps:
            return False
        
        cache_age = datetime.utcnow() - self._cache_timestamps[user_id]
        return cache_age < self._cache_ttl
    
    def _invalidate_user_cache(self, user_id: str):
        """Invalidate user permission cache."""
        self._permission_cache.pop(user_id, None)
        self._cache_timestamps.pop(user_id, None)
    
    def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get roles assigned to user."""
        if user_id not in self.users:
            return []
        
        user_roles = []
        for role_id in self.users[user_id].roles:
            if role_id in self.roles:
                role = self.roles[role_id]
                user_roles.append({
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "is_system_role": role.is_system_role
                })
        
        return user_roles
    
    def list_permissions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all permissions for user with details."""
        permission_ids = self.get_user_permissions(user_id)
        permissions_list = []
        
        for perm_id in permission_ids:
            if perm_id in self.permissions:
                perm = self.permissions[perm_id]
                permissions_list.append({
                    "id": perm.id,
                    "resource_type": perm.resource_type.value,
                    "action": perm.action.value,
                    "resource_id": perm.resource_id,
                    "conditions": perm.conditions,
                    "description": str(perm)
                })
        
        return permissions_list
    
    def export_rbac_config(self) -> Dict[str, Any]:
        """Export RBAC configuration for backup/migration."""
        return {
            "permissions": {pid: {
                "resource_type": p.resource_type.value,
                "action": p.action.value,
                "resource_id": p.resource_id,
                "conditions": p.conditions
            } for pid, p in self.permissions.items()},
            
            "roles": {rid: {
                "name": r.name,
                "description": r.description,
                "permissions": list(r.permissions),
                "parent_roles": list(r.parent_roles),
                "is_system_role": r.is_system_role
            } for rid, r in self.roles.items()},
            
            "users": {uid: {
                "email": u.email,
                "roles": list(u.roles),
                "direct_permissions": list(u.direct_permissions),
                "attributes": u.attributes,
                "is_active": u.is_active
            } for uid, u in self.users.items()}
        }


# Example usage
if __name__ == "__main__":
    # Initialize RBAC engine
    rbac = RBACEngine()
    
    # Create a user and assign roles
    user_id = rbac.create_user(
        email="analyst@company.com",
        role_ids=["data_analyst"],
        attributes={"department": "analytics", "clearance_level": "standard"}
    )
    
    # Check permissions
    can_read_lineage = rbac.check_permission(
        user_id, ResourceType.LINEAGE_GRAPH, Action.READ
    )
    can_delete_pipeline = rbac.check_permission(
        user_id, ResourceType.PIPELINE, Action.DELETE
    )
    
    print(f"Can read lineage: {can_read_lineage}")
    print(f"Can delete pipeline: {can_delete_pipeline}")
    
    # List user permissions
    permissions = rbac.list_permissions_for_user(user_id)
    print(f"User permissions: {len(permissions)}")
    for perm in permissions[:5]:  # Show first 5
        print(f"  - {perm['description']}")
