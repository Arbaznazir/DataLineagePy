"""
Encryption Module
Data encryption, key management, and HashiCorp Vault integration.
"""

from .data_encryption import EncryptionManager
from .key_management import EnterpriseKeyManager, VaultClient, KeyMetadata

__all__ = [
    'EncryptionManager',
    'EnterpriseKeyManager',
    'VaultClient',
    'KeyMetadata'
]
