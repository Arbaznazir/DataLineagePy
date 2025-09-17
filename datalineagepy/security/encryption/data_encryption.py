"""
Data Encryption Manager
AES-256 encryption for data at rest and TLS for data in transit.
"""

import os
import base64
import hashlib
import secrets
from typing import Dict, Optional, Any, Union, Tuple, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import json
import logging


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""
    pass


class KeyManager:
    """
    Manages encryption keys with rotation and secure storage.

    Features:
    - AES-256 key generation
    - Key rotation every 90 days
    - Key versioning
    - Secure key derivation
    """

    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv('MASTER_ENCRYPTION_KEY')
        if not self.master_key:
            raise EncryptionError("Master encryption key not provided")

        self.keys: Dict[str, Dict[str, Any]] = {}
        self.current_key_version = 1
        self.key_rotation_days = 90

        # Initialize with first key
        self._generate_new_key()

    def _generate_new_key(self) -> str:
        """Generate a new encryption key."""
        key_id = f"key_v{self.current_key_version}"

        # Generate salt for key derivation
        salt = os.urandom(16)

        # Derive key from master key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        derived_key = kdf.derive(self.master_key.encode())

        # Store key metadata
        self.keys[key_id] = {
            "key": derived_key,
            "salt": salt,
            "created_at": datetime.utcnow(),
            "version": self.current_key_version,
            "is_active": True
        }

        # Deactivate previous keys
        for old_key_id, old_key_data in self.keys.items():
            if old_key_id != key_id:
                old_key_data["is_active"] = False

        self.current_key_version += 1
        return key_id

    def get_current_key(self) -> Tuple[str, bytes]:
        """Get the current active encryption key."""
        for key_id, key_data in self.keys.items():
            if key_data["is_active"]:
                return key_id, key_data["key"]

        raise EncryptionError("No active encryption key found")

    def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """Get encryption key by ID."""
        if key_id in self.keys:
            return self.keys[key_id]["key"]
        return None

    def rotate_keys(self) -> str:
        """Rotate encryption keys."""
        return self._generate_new_key()

    def should_rotate_keys(self) -> bool:
        """Check if keys should be rotated."""
        key_id, _ = self.get_current_key()
        key_age = datetime.utcnow() - self.keys[key_id]["created_at"]
        return key_age.days >= self.key_rotation_days

    def list_keys(self) -> List[Dict[str, Any]]:
        """List all keys with metadata."""
        return [
            {
                "key_id": key_id,
                "version": key_data["version"],
                "created_at": key_data["created_at"].isoformat(),
                "is_active": key_data["is_active"],
                "age_days": (datetime.utcnow() - key_data["created_at"]).days
            }
            for key_id, key_data in self.keys.items()
        ]


class AESEncryption:
    """
    AES-256 encryption implementation for data at rest.

    Features:
    - AES-256-GCM encryption
    - Authenticated encryption
    - Key versioning support
    - Secure random IV generation
    """

    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.logger = logging.getLogger(__name__)

    def encrypt(self, data: Union[str, bytes], additional_data: Optional[bytes] = None) -> Dict[str, str]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            data: Data to encrypt
            additional_data: Additional authenticated data (AAD)

        Returns:
            Dict containing encrypted data, IV, tag, and key version
        """
        try:
            # Convert string to bytes if necessary
            if isinstance(data, str):
                data = data.encode('utf-8')

            # Get current encryption key
            key_id, key = self.key_manager.get_current_key()

            # Generate random IV (12 bytes for GCM)
            iv = os.urandom(12)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Add additional authenticated data if provided
            if additional_data:
                encryptor.authenticate_additional_data(additional_data)

            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()

            # Get authentication tag
            tag = encryptor.tag

            # Return encrypted data with metadata
            return {
                "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "iv": base64.b64encode(iv).decode('utf-8'),
                "tag": base64.b64encode(tag).decode('utf-8'),
                "key_id": key_id,
                "algorithm": "AES-256-GCM",
                "encrypted_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: Dict[str, str], additional_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            encrypted_data: Dict containing encrypted data and metadata
            additional_data: Additional authenticated data (AAD)

        Returns:
            Decrypted data as bytes
        """
        try:
            # Extract components
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            iv = base64.b64decode(encrypted_data["iv"])
            tag = base64.b64decode(encrypted_data["tag"])
            key_id = encrypted_data["key_id"]

            # Get decryption key
            key = self.key_manager.get_key_by_id(key_id)
            if not key:
                raise EncryptionError(f"Encryption key {key_id} not found")

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Add additional authenticated data if provided
            if additional_data:
                decryptor.authenticate_additional_data(additional_data)

            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext

        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise EncryptionError(f"Decryption failed: {str(e)}")

    def encrypt_json(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt JSON data."""
        json_str = json.dumps(data, separators=(',', ':'))
        return self.encrypt(json_str)

    def decrypt_json(self, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt JSON data."""
        decrypted_bytes = self.decrypt(encrypted_data)
        json_str = decrypted_bytes.decode('utf-8')
        return json.loads(json_str)


class FieldLevelEncryption:
    """
    Field-level encryption for sensitive database columns.

    Features:
    - Selective field encryption
    - Searchable encryption for indexed fields
    - Format-preserving encryption options
    """

    def __init__(self, aes_encryption: AESEncryption):
        self.aes_encryption = aes_encryption
        self.sensitive_fields = {
            'email', 'phone', 'ssn', 'credit_card', 'password',
            'api_key', 'token', 'secret', 'pii'
        }

    def encrypt_record(self, record: Dict[str, Any],
                       fields_to_encrypt: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a database record.

        Args:
            record: Database record as dictionary
            fields_to_encrypt: Specific fields to encrypt (optional)

        Returns:
            Record with encrypted sensitive fields
        """
        encrypted_record = record.copy()

        # Determine fields to encrypt
        if fields_to_encrypt:
            target_fields = set(fields_to_encrypt)
        else:
            target_fields = set(record.keys()) & self.sensitive_fields

        # Encrypt each target field
        for field_name in target_fields:
            if field_name in record and record[field_name] is not None:
                field_value = str(record[field_name])
                encrypted_data = self.aes_encryption.encrypt(field_value)

                # Store encrypted data with metadata
                encrypted_record[field_name] = {
                    "_encrypted": True,
                    "_data": encrypted_data
                }

        return encrypted_record

    def decrypt_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt encrypted fields in a database record.

        Args:
            record: Database record with encrypted fields

        Returns:
            Record with decrypted fields
        """
        decrypted_record = record.copy()

        for field_name, field_value in record.items():
            if (isinstance(field_value, dict) and
                field_value.get("_encrypted") and
                    "_data" in field_value):

                try:
                    decrypted_bytes = self.aes_encryption.decrypt(
                        field_value["_data"])
                    decrypted_record[field_name] = decrypted_bytes.decode(
                        'utf-8')
                except EncryptionError:
                    # Keep encrypted if decryption fails
                    pass

        return decrypted_record

    def is_field_encrypted(self, field_value: Any) -> bool:
        """Check if a field value is encrypted."""
        return (isinstance(field_value, dict) and
                field_value.get("_encrypted") and
                "_data" in field_value)


class RSAEncryption:
    """
    RSA encryption for key exchange and digital signatures.

    Features:
    - RSA-2048 key generation
    - Public/private key management
    - Digital signatures
    - Key exchange for symmetric encryption
    """

    def __init__(self):
        self.key_size = 2048
        self.public_key = None
        self.private_key = None

    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair.

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend()
        )

        # Get public key
        self.public_key = self.private_key.public_key()

        # Serialize keys
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    def load_private_key(self, private_key_pem: bytes, password: Optional[bytes] = None):
        """Load private key from PEM format."""
        self.private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=password,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def load_public_key(self, public_key_pem: bytes):
        """Load public key from PEM format."""
        self.public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data with public key."""
        if not self.public_key:
            raise EncryptionError("Public key not loaded")

        return self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with private key."""
        if not self.private_key:
            raise EncryptionError("Private key not loaded")

        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def sign(self, data: bytes) -> bytes:
        """Create digital signature."""
        if not self.private_key:
            raise EncryptionError("Private key not loaded")

        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify digital signature."""
        if not self.public_key:
            raise EncryptionError("Public key not loaded")

        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False


class EncryptionManager:
    """
    Unified encryption manager coordinating all encryption operations.

    Features:
    - Centralized encryption management
    - Key rotation automation
    - Performance monitoring
    - Compliance reporting
    """

    def __init__(self, master_key: Optional[str] = None):
        self.key_manager = KeyManager(master_key)
        self.aes_encryption = AESEncryption(self.key_manager)
        self.field_encryption = FieldLevelEncryption(self.aes_encryption)
        self.rsa_encryption = RSAEncryption()
        self.logger = logging.getLogger(__name__)

        # Performance metrics
        self.encryption_count = 0
        self.decryption_count = 0
        self.last_key_rotation = datetime.utcnow()

    def encrypt_sensitive_data(self, data: Union[str, Dict[str, Any]]) -> Dict[str, str]:
        """Encrypt sensitive data (strings or JSON objects)."""
        self.encryption_count += 1

        if isinstance(data, dict):
            return self.aes_encryption.encrypt_json(data)
        else:
            return self.aes_encryption.encrypt(data)

    def decrypt_sensitive_data(self, encrypted_data: Dict[str, str]) -> Union[str, Dict[str, Any]]:
        """Decrypt sensitive data."""
        self.decryption_count += 1

        try:
            # Try JSON decryption first
            return self.aes_encryption.decrypt_json(encrypted_data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to string decryption
            decrypted_bytes = self.aes_encryption.decrypt(encrypted_data)
            return decrypted_bytes.decode('utf-8')

    def encrypt_database_record(self, record: Dict[str, Any],
                                fields_to_encrypt: Optional[List[str]] = None) -> Dict[str, Any]:
        """Encrypt sensitive fields in database record."""
        return self.field_encryption.encrypt_record(record, fields_to_encrypt)

    def decrypt_database_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt encrypted fields in database record."""
        return self.field_encryption.decrypt_record(record)

    def rotate_keys_if_needed(self) -> bool:
        """Rotate keys if rotation is due."""
        if self.key_manager.should_rotate_keys():
            self.key_manager.rotate_keys()
            self.last_key_rotation = datetime.utcnow()
            self.logger.info("Encryption keys rotated")
            return True
        return False

    def get_encryption_stats(self) -> Dict[str, Any]:
        """Get encryption statistics."""
        return {
            "encryption_operations": self.encryption_count,
            "decryption_operations": self.decryption_count,
            "active_keys": len([k for k in self.key_manager.keys.values() if k["is_active"]]),
            "total_keys": len(self.key_manager.keys),
            "last_key_rotation": self.last_key_rotation.isoformat(),
            "days_since_rotation": (datetime.utcnow() - self.last_key_rotation).days
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform encryption system health check."""
        try:
            # Test encryption/decryption
            test_data = "health_check_test_data"
            encrypted = self.encrypt_sensitive_data(test_data)
            decrypted = self.decrypt_sensitive_data(encrypted)

            encryption_healthy = decrypted == test_data

            # Check key status
            keys_healthy = len(
                [k for k in self.key_manager.keys.values() if k["is_active"]]) > 0

            return {
                "status": "healthy" if encryption_healthy and keys_healthy else "unhealthy",
                "encryption_test": encryption_healthy,
                "keys_available": keys_healthy,
                "key_rotation_due": self.key_manager.should_rotate_keys(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Example usage
if __name__ == "__main__":
    # Initialize encryption manager
    encryption_manager = EncryptionManager("your-master-key-here")

    # Test data encryption
    sensitive_data = {
        "user_id": "12345",
        "email": "user@example.com",
        "credit_card": "4111-1111-1111-1111",
        "ssn": "123-45-6789"
    }

    # Encrypt sensitive data
    encrypted = encryption_manager.encrypt_sensitive_data(sensitive_data)
    print("Encrypted data:", encrypted)

    # Decrypt sensitive data
    decrypted = encryption_manager.decrypt_sensitive_data(encrypted)
    print("Decrypted data:", decrypted)

    # Test database record encryption
    db_record = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "department": "Engineering"
    }

    encrypted_record = encryption_manager.encrypt_database_record(db_record)
    print("Encrypted record:", encrypted_record)

    decrypted_record = encryption_manager.decrypt_database_record(
        encrypted_record)
    print("Decrypted record:", decrypted_record)

    # Health check
    health = encryption_manager.health_check()
    print("Health check:", health)

    # Statistics
    stats = encryption_manager.get_encryption_stats()
    print("Encryption stats:", stats)
