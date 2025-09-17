"""
Unified Compliance Framework
Integrates GDPR, SOX, HIPAA, and other compliance standards.
"""

import time
import uuid
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .gdpr import GDPRCompliance, LegalBasis, ProcessingPurpose
from .sox import SOXCompliance, ControlType, FinancialDataType
from .hipaa import HIPAACompliance, PHIType, AccessPurpose
from .audit import ComplianceAuditor, AuditLog, AuditEventType, AuditSeverity, ComplianceStandard

logger = logging.getLogger(__name__)


class ComplianceLevel(Enum):
    """Compliance implementation levels."""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


@dataclass
class ComplianceConfig:
    """Unified compliance configuration."""
    enabled_standards: List[str]
    compliance_level: ComplianceLevel
    audit_retention_days: int = 2555  # 7 years
    gdpr_config: Dict[str, Any] = None
    sox_config: Dict[str, Any] = None
    hipaa_config: Dict[str, Any] = None
    custom_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.gdpr_config is None:
            self.gdpr_config = {}
        if self.sox_config is None:
            self.sox_config = {}
        if self.hipaa_config is None:
            self.hipaa_config = {}
        if self.custom_config is None:
            self.custom_config = {}


class ComplianceFramework:
    """
    Unified compliance framework integrating multiple standards.
    
    Provides centralized compliance management for GDPR, SOX, HIPAA,
    and other regulatory requirements.
    """
    
    def __init__(self, standards: List[str] = None, config: Dict[str, Any] = None):
        """
        Initialize compliance framework.
        
        Args:
            standards: List of compliance standards to enable
            config: Framework configuration
        """
        self.standards = standards or ["GDPR", "SOX", "HIPAA"]
        self.config = config or {}
        
        # Initialize audit system
        self.audit_log = AuditLog(retention_days=self.config.get("audit_retention_days", 2555))
        self.auditor = ComplianceAuditor(self.audit_log)
        
        # Initialize compliance modules
        self.gdpr_compliance = None
        self.sox_compliance = None
        self.hipaa_compliance = None
        
        if "GDPR" in self.standards:
            self.gdpr_compliance = GDPRCompliance(self.config.get("gdpr", {}))
        
        if "SOX" in self.standards:
            self.sox_compliance = SOXCompliance(self.config.get("sox", {}))
        
        if "HIPAA" in self.standards:
            self.hipaa_compliance = HIPAACompliance(self.config.get("hipaa", {}))
        
        # Framework state
        self.lock = threading.Lock()
        self.compliance_policies: Dict[str, Dict[str, Any]] = {}
        self.violation_handlers: List[callable] = []
        
        # Initialize compliance policies
        self._initialize_policies()
        
        logger.info(f"Compliance Framework initialized with standards: {self.standards}")
    
    def _initialize_policies(self):
        """Initialize compliance policies."""
        # GDPR Policies
        if self.gdpr_compliance:
            self.compliance_policies["gdpr_data_processing"] = {
                "name": "GDPR Data Processing Policy",
                "description": "Ensures GDPR compliance for personal data processing",
                "rules": [
                    "Verify legal basis before processing personal data",
                    "Obtain explicit consent when required",
                    "Implement data minimization principles",
                    "Ensure data subject rights are respected"
                ],
                "enforcement": "mandatory"
            }
        
        # SOX Policies
        if self.sox_compliance:
            self.compliance_policies["sox_financial_controls"] = {
                "name": "SOX Financial Controls Policy",
                "description": "Ensures SOX compliance for financial data and processes",
                "rules": [
                    "Require approval for financial system changes",
                    "Maintain audit trails for financial transactions",
                    "Implement segregation of duties",
                    "Test internal controls regularly"
                ],
                "enforcement": "mandatory"
            }
        
        # HIPAA Policies
        if self.hipaa_compliance:
            self.compliance_policies["hipaa_phi_protection"] = {
                "name": "HIPAA PHI Protection Policy",
                "description": "Ensures HIPAA compliance for PHI handling",
                "rules": [
                    "Encrypt PHI at rest and in transit",
                    "Implement minimum necessary standard",
                    "Log all PHI access activities",
                    "Conduct regular risk assessments"
                ],
                "enforcement": "mandatory"
            }
    
    def process_data(self, data_type: str, data_value: Any, subject_id: str,
                    processing_context: Dict[str, Any]) -> str:
        """
        Process data with compliance checks across all enabled standards.
        
        Args:
            data_type: Type of data being processed
            data_value: Data value
            subject_id: Data subject identifier
            processing_context: Context information for compliance
            
        Returns:
            Processing ID
        """
        processing_id = str(uuid.uuid4())
        
        try:
            # Determine applicable compliance standards
            applicable_standards = self._determine_applicable_standards(data_type, processing_context)
            
            # GDPR Processing
            if "GDPR" in applicable_standards and self.gdpr_compliance:
                legal_basis = LegalBasis(processing_context.get("legal_basis", "consent"))
                purpose = ProcessingPurpose(processing_context.get("purpose", "operations"))
                
                self.gdpr_compliance.process_personal_data(
                    subject_id=subject_id,
                    data_type=data_type,
                    data_value=data_value,
                    legal_basis=legal_basis,
                    purpose=purpose
                )
            
            # SOX Processing
            if "SOX" in applicable_standards and self.sox_compliance:
                if "financial" in data_type.lower():
                    financial_type = FinancialDataType(processing_context.get("financial_type", "revenue"))
                    self.sox_compliance.financial_governance.classify_financial_data(
                        data_id=processing_id,
                        data_type=financial_type,
                        sensitivity="high"
                    )
            
            # HIPAA Processing
            if "HIPAA" in applicable_standards and self.hipaa_compliance:
                if "health" in data_type.lower() or "medical" in data_type.lower():
                    phi_type = PHIType(processing_context.get("phi_type", "medical_records"))
                    access_purpose = AccessPurpose(processing_context.get("access_purpose", "treatment"))
                    
                    self.hipaa_compliance.process_phi(
                        patient_id=subject_id,
                        phi_type=phi_type,
                        data_value=data_value,
                        user_id=processing_context.get("user_id", "system"),
                        purpose=access_purpose
                    )
            
            # Log compliance event
            self.audit_log.log_event(
                event_type=AuditEventType.DATA_MODIFICATION,
                severity=AuditSeverity.MEDIUM,
                user_id=processing_context.get("user_id", "system"),
                resource=f"data_{data_type}",
                action="process_data",
                outcome="success",
                details={
                    "processing_id": processing_id,
                    "data_type": data_type,
                    "subject_id": subject_id,
                    "applicable_standards": applicable_standards
                },
                compliance_standards=[ComplianceStandard(std.lower()) for std in applicable_standards]
            )
            
            logger.info(f"Data processing {processing_id} completed with compliance checks")
            return processing_id
            
        except Exception as e:
            # Log compliance violation
            self.audit_log.log_event(
                event_type=AuditEventType.COMPLIANCE_VIOLATION,
                severity=AuditSeverity.CRITICAL,
                user_id=processing_context.get("user_id", "system"),
                resource=f"data_{data_type}",
                action="process_data",
                outcome="failure",
                details={
                    "processing_id": processing_id,
                    "error": str(e),
                    "data_type": data_type,
                    "subject_id": subject_id
                }
            )
            
            # Notify violation handlers
            for handler in self.violation_handlers:
                try:
                    handler("data_processing_violation", str(e), processing_context)
                except Exception as handler_error:
                    logger.error(f"Error in violation handler: {handler_error}")
            
            raise
    
    def access_data(self, data_id: str, user_id: str, access_context: Dict[str, Any]) -> Any:
        """
        Access data with compliance checks.
        
        Args:
            data_id: Data identifier
            user_id: User requesting access
            access_context: Access context information
            
        Returns:
            Data value if access is authorized
        """
        try:
            # Determine data type and applicable standards
            data_type = access_context.get("data_type", "unknown")
            applicable_standards = self._determine_applicable_standards(data_type, access_context)
            
            # Check access permissions for each standard
            access_granted = True
            
            # GDPR Access Check
            if "GDPR" in applicable_standards and self.gdpr_compliance:
                # Check if user has valid consent or legal basis
                purpose = ProcessingPurpose(access_context.get("purpose", "operations"))
                subject_id = access_context.get("subject_id", "")
                
                if purpose == ProcessingPurpose.MARKETING:
                    if not self.gdpr_compliance.consent_manager.check_consent(subject_id, purpose):
                        access_granted = False
            
            # SOX Access Check
            if "SOX" in applicable_standards and self.sox_compliance:
                if "financial" in data_type.lower():
                    if not self.sox_compliance.financial_governance.check_access(user_id, data_id):
                        access_granted = False
            
            # HIPAA Access Check
            if "HIPAA" in applicable_standards and self.hipaa_compliance:
                if "health" in data_type.lower() or "medical" in data_type.lower():
                    access_purpose = AccessPurpose(access_context.get("access_purpose", "treatment"))
                    # Check if user is authorized for this purpose
                    if not self.hipaa_compliance.phi_protection._is_authorized(user_id, access_purpose):
                        access_granted = False
            
            # Log access attempt
            self.audit_log.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                severity=AuditSeverity.MEDIUM if access_granted else AuditSeverity.HIGH,
                user_id=user_id,
                resource=f"data_{data_id}",
                action="access_data",
                outcome="success" if access_granted else "failure",
                ip_address=access_context.get("ip_address", ""),
                user_agent=access_context.get("user_agent", ""),
                details={
                    "data_id": data_id,
                    "data_type": data_type,
                    "applicable_standards": applicable_standards,
                    "access_granted": access_granted
                },
                compliance_standards=[ComplianceStandard(std.lower()) for std in applicable_standards]
            )
            
            if not access_granted:
                raise PermissionError("Access denied due to compliance restrictions")
            
            # Return mock data (in real implementation, retrieve actual data)
            return f"[DATA_{data_id}]"
            
        except Exception as e:
            logger.error(f"Data access error for {data_id}: {e}")
            raise
    
    def _determine_applicable_standards(self, data_type: str, context: Dict[str, Any]) -> List[str]:
        """
        Determine which compliance standards apply to the data.
        
        Args:
            data_type: Type of data
            context: Processing context
            
        Returns:
            List of applicable standards
        """
        applicable = []
        
        # Check for personal data (GDPR)
        if any(keyword in data_type.lower() for keyword in ["personal", "user", "customer", "employee"]):
            if "GDPR" in self.standards:
                applicable.append("GDPR")
        
        # Check for financial data (SOX)
        if any(keyword in data_type.lower() for keyword in ["financial", "revenue", "expense", "transaction"]):
            if "SOX" in self.standards:
                applicable.append("SOX")
        
        # Check for health data (HIPAA)
        if any(keyword in data_type.lower() for keyword in ["health", "medical", "patient", "phi"]):
            if "HIPAA" in self.standards:
                applicable.append("HIPAA")
        
        # Check context-based indicators
        if context.get("contains_pii", False) and "GDPR" in self.standards:
            applicable.append("GDPR")
        
        if context.get("financial_impact", False) and "SOX" in self.standards:
            applicable.append("SOX")
        
        if context.get("contains_phi", False) and "HIPAA" in self.standards:
            applicable.append("HIPAA")
        
        return list(set(applicable))  # Remove duplicates
    
    def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance dashboard data.
        
        Returns:
            Dashboard data with compliance status across all standards
        """
        dashboard_data = {
            "compliance_overview": {
                "enabled_standards": self.standards,
                "last_updated": time.time(),
                "overall_status": "compliant"
            },
            "standards": {}
        }
        
        # GDPR Status
        if self.gdpr_compliance:
            gdpr_status = self.gdpr_compliance.get_compliance_status()
            dashboard_data["standards"]["GDPR"] = gdpr_status["gdpr_compliance"]
        
        # SOX Status
        if self.sox_compliance:
            sox_status = self.sox_compliance.get_compliance_status()
            dashboard_data["standards"]["SOX"] = sox_status["sox_compliance"]
        
        # HIPAA Status
        if self.hipaa_compliance:
            hipaa_status = self.hipaa_compliance.get_compliance_status()
            dashboard_data["standards"]["HIPAA"] = hipaa_status["hipaa_compliance"]
        
        # Audit Summary
        audit_summary = self.auditor.get_audit_summary()
        dashboard_data["audit"] = audit_summary["audit_summary"]
        
        return dashboard_data
    
    def run_compliance_assessment(self) -> Dict[str, str]:
        """
        Run comprehensive compliance assessment.
        
        Returns:
            Assessment results with report IDs
        """
        assessment_results = {}
        current_time = time.time()
        period_start = current_time - (30 * 24 * 3600)  # Last 30 days
        
        # Generate reports for each enabled standard
        if "GDPR" in self.standards:
            report_id = self.auditor.generate_compliance_report(
                ComplianceStandard.GDPR, period_start, current_time
            )
            assessment_results["GDPR"] = report_id
        
        if "SOX" in self.standards:
            report_id = self.auditor.generate_compliance_report(
                ComplianceStandard.SOX, period_start, current_time
            )
            assessment_results["SOX"] = report_id
        
        if "HIPAA" in self.standards:
            report_id = self.auditor.generate_compliance_report(
                ComplianceStandard.HIPAA, period_start, current_time
            )
            assessment_results["HIPAA"] = report_id
        
        logger.info(f"Compliance assessment completed: {assessment_results}")
        return assessment_results
    
    def add_violation_handler(self, handler: callable):
        """
        Add violation handler for compliance violations.
        
        Args:
            handler: Callable to handle violations
        """
        self.violation_handlers.append(handler)
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired data across all compliance standards.
        
        Returns:
            Cleanup statistics
        """
        cleanup_stats = {}
        
        if self.gdpr_compliance:
            cleanup_stats["GDPR"] = self.gdpr_compliance.cleanup_expired_data()
        
        if self.hipaa_compliance:
            cleanup_stats["HIPAA"] = self.hipaa_compliance.cleanup_expired_phi()
        
        # Clean up audit logs
        cleanup_stats["audit_logs"] = self.audit_log.cleanup_old_events()
        
        logger.info(f"Compliance cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def get_compliance_score(self) -> Dict[str, float]:
        """
        Calculate compliance scores for each standard.
        
        Returns:
            Compliance scores (0-100) for each standard
        """
        scores = {}
        
        # Generate recent reports to calculate scores
        current_time = time.time()
        period_start = current_time - (7 * 24 * 3600)  # Last 7 days
        
        for standard_name in self.standards:
            try:
                standard = ComplianceStandard(standard_name.lower())
                report_id = self.auditor.generate_compliance_report(standard, period_start, current_time)
                
                with self.auditor.lock:
                    report = self.auditor.compliance_reports.get(report_id)
                    if report:
                        scores[standard_name] = report.overall_score
                    else:
                        scores[standard_name] = 0.0
            except Exception as e:
                logger.error(f"Error calculating compliance score for {standard_name}: {e}")
                scores[standard_name] = 0.0
        
        return scores
