"""
Security Configuration Management
Centralized security configuration with environment-based settings and validation.
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import logging
from cryptography.fernet import Fernet
import base64


class SecurityLevel(Enum):
    """Security levels for different environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AuthenticationMethod(Enum):
    """Supported authentication methods."""
    JWT = "jwt"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"
    MFA = "mfa"


@dataclass
class JWTConfig:
    """JWT configuration."""
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "DataLineagePy"
    audience: str = "datalineage-users"


@dataclass
class MFAConfig:
    """Multi-Factor Authentication configuration."""
    enabled: bool = True
    issuer_name: str = "DataLineagePy"
    backup_codes_count: int = 10
    totp_window: int = 1
    rate_limit_attempts: int = 5
    rate_limit_window_minutes: int = 15


@dataclass
class SSOConfig:
    """Single Sign-On configuration."""
    enabled: bool = False
    default_provider: str = ""
    saml_settings: Dict[str, Any] = field(default_factory=dict)
    oauth2_providers: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ldap_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RBACConfig:
    """Role-Based Access Control configuration."""
    enabled: bool = True
    default_role: str = "viewer"
    role_hierarchy_enabled: bool = True
    permission_caching_ttl_minutes: int = 60
    max_roles_per_user: int = 10


@dataclass
class EncryptionConfig:
    """Encryption configuration."""
    algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    master_key_env_var: str = "MASTER_ENCRYPTION_KEY"
    field_encryption_enabled: bool = True
    backup_encryption_enabled: bool = True


@dataclass
class AuditConfig:
    """Audit logging configuration."""
    enabled: bool = True
    log_level: str = "INFO"
    storage_backend: str = "file"  # file, database, elasticsearch
    retention_days: int = 2555  # 7 years
    async_processing: bool = True
    queue_size: int = 10000
    log_directory: str = "audit_logs"
    max_file_size_mb: int = 100
    max_files: int = 1000


@dataclass
class APISecurityConfig:
    """API security configuration."""
    rate_limiting_enabled: bool = True
    default_rate_limit_per_minute: int = 60
    default_rate_limit_per_hour: int = 1000
    cors_enabled: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size_mb: int = 10
    input_validation_enabled: bool = True
    security_headers_enabled: bool = True


@dataclass
class ComplianceConfig:
    """Compliance framework configuration."""
    gdpr_enabled: bool = True
    sox_enabled: bool = False
    hipaa_enabled: bool = False
    pci_dss_enabled: bool = False
    data_retention_days: int = 2555
    right_to_be_forgotten_enabled: bool = True
    data_portability_enabled: bool = True


@dataclass
class SecurityConfiguration:
    """Main security configuration class."""
    # Environment
    security_level: SecurityLevel = SecurityLevel.DEVELOPMENT
    debug_mode: bool = False
    
    # Authentication
    authentication_methods: List[AuthenticationMethod] = field(
        default_factory=lambda: [AuthenticationMethod.JWT]
    )
    jwt_config: JWTConfig = field(default_factory=JWTConfig)
    mfa_config: MFAConfig = field(default_factory=MFAConfig)
    sso_config: SSOConfig = field(default_factory=SSOConfig)
    
    # Authorization
    rbac_config: RBACConfig = field(default_factory=RBACConfig)
    
    # Encryption
    encryption_config: EncryptionConfig = field(default_factory=EncryptionConfig)
    
    # Audit
    audit_config: AuditConfig = field(default_factory=AuditConfig)
    
    # API Security
    api_security_config: APISecurityConfig = field(default_factory=APISecurityConfig)
    
    # Compliance
    compliance_config: ComplianceConfig = field(default_factory=ComplianceConfig)
    
    # Redis (for caching and session management)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Database
    database_encryption_enabled: bool = True
    database_ssl_enabled: bool = True
    
    # Monitoring
    security_monitoring_enabled: bool = True
    alert_webhook_url: str = ""
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        self._validate_configuration()
        self._apply_security_level_defaults()
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        errors = []
        
        # JWT validation
        if AuthenticationMethod.JWT in self.authentication_methods:
            if not self.jwt_config.secret_key and not os.getenv('JWT_SECRET_KEY'):
                errors.append("JWT secret key must be configured")
        
        # Encryption validation
        if not os.getenv(self.encryption_config.master_key_env_var):
            errors.append(f"Master encryption key environment variable {self.encryption_config.master_key_env_var} not set")
        
        # Production security checks
        if self.security_level == SecurityLevel.PRODUCTION:
            if self.debug_mode:
                errors.append("Debug mode must be disabled in production")
            
            if "*" in self.api_security_config.allowed_origins:
                errors.append("Wildcard CORS origins not allowed in production")
            
            if not self.audit_config.enabled:
                errors.append("Audit logging must be enabled in production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _apply_security_level_defaults(self):
        """Apply security level-specific defaults."""
        if self.security_level == SecurityLevel.PRODUCTION:
            # Production hardening
            self.debug_mode = False
            self.mfa_config.enabled = True
            self.audit_config.enabled = True
            self.database_encryption_enabled = True
            self.database_ssl_enabled = True
            self.api_security_config.rate_limiting_enabled = True
            self.api_security_config.input_validation_enabled = True
            self.api_security_config.security_headers_enabled = True
            
        elif self.security_level == SecurityLevel.STAGING:
            # Staging configuration
            self.debug_mode = False
            self.audit_config.enabled = True
            
        elif self.security_level == SecurityLevel.DEVELOPMENT:
            # Development configuration (more permissive)
            self.mfa_config.enabled = False
            self.api_security_config.rate_limiting_enabled = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        config_dict = asdict(self)
        
        # Convert enums to strings
        config_dict['security_level'] = self.security_level.value
        config_dict['authentication_methods'] = [method.value for method in self.authentication_methods]
        
        return config_dict
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False)


class SecurityConfigManager:
    """
    Security configuration manager with environment-based loading and encryption.
    
    Features:
    - Environment-based configuration loading
    - Configuration encryption for sensitive settings
    - Configuration validation
    - Hot reloading
    - Configuration versioning
    """
    
    def __init__(self, config_file: Optional[str] = None, 
                 environment: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.logger = logging.getLogger(__name__)
        
        # Configuration encryption key
        self.encryption_key = self._get_or_create_config_encryption_key()
        
        # Load configuration
        self.config = self._load_configuration()
    
    def _get_default_config_file(self) -> str:
        """Get default configuration file path."""
        config_dir = Path.home() / ".datalineagepy" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / "security.yaml")
    
    def _get_or_create_config_encryption_key(self) -> bytes:
        """Get or create configuration encryption key."""
        key_file = Path.home() / ".datalineagepy" / "config_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions
            key_file.chmod(0o600)
            
            return key
    
    def _encrypt_sensitive_value(self, value: str) -> str:
        """Encrypt sensitive configuration value."""
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_sensitive_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value."""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt configuration value: {str(e)}")
            return ""
    
    def _load_configuration(self) -> SecurityConfiguration:
        """Load configuration from file and environment."""
        config_data = {}
        
        # Load from file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                # Get environment-specific config
                if self.environment in file_config:
                    config_data = file_config[self.environment]
                else:
                    config_data = file_config
                    
            except Exception as e:
                self.logger.error(f"Failed to load configuration file: {str(e)}")
        
        # Override with environment variables
        env_overrides = self._load_from_environment()
        config_data.update(env_overrides)
        
        # Decrypt sensitive values
        config_data = self._decrypt_config_values(config_data)
        
        # Create configuration object
        return self._create_config_from_dict(config_data)
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Environment mapping
        env_mappings = {
            'SECURITY_LEVEL': 'security_level',
            'DEBUG_MODE': 'debug_mode',
            'JWT_SECRET_KEY': 'jwt_config.secret_key',
            'JWT_ALGORITHM': 'jwt_config.algorithm',
            'JWT_ACCESS_TOKEN_EXPIRE_MINUTES': 'jwt_config.access_token_expire_minutes',
            'MFA_ENABLED': 'mfa_config.enabled',
            'AUDIT_ENABLED': 'audit_config.enabled',
            'AUDIT_LOG_LEVEL': 'audit_config.log_level',
            'REDIS_HOST': 'redis_host',
            'REDIS_PORT': 'redis_port',
            'REDIS_PASSWORD': 'redis_password',
            'RATE_LIMIT_ENABLED': 'api_security_config.rate_limiting_enabled',
            'CORS_ALLOWED_ORIGINS': 'api_security_config.allowed_origins',
            'GDPR_ENABLED': 'compliance_config.gdpr_enabled',
            'SOX_ENABLED': 'compliance_config.sox_enabled',
            'HIPAA_ENABLED': 'compliance_config.hipaa_enabled'
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif ',' in value:  # List values
                    value = [item.strip() for item in value.split(',')]
                
                # Set nested configuration
                self._set_nested_config(env_config, config_path, value)
        
        return env_config
    
    def _set_nested_config(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested configuration value using dot notation."""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _decrypt_config_values(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt encrypted configuration values."""
        # Define which fields should be decrypted
        encrypted_fields = [
            'jwt_config.secret_key',
            'redis_password',
            'database_password'
        ]
        
        for field_path in encrypted_fields:
            value = self._get_nested_value(config_data, field_path)
            if value and isinstance(value, str) and value.startswith('encrypted:'):
                encrypted_value = value[10:]  # Remove 'encrypted:' prefix
                decrypted_value = self._decrypt_sensitive_value(encrypted_value)
                self._set_nested_config(config_data, field_path, decrypted_value)
        
        return config_data
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> SecurityConfiguration:
        """Create SecurityConfiguration from dictionary."""
        # Convert string enums back to enum objects
        if 'security_level' in config_data:
            config_data['security_level'] = SecurityLevel(config_data['security_level'])
        
        if 'authentication_methods' in config_data:
            config_data['authentication_methods'] = [
                AuthenticationMethod(method) for method in config_data['authentication_methods']
            ]
        
        # Create nested configuration objects
        nested_configs = {
            'jwt_config': JWTConfig,
            'mfa_config': MFAConfig,
            'sso_config': SSOConfig,
            'rbac_config': RBACConfig,
            'encryption_config': EncryptionConfig,
            'audit_config': AuditConfig,
            'api_security_config': APISecurityConfig,
            'compliance_config': ComplianceConfig
        }
        
        for config_key, config_class in nested_configs.items():
            if config_key in config_data and isinstance(config_data[config_key], dict):
                config_data[config_key] = config_class(**config_data[config_key])
        
        return SecurityConfiguration(**config_data)
    
    def save_configuration(self, config: Optional[SecurityConfiguration] = None):
        """Save configuration to file."""
        config = config or self.config
        
        try:
            # Encrypt sensitive values before saving
            config_dict = self._encrypt_config_values(config.to_dict())
            
            # Create environment-specific structure
            file_config = {self.environment: config_dict}
            
            # Save to file
            with open(self.config_file, 'w') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(file_config, f, default_flow_style=False)
                else:
                    json.dump(file_config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            raise
    
    def _encrypt_config_values(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive configuration values before saving."""
        # Define which fields should be encrypted
        sensitive_fields = [
            'jwt_config.secret_key',
            'redis_password'
        ]
        
        for field_path in sensitive_fields:
            value = self._get_nested_value(config_dict, field_path)
            if value and isinstance(value, str) and not value.startswith('encrypted:'):
                encrypted_value = 'encrypted:' + self._encrypt_sensitive_value(value)
                self._set_nested_config(config_dict, field_path, encrypted_value)
        
        return config_dict
    
    def reload_configuration(self) -> SecurityConfiguration:
        """Reload configuration from file and environment."""
        self.config = self._load_configuration()
        self.logger.info("Configuration reloaded")
        return self.config
    
    def get_config(self) -> SecurityConfiguration:
        """Get current configuration."""
        return self.config
    
    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return any errors."""
        try:
            self.config._validate_configuration()
            return []
        except ValueError as e:
            return str(e).split(': ', 1)[1].split('; ')


# Global configuration instance
_config_manager = None

def get_security_config() -> SecurityConfiguration:
    """Get global security configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecurityConfigManager()
    return _config_manager.get_config()

def reload_security_config() -> SecurityConfiguration:
    """Reload global security configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecurityConfigManager()
    return _config_manager.reload_configuration()


# Example usage
if __name__ == "__main__":
    # Initialize configuration manager
    config_manager = SecurityConfigManager()
    
    # Get configuration
    config = config_manager.get_config()
    
    print(f"Security Level: {config.security_level.value}")
    print(f"JWT Enabled: {AuthenticationMethod.JWT in config.authentication_methods}")
    print(f"MFA Enabled: {config.mfa_config.enabled}")
    print(f"Audit Enabled: {config.audit_config.enabled}")
    
    # Save configuration
    config_manager.save_configuration()
    
    # Validate configuration
    errors = config_manager.validate_configuration()
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("Configuration is valid")
