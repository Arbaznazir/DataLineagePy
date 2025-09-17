"""
DataLineagePy Security Module
Enterprise-grade security framework for data lineage applications.

This module provides comprehensive security features including:
- Multi-factor authentication (MFA)
- JWT token management
- Single Sign-On (SSO) integration
- Role-based access control (RBAC)
- Policy-based authorization
- Data encryption (AES-256, RSA)
- Key management with HashiCorp Vault
- Comprehensive audit logging
- API security middleware
- Compliance framework support (GDPR, SOX, HIPAA)
"""

from .config.security_config import (
    SecurityConfiguration,
    SecurityConfigManager,
    get_security_config,
    reload_security_config,
    SecurityLevel,
    AuthenticationMethod
)

from .authentication.mfa_manager import MFAManager
from .authentication.jwt_manager import JWTManager
from .authentication.sso_integration import (
    SSOManager,
    SAMLProvider,
    OAuth2Provider,
    LDAPProvider
)

from .authorization.rbac_engine import RBACEngine
from .authorization.policy_engine import PolicyEngine

from .encryption.data_encryption import EncryptionManager
from .encryption.key_management import (
    EnterpriseKeyManager,
    VaultClient,
    KeyMetadata
)

from .audit.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    ComplianceFramework
)

from .api.security_middleware import (
    SecurityMiddleware,
    SecurityConfig as APISecurityConfig,
    RateLimitRule,
    require_security
)

__version__ = "1.0.0"
__author__ = "DataLineagePy Security Team"

# Security module metadata
SECURITY_FEATURES = [
    "Multi-Factor Authentication (MFA)",
    "JWT Token Management",
    "Single Sign-On (SSO)",
    "Role-Based Access Control (RBAC)",
    "Policy-Based Authorization",
    "AES-256 Data Encryption",
    "RSA Key Exchange",
    "HashiCorp Vault Integration",
    "Comprehensive Audit Logging",
    "API Security Middleware",
    "Rate Limiting",
    "Input Validation",
    "CORS Protection",
    "Compliance Framework Support"
]

SUPPORTED_COMPLIANCE_FRAMEWORKS = [
    "GDPR (General Data Protection Regulation)",
    "SOX (Sarbanes-Oxley Act)",
    "HIPAA (Health Insurance Portability and Accountability Act)",
    "PCI DSS (Payment Card Industry Data Security Standard)",
    "ISO 27001",
    "NIST Cybersecurity Framework"
]

def get_security_info():
    """Get information about the security module."""
    return {
        "version": __version__,
        "features": SECURITY_FEATURES,
        "compliance_frameworks": SUPPORTED_COMPLIANCE_FRAMEWORKS,
        "components": {
            "authentication": [
                "MFA with TOTP",
                "JWT tokens with refresh",
                "SSO (SAML, OAuth2, LDAP)"
            ],
            "authorization": [
                "RBAC with role hierarchy",
                "Policy engine with ABAC",
                "Permission caching"
            ],
            "encryption": [
                "AES-256-GCM encryption",
                "RSA key exchange",
                "Key rotation and management",
                "HashiCorp Vault integration"
            ],
            "audit": [
                "Comprehensive event logging",
                "Compliance reporting",
                "Integrity verification",
                "Retention management"
            ],
            "api_security": [
                "Rate limiting",
                "Input validation",
                "CORS protection",
                "Security headers",
                "IP filtering"
            ]
        }
    }

# Quick setup function for common configurations
def setup_enterprise_security(security_level: str = "production") -> dict:
    """
    Quick setup for enterprise security configuration.
    
    Args:
        security_level: Security level (development, staging, production)
        
    Returns:
        Dictionary with initialized security components
    """
    # Load configuration
    config = get_security_config()
    
    # Initialize core components
    components = {}
    
    try:
        # Authentication
        components['mfa'] = MFAManager()
        components['jwt'] = JWTManager(
            secret_key=config.jwt_config.secret_key,
            algorithm=config.jwt_config.algorithm
        )
        components['sso'] = SSOManager()
        
        # Authorization
        components['rbac'] = RBACEngine()
        components['policy'] = PolicyEngine()
        
        # Encryption
        components['encryption'] = EncryptionManager()
        
        # Audit
        components['audit'] = AuditLogger()
        
        # API Security
        api_config = APISecurityConfig(
            default_rate_limit=RateLimitRule(
                requests_per_minute=config.api_security_config.default_rate_limit_per_minute,
                requests_per_hour=config.api_security_config.default_rate_limit_per_hour,
                requests_per_day=config.api_security_config.default_rate_limit_per_hour * 24
            ),
            allowed_origins=config.api_security_config.allowed_origins,
            max_request_size=config.api_security_config.max_request_size_mb * 1024 * 1024
        )
        components['api_security'] = SecurityMiddleware(api_config)
        
        return {
            "status": "success",
            "components": components,
            "config": config,
            "security_level": security_level
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "components": components
        }

# Export all main classes and functions
__all__ = [
    # Configuration
    'SecurityConfiguration',
    'SecurityConfigManager',
    'get_security_config',
    'reload_security_config',
    'SecurityLevel',
    'AuthenticationMethod',
    
    # Authentication
    'MFAManager',
    'JWTManager',
    'SSOManager',
    'SAMLProvider',
    'OAuth2Provider',
    'LDAPProvider',
    
    # Authorization
    'RBACEngine',
    'PolicyEngine',
    
    # Encryption
    'EncryptionManager',
    'EnterpriseKeyManager',
    'VaultClient',
    'KeyMetadata',
    
    # Audit
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditSeverity',
    'ComplianceFramework',
    
    # API Security
    'SecurityMiddleware',
    'APISecurityConfig',
    'RateLimitRule',
    'require_security',
    
    # Utilities
    'get_security_info',
    'setup_enterprise_security'
]
