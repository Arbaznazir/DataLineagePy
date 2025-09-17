"""
Compliance Audit Framework
Comprehensive auditing and reporting for compliance standards.
"""

import time
import uuid
import logging
import threading
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_CONFIGURATION = "system_configuration"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SECURITY_INCIDENT = "security_incident"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Compliance standards for auditing."""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"


@dataclass
class AuditEvent:
    """Individual audit event record."""
    event_id: str
    timestamp: float
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: str
    resource: str
    action: str
    outcome: str
    ip_address: str
    user_agent: str
    session_id: str
    details: Dict[str, Any]
    compliance_standards: List[ComplianceStandard]
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.compliance_standards:
            self.compliance_standards = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "resource": self.resource,
            "action": self.action,
            "outcome": self.outcome,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "details": self.details,
            "compliance_standards": [std.value for std in self.compliance_standards]
        }


@dataclass
class AuditFilter:
    """Filter criteria for audit queries."""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    event_types: Optional[List[AuditEventType]] = None
    severities: Optional[List[AuditSeverity]] = None
    user_ids: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None
    outcome: Optional[str] = None
    limit: int = 1000


class AuditLog:
    """Centralized audit logging system."""
    
    def __init__(self, retention_days: int = 2555):  # 7 years default
        """
        Initialize audit log.
        
        Args:
            retention_days: How long to retain audit logs
        """
        self.events: List[AuditEvent] = []
        self.retention_days = retention_days
        self.lock = threading.Lock()
        self.event_handlers: List[callable] = []
        
        logger.info(f"Audit log initialized with {retention_days} days retention")
    
    def log_event(self, event_type: AuditEventType, severity: AuditSeverity,
                  user_id: str, resource: str, action: str, outcome: str,
                  ip_address: str = "", user_agent: str = "", session_id: str = "",
                  details: Dict[str, Any] = None,
                  compliance_standards: List[ComplianceStandard] = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            severity: Event severity
            user_id: User performing action
            resource: Resource being accessed/modified
            action: Action being performed
            outcome: Result of the action
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: Session identifier
            details: Additional event details
            compliance_standards: Relevant compliance standards
            
        Returns:
            Event ID
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            resource=resource,
            action=action,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=details or {},
            compliance_standards=compliance_standards or []
        )
        
        with self.lock:
            self.events.append(event)
        
        # Notify event handlers
        for handler in self.event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in audit event handler: {e}")
        
        logger.debug(f"Logged audit event {event.event_id}")
        return event.event_id
    
    def query_events(self, filter_criteria: AuditFilter) -> List[AuditEvent]:
        """
        Query audit events with filtering.
        
        Args:
            filter_criteria: Filter criteria
            
        Returns:
            Filtered audit events
        """
        with self.lock:
            results = self.events.copy()
        
        # Apply filters
        if filter_criteria.start_time:
            results = [e for e in results if e.timestamp >= filter_criteria.start_time]
        
        if filter_criteria.end_time:
            results = [e for e in results if e.timestamp <= filter_criteria.end_time]
        
        if filter_criteria.event_types:
            results = [e for e in results if e.event_type in filter_criteria.event_types]
        
        if filter_criteria.severities:
            results = [e for e in results if e.severity in filter_criteria.severities]
        
        if filter_criteria.user_ids:
            results = [e for e in results if e.user_id in filter_criteria.user_ids]
        
        if filter_criteria.resources:
            results = [e for e in results if e.resource in filter_criteria.resources]
        
        if filter_criteria.compliance_standards:
            results = [e for e in results 
                      if any(std in e.compliance_standards for std in filter_criteria.compliance_standards)]
        
        if filter_criteria.outcome:
            results = [e for e in results if e.outcome == filter_criteria.outcome]
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:filter_criteria.limit]
    
    def add_event_handler(self, handler: callable):
        """Add event handler for real-time processing."""
        self.event_handlers.append(handler)
    
    def cleanup_old_events(self) -> int:
        """Clean up old audit events based on retention policy."""
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        removed_count = 0
        
        with self.lock:
            original_count = len(self.events)
            self.events = [e for e in self.events if e.timestamp >= cutoff_time]
            removed_count = original_count - len(self.events)
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old audit events")
        
        return removed_count


@dataclass
class ComplianceReport:
    """Compliance assessment report."""
    report_id: str
    standard: ComplianceStandard
    generated_at: float
    period_start: float
    period_end: float
    overall_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    risk_level: str
    
    def __post_init__(self):
        if not self.report_id:
            self.report_id = str(uuid.uuid4())


@dataclass
class RiskAssessment:
    """Risk assessment for compliance."""
    assessment_id: str
    standard: ComplianceStandard
    conducted_at: float
    risk_factors: List[Dict[str, Any]]
    overall_risk: str
    mitigation_strategies: List[str]
    next_assessment_due: float
    
    def __post_init__(self):
        if not self.assessment_id:
            self.assessment_id = str(uuid.uuid4())


class ComplianceAuditor:
    """Main compliance auditing system."""
    
    def __init__(self, audit_log: AuditLog = None):
        """
        Initialize compliance auditor.
        
        Args:
            audit_log: Audit log instance
        """
        self.audit_log = audit_log or AuditLog()
        self.compliance_reports: Dict[str, ComplianceReport] = {}
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        self.compliance_rules: Dict[ComplianceStandard, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        
        # Initialize compliance rules
        self._initialize_compliance_rules()
        
        logger.info("Compliance Auditor initialized")
    
    def _initialize_compliance_rules(self):
        """Initialize compliance rules for different standards."""
        # GDPR Rules
        self.compliance_rules[ComplianceStandard.GDPR] = [
            {
                "rule_id": "gdpr_data_access",
                "description": "All personal data access must be logged",
                "severity": AuditSeverity.HIGH,
                "check_function": self._check_gdpr_data_access
            },
            {
                "rule_id": "gdpr_consent",
                "description": "Data processing requires valid consent",
                "severity": AuditSeverity.CRITICAL,
                "check_function": self._check_gdpr_consent
            }
        ]
        
        # SOX Rules
        self.compliance_rules[ComplianceStandard.SOX] = [
            {
                "rule_id": "sox_financial_access",
                "description": "Financial data access must be authorized",
                "severity": AuditSeverity.CRITICAL,
                "check_function": self._check_sox_financial_access
            },
            {
                "rule_id": "sox_change_approval",
                "description": "System changes require approval",
                "severity": AuditSeverity.HIGH,
                "check_function": self._check_sox_change_approval
            }
        ]
        
        # HIPAA Rules
        self.compliance_rules[ComplianceStandard.HIPAA] = [
            {
                "rule_id": "hipaa_phi_access",
                "description": "PHI access must be for authorized purposes",
                "severity": AuditSeverity.CRITICAL,
                "check_function": self._check_hipaa_phi_access
            },
            {
                "rule_id": "hipaa_minimum_necessary",
                "description": "Only minimum necessary PHI should be accessed",
                "severity": AuditSeverity.HIGH,
                "check_function": self._check_hipaa_minimum_necessary
            }
        ]
    
    def generate_compliance_report(self, standard: ComplianceStandard,
                                 period_start: float, period_end: float) -> str:
        """
        Generate compliance report for a specific standard.
        
        Args:
            standard: Compliance standard
            period_start: Report period start time
            period_end: Report period end time
            
        Returns:
            Report ID
        """
        # Query relevant audit events
        filter_criteria = AuditFilter(
            start_time=period_start,
            end_time=period_end,
            compliance_standards=[standard],
            limit=10000
        )
        
        events = self.audit_log.query_events(filter_criteria)
        
        # Run compliance checks
        findings = []
        violations = 0
        
        rules = self.compliance_rules.get(standard, [])
        for rule in rules:
            try:
                rule_findings = rule["check_function"](events, period_start, period_end)
                findings.extend(rule_findings)
                violations += len([f for f in rule_findings if f.get("violation", False)])
            except Exception as e:
                logger.error(f"Error checking rule {rule['rule_id']}: {e}")
        
        # Calculate compliance score
        total_checks = len(rules) * max(1, len(events) // 100)  # Scale with event volume
        compliance_score = max(0, (total_checks - violations) / max(1, total_checks) * 100)
        
        # Determine risk level
        if compliance_score >= 90:
            risk_level = "low"
        elif compliance_score >= 70:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(standard, findings)
        
        # Create report
        report = ComplianceReport(
            report_id=str(uuid.uuid4()),
            standard=standard,
            generated_at=time.time(),
            period_start=period_start,
            period_end=period_end,
            overall_score=compliance_score,
            findings=findings,
            recommendations=recommendations,
            risk_level=risk_level
        )
        
        with self.lock:
            self.compliance_reports[report.report_id] = report
        
        logger.info(f"Generated compliance report {report.report_id} for {standard.value}")
        return report.report_id
    
    def conduct_risk_assessment(self, standard: ComplianceStandard) -> str:
        """
        Conduct risk assessment for compliance standard.
        
        Args:
            standard: Compliance standard
            
        Returns:
            Assessment ID
        """
        # Analyze recent events for risk factors
        recent_events = self.audit_log.query_events(AuditFilter(
            start_time=time.time() - (30 * 24 * 3600),  # Last 30 days
            compliance_standards=[standard],
            limit=5000
        ))
        
        risk_factors = []
        
        # Check for high-severity events
        critical_events = [e for e in recent_events if e.severity == AuditSeverity.CRITICAL]
        if critical_events:
            risk_factors.append({
                "factor": "Critical security events",
                "count": len(critical_events),
                "risk_level": "high",
                "description": f"{len(critical_events)} critical events in last 30 days"
            })
        
        # Check for failed access attempts
        failed_access = [e for e in recent_events if e.outcome == "failure" and e.event_type == AuditEventType.DATA_ACCESS]
        if len(failed_access) > 10:
            risk_factors.append({
                "factor": "Failed access attempts",
                "count": len(failed_access),
                "risk_level": "medium",
                "description": f"{len(failed_access)} failed access attempts"
            })
        
        # Determine overall risk
        high_risk_factors = [f for f in risk_factors if f["risk_level"] == "high"]
        medium_risk_factors = [f for f in risk_factors if f["risk_level"] == "medium"]
        
        if high_risk_factors:
            overall_risk = "high"
        elif len(medium_risk_factors) >= 2:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        # Generate mitigation strategies
        mitigation_strategies = self._generate_mitigation_strategies(standard, risk_factors)
        
        # Create assessment
        assessment = RiskAssessment(
            assessment_id=str(uuid.uuid4()),
            standard=standard,
            conducted_at=time.time(),
            risk_factors=risk_factors,
            overall_risk=overall_risk,
            mitigation_strategies=mitigation_strategies,
            next_assessment_due=time.time() + (90 * 24 * 3600)  # 90 days
        )
        
        with self.lock:
            self.risk_assessments[assessment.assessment_id] = assessment
        
        logger.info(f"Conducted risk assessment {assessment.assessment_id} for {standard.value}")
        return assessment.assessment_id
    
    def _check_gdpr_data_access(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check GDPR data access compliance."""
        findings = []
        
        # Check for unlogged personal data access
        data_access_events = [e for e in events if e.event_type == AuditEventType.DATA_ACCESS]
        
        for event in data_access_events:
            if "personal_data" in event.details and not event.details.get("consent_verified", False):
                findings.append({
                    "rule_id": "gdpr_data_access",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "Personal data accessed without consent verification",
                    "severity": "high"
                })
        
        return findings
    
    def _check_gdpr_consent(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check GDPR consent compliance."""
        findings = []
        
        # Check for data processing without consent
        processing_events = [e for e in events if e.event_type == AuditEventType.DATA_MODIFICATION]
        
        for event in processing_events:
            if "personal_data" in event.details and not event.details.get("legal_basis"):
                findings.append({
                    "rule_id": "gdpr_consent",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "Personal data processed without legal basis",
                    "severity": "critical"
                })
        
        return findings
    
    def _check_sox_financial_access(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check SOX financial data access compliance."""
        findings = []
        
        financial_access_events = [e for e in events 
                                 if e.event_type == AuditEventType.DATA_ACCESS 
                                 and "financial" in event.resource.lower()]
        
        for event in financial_access_events:
            if event.outcome == "failure":
                findings.append({
                    "rule_id": "sox_financial_access",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "Unauthorized financial data access attempt",
                    "severity": "critical"
                })
        
        return findings
    
    def _check_sox_change_approval(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check SOX change approval compliance."""
        findings = []
        
        config_events = [e for e in events if e.event_type == AuditEventType.SYSTEM_CONFIGURATION]
        
        for event in config_events:
            if not event.details.get("approval_id"):
                findings.append({
                    "rule_id": "sox_change_approval",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "System change made without approval",
                    "severity": "high"
                })
        
        return findings
    
    def _check_hipaa_phi_access(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check HIPAA PHI access compliance."""
        findings = []
        
        phi_access_events = [e for e in events 
                           if e.event_type == AuditEventType.DATA_ACCESS 
                           and "phi" in event.resource.lower()]
        
        for event in phi_access_events:
            if not event.details.get("access_purpose"):
                findings.append({
                    "rule_id": "hipaa_phi_access",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "PHI accessed without documented purpose",
                    "severity": "critical"
                })
        
        return findings
    
    def _check_hipaa_minimum_necessary(self, events: List[AuditEvent], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Check HIPAA minimum necessary compliance."""
        findings = []
        
        phi_access_events = [e for e in events 
                           if e.event_type == AuditEventType.DATA_ACCESS 
                           and "phi" in event.resource.lower()]
        
        for event in phi_access_events:
            if not event.details.get("minimum_necessary_verified", False):
                findings.append({
                    "rule_id": "hipaa_minimum_necessary",
                    "event_id": event.event_id,
                    "violation": True,
                    "description": "PHI access did not verify minimum necessary standard",
                    "severity": "high"
                })
        
        return findings
    
    def _generate_recommendations(self, standard: ComplianceStandard, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations based on findings."""
        recommendations = []
        
        violation_counts = {}
        for finding in findings:
            if finding.get("violation"):
                rule_id = finding.get("rule_id", "unknown")
                violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1
        
        # Standard-specific recommendations
        if standard == ComplianceStandard.GDPR:
            if violation_counts.get("gdpr_consent", 0) > 0:
                recommendations.append("Implement consent verification before processing personal data")
            if violation_counts.get("gdpr_data_access", 0) > 0:
                recommendations.append("Enhance personal data access logging and monitoring")
        
        elif standard == ComplianceStandard.SOX:
            if violation_counts.get("sox_change_approval", 0) > 0:
                recommendations.append("Implement mandatory change approval workflow")
            if violation_counts.get("sox_financial_access", 0) > 0:
                recommendations.append("Strengthen financial data access controls")
        
        elif standard == ComplianceStandard.HIPAA:
            if violation_counts.get("hipaa_phi_access", 0) > 0:
                recommendations.append("Implement PHI access purpose documentation")
            if violation_counts.get("hipaa_minimum_necessary", 0) > 0:
                recommendations.append("Enforce minimum necessary standard verification")
        
        return recommendations
    
    def _generate_mitigation_strategies(self, standard: ComplianceStandard, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation strategies."""
        strategies = []
        
        for factor in risk_factors:
            if factor["factor"] == "Critical security events":
                strategies.append("Implement enhanced security monitoring and incident response")
            elif factor["factor"] == "Failed access attempts":
                strategies.append("Review and strengthen access controls and authentication")
        
        # Standard-specific strategies
        if standard == ComplianceStandard.GDPR:
            strategies.append("Conduct privacy impact assessments for high-risk processing")
            strategies.append("Implement data protection by design and by default")
        
        elif standard == ComplianceStandard.SOX:
            strategies.append("Enhance internal controls testing and documentation")
            strategies.append("Implement segregation of duties for financial processes")
        
        elif standard == ComplianceStandard.HIPAA:
            strategies.append("Conduct regular HIPAA risk assessments")
            strategies.append("Enhance PHI access controls and monitoring")
        
        return strategies
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get audit system summary."""
        with self.lock:
            recent_events = self.audit_log.query_events(AuditFilter(
                start_time=time.time() - (24 * 3600),  # Last 24 hours
                limit=10000
            ))
            
            return {
                "audit_summary": {
                    "total_events": len(self.audit_log.events),
                    "recent_events_24h": len(recent_events),
                    "compliance_reports": len(self.compliance_reports),
                    "risk_assessments": len(self.risk_assessments),
                    "critical_events_24h": len([e for e in recent_events if e.severity == AuditSeverity.CRITICAL]),
                    "failed_events_24h": len([e for e in recent_events if e.outcome == "failure"])
                }
            }
