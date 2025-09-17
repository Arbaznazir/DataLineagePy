"""
Enterprise Security Integration Example
Demonstrates how to integrate all security components for a complete enterprise solution.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import all security components
from datalineagepy.security import (
    # Configuration
    SecurityConfiguration,
    SecurityConfigManager,
    SecurityLevel,
    AuthenticationMethod,
    
    # Authentication
    MFAManager,
    JWTManager,
    SSOManager,
    
    # Authorization
    RBACEngine,
    PolicyEngine,
    
    # Encryption
    EncryptionManager,
    EnterpriseKeyManager,
    VaultClient,
    
    # Audit
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    ComplianceFramework,
    
    # API Security
    SecurityMiddleware,
    SecurityConfig as APISecurityConfig,
    RateLimitRule,
    
    # Utilities
    setup_enterprise_security
)


class EnterpriseSecurityManager:
    """
    Unified enterprise security manager that orchestrates all security components.
    
    This class demonstrates how to integrate:
    - Authentication (MFA, JWT, SSO)
    - Authorization (RBAC, Policies)
    - Encryption (Data, Keys)
    - Audit Logging
    - API Security
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize enterprise security manager."""
        # Load configuration
        self.config_manager = SecurityConfigManager(config_file)
        self.config = self.config_manager.get_config()
        
        # Initialize components
        self._initialize_components()
        
        print(f"✅ Enterprise Security Manager initialized with {self.config.security_level.value} security level")
    
    def _initialize_components(self):
        """Initialize all security components."""
        try:
            # Authentication components
            self.mfa_manager = MFAManager()
            self.jwt_manager = JWTManager(
                secret_key=self.config.jwt_config.secret_key or "demo-secret-key",
                algorithm=self.config.jwt_config.algorithm
            )
            self.sso_manager = SSOManager()
            
            # Authorization components
            self.rbac_engine = RBACEngine()
            self.policy_engine = PolicyEngine()
            
            # Encryption components
            self.encryption_manager = EncryptionManager()
            
            # Key management (with mock Vault for demo)
            vault_client = None  # VaultClient("https://vault.company.com") for production
            self.key_manager = EnterpriseKeyManager(vault_client=vault_client)
            
            # Audit logging
            self.audit_logger = AuditLogger()
            
            # API security
            api_config = APISecurityConfig(
                default_rate_limit=RateLimitRule(
                    requests_per_minute=self.config.api_security_config.default_rate_limit_per_minute,
                    requests_per_hour=self.config.api_security_config.default_rate_limit_per_hour,
                    requests_per_day=self.config.api_security_config.default_rate_limit_per_hour * 24
                ),
                allowed_origins=self.config.api_security_config.allowed_origins,
                max_request_size=self.config.api_security_config.max_request_size_mb * 1024 * 1024
            )
            self.api_security = SecurityMiddleware(api_config)
            
            # Initialize default security setup
            self._setup_default_security()
            
        except Exception as e:
            print(f"❌ Failed to initialize security components: {str(e)}")
            raise
    
    def _setup_default_security(self):
        """Set up default security configuration."""
        # Initialize RBAC roles and permissions
        self._setup_default_rbac()
        
        # Initialize default policies
        self._setup_default_policies()
        
        # Generate default encryption keys
        self._setup_default_encryption()
        
        print("🔧 Default security setup completed")
    
    def _setup_default_rbac(self):
        """Set up default RBAC roles and permissions."""
        # Create default roles
        roles = [
            ("admin", "Full system administration access"),
            ("data_engineer", "Data pipeline and lineage management"),
            ("data_analyst", "Data analysis and reporting"),
            ("viewer", "Read-only access to lineage data")
        ]
        
        for role_name, description in roles:
            self.rbac_engine.create_role(role_name, description)
        
        # Create permissions
        permissions = [
            ("lineage.read", "Read lineage data", "lineage"),
            ("lineage.write", "Modify lineage data", "lineage"),
            ("lineage.delete", "Delete lineage data", "lineage"),
            ("users.manage", "Manage users", "users"),
            ("system.admin", "System administration", "system"),
            ("reports.generate", "Generate reports", "reports")
        ]
        
        for perm_name, description, resource in permissions:
            self.rbac_engine.create_permission(perm_name, description, resource)
        
        # Assign permissions to roles
        role_permissions = {
            "admin": ["lineage.read", "lineage.write", "lineage.delete", "users.manage", "system.admin", "reports.generate"],
            "data_engineer": ["lineage.read", "lineage.write", "reports.generate"],
            "data_analyst": ["lineage.read", "reports.generate"],
            "viewer": ["lineage.read"]
        }
        
        for role, permissions in role_permissions.items():
            for permission in permissions:
                self.rbac_engine.assign_permission_to_role(role, permission)
    
    def _setup_default_policies(self):
        """Set up default authorization policies."""
        # Business hours policy
        business_hours_policy = {
            "name": "business_hours_access",
            "description": "Allow access only during business hours",
            "priority": 100,
            "conditions": [
                {
                    "attribute": "time.hour",
                    "operator": ">=",
                    "value": 9
                },
                {
                    "attribute": "time.hour",
                    "operator": "<=",
                    "value": 17
                }
            ],
            "effect": "allow"
        }
        
        # Sensitive data policy
        sensitive_data_policy = {
            "name": "sensitive_data_protection",
            "description": "Restrict access to sensitive data",
            "priority": 200,
            "conditions": [
                {
                    "attribute": "resource.classification",
                    "operator": "==",
                    "value": "sensitive"
                },
                {
                    "attribute": "user.clearance_level",
                    "operator": ">=",
                    "value": 3
                }
            ],
            "effect": "allow"
        }
        
        self.policy_engine.add_policy(business_hours_policy)
        self.policy_engine.add_policy(sensitive_data_policy)
    
    def _setup_default_encryption(self):
        """Set up default encryption keys."""
        # Generate master encryption key
        self.key_manager.generate_key(
            key_id="master_data_key",
            algorithm="AES-256",
            key_size=32,
            expires_in_days=365
        )
        
        # Generate field-specific keys
        field_keys = [
            "user_pii_key",
            "financial_data_key",
            "system_logs_key"
        ]
        
        for key_id in field_keys:
            self.key_manager.generate_key(
                key_id=key_id,
                algorithm="AES-256",
                key_size=32,
                expires_in_days=90
            )
    
    def authenticate_user(self, username: str, password: str, 
                         mfa_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive user authentication with MFA.
        
        Args:
            username: User's username
            password: User's password
            mfa_token: Optional MFA token
            
        Returns:
            Authentication result with JWT tokens
        """
        try:
            # Log authentication attempt
            self.audit_logger.log_authentication(
                user_id=username,
                user_email=f"{username}@company.com",
                outcome="attempt",
                details={"method": "password"}
            )
            
            # Simulate password verification (in production, verify against user store)
            if not self._verify_password(username, password):
                self.audit_logger.log_authentication(
                    user_id=username,
                    user_email=f"{username}@company.com",
                    outcome="failure",
                    details={"reason": "invalid_password"}
                )
                return {"success": False, "error": "Invalid credentials"}
            
            # Check MFA if enabled
            if self.config.mfa_config.enabled:
                if not mfa_token:
                    return {"success": False, "error": "MFA token required", "mfa_required": True}
                
                # Get user's MFA secret (in production, retrieve from user store)
                user_secret = self._get_user_mfa_secret(username)
                if not self.mfa_manager.verify_totp(user_secret, mfa_token):
                    self.audit_logger.log_authentication(
                        user_id=username,
                        user_email=f"{username}@company.com",
                        outcome="failure",
                        details={"reason": "invalid_mfa"}
                    )
                    return {"success": False, "error": "Invalid MFA token"}
            
            # Generate JWT tokens
            user_data = {
                "user_id": username,
                "email": f"{username}@company.com",
                "roles": self._get_user_roles(username)
            }
            
            access_token = self.jwt_manager.create_access_token(user_data)
            refresh_token = self.jwt_manager.create_refresh_token(user_data)
            
            # Log successful authentication
            self.audit_logger.log_authentication(
                user_id=username,
                user_email=f"{username}@company.com",
                outcome="success",
                details={"mfa_used": self.config.mfa_config.enabled}
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data
            }
            
        except Exception as e:
            self.audit_logger.log_authentication(
                user_id=username,
                user_email=f"{username}@company.com",
                outcome="error",
                details={"error": str(e)}
            )
            return {"success": False, "error": "Authentication failed"}
    
    def authorize_access(self, user_id: str, resource: str, action: str,
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive authorization check using RBAC and policies.
        
        Args:
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed
            context: Additional context for policy evaluation
            
        Returns:
            Authorization result
        """
        try:
            # Get user roles
            user_roles = self._get_user_roles(user_id)
            
            # Check RBAC permissions
            rbac_allowed = False
            for role in user_roles:
                if self.rbac_engine.check_permission(user_id, f"{resource}.{action}"):
                    rbac_allowed = True
                    break
            
            # Evaluate policies
            policy_context = {
                "user": {"id": user_id, "roles": user_roles},
                "resource": {"type": resource, "id": resource},
                "action": action,
                "time": {"hour": datetime.now().hour},
                **(context or {})
            }
            
            policy_result = self.policy_engine.evaluate_access(
                user_id, resource, action, policy_context
            )
            
            # Final decision (both RBAC and policies must allow)
            allowed = rbac_allowed and policy_result["allowed"]
            
            # Log authorization event
            self.audit_logger.log_event(
                event_type=AuditEventType.AUTHORIZATION,
                message=f"Authorization check: {action} on {resource}",
                user_id=user_id,
                resource_type=resource,
                action=action,
                outcome="success" if allowed else "denied",
                severity=AuditSeverity.MEDIUM,
                details={
                    "rbac_allowed": rbac_allowed,
                    "policy_result": policy_result,
                    "final_decision": allowed
                }
            )
            
            return {
                "allowed": allowed,
                "rbac_result": rbac_allowed,
                "policy_result": policy_result,
                "user_roles": user_roles
            }
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.AUTHORIZATION,
                message=f"Authorization error: {str(e)}",
                user_id=user_id,
                outcome="error",
                severity=AuditSeverity.HIGH
            )
            return {"allowed": False, "error": str(e)}
    
    def encrypt_sensitive_data(self, data: Dict[str, Any], 
                             classification: str = "sensitive") -> Dict[str, Any]:
        """
        Encrypt sensitive data fields based on classification.
        
        Args:
            data: Data to encrypt
            classification: Data classification level
            
        Returns:
            Data with encrypted sensitive fields
        """
        try:
            # Define sensitive fields by classification
            sensitive_fields = {
                "sensitive": ["email", "phone", "ssn"],
                "confidential": ["salary", "performance_rating"],
                "restricted": ["security_clearance", "access_codes"]
            }
            
            fields_to_encrypt = sensitive_fields.get(classification, [])
            encrypted_data = data.copy()
            
            for field in fields_to_encrypt:
                if field in encrypted_data:
                    # Encrypt the field
                    encrypted_value = self.encryption_manager.encrypt_field(
                        str(encrypted_data[field]), field
                    )
                    encrypted_data[field] = encrypted_value
            
            # Log data encryption
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_MODIFICATION,
                message=f"Data encrypted with classification: {classification}",
                action="encrypt",
                outcome="success",
                data_classification=classification,
                details={"fields_encrypted": fields_to_encrypt}
            )
            
            return encrypted_data
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.ERROR_EVENT,
                message=f"Encryption failed: {str(e)}",
                outcome="error",
                severity=AuditSeverity.HIGH
            )
            raise
    
    def generate_compliance_report(self, framework: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate compliance report for specified framework.
        
        Args:
            framework: Compliance framework (gdpr, sox, hipaa)
            days: Number of days to include in report
            
        Returns:
            Compliance report
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Map framework names to enum values
            framework_map = {
                "gdpr": ComplianceFramework.GDPR,
                "sox": ComplianceFramework.SOX,
                "hipaa": ComplianceFramework.HIPAA,
                "pci_dss": ComplianceFramework.PCI_DSS
            }
            
            framework_enum = framework_map.get(framework.lower())
            if not framework_enum:
                raise ValueError(f"Unsupported compliance framework: {framework}")
            
            # Generate report
            report = self.audit_logger.generate_compliance_report(
                framework_enum, start_time, end_time
            )
            
            # Add security metrics
            report["security_metrics"] = {
                "authentication_events": len([e for e in self.audit_logger.search_events(
                    start_time, end_time, {"event_type": AuditEventType.AUTHENTICATION.value}
                )]),
                "authorization_events": len([e for e in self.audit_logger.search_events(
                    start_time, end_time, {"event_type": AuditEventType.AUTHORIZATION.value}
                )]),
                "data_access_events": len([e for e in self.audit_logger.search_events(
                    start_time, end_time, {"event_type": AuditEventType.DATA_ACCESS.value}
                )]),
                "security_events": len([e for e in self.audit_logger.search_events(
                    start_time, end_time, {"event_type": AuditEventType.SECURITY_EVENT.value}
                )])
            }
            
            # Add key management status
            report["key_management"] = {
                "total_keys": len(self.key_manager.list_keys()),
                "keys_needing_rotation": len(self.key_manager.check_rotation_needed()),
                "expiring_keys": len(self.key_manager.check_key_expiration())
            }
            
            return report
            
        except Exception as e:
            self.audit_logger.log_event(
                event_type=AuditEventType.COMPLIANCE_EVENT,
                message=f"Compliance report generation failed: {str(e)}",
                outcome="error",
                severity=AuditSeverity.HIGH
            )
            raise
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard metrics."""
        try:
            return {
                "authentication": {
                    "mfa_enabled": self.config.mfa_config.enabled,
                    "jwt_algorithm": self.config.jwt_config.algorithm,
                    "sso_providers": len(self.sso_manager.providers)
                },
                "authorization": {
                    "rbac_enabled": self.config.rbac_config.enabled,
                    "total_roles": len(self.rbac_engine.roles),
                    "total_permissions": len(self.rbac_engine.permissions),
                    "active_policies": len(self.policy_engine.policies)
                },
                "encryption": {
                    "algorithm": self.config.encryption_config.algorithm,
                    "key_rotation_days": self.config.encryption_config.key_rotation_days,
                    "total_keys": len(self.key_manager.list_keys()),
                    "health_status": self.key_manager.health_check()["status"]
                },
                "audit": {
                    "enabled": self.config.audit_config.enabled,
                    "events_logged": self.audit_logger.get_metrics()["events_logged"],
                    "storage_backend": self.config.audit_config.storage_backend
                },
                "api_security": {
                    "rate_limiting": self.config.api_security_config.rate_limiting_enabled,
                    "cors_enabled": self.config.api_security_config.cors_enabled,
                    "requests_processed": self.api_security.get_metrics()["requests_processed"],
                    "requests_blocked": self.api_security.get_metrics()["requests_blocked"]
                },
                "compliance": {
                    "gdpr_enabled": self.config.compliance_config.gdpr_enabled,
                    "sox_enabled": self.config.compliance_config.sox_enabled,
                    "hipaa_enabled": self.config.compliance_config.hipaa_enabled,
                    "data_retention_days": self.config.compliance_config.data_retention_days
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # Helper methods (would be implemented with actual user store in production)
    def _verify_password(self, username: str, password: str) -> bool:
        """Verify user password (mock implementation)."""
        # In production, verify against secure user store
        return password == "demo123"  # Demo only
    
    def _get_user_mfa_secret(self, username: str) -> str:
        """Get user's MFA secret (mock implementation)."""
        # In production, retrieve from secure user store
        return "JBSWY3DPEHPK3PXP"  # Demo secret
    
    def _get_user_roles(self, username: str) -> list:
        """Get user roles (mock implementation)."""
        # In production, retrieve from user store
        role_mapping = {
            "admin": ["admin"],
            "engineer": ["data_engineer"],
            "analyst": ["data_analyst"],
            "user": ["viewer"]
        }
        return role_mapping.get(username, ["viewer"])
    
    def shutdown(self):
        """Gracefully shutdown all security components."""
        try:
            self.audit_logger.shutdown()
            self.key_manager.stop_automatic_rotation()
            print("🔒 Enterprise Security Manager shutdown complete")
        except Exception as e:
            print(f"⚠️ Error during shutdown: {str(e)}")


def main():
    """Demonstrate enterprise security integration."""
    print("🚀 DataLineagePy Enterprise Security Integration Demo")
    print("=" * 60)
    
    # Initialize enterprise security
    security_manager = EnterpriseSecurityManager()
    
    # Demo 1: User Authentication
    print("\n1. 👤 User Authentication Demo")
    print("-" * 30)
    
    auth_result = security_manager.authenticate_user("engineer", "demo123")
    if auth_result["success"]:
        print(f"✅ Authentication successful for user: {auth_result['user']['user_id']}")
        print(f"   Roles: {auth_result['user']['roles']}")
        access_token = auth_result["access_token"]
    else:
        print(f"❌ Authentication failed: {auth_result['error']}")
        return
    
    # Demo 2: Authorization Check
    print("\n2. 🔐 Authorization Demo")
    print("-" * 30)
    
    auth_check = security_manager.authorize_access("engineer", "lineage", "read")
    print(f"✅ Authorization result: {'ALLOWED' if auth_check['allowed'] else 'DENIED'}")
    print(f"   RBAC result: {auth_check['rbac_result']}")
    print(f"   Policy result: {auth_check['policy_result']['allowed']}")
    
    # Demo 3: Data Encryption
    print("\n3. 🔒 Data Encryption Demo")
    print("-" * 30)
    
    sample_data = {
        "user_id": "12345",
        "name": "John Doe",
        "email": "john.doe@company.com",
        "department": "Engineering"
    }
    
    encrypted_data = security_manager.encrypt_sensitive_data(sample_data, "sensitive")
    print(f"✅ Data encrypted successfully")
    print(f"   Original email: {sample_data['email']}")
    print(f"   Encrypted email: {encrypted_data['email'][:50]}...")
    
    # Demo 4: Compliance Report
    print("\n4. 📊 Compliance Report Demo")
    print("-" * 30)
    
    try:
        gdpr_report = security_manager.generate_compliance_report("gdpr", days=1)
        print(f"✅ GDPR compliance report generated")
        print(f"   Total events: {gdpr_report['total_events']}")
        print(f"   Critical events: {len(gdpr_report['critical_events'])}")
        print(f"   Integrity status: {gdpr_report['integrity_status']}")
    except Exception as e:
        print(f"⚠️ Compliance report generation: {str(e)}")
    
    # Demo 5: Security Dashboard
    print("\n5. 📈 Security Dashboard")
    print("-" * 30)
    
    dashboard = security_manager.get_security_dashboard()
    print(f"✅ Security dashboard metrics:")
    print(f"   MFA enabled: {dashboard['authentication']['mfa_enabled']}")
    print(f"   Total roles: {dashboard['authorization']['total_roles']}")
    print(f"   Total keys: {dashboard['encryption']['total_keys']}")
    print(f"   Events logged: {dashboard['audit']['events_logged']}")
    print(f"   Requests processed: {dashboard['api_security']['requests_processed']}")
    
    # Cleanup
    print("\n6. 🧹 Cleanup")
    print("-" * 30)
    security_manager.shutdown()
    
    print("\n✨ Enterprise Security Integration Demo Complete!")
    print("🎯 All security components working together seamlessly")


if __name__ == "__main__":
    main()
