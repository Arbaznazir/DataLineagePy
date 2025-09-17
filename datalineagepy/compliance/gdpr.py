"""
GDPR Compliance Implementation
General Data Protection Regulation compliance features.
"""

import time
import uuid
import logging
import threading
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LegalBasis(Enum):
    """GDPR legal basis for processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataSubjectRightType(Enum):
    """Data subject rights under GDPR."""
    ACCESS = "access"                    # Right to access
    RECTIFICATION = "rectification"      # Right to rectification
    ERASURE = "erasure"                 # Right to erasure (right to be forgotten)
    RESTRICT = "restrict"               # Right to restrict processing
    PORTABILITY = "portability"         # Right to data portability
    OBJECT = "object"                   # Right to object
    AUTOMATED_DECISION = "automated_decision"  # Rights related to automated decision making


class ConsentStatus(Enum):
    """Consent status."""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class ProcessingPurpose(Enum):
    """Data processing purposes."""
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    LEGAL_COMPLIANCE = "legal_compliance"
    SECURITY = "security"
    RESEARCH = "research"
    CUSTOMER_SERVICE = "customer_service"


@dataclass
class PersonalData:
    """Personal data record."""
    data_id: str
    subject_id: str
    data_type: str
    data_value: Any
    legal_basis: LegalBasis
    processing_purpose: ProcessingPurpose
    collected_at: float
    retention_period: int  # days
    pseudonymized: bool = False
    encrypted: bool = False
    source_system: str = "datalineagepy"
    data_controller: str = ""
    data_processor: str = ""
    
    def __post_init__(self):
        if not self.data_id:
            self.data_id = str(uuid.uuid4())
    
    def is_expired(self) -> bool:
        """Check if data retention period has expired."""
        expiry_time = self.collected_at + (self.retention_period * 24 * 3600)
        return time.time() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "data_id": self.data_id,
            "subject_id": self.subject_id,
            "data_type": self.data_type,
            "data_value": self.data_value if not self.pseudonymized else "[PSEUDONYMIZED]",
            "legal_basis": self.legal_basis.value,
            "processing_purpose": self.processing_purpose.value,
            "collected_at": self.collected_at,
            "retention_period": self.retention_period,
            "pseudonymized": self.pseudonymized,
            "encrypted": self.encrypted,
            "source_system": self.source_system,
            "data_controller": self.data_controller,
            "data_processor": self.data_processor
        }


@dataclass
class ConsentRecord:
    """Consent record for GDPR compliance."""
    consent_id: str
    subject_id: str
    purpose: ProcessingPurpose
    status: ConsentStatus
    given_at: float
    withdrawn_at: Optional[float] = None
    expires_at: Optional[float] = None
    consent_text: str = ""
    version: str = "1.0"
    ip_address: str = ""
    user_agent: str = ""
    
    def __post_init__(self):
        if not self.consent_id:
            self.consent_id = str(uuid.uuid4())
    
    def is_valid(self) -> bool:
        """Check if consent is valid."""
        if self.status != ConsentStatus.GIVEN:
            return False
        
        if self.expires_at and time.time() > self.expires_at:
            return False
        
        return True
    
    def withdraw(self):
        """Withdraw consent."""
        self.status = ConsentStatus.WITHDRAWN
        self.withdrawn_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "consent_id": self.consent_id,
            "subject_id": self.subject_id,
            "purpose": self.purpose.value,
            "status": self.status.value,
            "given_at": self.given_at,
            "withdrawn_at": self.withdrawn_at,
            "expires_at": self.expires_at,
            "consent_text": self.consent_text,
            "version": self.version,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }


@dataclass
class DataSubjectRequest:
    """Data subject request."""
    request_id: str
    subject_id: str
    request_type: DataSubjectRightType
    requested_at: float
    processed_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    details: Dict[str, Any] = field(default_factory=dict)
    response_data: Optional[Any] = None
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
    
    def is_overdue(self, deadline_days: int = 30) -> bool:
        """Check if request is overdue."""
        deadline = self.requested_at + (deadline_days * 24 * 3600)
        return time.time() > deadline and not self.completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "subject_id": self.subject_id,
            "request_type": self.request_type.value,
            "requested_at": self.requested_at,
            "processed_at": self.processed_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "details": self.details,
            "response_data": self.response_data
        }


class ConsentManager:
    """
    GDPR Consent Management System.
    
    Manages consent collection, storage, and validation.
    """
    
    def __init__(self):
        """Initialize consent manager."""
        self.consents: Dict[str, ConsentRecord] = {}
        self.lock = threading.Lock()
        
        logger.info("GDPR Consent Manager initialized")
    
    def record_consent(self, subject_id: str, purpose: ProcessingPurpose,
                      consent_text: str, version: str = "1.0",
                      expires_days: int = 365, metadata: Dict[str, Any] = None) -> str:
        """
        Record consent from data subject.
        
        Args:
            subject_id: Data subject identifier
            purpose: Processing purpose
            consent_text: Consent text shown to user
            version: Consent version
            expires_days: Consent expiry in days
            metadata: Additional metadata (IP, user agent, etc.)
            
        Returns:
            Consent ID
        """
        metadata = metadata or {}
        
        consent = ConsentRecord(
            consent_id=str(uuid.uuid4()),
            subject_id=subject_id,
            purpose=purpose,
            status=ConsentStatus.GIVEN,
            given_at=time.time(),
            expires_at=time.time() + (expires_days * 24 * 3600),
            consent_text=consent_text,
            version=version,
            ip_address=metadata.get("ip_address", ""),
            user_agent=metadata.get("user_agent", "")
        )
        
        with self.lock:
            self.consents[consent.consent_id] = consent
        
        logger.info(f"Recorded consent {consent.consent_id} for subject {subject_id}")
        return consent.consent_id
    
    def withdraw_consent(self, subject_id: str, purpose: ProcessingPurpose) -> bool:
        """
        Withdraw consent for a specific purpose.
        
        Args:
            subject_id: Data subject identifier
            purpose: Processing purpose
            
        Returns:
            True if consent was withdrawn
        """
        with self.lock:
            for consent in self.consents.values():
                if (consent.subject_id == subject_id and 
                    consent.purpose == purpose and 
                    consent.status == ConsentStatus.GIVEN):
                    consent.withdraw()
                    logger.info(f"Withdrew consent {consent.consent_id} for subject {subject_id}")
                    return True
        
        return False
    
    def check_consent(self, subject_id: str, purpose: ProcessingPurpose) -> bool:
        """
        Check if valid consent exists for processing.
        
        Args:
            subject_id: Data subject identifier
            purpose: Processing purpose
            
        Returns:
            True if valid consent exists
        """
        with self.lock:
            for consent in self.consents.values():
                if (consent.subject_id == subject_id and 
                    consent.purpose == purpose and 
                    consent.is_valid()):
                    return True
        
        return False
    
    def get_subject_consents(self, subject_id: str) -> List[ConsentRecord]:
        """
        Get all consents for a data subject.
        
        Args:
            subject_id: Data subject identifier
            
        Returns:
            List of consent records
        """
        with self.lock:
            return [
                consent for consent in self.consents.values()
                if consent.subject_id == subject_id
            ]
    
    def cleanup_expired_consents(self) -> int:
        """
        Clean up expired consents.
        
        Returns:
            Number of expired consents removed
        """
        current_time = time.time()
        expired_count = 0
        
        with self.lock:
            expired_ids = []
            for consent_id, consent in self.consents.items():
                if consent.expires_at and current_time > consent.expires_at:
                    consent.status = ConsentStatus.EXPIRED
                    expired_ids.append(consent_id)
                    expired_count += 1
            
            # Remove expired consents
            for consent_id in expired_ids:
                del self.consents[consent_id]
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired consents")
        
        return expired_count


class DataSubjectRights:
    """
    GDPR Data Subject Rights Implementation.
    
    Handles data subject requests and rights fulfillment.
    """
    
    def __init__(self, data_store=None):
        """
        Initialize data subject rights handler.
        
        Args:
            data_store: Data storage backend
        """
        self.data_store = data_store or {}
        self.requests: Dict[str, DataSubjectRequest] = {}
        self.personal_data: Dict[str, PersonalData] = {}
        self.lock = threading.Lock()
        
        logger.info("GDPR Data Subject Rights handler initialized")
    
    def submit_request(self, subject_id: str, request_type: DataSubjectRightType,
                      details: Dict[str, Any] = None) -> str:
        """
        Submit a data subject request.
        
        Args:
            subject_id: Data subject identifier
            request_type: Type of request
            details: Additional request details
            
        Returns:
            Request ID
        """
        request = DataSubjectRequest(
            request_id=str(uuid.uuid4()),
            subject_id=subject_id,
            request_type=request_type,
            requested_at=time.time(),
            details=details or {}
        )
        
        with self.lock:
            self.requests[request.request_id] = request
        
        logger.info(f"Submitted {request_type.value} request {request.request_id} for subject {subject_id}")
        return request.request_id
    
    def process_access_request(self, request_id: str) -> Dict[str, Any]:
        """
        Process right to access request.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Subject's personal data
        """
        with self.lock:
            request = self.requests.get(request_id)
            if not request or request.request_type != DataSubjectRightType.ACCESS:
                raise ValueError("Invalid access request")
            
            # Collect all personal data for subject
            subject_data = []
            for data in self.personal_data.values():
                if data.subject_id == request.subject_id:
                    subject_data.append(data.to_dict())
            
            # Update request
            request.processed_at = time.time()
            request.completed_at = time.time()
            request.status = "completed"
            request.response_data = {
                "subject_id": request.subject_id,
                "data_records": subject_data,
                "total_records": len(subject_data),
                "generated_at": time.time()
            }
        
        logger.info(f"Processed access request {request_id}")
        return request.response_data
    
    def process_erasure_request(self, request_id: str) -> bool:
        """
        Process right to erasure (right to be forgotten) request.
        
        Args:
            request_id: Request identifier
            
        Returns:
            True if data was erased
        """
        with self.lock:
            request = self.requests.get(request_id)
            if not request or request.request_type != DataSubjectRightType.ERASURE:
                raise ValueError("Invalid erasure request")
            
            # Find and remove personal data
            subject_id = request.subject_id
            data_ids_to_remove = []
            
            for data_id, data in self.personal_data.items():
                if data.subject_id == subject_id:
                    # Check if erasure is allowed (legal obligations, etc.)
                    if self._can_erase_data(data):
                        data_ids_to_remove.append(data_id)
            
            # Remove data
            for data_id in data_ids_to_remove:
                del self.personal_data[data_id]
            
            # Update request
            request.processed_at = time.time()
            request.completed_at = time.time()
            request.status = "completed"
            request.response_data = {
                "erased_records": len(data_ids_to_remove),
                "subject_id": subject_id
            }
        
        logger.info(f"Processed erasure request {request_id}, erased {len(data_ids_to_remove)} records")
        return len(data_ids_to_remove) > 0
    
    def process_portability_request(self, request_id: str) -> Dict[str, Any]:
        """
        Process right to data portability request.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Portable data format
        """
        with self.lock:
            request = self.requests.get(request_id)
            if not request or request.request_type != DataSubjectRightType.PORTABILITY:
                raise ValueError("Invalid portability request")
            
            # Collect portable data (consent-based processing only)
            portable_data = []
            for data in self.personal_data.values():
                if (data.subject_id == request.subject_id and 
                    data.legal_basis == LegalBasis.CONSENT):
                    portable_data.append(data.to_dict())
            
            # Create portable format
            export_data = {
                "subject_id": request.subject_id,
                "export_format": "JSON",
                "export_date": datetime.now().isoformat(),
                "data_controller": "DataLineagePy",
                "data": portable_data
            }
            
            # Update request
            request.processed_at = time.time()
            request.completed_at = time.time()
            request.status = "completed"
            request.response_data = export_data
        
        logger.info(f"Processed portability request {request_id}")
        return export_data
    
    def _can_erase_data(self, data: PersonalData) -> bool:
        """
        Check if data can be erased based on legal basis.
        
        Args:
            data: Personal data record
            
        Returns:
            True if data can be erased
        """
        # Cannot erase data required for legal obligations
        if data.legal_basis == LegalBasis.LEGAL_OBLIGATION:
            return False
        
        # Cannot erase data for vital interests
        if data.legal_basis == LegalBasis.VITAL_INTERESTS:
            return False
        
        # Check retention requirements
        if not data.is_expired():
            # Data still within retention period
            return data.legal_basis == LegalBasis.CONSENT
        
        return True
    
    def add_personal_data(self, data: PersonalData):
        """
        Add personal data record.
        
        Args:
            data: Personal data record
        """
        with self.lock:
            self.personal_data[data.data_id] = data
        
        logger.debug(f"Added personal data record {data.data_id}")
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get request status.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Request status information
        """
        with self.lock:
            request = self.requests.get(request_id)
            return request.to_dict() if request else None


@dataclass
class DataProcessingRecord:
    """Record of Processing Activities (ROPA) under GDPR Article 30."""
    record_id: str
    controller_name: str
    controller_contact: str
    processing_purposes: List[ProcessingPurpose]
    data_categories: List[str]
    data_subjects: List[str]
    recipients: List[str]
    third_country_transfers: List[str]
    retention_periods: Dict[str, int]
    security_measures: List[str]
    created_at: float
    updated_at: float
    
    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "record_id": self.record_id,
            "controller_name": self.controller_name,
            "controller_contact": self.controller_contact,
            "processing_purposes": [p.value for p in self.processing_purposes],
            "data_categories": self.data_categories,
            "data_subjects": self.data_subjects,
            "recipients": self.recipients,
            "third_country_transfers": self.third_country_transfers,
            "retention_periods": self.retention_periods,
            "security_measures": self.security_measures,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class GDPRCompliance:
    """
    Main GDPR Compliance Manager.
    
    Coordinates all GDPR compliance activities and requirements.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GDPR compliance manager.
        
        Args:
            config: GDPR configuration
        """
        self.config = config or {}
        self.consent_manager = ConsentManager()
        self.data_subject_rights = DataSubjectRights()
        self.processing_records: Dict[str, DataProcessingRecord] = {}
        self.breach_notifications: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
        # Configuration
        self.data_retention_days = self.config.get("data_retention_days", 2555)
        self.consent_expiry_days = self.config.get("consent_expiry_days", 365)
        self.breach_notification_hours = self.config.get("breach_notification_hours", 72)
        
        logger.info("GDPR Compliance Manager initialized")
    
    def process_personal_data(self, subject_id: str, data_type: str, data_value: Any,
                            legal_basis: LegalBasis, purpose: ProcessingPurpose,
                            retention_days: int = None) -> str:
        """
        Process personal data with GDPR compliance.
        
        Args:
            subject_id: Data subject identifier
            data_type: Type of personal data
            data_value: Data value
            legal_basis: Legal basis for processing
            purpose: Processing purpose
            retention_days: Data retention period
            
        Returns:
            Data ID
        """
        # Check consent if required
        if legal_basis == LegalBasis.CONSENT:
            if not self.consent_manager.check_consent(subject_id, purpose):
                raise ValueError(f"No valid consent for {purpose.value} processing")
        
        # Create personal data record
        personal_data = PersonalData(
            data_id=str(uuid.uuid4()),
            subject_id=subject_id,
            data_type=data_type,
            data_value=data_value,
            legal_basis=legal_basis,
            processing_purpose=purpose,
            collected_at=time.time(),
            retention_period=retention_days or self.data_retention_days,
            pseudonymized=self.config.get("pseudonymization_enabled", True),
            encrypted=self.config.get("encryption_required", True)
        )
        
        # Add to data subject rights handler
        self.data_subject_rights.add_personal_data(personal_data)
        
        logger.info(f"Processed personal data {personal_data.data_id} for subject {subject_id}")
        return personal_data.data_id
    
    def handle_data_breach(self, breach_details: Dict[str, Any]) -> str:
        """
        Handle data breach notification requirements.
        
        Args:
            breach_details: Breach information
            
        Returns:
            Breach notification ID
        """
        breach_id = str(uuid.uuid4())
        breach_time = time.time()
        
        breach_record = {
            "breach_id": breach_id,
            "reported_at": breach_time,
            "details": breach_details,
            "notification_deadline": breach_time + (self.breach_notification_hours * 3600),
            "authority_notified": False,
            "subjects_notified": False,
            "high_risk": breach_details.get("high_risk", False)
        }
        
        with self.lock:
            self.breach_notifications.append(breach_record)
        
        logger.critical(f"Data breach {breach_id} recorded - notification required within {self.breach_notification_hours} hours")
        return breach_id
    
    def create_processing_record(self, controller_name: str, controller_contact: str,
                               purposes: List[ProcessingPurpose], data_categories: List[str],
                               data_subjects: List[str]) -> str:
        """
        Create Record of Processing Activities (ROPA).
        
        Args:
            controller_name: Data controller name
            controller_contact: Controller contact information
            purposes: Processing purposes
            data_categories: Categories of personal data
            data_subjects: Categories of data subjects
            
        Returns:
            Record ID
        """
        record = DataProcessingRecord(
            record_id=str(uuid.uuid4()),
            controller_name=controller_name,
            controller_contact=controller_contact,
            processing_purposes=purposes,
            data_categories=data_categories,
            data_subjects=data_subjects,
            recipients=[],
            third_country_transfers=[],
            retention_periods={},
            security_measures=[],
            created_at=time.time(),
            updated_at=time.time()
        )
        
        with self.lock:
            self.processing_records[record.record_id] = record
        
        logger.info(f"Created processing record {record.record_id}")
        return record.record_id
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get GDPR compliance status.
        
        Returns:
            Compliance status report
        """
        with self.lock:
            active_consents = sum(1 for c in self.consent_manager.consents.values() if c.is_valid())
            pending_requests = sum(1 for r in self.data_subject_rights.requests.values() if r.status == "pending")
            overdue_requests = sum(1 for r in self.data_subject_rights.requests.values() if r.is_overdue())
            
            return {
                "gdpr_compliance": {
                    "consent_management": {
                        "total_consents": len(self.consent_manager.consents),
                        "active_consents": active_consents,
                        "expired_consents": len(self.consent_manager.consents) - active_consents
                    },
                    "data_subject_rights": {
                        "total_requests": len(self.data_subject_rights.requests),
                        "pending_requests": pending_requests,
                        "overdue_requests": overdue_requests
                    },
                    "processing_records": len(self.processing_records),
                    "breach_notifications": len(self.breach_notifications),
                    "personal_data_records": len(self.data_subject_rights.personal_data)
                }
            }
    
    def cleanup_expired_data(self) -> int:
        """
        Clean up expired personal data.
        
        Returns:
            Number of records cleaned up
        """
        expired_count = 0
        current_time = time.time()
        
        with self.lock:
            expired_ids = []
            for data_id, data in self.data_subject_rights.personal_data.items():
                if data.is_expired():
                    expired_ids.append(data_id)
                    expired_count += 1
            
            # Remove expired data
            for data_id in expired_ids:
                del self.data_subject_rights.personal_data[data_id]
        
        # Also cleanup expired consents
        expired_count += self.consent_manager.cleanup_expired_consents()
        
        if expired_count > 0:
            logger.info(f"GDPR cleanup: removed {expired_count} expired records")
        
        return expired_count


# Additional GDPR classes for completeness
class PrivacyImpactAssessment:
    """Privacy Impact Assessment (PIA) for high-risk processing."""
    
    def __init__(self, processing_description: str):
        self.pia_id = str(uuid.uuid4())
        self.processing_description = processing_description
        self.created_at = time.time()
        self.risk_level = "unknown"
        self.mitigation_measures = []
    
    def assess_risk(self) -> str:
        """Assess privacy risk level."""
        # Simplified risk assessment
        high_risk_indicators = [
            "automated decision making",
            "profiling",
            "large scale",
            "sensitive data",
            "vulnerable individuals",
            "innovative technology"
        ]
        
        description_lower = self.processing_description.lower()
        risk_score = sum(1 for indicator in high_risk_indicators if indicator in description_lower)
        
        if risk_score >= 3:
            self.risk_level = "high"
        elif risk_score >= 1:
            self.risk_level = "medium"
        else:
            self.risk_level = "low"
        
        return self.risk_level


class DataProtectionOfficer:
    """Data Protection Officer (DPO) management."""
    
    def __init__(self, name: str, contact: str):
        self.name = name
        self.contact = contact
        self.appointed_at = time.time()
        self.responsibilities = [
            "Monitor GDPR compliance",
            "Conduct privacy impact assessments",
            "Serve as contact point for data subjects",
            "Cooperate with supervisory authorities",
            "Provide GDPR training and awareness"
        ]
    
    def get_contact_info(self) -> Dict[str, str]:
        """Get DPO contact information."""
        return {
            "name": self.name,
            "contact": self.contact,
            "role": "Data Protection Officer"
        }
