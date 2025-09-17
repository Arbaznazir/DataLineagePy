"""
DataLineagePy Compliance Module
Comprehensive compliance framework for GDPR, SOX, HIPAA, and other regulatory standards.
"""

from .gdpr import (
    GDPRCompliance,
    ConsentManager,
    DataSubjectRights,
    PersonalDataHandler,
    DataProcessingRecord,
    BreachNotificationHandler,
    PrivacyImpactAssessment,
    DataProtectionOfficer,
    LegalBasis,
    ProcessingPurpose,
    ConsentStatus
)

from .sox import (
    SOXCompliance,
    FinancialDataGovernance,
    InternalControls,
    AuditTrailManager,
    ChangeManagement,
    ControlType,
    FinancialDataType,
    ChangeStatus
)

from .hipaa import (
    HIPAACompliance,
    PHIProtection,
    SecurityRule,
    PrivacyRule,
    BreachNotification,
    BusinessAssociateAgreement,
    PHIType,
    AccessPurpose,
    BreachSeverity
)

from .audit import (
    ComplianceAuditor,
    AuditLog,
    AuditEvent,
    AuditFilter,
    ComplianceReport,
    RiskAssessment,
    AuditEventType,
    AuditSeverity,
    ComplianceStandard
)

from .framework import (
    ComplianceFramework,
    ComplianceLevel,
    ComplianceConfig
)

from .data_governance import (
    DataGovernanceFramework,
    DataClassification,
    DataRetention,
    DataLineageCompliance,
    DataQuality,
    DataSteward
)

from .policy_engine import (
    PolicyEngine,
    CompliancePolicy,
    PolicyRule,
    PolicyViolation,
    PolicyEnforcement,
    PolicyTemplate
)

# Default compliance configurations
DEFAULT_GDPR_CONFIG = {
    "consent_retention_days": 1095,  # 3 years
    "breach_notification_hours": 72,
    "data_retention_days": 2555,  # 7 years
    "require_explicit_consent": True,
    "enable_right_to_be_forgotten": True,
    "enable_data_portability": True,
    "privacy_by_design": True
}

DEFAULT_SOX_CONFIG = {
    "audit_retention_years": 7,
    "require_change_approval": True,
    "segregation_of_duties": True,
    "financial_controls_testing": True,
    "quarterly_assessments": True,
    "management_certification": True
}

DEFAULT_HIPAA_CONFIG = {
    "phi_retention_years": 6,
    "encryption_required": True,
    "access_logging_required": True,
    "breach_notification_days": 60,
    "minimum_necessary_standard": True,
    "business_associate_agreements": True,
    "risk_assessment_frequency_months": 12
}

DEFAULT_AUDIT_CONFIG = {
    "retention_days": 2555,  # 7 years
    "enable_real_time_monitoring": True,
    "alert_on_violations": True,
    "export_to_siem": False,
    "compliance_reporting": True
}

DEFAULT_FRAMEWORK_CONFIG = {
    "enabled_standards": ["GDPR", "SOX", "HIPAA"],
    "compliance_level": "enterprise",
    "audit_retention_days": 2555,
    "auto_remediation": False,
    "real_time_monitoring": True
}

# Supported compliance standards
SUPPORTED_STANDARDS = [
    "GDPR",
    "SOX",
    "HIPAA",
    "PCI_DSS",
    "ISO27001",
    "NIST"
]

# Compliance levels
COMPLIANCE_LEVELS = [
    "basic",
    "standard",
    "advanced",
    "enterprise"
]

# Audit event types
AUDIT_EVENT_TYPES = [
    "data_access",
    "data_modification",
    "user_login",
    "user_logout",
    "permission_change",
    "system_configuration",
    "compliance_violation",
    "security_incident",
    "data_export",
    "data_deletion"
]

__all__ = [
    # GDPR
    "GDPRCompliance",
    "ConsentManager",
    "DataSubjectRights",
    "PersonalDataHandler",
    "DataProcessingRecord",
    "BreachNotificationHandler",
    "PrivacyImpactAssessment",
    "DataProtectionOfficer",
    "LegalBasis",
    "ProcessingPurpose",
    "ConsentStatus",
    
    # SOX
    "SOXCompliance",
    "FinancialDataGovernance",
    "InternalControls",
    "AuditTrailManager",
    "ChangeManagement",
    "ControlType",
    "FinancialDataType",
    "ChangeStatus",
    
    # HIPAA
    "HIPAACompliance",
    "PHIProtection",
    "SecurityRule",
    "PrivacyRule",
    "BreachNotification",
    "BusinessAssociateAgreement",
    "PHIType",
    "AccessPurpose",
    "BreachSeverity",
    
    # Audit System
    "ComplianceAuditor",
    "AuditLog",
    "AuditEvent",
    "AuditFilter",
    "ComplianceReport",
    "RiskAssessment",
    "AuditEventType",
    "AuditSeverity",
    "ComplianceStandard",
    
    # Framework
    "ComplianceFramework",
    "ComplianceLevel",
    "ComplianceConfig",
    
    # Data Governance
    "DataGovernanceFramework",
    "DataClassification",
    "DataRetention",
    "DataLineageCompliance",
    "DataQuality",
    "DataSteward",
    
    # Policy Engine
    "PolicyEngine",
    "CompliancePolicy",
    "PolicyRule",
    "PolicyViolation",
    "PolicyEnforcement",
    "PolicyTemplate",
    
    # Configuration and factory functions
    "DEFAULT_GDPR_CONFIG",
    "DEFAULT_SOX_CONFIG",
    "DEFAULT_HIPAA_CONFIG",
    "DEFAULT_AUDIT_CONFIG",
    "DEFAULT_FRAMEWORK_CONFIG",
    "SUPPORTED_STANDARDS",
    "COMPLIANCE_LEVELS",
    "AUDIT_EVENT_TYPES",
    "create_compliance_framework",
    "create_audit_system",
    "create_gdpr_compliance",
    "create_sox_compliance",
    "create_hipaa_compliance"
]
