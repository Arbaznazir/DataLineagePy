"""
JWT Token Management System
Handles JWT token generation, validation, and revocation for enterprise authentication.
"""

import jwt
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
import json
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64


class InvalidTokenError(Exception):
    """Raised when token validation fails."""
    pass


class JWTManager:
    """
    JWT Token Manager with enterprise features.
    
    Features:
    - Access and refresh token generation
    - Token validation and expiration
    - Token revocation and blacklisting
    - Role and permission embedding
    - Secure key management
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", redis_client=None):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expiry = timedelta(hours=1)  # Short-lived access tokens
        self.refresh_token_expiry = timedelta(days=30)  # Long-lived refresh tokens
        self.redis_client = redis_client or self._create_redis_client()
        
        # Token blacklist key prefix
        self.blacklist_prefix = "jwt_blacklist:"
        self.refresh_prefix = "refresh_token:"
    
    def _create_redis_client(self):
        """Create Redis client for token management."""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
        except Exception:
            # Fallback to in-memory storage (not recommended for production)
            return None
    
    def generate_token_pair(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate access and refresh token pair.
        
        Args:
            user_data: User information including id, email, roles, permissions
            
        Returns:
            Dict containing access_token and refresh_token
        """
        # Generate unique token IDs
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        current_time = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "roles": user_data.get("roles", []),
            "permissions": user_data.get("permissions", []),
            "token_type": "access",
            "exp": current_time + self.access_token_expiry,
            "iat": current_time,
            "jti": access_jti,
            "refresh_jti": refresh_jti  # Link to refresh token
        }
        
        # Refresh token payload (minimal data)
        refresh_payload = {
            "user_id": user_data["id"],
            "token_type": "refresh",
            "exp": current_time + self.refresh_token_expiry,
            "iat": current_time,
            "jti": refresh_jti,
            "access_jti": access_jti  # Link to access token
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token metadata in Redis
        if self.redis_client:
            refresh_data = {
                "user_id": user_data["id"],
                "created_at": current_time.isoformat(),
                "access_jti": access_jti
            }
            self.redis_client.setex(
                f"{self.refresh_prefix}{refresh_jti}",
                int(self.refresh_token_expiry.total_seconds()),
                json.dumps(refresh_data)
            )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(self.access_token_expiry.total_seconds())
        }
    
    def validate_access_token(self, token: str) -> Dict[str, Any]:
        """
        Validate access token and return payload.
        
        Args:
            token: JWT access token
            
        Returns:
            Token payload if valid
            
        Raises:
            InvalidTokenError: If token is invalid, expired, or blacklisted
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("token_type") != "access":
                raise InvalidTokenError("Invalid token type")
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(payload["jti"]):
                raise InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token pair
            
        Raises:
            InvalidTokenError: If refresh token is invalid or expired
        """
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("token_type") != "refresh":
                raise InvalidTokenError("Invalid token type")
            
            # Check if refresh token exists in Redis
            refresh_jti = payload["jti"]
            if self.redis_client:
                refresh_data = self.redis_client.get(f"{self.refresh_prefix}{refresh_jti}")
                if not refresh_data:
                    raise InvalidTokenError("Refresh token not found or expired")
            
            # Get user data (in real implementation, fetch from database)
            user_data = {
                "id": payload["user_id"],
                "email": "user@example.com",  # Fetch from DB
                "roles": ["user"],  # Fetch from DB
                "permissions": ["read"]  # Fetch from DB
            }
            
            # Revoke old access token
            if self.redis_client:
                old_refresh_data = json.loads(refresh_data)
                old_access_jti = old_refresh_data.get("access_jti")
                if old_access_jti:
                    self.blacklist_token(old_access_jti)
            
            # Generate new token pair
            return self.generate_token_pair(user_data)
            
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (add to blacklist).
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successfully revoked
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jti = payload["jti"]
            
            # Add to blacklist
            self.blacklist_token(jti)
            
            # If it's a refresh token, remove from Redis
            if payload.get("token_type") == "refresh" and self.redis_client:
                self.redis_client.delete(f"{self.refresh_prefix}{jti}")
            
            return True
            
        except jwt.InvalidTokenError:
            return False
    
    def blacklist_token(self, jti: str) -> None:
        """Add token JTI to blacklist."""
        if self.redis_client:
            # Blacklist for remaining token lifetime
            self.redis_client.setex(
                f"{self.blacklist_prefix}{jti}",
                int(self.access_token_expiry.total_seconds()),
                "revoked"
            )
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token JTI is blacklisted."""
        if self.redis_client:
            return self.redis_client.exists(f"{self.blacklist_prefix}{jti}")
        return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens revoked
        """
        if not self.redis_client:
            return 0
        
        revoked_count = 0
        
        # Find all refresh tokens for user
        pattern = f"{self.refresh_prefix}*"
        for key in self.redis_client.scan_iter(match=pattern):
            refresh_data = self.redis_client.get(key)
            if refresh_data:
                data = json.loads(refresh_data)
                if data.get("user_id") == user_id:
                    # Extract JTI from key
                    jti = key.replace(self.refresh_prefix, "")
                    self.blacklist_token(jti)
                    
                    # Also blacklist associated access token
                    access_jti = data.get("access_jti")
                    if access_jti:
                        self.blacklist_token(access_jti)
                    
                    # Remove refresh token
                    self.redis_client.delete(key)
                    revoked_count += 1
        
        return revoked_count
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get information about a token without validating expiration.
        
        Args:
            token: JWT token
            
        Returns:
            Token information
        """
        try:
            # Decode without verification for info only
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "token_type": payload.get("token_type"),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "jti": payload.get("jti"),
                "is_expired": datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0))
            }
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from blacklist and refresh token storage.
        
        Returns:
            Number of tokens cleaned up
        """
        if not self.redis_client:
            return 0
        
        cleaned_count = 0
        
        # Redis automatically expires keys, but we can manually clean up if needed
        # This is mainly for monitoring purposes
        
        return cleaned_count


# Token validation decorator
def require_valid_token(jwt_manager: JWTManager):
    """Decorator to require valid JWT token for API endpoints."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract token from request headers
            # This would be implemented based on your web framework
            token = "dummy_token"  # Extract from Authorization header
            
            try:
                payload = jwt_manager.validate_access_token(token)
                # Add user info to request context
                kwargs['user'] = payload
                return func(*args, **kwargs)
            except InvalidTokenError as e:
                return {"error": str(e)}, 401
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize JWT manager
    jwt_manager = JWTManager("your-secret-key-here")
    
    # User data
    user_data = {
        "id": "user123",
        "email": "user@example.com",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete"]
    }
    
    # Generate token pair
    tokens = jwt_manager.generate_token_pair(user_data)
    print("Access Token:", tokens["access_token"])
    print("Refresh Token:", tokens["refresh_token"])
    
    # Validate access token
    try:
        payload = jwt_manager.validate_access_token(tokens["access_token"])
        print("Token is valid:", payload)
    except InvalidTokenError as e:
        print("Token validation failed:", e)
    
    # Get token info
    info = jwt_manager.get_token_info(tokens["access_token"])
    print("Token info:", info)
