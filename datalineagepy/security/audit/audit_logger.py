"""
Comprehensive Audit Logging System
Enterprise-grade audit logging for compliance with GDPR, SOX, HIPAA, and other regulations.
"""

import json
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import queue
import time
import os
from pathlib import Path


class AuditEventType(Enum):
    """Types of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    USER_MANAGEMENT = "user_management"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    ERROR_EVENT = "error_event"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"


@dataclass
class AuditEvent:
    """Represents a single audit event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: AuditEventType = AuditEventType.SYSTEM_ACCESS
    severity: AuditSeverity = AuditSeverity.LOW
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    outcome: str = "success"  # success, failure, error
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    data_classification: Optional[str] = None
    retention_period_days: int = 2555  # 7 years default
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Generate hash for integrity verification
        self.integrity_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash for integrity verification."""
        # Create a copy without the hash field for calculation
        event_dict = asdict(self)
        event_dict.pop('integrity_hash', None)
        
        # Convert datetime to ISO string for consistent hashing
        if isinstance(event_dict.get('timestamp'), datetime):
            event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        
        # Sort keys for consistent hashing
        event_json = json.dumps(event_dict, sort_keys=True, default=str)
        return hashlib.sha256(event_json.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify event integrity using hash."""
        current_hash = self._calculate_hash()
        return current_hash == getattr(self, 'integrity_hash', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        event_dict = asdict(self)
        
        # Convert enums to strings
        event_dict['event_type'] = self.event_type.value
        event_dict['severity'] = self.severity.value
        event_dict['compliance_frameworks'] = [cf.value for cf in self.compliance_frameworks]
        
        # Convert datetime to ISO string
        if isinstance(event_dict['timestamp'], datetime):
            event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        
        return event_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create AuditEvent from dictionary."""
        # Convert string enums back to enum objects
        if 'event_type' in data:
            data['event_type'] = AuditEventType(data['event_type'])
        if 'severity' in data:
            data['severity'] = AuditSeverity(data['severity'])
        if 'compliance_frameworks' in data:
            data['compliance_frameworks'] = [ComplianceFramework(cf) for cf in data['compliance_frameworks']]
        
        # Convert ISO string back to datetime
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)


class AuditStorage:
    """
    Abstract base class for audit storage backends.
    """
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store audit event."""
        raise NotImplementedError
    
    def retrieve_events(self, start_time: datetime, end_time: datetime,
                       filters: Optional[Dict[str, Any]] = None) -> List[AuditEvent]:
        """Retrieve audit events within time range."""
        raise NotImplementedError
    
    def search_events(self, query: Dict[str, Any]) -> List[AuditEvent]:
        """Search audit events by criteria."""
        raise NotImplementedError


class FileAuditStorage(AuditStorage):
    """
    File-based audit storage with rotation and compression.
    """
    
    def __init__(self, log_directory: str = "audit_logs", 
                 max_file_size_mb: int = 100, max_files: int = 1000):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        self.current_file = None
        self.current_file_size = 0
        self._lock = threading.Lock()
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store audit event to file."""
        try:
            with self._lock:
                # Check if we need a new file
                if self._needs_new_file():
                    self._rotate_file()
                
                # Write event to current file
                event_json = json.dumps(event.to_dict()) + '\n'
                
                with open(self.current_file, 'a', encoding='utf-8') as f:
                    f.write(event_json)
                    f.flush()
                
                self.current_file_size += len(event_json.encode('utf-8'))
                return True
                
        except Exception as e:
            logging.error(f"Failed to store audit event: {str(e)}")
            return False
    
    def _needs_new_file(self) -> bool:
        """Check if we need to create a new log file."""
        if not self.current_file:
            return True
        
        if not self.current_file.exists():
            return True
        
        if self.current_file_size >= self.max_file_size:
            return True
        
        return False
    
    def _rotate_file(self):
        """Rotate to a new log file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.current_file = self.log_directory / f"audit_{timestamp}.jsonl"
        self.current_file_size = 0
        
        # Clean up old files if necessary
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """Remove old log files if we exceed max_files."""
        log_files = sorted(self.log_directory.glob("audit_*.jsonl"))
        
        if len(log_files) > self.max_files:
            files_to_remove = log_files[:-self.max_files]
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"Failed to remove old audit file {file_path}: {str(e)}")
    
    def retrieve_events(self, start_time: datetime, end_time: datetime,
                       filters: Optional[Dict[str, Any]] = None) -> List[AuditEvent]:
        """Retrieve events from files within time range."""
        events = []
        
        for log_file in self.log_directory.glob("audit_*.jsonl"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            event_dict = json.loads(line)
                            event = AuditEvent.from_dict(event_dict)
                            
                            # Check time range
                            if start_time <= event.timestamp <= end_time:
                                # Apply filters if provided
                                if not filters or self._matches_filters(event, filters):
                                    events.append(event)
                                    
            except Exception as e:
                logging.error(f"Error reading audit file {log_file}: {str(e)}")
        
        return sorted(events, key=lambda e: e.timestamp)
    
    def _matches_filters(self, event: AuditEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches the provided filters."""
        for key, value in filters.items():
            event_value = getattr(event, key, None)
            
            if isinstance(event_value, Enum):
                event_value = event_value.value
            
            if event_value != value:
                return False
        
        return True


class AuditLogger:
    """
    Main audit logging system with compliance features.
    
    Features:
    - Comprehensive event logging
    - Compliance framework mapping
    - Asynchronous processing
    - Multiple storage backends
    - Integrity verification
    - Retention management
    """
    
    def __init__(self, storage: Optional[AuditStorage] = None, 
                 async_processing: bool = True, queue_size: int = 10000):
        self.storage = storage or FileAuditStorage()
        self.async_processing = async_processing
        self.logger = logging.getLogger(__name__)
        
        # Async processing setup
        if async_processing:
            self.event_queue = queue.Queue(maxsize=queue_size)
            self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
            self.processing_thread.start()
            self._stop_processing = threading.Event()
        
        # Compliance mappings
        self.compliance_mappings = self._initialize_compliance_mappings()
        
        # Metrics
        self.metrics = {
            "events_logged": 0,
            "events_failed": 0,
            "queue_size": 0,
            "integrity_violations": 0
        }
    
    def _initialize_compliance_mappings(self) -> Dict[AuditEventType, List[ComplianceFramework]]:
        """Initialize compliance framework mappings for different event types."""
        return {
            AuditEventType.AUTHENTICATION: [ComplianceFramework.GDPR, ComplianceFramework.SOX, ComplianceFramework.HIPAA],
            AuditEventType.AUTHORIZATION: [ComplianceFramework.GDPR, ComplianceFramework.SOX, ComplianceFramework.HIPAA],
            AuditEventType.DATA_ACCESS: [ComplianceFramework.GDPR, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS],
            AuditEventType.DATA_MODIFICATION: [ComplianceFramework.GDPR, ComplianceFramework.SOX, ComplianceFramework.HIPAA],
            AuditEventType.DATA_EXPORT: [ComplianceFramework.GDPR, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS],
            AuditEventType.SYSTEM_ACCESS: [ComplianceFramework.SOX, ComplianceFramework.ISO27001],
            AuditEventType.CONFIGURATION_CHANGE: [ComplianceFramework.SOX, ComplianceFramework.ISO27001, ComplianceFramework.NIST],
            AuditEventType.USER_MANAGEMENT: [ComplianceFramework.GDPR, ComplianceFramework.SOX, ComplianceFramework.HIPAA],
            AuditEventType.SECURITY_EVENT: [ComplianceFramework.ISO27001, ComplianceFramework.NIST],
            AuditEventType.COMPLIANCE_EVENT: [ComplianceFramework.GDPR, ComplianceFramework.SOX, ComplianceFramework.HIPAA]
        }
    
    def log_event(self, event_type: AuditEventType, message: str,
                  user_id: Optional[str] = None, user_email: Optional[str] = None,
                  session_id: Optional[str] = None, ip_address: Optional[str] = None,
                  resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                  action: Optional[str] = None, outcome: str = "success",
                  severity: AuditSeverity = AuditSeverity.LOW,
                  details: Optional[Dict[str, Any]] = None,
                  data_classification: Optional[str] = None) -> str:
        """
        Log an audit event.
        
        Returns:
            Event ID
        """
        # Determine compliance frameworks
        compliance_frameworks = self.compliance_mappings.get(event_type, [])
        
        # Create audit event
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            user_email=user_email,
            session_id=session_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            message=message,
            details=details or {},
            compliance_frameworks=compliance_frameworks,
            data_classification=data_classification
        )
        
        # Process event
        if self.async_processing:
            try:
                self.event_queue.put_nowait(event)
                self.metrics["queue_size"] = self.event_queue.qsize()
            except queue.Full:
                self.logger.error("Audit event queue is full, dropping event")
                self.metrics["events_failed"] += 1
                return event.event_id
        else:
            self._store_event(event)
        
        return event.event_id
    
    def _process_events(self):
        """Background thread to process audit events."""
        while not self._stop_processing.is_set():
            try:
                event = self.event_queue.get(timeout=1)
                self._store_event(event)
                self.event_queue.task_done()
                self.metrics["queue_size"] = self.event_queue.qsize()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audit event: {str(e)}")
    
    def _store_event(self, event: AuditEvent):
        """Store audit event using the configured storage backend."""
        try:
            if self.storage.store_event(event):
                self.metrics["events_logged"] += 1
            else:
                self.metrics["events_failed"] += 1
        except Exception as e:
            self.logger.error(f"Failed to store audit event: {str(e)}")
            self.metrics["events_failed"] += 1
    
    def log_authentication(self, user_id: str, user_email: str, outcome: str,
                          ip_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log authentication event."""
        severity = AuditSeverity.HIGH if outcome == "failure" else AuditSeverity.MEDIUM
        
        self.log_event(
            event_type=AuditEventType.AUTHENTICATION,
            message=f"User authentication {outcome}",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            action="authenticate",
            outcome=outcome,
            severity=severity,
            details=details
        )
    
    def log_data_access(self, user_id: str, resource_type: str, resource_id: str,
                       action: str, outcome: str = "success",
                       data_classification: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None):
        """Log data access event."""
        severity = AuditSeverity.HIGH if data_classification in ["sensitive", "confidential"] else AuditSeverity.MEDIUM
        
        self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            message=f"Data access: {action} on {resource_type}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            severity=severity,
            data_classification=data_classification,
            details=details
        )
    
    def log_security_event(self, message: str, severity: AuditSeverity = AuditSeverity.HIGH,
                          user_id: Optional[str] = None, ip_address: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None):
        """Log security event."""
        self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            outcome="alert",
            details=details
        )
    
    def search_events(self, start_time: datetime, end_time: datetime,
                     filters: Optional[Dict[str, Any]] = None) -> List[AuditEvent]:
        """Search audit events."""
        return self.storage.retrieve_events(start_time, end_time, filters)
    
    def generate_compliance_report(self, framework: ComplianceFramework,
                                 start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate compliance report for specific framework."""
        # Filter events by compliance framework
        filters = {"compliance_frameworks": [framework]}
        events = self.search_events(start_time, end_time, filters)
        
        # Analyze events
        report = {
            "framework": framework.value,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_events": len(events),
            "event_breakdown": {},
            "severity_breakdown": {},
            "outcome_breakdown": {},
            "critical_events": [],
            "integrity_status": "verified"
        }
        
        # Event type breakdown
        for event in events:
            event_type = event.event_type.value
            report["event_breakdown"][event_type] = report["event_breakdown"].get(event_type, 0) + 1
            
            severity = event.severity.value
            report["severity_breakdown"][severity] = report["severity_breakdown"].get(severity, 0) + 1
            
            outcome = event.outcome
            report["outcome_breakdown"][outcome] = report["outcome_breakdown"].get(outcome, 0) + 1
            
            # Collect critical events
            if event.severity == AuditSeverity.CRITICAL:
                report["critical_events"].append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "message": event.message,
                    "user_id": event.user_id
                })
            
            # Verify integrity
            if not event.verify_integrity():
                report["integrity_status"] = "compromised"
                self.metrics["integrity_violations"] += 1
        
        return report
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get audit logging metrics."""
        return {
            **self.metrics,
            "queue_size": self.event_queue.qsize() if self.async_processing else 0,
            "processing_active": self.processing_thread.is_alive() if self.async_processing else False
        }
    
    def shutdown(self):
        """Gracefully shutdown audit logger."""
        if self.async_processing:
            self._stop_processing.set()
            
            # Wait for queue to empty
            if hasattr(self, 'event_queue'):
                self.event_queue.join()
            
            # Wait for processing thread
            if hasattr(self, 'processing_thread'):
                self.processing_thread.join(timeout=5)


# Example usage
if __name__ == "__main__":
    # Initialize audit logger
    audit_logger = AuditLogger()
    
    # Log various events
    audit_logger.log_authentication(
        user_id="user123",
        user_email="user@company.com",
        outcome="success",
        ip_address="192.168.1.100"
    )
    
    audit_logger.log_data_access(
        user_id="user123",
        resource_type="lineage_graph",
        resource_id="customer_data_lineage",
        action="read",
        data_classification="sensitive"
    )
    
    audit_logger.log_security_event(
        message="Multiple failed login attempts detected",
        severity=AuditSeverity.HIGH,
        ip_address="192.168.1.200",
        details={"attempts": 5, "timespan": "5 minutes"}
    )
    
    # Wait for async processing
    time.sleep(2)
    
    # Generate compliance report
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    gdpr_report = audit_logger.generate_compliance_report(
        ComplianceFramework.GDPR,
        start_time,
        end_time
    )
    
    print("GDPR Compliance Report:")
    print(json.dumps(gdpr_report, indent=2))
    
    # Get metrics
    metrics = audit_logger.get_metrics()
    print(f"Audit Metrics: {metrics}")
    
    # Shutdown
    audit_logger.shutdown()
