"""
Tenant Authentication for Multi-Tenant DataLineagePy

Provides authentication and authorization capabilities for multi-tenant environments.
"""

import uuid
import hashlib
import secrets
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import logging
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods."""
    PASSWORD = "password"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"
    SAML = "saml"


class UserRole(Enum):
    """User roles within a tenant."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    ANALYST = "analyst"
    DEVELOPER = "developer"


@dataclass
class TenantUser:
    """Represents a user within a tenant."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    tenant_id: str = ""
    roles: Set[UserRole] = field(default_factory=set)
    password_hash: Optional[str] = None
    api_keys: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantContext:
    """Represents the current tenant context."""
    tenant_id: str
    user_id: str
    username: str
    roles: Set[UserRole]
    permissions: Set[str]
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class AuthSession:
    """Represents an authentication session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    tenant_id: str = ""
    method: AuthMethod = AuthMethod.PASSWORD
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    active: bool = True


class TenantAuthenticator:
    """Handles authentication and authorization for multi-tenant environments."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.users: Dict[str, TenantUser] = {}
        self.sessions: Dict[str, AuthSession] = {}
        self.tenant_contexts: Dict[str, TenantContext] = {}  # thread_id -> context
        self._lock = threading.RLock()
        
        # Configuration
        self.jwt_secret = self.config.get('jwt_secret', secrets.token_urlsafe(32))
        self.session_timeout = self.config.get('session_timeout_minutes', 60)
        self.max_sessions_per_user = self.config.get('max_sessions_per_user', 5)
        self.password_min_length = self.config.get('password_min_length', 8)
        
        logger.info("TenantAuthenticator initialized")
    
    def create_user(self, username: str, email: str, tenant_id: str, 
                   password: str, roles: Optional[Set[UserRole]] = None) -> str:
        """Create a new tenant user."""
        with self._lock:
            # Check if user already exists
            existing_user = self._find_user_by_username(username, tenant_id)
            if existing_user:
                raise ValueError(f"User {username} already exists in tenant {tenant_id}")
            
            # Validate password
            if len(password) < self.password_min_length:
                raise ValueError(f"Password must be at least {self.password_min_length} characters")
            
            user = TenantUser(
                username=username,
                email=email,
                tenant_id=tenant_id,
                roles=roles or {UserRole.USER},
                password_hash=self._hash_password(password)
            )
            
            self.users[user.id] = user
            logger.info(f"Created user {username} in tenant {tenant_id}")
            return user.id
    
    def authenticate_user(self, username: str, password: str, tenant_id: str) -> Optional[str]:
        """Authenticate a user with username/password."""
        with self._lock:
            user = self._find_user_by_username(username, tenant_id)
            if not user or not user.active:
                return None
            
            if not self._verify_password(password, user.password_hash):
                return None
            
            # Create session
            session = AuthSession(
                user_id=user.id,
                tenant_id=tenant_id,
                method=AuthMethod.PASSWORD,
                expires_at=datetime.now() + timedelta(minutes=self.session_timeout)
            )
            
            # Clean up old sessions if needed
            self._cleanup_user_sessions(user.id)
            
            self.sessions[session.id] = session
            user.last_login = datetime.now()
            
            logger.info(f"User {username} authenticated in tenant {tenant_id}")
            return session.id
    
    def authenticate_api_key(self, api_key: str, tenant_id: str) -> Optional[str]:
        """Authenticate using API key."""
        with self._lock:
            user = self._find_user_by_api_key(api_key, tenant_id)
            if not user or not user.active:
                return None
            
            # Create session
            session = AuthSession(
                user_id=user.id,
                tenant_id=tenant_id,
                method=AuthMethod.API_KEY,
                expires_at=datetime.now() + timedelta(minutes=self.session_timeout)
            )
            
            self.sessions[session.id] = session
            user.last_login = datetime.now()
            
            logger.info(f"User {user.username} authenticated via API key in tenant {tenant_id}")
            return session.id
    
    def authenticate_jwt(self, token: str) -> Optional[str]:
        """Authenticate using JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            user_id = payload.get('user_id')
            tenant_id = payload.get('tenant_id')
            
            with self._lock:
                user = self.users.get(user_id)
                if not user or not user.active or user.tenant_id != tenant_id:
                    return None
                
                # Create session
                session = AuthSession(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    method=AuthMethod.JWT,
                    expires_at=datetime.now() + timedelta(minutes=self.session_timeout)
                )
                
                self.sessions[session.id] = session
                user.last_login = datetime.now()
                
                logger.info(f"User {user.username} authenticated via JWT in tenant {tenant_id}")
                return session.id
        
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token provided")
            return None
    
    def create_tenant_context(self, session_id: str) -> Optional[TenantContext]:
        """Create a tenant context from a session."""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session or not session.active:
                return None
            
            if session.expires_at and session.expires_at < datetime.now():
                session.active = False
                return None
            
            user = self.users.get(session.user_id)
            if not user or not user.active:
                return None
            
            # Update session activity
            session.last_activity = datetime.now()
            
            # Create context
            context = TenantContext(
                tenant_id=session.tenant_id,
                user_id=user.id,
                username=user.username,
                roles=user.roles,
                permissions=self._get_user_permissions(user),
                session_id=session_id,
                expires_at=session.expires_at
            )
            
            # Store context for current thread
            thread_id = str(threading.current_thread().ident)
            self.tenant_contexts[thread_id] = context
            
            return context
    
    def get_current_context(self) -> Optional[TenantContext]:
        """Get the current tenant context for this thread."""
        thread_id = str(threading.current_thread().ident)
        with self._lock:
            return self.tenant_contexts.get(thread_id)
    
    def clear_context(self) -> None:
        """Clear the tenant context for this thread."""
        thread_id = str(threading.current_thread().ident)
        with self._lock:
            self.tenant_contexts.pop(thread_id, None)
    
    def logout_session(self, session_id: str) -> bool:
        """Logout a session."""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session.active = False
            
            # Clear any contexts using this session
            contexts_to_remove = [
                thread_id for thread_id, context in self.tenant_contexts.items()
                if context.session_id == session_id
            ]
            for thread_id in contexts_to_remove:
                del self.tenant_contexts[thread_id]
            
            logger.info(f"Logged out session {session_id}")
            return True
    
    def generate_api_key(self, user_id: str) -> str:
        """Generate a new API key for a user."""
        with self._lock:
            user = self.users.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            api_key = secrets.token_urlsafe(32)
            user.api_keys.append(api_key)
            
            logger.info(f"Generated API key for user {user.username}")
            return api_key
    
    def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke an API key."""
        with self._lock:
            user = self.users.get(user_id)
            if not user:
                return False
            
            if api_key in user.api_keys:
                user.api_keys.remove(api_key)
                logger.info(f"Revoked API key for user {user.username}")
                return True
            
            return False
    
    def generate_jwt_token(self, user_id: str, tenant_id: str, 
                          expires_in: int = 3600) -> Optional[str]:
        """Generate JWT token for user."""
        with self._lock:
            if not JWT_AVAILABLE:
                logger.warning("JWT library not available - using simple token")
                # Generate a simple token as fallback
                import base64
                token_data = f"{user_id}:{tenant_id}:{datetime.utcnow().timestamp()}"
                return base64.b64encode(token_data.encode()).decode()
            
            if not self.config.get('jwt_secret'):
                logger.error("JWT secret not configured")
                return None
            
            payload = {
                'user_id': user_id,
                'tenant_id': tenant_id,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow(),
                'iss': 'datalineagepy'
            }
            
            try:
                token = jwt.encode(
                    payload,
                    self.config['jwt_secret'],
                    algorithm=self.config.get('jwt_algorithm', 'HS256')
                )
                logger.debug(f"Generated JWT token for user {user_id}")
                return token
            except Exception as e:
                logger.error(f"Error generating JWT token: {e}")
                return None
    
    def check_permission(self, permission: str, context: Optional[TenantContext] = None) -> bool:
        """Check if the current user has a specific permission."""
        if not context:
            context = self.get_current_context()
        
        if not context:
            return False
        
        return permission in context.permissions
    
    def _find_user_by_username(self, username: str, tenant_id: str) -> Optional[TenantUser]:
        """Find a user by username within a tenant."""
        for user in self.users.values():
            if user.username == username and user.tenant_id == tenant_id:
                return user
        return None
    
    def _find_user_by_api_key(self, api_key: str, tenant_id: str) -> Optional[TenantUser]:
        """Find a user by API key within a tenant."""
        for user in self.users.values():
            if api_key in user.api_keys and user.tenant_id == tenant_id:
                return user
        return None
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, hash_value = password_hash.split(':')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == hash_value
        except ValueError:
            return False
    
    def _get_user_permissions(self, user: TenantUser) -> Set[str]:
        """Get permissions for a user based on their roles."""
        permissions = set()
        
        for role in user.roles:
            if role == UserRole.ADMIN:
                permissions.update([
                    'read_all', 'write_all', 'delete_all', 'manage_users',
                    'manage_tenant', 'view_audit_logs', 'manage_sharing'
                ])
            elif role == UserRole.USER:
                permissions.update([
                    'read_own', 'write_own', 'create_lineage', 'view_lineage'
                ])
            elif role == UserRole.VIEWER:
                permissions.update([
                    'read_own', 'view_lineage'
                ])
            elif role == UserRole.ANALYST:
                permissions.update([
                    'read_all', 'create_lineage', 'view_lineage', 'analyze_data'
                ])
            elif role == UserRole.DEVELOPER:
                permissions.update([
                    'read_all', 'write_own', 'create_lineage', 'view_lineage',
                    'manage_integrations', 'view_api_docs'
                ])
        
        return permissions
    
    def _cleanup_user_sessions(self, user_id: str) -> None:
        """Clean up old sessions for a user."""
        user_sessions = [
            session for session in self.sessions.values()
            if session.user_id == user_id and session.active
        ]
        
        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest sessions
            user_sessions.sort(key=lambda s: s.last_activity)
            sessions_to_remove = user_sessions[:-self.max_sessions_per_user + 1]
            
            for session in sessions_to_remove:
                session.active = False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        with self._lock:
            expired_count = 0
            now = datetime.now()
            
            for session in self.sessions.values():
                if (session.expires_at and session.expires_at < now) or not session.active:
                    session.active = False
                    expired_count += 1
            
            # Clean up contexts for expired sessions
            contexts_to_remove = [
                thread_id for thread_id, context in self.tenant_contexts.items()
                if context.expires_at and context.expires_at < now
            ]
            for thread_id in contexts_to_remove:
                del self.tenant_contexts[thread_id]
            
            logger.info(f"Cleaned up {expired_count} expired sessions")
            return expired_count
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        with self._lock:
            active_sessions = sum(1 for s in self.sessions.values() if s.active)
            active_users = sum(1 for u in self.users.values() if u.active)
            
            return {
                'total_users': len(self.users),
                'active_users': active_users,
                'total_sessions': len(self.sessions),
                'active_sessions': active_sessions,
                'active_contexts': len(self.tenant_contexts)
            }


def create_tenant_authenticator(config: Optional[Dict[str, Any]] = None) -> TenantAuthenticator:
    """Factory function to create a tenant authenticator."""
    return TenantAuthenticator(config)
