"""
SOX Compliance Implementation
Sarbanes-Oxley Act compliance features for financial data governance.
"""

import time
import uuid
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ControlType(Enum):
    """SOX control types."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class ControlFrequency(Enum):
    """Control testing frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class FinancialDataType(Enum):
    """Financial data categories."""
    REVENUE = "revenue"
    EXPENSES = "expenses"
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    EQUITY = "equity"
    CASH_FLOW = "cash_flow"
    JOURNAL_ENTRIES = "journal_entries"


@dataclass
class InternalControl:
    """SOX internal control definition."""
    control_id: str
    name: str
    description: str
    control_type: ControlType
    frequency: ControlFrequency
    owner: str
    financial_assertion: str
    risk_rating: str
    testing_procedures: List[str]
    created_at: float
    last_tested: Optional[float] = None
    test_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.control_id:
            self.control_id = str(uuid.uuid4())
        if self.test_results is None:
            self.test_results = []


@dataclass
class AuditTrailEntry:
    """SOX audit trail entry."""
    entry_id: str
    user_id: str
    action: str
    resource: str
    timestamp: float
    ip_address: str
    details: Dict[str, Any]
    financial_impact: bool = False
    
    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = str(uuid.uuid4())


class FinancialDataGovernance:
    """Financial data governance for SOX compliance."""
    
    def __init__(self):
        self.financial_data: Dict[str, Dict[str, Any]] = {}
        self.access_controls: Dict[str, List[str]] = {}
        self.lock = threading.Lock()
    
    def classify_financial_data(self, data_id: str, data_type: FinancialDataType,
                              sensitivity: str, retention_years: int = 7) -> bool:
        """Classify financial data for SOX compliance."""
        with self.lock:
            self.financial_data[data_id] = {
                "data_type": data_type.value,
                "sensitivity": sensitivity,
                "retention_years": retention_years,
                "classified_at": time.time(),
                "sox_relevant": True
            }
        return True
    
    def set_access_controls(self, data_id: str, authorized_users: List[str]) -> bool:
        """Set access controls for financial data."""
        with self.lock:
            self.access_controls[data_id] = authorized_users
        return True
    
    def check_access(self, user_id: str, data_id: str) -> bool:
        """Check if user has access to financial data."""
        with self.lock:
            authorized_users = self.access_controls.get(data_id, [])
            return user_id in authorized_users


class AuditTrail:
    """SOX audit trail management."""
    
    def __init__(self, retention_years: int = 7):
        self.entries: List[AuditTrailEntry] = []
        self.retention_years = retention_years
        self.lock = threading.Lock()
    
    def log_activity(self, user_id: str, action: str, resource: str,
                    ip_address: str = "", details: Dict[str, Any] = None,
                    financial_impact: bool = False) -> str:
        """Log activity for audit trail."""
        entry = AuditTrailEntry(
            entry_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=time.time(),
            ip_address=ip_address,
            details=details or {},
            financial_impact=financial_impact
        )
        
        with self.lock:
            self.entries.append(entry)
        
        logger.info(f"Audit trail entry {entry.entry_id} logged")
        return entry.entry_id
    
    def search_entries(self, user_id: str = None, action: str = None,
                      start_time: float = None, end_time: float = None) -> List[AuditTrailEntry]:
        """Search audit trail entries."""
        with self.lock:
            results = self.entries.copy()
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if action:
            results = [e for e in results if e.action == action]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        return results


class ChangeManagement:
    """SOX change management controls."""
    
    def __init__(self):
        self.change_requests: Dict[str, Dict[str, Any]] = {}
        self.approvers: List[str] = []
        self.lock = threading.Lock()
    
    def submit_change_request(self, requester: str, description: str,
                            financial_impact: bool = False) -> str:
        """Submit change request for approval."""
        change_id = str(uuid.uuid4())
        
        with self.lock:
            self.change_requests[change_id] = {
                "requester": requester,
                "description": description,
                "financial_impact": financial_impact,
                "status": "pending",
                "submitted_at": time.time(),
                "approvals": [],
                "implemented_at": None
            }
        
        logger.info(f"Change request {change_id} submitted")
        return change_id
    
    def approve_change(self, change_id: str, approver: str) -> bool:
        """Approve change request."""
        with self.lock:
            if change_id not in self.change_requests:
                return False
            
            change = self.change_requests[change_id]
            if approver not in change["approvals"]:
                change["approvals"].append(approver)
            
            # Check if sufficient approvals
            if len(change["approvals"]) >= 2:  # Require 2 approvals
                change["status"] = "approved"
        
        return True


class SOXCompliance:
    """Main SOX compliance manager."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.financial_governance = FinancialDataGovernance()
        self.audit_trail = AuditTrail()
        self.change_management = ChangeManagement()
        self.internal_controls: Dict[str, InternalControl] = {}
        self.lock = threading.Lock()
        
        logger.info("SOX Compliance Manager initialized")
    
    def add_internal_control(self, name: str, description: str,
                           control_type: ControlType, frequency: ControlFrequency,
                           owner: str, financial_assertion: str) -> str:
        """Add internal control."""
        control = InternalControl(
            control_id=str(uuid.uuid4()),
            name=name,
            description=description,
            control_type=control_type,
            frequency=frequency,
            owner=owner,
            financial_assertion=financial_assertion,
            risk_rating="medium",
            testing_procedures=[],
            created_at=time.time()
        )
        
        with self.lock:
            self.internal_controls[control.control_id] = control
        
        return control.control_id
    
    def test_control(self, control_id: str, tester: str, results: Dict[str, Any]) -> bool:
        """Test internal control effectiveness."""
        with self.lock:
            if control_id not in self.internal_controls:
                return False
            
            control = self.internal_controls[control_id]
            control.last_tested = time.time()
            control.test_results.append({
                "tester": tester,
                "tested_at": time.time(),
                "results": results,
                "effective": results.get("effective", True)
            })
        
        # Log audit trail
        self.audit_trail.log_activity(
            user_id=tester,
            action="control_test",
            resource=f"control_{control_id}",
            details=results,
            financial_impact=True
        )
        
        return True
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get SOX compliance status."""
        with self.lock:
            total_controls = len(self.internal_controls)
            tested_controls = sum(1 for c in self.internal_controls.values() if c.last_tested)
            
            return {
                "sox_compliance": {
                    "internal_controls": {
                        "total": total_controls,
                        "tested": tested_controls,
                        "testing_coverage": (tested_controls / total_controls * 100) if total_controls > 0 else 0
                    },
                    "audit_trail": {
                        "total_entries": len(self.audit_trail.entries),
                        "financial_impact_entries": sum(1 for e in self.audit_trail.entries if e.financial_impact)
                    },
                    "change_management": {
                        "pending_changes": sum(1 for c in self.change_management.change_requests.values() if c["status"] == "pending"),
                        "approved_changes": sum(1 for c in self.change_management.change_requests.values() if c["status"] == "approved")
                    },
                    "financial_data": {
                        "classified_datasets": len(self.financial_governance.financial_data),
                        "access_controlled_datasets": len(self.financial_governance.access_controls)
                    }
                }
            }


# Additional SOX classes
class AccessControls:
    """SOX access control management."""
    
    def __init__(self):
        self.user_roles: Dict[str, List[str]] = {}
        self.role_permissions: Dict[str, List[str]] = {}
        self.lock = threading.Lock()
    
    def assign_role(self, user_id: str, role: str) -> bool:
        """Assign role to user."""
        with self.lock:
            if user_id not in self.user_roles:
                self.user_roles[user_id] = []
            if role not in self.user_roles[user_id]:
                self.user_roles[user_id].append(role)
        return True
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission."""
        with self.lock:
            user_roles = self.user_roles.get(user_id, [])
            for role in user_roles:
                role_perms = self.role_permissions.get(role, [])
                if permission in role_perms:
                    return True
        return False
