"""
Data Governance Module for DataLineagePy

Provides comprehensive data governance capabilities including data stewardship workflows,
automated data classification, policy enforcement, and data retention management.
"""

from .stewardship_manager import StewardshipManager, DataSteward, StewardshipWorkflow
from .classification_engine import ClassificationEngine, ClassificationRule, DataClassification
from .policy_engine import PolicyEngine, DataPolicy, PolicyRule, PolicyAction
from .retention_manager import RetentionManager, RetentionPolicy, RetentionSchedule
from .governance_dashboard import GovernanceDashboard, GovernanceMetrics
from .compliance_checker import ComplianceChecker, ComplianceRule, ComplianceReport

# Factory functions
def create_stewardship_manager(config=None):
    """Create a new stewardship manager instance."""
    return StewardshipManager(config)

def create_classification_engine(config=None):
    """Create a new classification engine instance."""
    return ClassificationEngine(config)

def create_policy_engine(config=None):
    """Create a new policy engine instance."""
    return PolicyEngine(config)

def create_retention_manager(config=None):
    """Create a new retention manager instance."""
    return RetentionManager(config)

def create_governance_dashboard(config=None):
    """Create a new governance dashboard instance."""
    return GovernanceDashboard(config)

def create_compliance_checker(config=None):
    """Create a new compliance checker instance."""
    return ComplianceChecker(config)

# Default configurations
DEFAULT_STEWARDSHIP_CONFIG = {
    "workflow_timeout": 86400,  # 24 hours
    "auto_assignment": True,
    "escalation_enabled": True,
    "notification_enabled": True,
    "approval_required": True,
    "audit_enabled": True
}

DEFAULT_CLASSIFICATION_CONFIG = {
    "auto_classification": True,
    "confidence_threshold": 0.8,
    "ml_enabled": True,
    "pattern_matching": True,
    "content_analysis": True,
    "metadata_analysis": True
}

DEFAULT_POLICY_CONFIG = {
    "enforcement_mode": "strict",
    "real_time_monitoring": True,
    "violation_alerts": True,
    "auto_remediation": False,
    "audit_logging": True,
    "policy_versioning": True
}

DEFAULT_RETENTION_CONFIG = {
    "default_retention_days": 2555,  # 7 years
    "auto_archival": True,
    "compression_enabled": True,
    "encryption_required": True,
    "legal_hold_support": True,
    "audit_trail": True
}

# Supported features
SUPPORTED_CLASSIFICATION_TYPES = [
    "PII", "PHI", "FINANCIAL", "CONFIDENTIAL", "PUBLIC", "INTERNAL", "RESTRICTED"
]

SUPPORTED_POLICY_ACTIONS = [
    "ALLOW", "DENY", "MASK", "ENCRYPT", "AUDIT", "ALERT", "QUARANTINE"
]

SUPPORTED_RETENTION_ACTIONS = [
    "ARCHIVE", "DELETE", "MIGRATE", "COMPRESS", "ENCRYPT", "LEGAL_HOLD"
]

__all__ = [
    "StewardshipManager",
    "DataSteward",
    "StewardshipWorkflow",
    "ClassificationEngine",
    "ClassificationRule",
    "DataClassification",
    "PolicyEngine",
    "DataPolicy",
    "PolicyRule",
    "PolicyAction",
    "RetentionManager",
    "RetentionPolicy",
    "RetentionSchedule",
    "GovernanceDashboard",
    "GovernanceMetrics",
    "ComplianceChecker",
    "ComplianceRule",
    "ComplianceReport",
    "create_stewardship_manager",
    "create_classification_engine",
    "create_policy_engine",
    "create_retention_manager",
    "create_governance_dashboard",
    "create_compliance_checker",
    "DEFAULT_STEWARDSHIP_CONFIG",
    "DEFAULT_CLASSIFICATION_CONFIG",
    "DEFAULT_POLICY_CONFIG",
    "DEFAULT_RETENTION_CONFIG",
    "SUPPORTED_CLASSIFICATION_TYPES",
    "SUPPORTED_POLICY_ACTIONS",
    "SUPPORTED_RETENTION_ACTIONS"
]
