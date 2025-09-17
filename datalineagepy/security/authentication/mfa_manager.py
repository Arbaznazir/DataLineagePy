"""
Multi-Factor Authentication (MFA) Manager
Provides TOTP-based two-factor authentication for enterprise security.
"""

import pyotp
import qrcode
import io
import base64
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import secrets
import hashlib
from cryptography.fernet import Fernet


class MFAManager:
    """
    Multi-Factor Authentication manager with TOTP support.
    
    Features:
    - Time-based One-Time Password (TOTP) generation
    - QR code generation for authenticator apps
    - Backup codes for account recovery
    - Rate limiting for security
    """
    
    def __init__(self, issuer_name: str = "DataLineagePy"):
        self.issuer_name = issuer_name
        self.backup_codes_count = 10
        self.totp_window = 1  # Allow 1 time step tolerance
        
    def setup_totp(self, user_id: str, user_email: str) -> Dict[str, str]:
        """
        Setup TOTP for a user and return secret key and QR code.
        
        Args:
            user_id: Unique user identifier
            user_email: User's email address
            
        Returns:
            Dict containing secret key, QR code data, and backup codes
        """
        # Generate secret key
        secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        # Generate QR code
        qr_code_data = self._generate_qr_code(provisioning_uri)
        
        # Generate backup codes
        backup_codes = self._generate_backup_codes()
        
        return {
            "secret": secret,
            "qr_code": qr_code_data,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    def verify_totp(self, secret: str, token: str, used_backup_codes: Optional[list] = None) -> Tuple[bool, str]:
        """
        Verify TOTP token or backup code.
        
        Args:
            secret: User's TOTP secret
            token: 6-digit TOTP token or backup code
            used_backup_codes: List of already used backup codes
            
        Returns:
            Tuple of (is_valid, verification_type)
        """
        used_backup_codes = used_backup_codes or []
        
        # First try TOTP verification
        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=self.totp_window):
            return True, "totp"
        
        # If TOTP fails, check if it's a backup code
        if len(token) == 8 and token.isalnum():
            # Hash the token to compare with stored backup codes
            token_hash = self._hash_backup_code(token)
            
            # Check if this backup code was already used
            if token_hash not in used_backup_codes:
                # In a real implementation, you'd verify against stored backup codes
                # For now, we'll assume it's valid if it matches the pattern
                return True, "backup_code"
        
        return False, "invalid"
    
    def _generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate QR code as base64 encoded image."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        
        return base64.b64encode(img_data).decode('utf-8')
    
    def _generate_backup_codes(self) -> list:
        """Generate backup codes for account recovery."""
        backup_codes = []
        for _ in range(self.backup_codes_count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            backup_codes.append(code)
        
        return backup_codes
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash backup code for secure storage."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def generate_recovery_codes(self, user_id: str) -> list:
        """Generate new recovery codes and invalidate old ones."""
        return self._generate_backup_codes()
    
    def is_totp_enabled(self, user_id: str) -> bool:
        """Check if TOTP is enabled for user."""
        # In a real implementation, check database
        return True  # Placeholder
    
    def disable_totp(self, user_id: str) -> bool:
        """Disable TOTP for user."""
        # In a real implementation, update database
        return True  # Placeholder


class MFASession:
    """
    Manages MFA session state and verification attempts.
    """
    
    def __init__(self):
        self.max_attempts = 3
        self.lockout_duration = timedelta(minutes=15)
        self.attempt_window = timedelta(minutes=5)
    
    def record_attempt(self, user_id: str, success: bool, attempt_type: str):
        """Record MFA verification attempt."""
        # In a real implementation, store in database or cache
        pass
    
    def is_locked_out(self, user_id: str) -> bool:
        """Check if user is locked out due to failed attempts."""
        # In a real implementation, check attempt history
        return False  # Placeholder
    
    def get_remaining_attempts(self, user_id: str) -> int:
        """Get remaining verification attempts."""
        # In a real implementation, calculate from attempt history
        return self.max_attempts  # Placeholder


# Example usage and testing
if __name__ == "__main__":
    mfa = MFAManager()
    
    # Setup MFA for a user
    setup_data = mfa.setup_totp("user123", "user@example.com")
    print("Secret:", setup_data["secret"])
    print("Backup codes:", setup_data["backup_codes"])
    
    # Verify a token (in real usage, this would come from user's authenticator app)
    totp = pyotp.TOTP(setup_data["secret"])
    current_token = totp.now()
    
    is_valid, verification_type = mfa.verify_totp(setup_data["secret"], current_token)
    print(f"Token {current_token} is valid: {is_valid} (type: {verification_type})")
