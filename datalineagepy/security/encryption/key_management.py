"""
Key Management System with HashiCorp Vault Integration
Enterprise-grade key management with automatic rotation and secure storage.
"""

import os
import json
import requests
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging
import threading
import time


@dataclass
class KeyMetadata:
    """Metadata for encryption keys."""
    key_id: str
    version: int
    created_at: datetime
    expires_at: Optional[datetime]
    algorithm: str
    key_size: int
    is_active: bool = True
    rotation_count: int = 0
    last_used: Optional[datetime] = None
    usage_count: int = 0


class VaultClient:
    """
    HashiCorp Vault client for secure key storage.
    
    Features:
    - Vault authentication
    - Key storage and retrieval
    - Secret versioning
    - Audit logging
    """
    
    def __init__(self, vault_url: str, vault_token: Optional[str] = None):
        self.vault_url = vault_url.rstrip('/')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            'X-Vault-Token': self.vault_token,
            'Content-Type': 'application/json'
        })
        self.logger = logging.getLogger(__name__)
    
    def authenticate_with_approle(self, role_id: str, secret_id: str) -> bool:
        """Authenticate with Vault using AppRole."""
        try:
            auth_data = {
                "role_id": role_id,
                "secret_id": secret_id
            }
            
            response = self.session.post(
                f"{self.vault_url}/v1/auth/approle/login",
                json=auth_data
            )
            response.raise_for_status()
            
            auth_response = response.json()
            self.vault_token = auth_response['auth']['client_token']
            self.session.headers['X-Vault-Token'] = self.vault_token
            
            self.logger.info("Successfully authenticated with Vault using AppRole")
            return True
            
        except Exception as e:
            self.logger.error(f"Vault AppRole authentication failed: {str(e)}")
            return False
    
    def store_key(self, path: str, key_data: Dict[str, Any], version: Optional[int] = None) -> bool:
        """Store encryption key in Vault."""
        try:
            # Use KV v2 engine
            vault_path = f"v1/secret/data/{path}"
            
            payload = {
                "data": key_data,
                "options": {}
            }
            
            if version:
                payload["options"]["cas"] = version
            
            response = self.session.post(f"{self.vault_url}/{vault_path}", json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Key stored in Vault at path: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store key in Vault: {str(e)}")
            return False
    
    def retrieve_key(self, path: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve encryption key from Vault."""
        try:
            vault_path = f"v1/secret/data/{path}"
            
            params = {}
            if version:
                params["version"] = version
            
            response = self.session.get(f"{self.vault_url}/{vault_path}", params=params)
            response.raise_for_status()
            
            vault_response = response.json()
            return vault_response['data']['data']
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve key from Vault: {str(e)}")
            return None
    
    def delete_key(self, path: str) -> bool:
        """Delete key from Vault."""
        try:
            vault_path = f"v1/secret/data/{path}"
            response = self.session.delete(f"{self.vault_url}/{vault_path}")
            response.raise_for_status()
            
            self.logger.info(f"Key deleted from Vault at path: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete key from Vault: {str(e)}")
            return False
    
    def list_keys(self, path: str) -> List[str]:
        """List keys at a given path."""
        try:
            vault_path = f"v1/secret/metadata/{path}"
            response = self.session.get(f"{self.vault_url}/{vault_path}?list=true")
            response.raise_for_status()
            
            vault_response = response.json()
            return vault_response['data']['keys']
            
        except Exception as e:
            self.logger.error(f"Failed to list keys from Vault: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check Vault health status."""
        try:
            response = self.session.get(f"{self.vault_url}/v1/sys/health")
            return response.json()
        except Exception as e:
            return {"error": str(e), "healthy": False}


class EnterpriseKeyManager:
    """
    Enterprise key management system with Vault integration.
    
    Features:
    - Automatic key rotation
    - Key versioning and lifecycle management
    - Vault integration for secure storage
    - Compliance and audit logging
    - Performance monitoring
    """
    
    def __init__(self, vault_client: Optional[VaultClient] = None, 
                 rotation_days: int = 90, backup_storage: bool = True):
        self.vault_client = vault_client
        self.rotation_days = rotation_days
        self.backup_storage = backup_storage
        self.logger = logging.getLogger(__name__)
        
        # In-memory key cache for performance
        self.key_cache: Dict[str, KeyMetadata] = {}
        self.key_data_cache: Dict[str, bytes] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Key rotation scheduler
        self.rotation_thread = None
        self.rotation_stop_event = threading.Event()
        
        # Metrics
        self.metrics = {
            "keys_generated": 0,
            "keys_rotated": 0,
            "vault_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Start automatic rotation if enabled
        if self.rotation_days > 0:
            self.start_automatic_rotation()
    
    def generate_key(self, key_id: str, algorithm: str = "AES-256", 
                    key_size: int = 32, expires_in_days: Optional[int] = None) -> bool:
        """
        Generate a new encryption key.
        
        Args:
            key_id: Unique identifier for the key
            algorithm: Encryption algorithm
            key_size: Key size in bytes
            expires_in_days: Optional expiration in days
            
        Returns:
            True if key generated successfully
        """
        try:
            # Generate cryptographically secure random key
            key_bytes = os.urandom(key_size)
            
            # Create key metadata
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(days=expires_in_days) if expires_in_days else None
            
            metadata = KeyMetadata(
                key_id=key_id,
                version=1,
                created_at=created_at,
                expires_at=expires_at,
                algorithm=algorithm,
                key_size=key_size,
                is_active=True
            )
            
            # Store in Vault if available
            if self.vault_client:
                key_data = {
                    "key": base64.b64encode(key_bytes).decode('utf-8'),
                    "metadata": {
                        "key_id": key_id,
                        "version": metadata.version,
                        "created_at": created_at.isoformat(),
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "algorithm": algorithm,
                        "key_size": key_size,
                        "is_active": True
                    }
                }
                
                vault_path = f"datalineage/keys/{key_id}"
                if not self.vault_client.store_key(vault_path, key_data):
                    self.logger.error(f"Failed to store key {key_id} in Vault")
                    return False
                
                self.metrics["vault_operations"] += 1
            
            # Cache the key
            self.key_cache[key_id] = metadata
            self.key_data_cache[key_id] = key_bytes
            
            self.metrics["keys_generated"] += 1
            self.logger.info(f"Generated new key: {key_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate key {key_id}: {str(e)}")
            return False
    
    def get_key(self, key_id: str) -> Optional[Tuple[bytes, KeyMetadata]]:
        """
        Retrieve encryption key and metadata.
        
        Args:
            key_id: Key identifier
            
        Returns:
            Tuple of (key_bytes, metadata) or None if not found
        """
        # Check cache first
        if key_id in self.key_data_cache and key_id in self.key_cache:
            metadata = self.key_cache[key_id]
            
            # Check if cached data is still valid
            if metadata.expires_at is None or datetime.utcnow() < metadata.expires_at:
                # Update usage statistics
                metadata.last_used = datetime.utcnow()
                metadata.usage_count += 1
                self.metrics["cache_hits"] += 1
                
                return self.key_data_cache[key_id], metadata
        
        # Cache miss - retrieve from Vault
        self.metrics["cache_misses"] += 1
        
        if self.vault_client:
            vault_path = f"datalineage/keys/{key_id}"
            key_data = self.vault_client.retrieve_key(vault_path)
            
            if key_data:
                key_bytes = base64.b64decode(key_data["key"])
                metadata_dict = key_data["metadata"]
                
                # Reconstruct metadata
                metadata = KeyMetadata(
                    key_id=metadata_dict["key_id"],
                    version=metadata_dict["version"],
                    created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                    expires_at=datetime.fromisoformat(metadata_dict["expires_at"]) if metadata_dict["expires_at"] else None,
                    algorithm=metadata_dict["algorithm"],
                    key_size=metadata_dict["key_size"],
                    is_active=metadata_dict["is_active"]
                )
                
                # Update cache
                self.key_cache[key_id] = metadata
                self.key_data_cache[key_id] = key_bytes
                
                # Update usage statistics
                metadata.last_used = datetime.utcnow()
                metadata.usage_count += 1
                
                self.metrics["vault_operations"] += 1
                
                return key_bytes, metadata
        
        self.logger.warning(f"Key {key_id} not found")
        return None
    
    def rotate_key(self, key_id: str) -> bool:
        """
        Rotate an existing key.
        
        Args:
            key_id: Key identifier to rotate
            
        Returns:
            True if rotation successful
        """
        try:
            # Get current key metadata
            current_key_data = self.get_key(key_id)
            if not current_key_data:
                self.logger.error(f"Cannot rotate key {key_id}: key not found")
                return False
            
            _, current_metadata = current_key_data
            
            # Generate new key with incremented version
            new_key_bytes = os.urandom(current_metadata.key_size)
            new_version = current_metadata.version + 1
            
            # Create new metadata
            new_metadata = KeyMetadata(
                key_id=key_id,
                version=new_version,
                created_at=datetime.utcnow(),
                expires_at=current_metadata.expires_at,
                algorithm=current_metadata.algorithm,
                key_size=current_metadata.key_size,
                is_active=True,
                rotation_count=current_metadata.rotation_count + 1
            )
            
            # Store new version in Vault
            if self.vault_client:
                key_data = {
                    "key": base64.b64encode(new_key_bytes).decode('utf-8'),
                    "metadata": {
                        "key_id": key_id,
                        "version": new_version,
                        "created_at": new_metadata.created_at.isoformat(),
                        "expires_at": new_metadata.expires_at.isoformat() if new_metadata.expires_at else None,
                        "algorithm": new_metadata.algorithm,
                        "key_size": new_metadata.key_size,
                        "is_active": True,
                        "rotation_count": new_metadata.rotation_count
                    }
                }
                
                vault_path = f"datalineage/keys/{key_id}"
                if not self.vault_client.store_key(vault_path, key_data, version=new_version):
                    self.logger.error(f"Failed to store rotated key {key_id} in Vault")
                    return False
            
            # Update cache
            self.key_cache[key_id] = new_metadata
            self.key_data_cache[key_id] = new_key_bytes
            
            self.metrics["keys_rotated"] += 1
            self.logger.info(f"Rotated key {key_id} to version {new_version}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate key {key_id}: {str(e)}")
            return False
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all managed keys with metadata."""
        keys_info = []
        
        # Get keys from cache
        for key_id, metadata in self.key_cache.items():
            keys_info.append({
                "key_id": key_id,
                "version": metadata.version,
                "algorithm": metadata.algorithm,
                "key_size": metadata.key_size,
                "created_at": metadata.created_at.isoformat(),
                "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                "is_active": metadata.is_active,
                "rotation_count": metadata.rotation_count,
                "last_used": metadata.last_used.isoformat() if metadata.last_used else None,
                "usage_count": metadata.usage_count,
                "days_until_expiry": (metadata.expires_at - datetime.utcnow()).days if metadata.expires_at else None
            })
        
        # Also check Vault for any keys not in cache
        if self.vault_client:
            vault_keys = self.vault_client.list_keys("datalineage/keys")
            for vault_key in vault_keys:
                if vault_key not in self.key_cache:
                    # Load key metadata from Vault
                    key_data = self.vault_client.retrieve_key(f"datalineage/keys/{vault_key}")
                    if key_data and "metadata" in key_data:
                        metadata_dict = key_data["metadata"]
                        keys_info.append({
                            "key_id": vault_key,
                            "version": metadata_dict.get("version", 1),
                            "algorithm": metadata_dict.get("algorithm", "unknown"),
                            "key_size": metadata_dict.get("key_size", 0),
                            "created_at": metadata_dict.get("created_at"),
                            "expires_at": metadata_dict.get("expires_at"),
                            "is_active": metadata_dict.get("is_active", False),
                            "rotation_count": metadata_dict.get("rotation_count", 0),
                            "source": "vault_only"
                        })
        
        return keys_info
    
    def check_key_expiration(self) -> List[str]:
        """Check for keys that are expired or expiring soon."""
        expiring_keys = []
        warning_days = 7  # Warn 7 days before expiration
        
        for key_id, metadata in self.key_cache.items():
            if metadata.expires_at:
                days_until_expiry = (metadata.expires_at - datetime.utcnow()).days
                if days_until_expiry <= warning_days:
                    expiring_keys.append(key_id)
        
        return expiring_keys
    
    def check_rotation_needed(self) -> List[str]:
        """Check for keys that need rotation."""
        keys_needing_rotation = []
        
        for key_id, metadata in self.key_cache.items():
            days_since_creation = (datetime.utcnow() - metadata.created_at).days
            if days_since_creation >= self.rotation_days:
                keys_needing_rotation.append(key_id)
        
        return keys_needing_rotation
    
    def start_automatic_rotation(self):
        """Start automatic key rotation background thread."""
        if self.rotation_thread and self.rotation_thread.is_alive():
            return
        
        self.rotation_thread = threading.Thread(target=self._rotation_worker, daemon=True)
        self.rotation_thread.start()
        self.logger.info("Started automatic key rotation")
    
    def stop_automatic_rotation(self):
        """Stop automatic key rotation."""
        if self.rotation_thread:
            self.rotation_stop_event.set()
            self.rotation_thread.join(timeout=5)
            self.logger.info("Stopped automatic key rotation")
    
    def _rotation_worker(self):
        """Background worker for automatic key rotation."""
        check_interval = 3600  # Check every hour
        
        while not self.rotation_stop_event.wait(check_interval):
            try:
                # Check for keys needing rotation
                keys_to_rotate = self.check_rotation_needed()
                
                for key_id in keys_to_rotate:
                    self.logger.info(f"Auto-rotating key: {key_id}")
                    self.rotate_key(key_id)
                
                # Check for expiring keys
                expiring_keys = self.check_key_expiration()
                for key_id in expiring_keys:
                    self.logger.warning(f"Key {key_id} is expiring soon")
                
            except Exception as e:
                self.logger.error(f"Error in key rotation worker: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get key management metrics."""
        return {
            **self.metrics,
            "total_keys": len(self.key_cache),
            "active_keys": sum(1 for m in self.key_cache.values() if m.is_active),
            "cache_size": len(self.key_data_cache),
            "keys_needing_rotation": len(self.check_rotation_needed()),
            "expiring_keys": len(self.check_key_expiration())
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on key management system."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Check Vault connectivity
            if self.vault_client:
                vault_health = self.vault_client.health_check()
                health_status["checks"]["vault"] = {
                    "status": "healthy" if vault_health.get("sealed") == False else "unhealthy",
                    "details": vault_health
                }
            
            # Check key availability
            active_keys = sum(1 for m in self.key_cache.values() if m.is_active)
            health_status["checks"]["keys"] = {
                "status": "healthy" if active_keys > 0 else "unhealthy",
                "active_keys": active_keys,
                "total_keys": len(self.key_cache)
            }
            
            # Check rotation status
            keys_needing_rotation = len(self.check_rotation_needed())
            health_status["checks"]["rotation"] = {
                "status": "healthy" if keys_needing_rotation < 5 else "warning",
                "keys_needing_rotation": keys_needing_rotation
            }
            
            # Overall status
            unhealthy_checks = [check for check in health_status["checks"].values() 
                             if check["status"] == "unhealthy"]
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status


# Example usage
if __name__ == "__main__":
    # Initialize Vault client
    vault_client = VaultClient("https://vault.company.com:8200")
    
    # Authenticate with AppRole (in production, use proper credentials)
    # vault_client.authenticate_with_approle("role-id", "secret-id")
    
    # Initialize key manager
    key_manager = EnterpriseKeyManager(
        vault_client=vault_client,
        rotation_days=90
    )
    
    # Generate a new key
    key_manager.generate_key("data_encryption_key", "AES-256", 32, expires_in_days=365)
    
    # Retrieve the key
    key_data = key_manager.get_key("data_encryption_key")
    if key_data:
        key_bytes, metadata = key_data
        print(f"Retrieved key: {metadata.key_id} (version {metadata.version})")
    
    # List all keys
    keys = key_manager.list_keys()
    print(f"Total keys: {len(keys)}")
    
    # Check health
    health = key_manager.health_check()
    print(f"Health status: {health['status']}")
    
    # Get metrics
    metrics = key_manager.get_metrics()
    print(f"Metrics: {metrics}")
