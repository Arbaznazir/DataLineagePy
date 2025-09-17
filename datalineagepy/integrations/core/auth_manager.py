"""
Authentication manager for enterprise integrations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
try:
    import jwt
except ImportError:
    jwt = None
import hashlib
import secrets
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Supported authentication types."""
    USERNAME_PASSWORD = "username_password"
    PERSONAL_ACCESS_TOKEN = "personal_access_token"
    OAUTH2 = "oauth2"
    SERVICE_PRINCIPAL = "service_principal"
    PRIVATE_KEY = "private_key"
    SAML = "saml"
    LDAP = "ldap"
    API_KEY = "api_key"


@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: AuthType
    credentials: Dict[str, Any] = field(default_factory=dict)
    token_url: Optional[str] = None
    authorization_url: Optional[str] = None
    scope: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_storage_path: Optional[str] = None
    encryption_key: Optional[str] = None


@dataclass
class AuthToken:
    """Authentication token."""
    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until token expires."""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds()))


class AuthenticationManager:
    """Manages authentication for enterprise integrations."""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.tokens: Dict[str, AuthToken] = {}
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key for secure credential storage."""
        if self.config.encryption_key:
            return self.config.encryption_key.encode()
        return None
    
    def _encrypt_credentials(self, credentials: str) -> str:
        """Encrypt sensitive credentials."""
        if not self.cipher:
            return credentials
        return self.cipher.encrypt(credentials.encode()).decode()
    
    def _decrypt_credentials(self, encrypted_credentials: str) -> str:
        """Decrypt sensitive credentials."""
        if not self.cipher:
            return encrypted_credentials
        return self.cipher.decrypt(encrypted_credentials.encode()).decode()
    
    async def authenticate(self, connector_name: str) -> AuthToken:
        """Authenticate and get access token."""
        try:
            # Check if we have a valid cached token
            if connector_name in self.tokens:
                token = self.tokens[connector_name]
                if not token.is_expired:
                    logger.debug(f"Using cached token for {connector_name}")
                    return token
                
                # Try to refresh if possible
                if token.refresh_token:
                    refreshed_token = await self._refresh_token(token.refresh_token)
                    if refreshed_token:
                        self.tokens[connector_name] = refreshed_token
                        return refreshed_token
            
            # Authenticate based on auth type
            if self.config.auth_type == AuthType.USERNAME_PASSWORD:
                token = await self._authenticate_username_password()
            elif self.config.auth_type == AuthType.PERSONAL_ACCESS_TOKEN:
                token = await self._authenticate_pat()
            elif self.config.auth_type == AuthType.OAUTH2:
                token = await self._authenticate_oauth2()
            elif self.config.auth_type == AuthType.SERVICE_PRINCIPAL:
                token = await self._authenticate_service_principal()
            elif self.config.auth_type == AuthType.PRIVATE_KEY:
                token = await self._authenticate_private_key()
            elif self.config.auth_type == AuthType.API_KEY:
                token = await self._authenticate_api_key()
            else:
                raise ValueError(f"Unsupported auth type: {self.config.auth_type}")
            
            # Cache the token
            self.tokens[connector_name] = token
            logger.info(f"Successfully authenticated {connector_name}")
            return token
            
        except Exception as e:
            logger.error(f"Authentication failed for {connector_name}: {e}")
            raise
    
    async def _authenticate_username_password(self) -> AuthToken:
        """Authenticate using username/password."""
        username = self.config.credentials.get('username')
        password = self.config.credentials.get('password')
        
        if not username or not password:
            raise ValueError("Username and password required")
        
        # Create a simple token (in real implementation, this would call the actual auth service)
        token_data = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        access_token = jwt.encode(token_data, 'secret', algorithm='HS256')
        
        return AuthToken(
            access_token=access_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    async def _authenticate_pat(self) -> AuthToken:
        """Authenticate using Personal Access Token."""
        token_name = self.config.credentials.get('token_name')
        token_secret = self.config.credentials.get('token_secret')
        
        if not token_name or not token_secret:
            raise ValueError("Token name and secret required")
        
        return AuthToken(
            access_token=token_secret,
            token_type="PersonalAccessToken"
        )
    
    async def _authenticate_oauth2(self) -> AuthToken:
        """Authenticate using OAuth2 flow."""
        import aiohttp
        
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("Client ID and secret required for OAuth2")
        
        if not self.config.token_url:
            raise ValueError("Token URL required for OAuth2")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        }
        
        if self.config.scope:
            data['scope'] = self.config.scope
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.config.token_url, data=data) as response:
                if response.status != 200:
                    raise ValueError(f"OAuth2 authentication failed: {response.status}")
                
                token_data = await response.json()
                
                expires_at = None
                if 'expires_in' in token_data:
                    expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                
                return AuthToken(
                    access_token=token_data['access_token'],
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_at=expires_at,
                    refresh_token=token_data.get('refresh_token'),
                    scope=token_data.get('scope')
                )
    
    async def _authenticate_service_principal(self) -> AuthToken:
        """Authenticate using service principal."""
        tenant_id = self.config.credentials.get('tenant_id')
        client_id = self.config.credentials.get('client_id')
        client_secret = self.config.credentials.get('client_secret')
        
        if not all([tenant_id, client_id, client_secret]):
            raise ValueError("Tenant ID, client ID, and client secret required")
        
        # Azure AD token endpoint
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': self.config.scope or 'https://graph.microsoft.com/.default'
        }
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    raise ValueError(f"Service principal authentication failed: {response.status}")
                
                token_data = await response.json()
                
                return AuthToken(
                    access_token=token_data['access_token'],
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_at=datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
                )
    
    async def _authenticate_private_key(self) -> AuthToken:
        """Authenticate using private key."""
        private_key = self.config.credentials.get('private_key')
        username = self.config.credentials.get('username')
        
        if not private_key or not username:
            raise ValueError("Private key and username required")
        
        # Create JWT token with private key
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        access_token = self._create_jwt_token(payload, private_key)
        
        return AuthToken(
            access_token=access_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
    
    async def _authenticate_api_key(self) -> AuthToken:
        """Authenticate using API key."""
        api_key = self.config.credentials.get('api_key')
        
        if not api_key:
            raise ValueError("API key required")
        
        return AuthToken(
            access_token=api_key,
            token_type="ApiKey"
        )
    
    async def _refresh_token(self, refresh_token: str) -> Optional[AuthToken]:
        """Refresh an expired token."""
        if not self.config.token_url:
            return None
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.token_url, data=data) as response:
                    if response.status != 200:
                        logger.warning(f"Token refresh failed: {response.status}")
                        return None
                    
                    token_data = await response.json()
                    
                    expires_at = None
                    if 'expires_in' in token_data:
                        expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                    
                    return AuthToken(
                        access_token=token_data['access_token'],
                        token_type=token_data.get('token_type', 'Bearer'),
                        expires_at=expires_at,
                        refresh_token=token_data.get('refresh_token', refresh_token),
                        scope=token_data.get('scope')
                    )
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def revoke_token(self, connector_name: str) -> bool:
        """Revoke authentication token."""
        try:
            if connector_name in self.tokens:
                del self.tokens[connector_name]
                logger.info(f"Revoked token for {connector_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Token revocation failed for {connector_name}: {e}")
            return False
    
    def get_auth_headers(self, connector_name: str) -> Dict[str, str]:
        """Get authentication headers for requests."""
        if connector_name not in self.tokens:
            raise ValueError(f"No token available for {connector_name}")
        
        token = self.tokens[connector_name]
        
        if token.is_expired:
            raise ValueError(f"Token expired for {connector_name}")
        
        if token.token_type == "PersonalAccessToken":
            return {"X-Tableau-Auth": token.access_token}


def create_auth_manager(auth_type: AuthType, credentials: Dict[str, Any], **kwargs) -> AuthenticationManager:
    """Factory function to create authentication manager."""
    config = AuthConfig(
        auth_type=auth_type,
        credentials=credentials,
        **kwargs
    )
    return AuthenticationManager(config)
