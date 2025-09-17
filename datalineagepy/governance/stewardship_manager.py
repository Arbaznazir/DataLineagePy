"""
Data Stewardship Manager for DataLineagePy

Provides comprehensive data stewardship workflows, data steward management,
and governance process automation.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable
from threading import Lock

logger = logging.getLogger(__name__)

class StewardshipRole(Enum):
    """Data stewardship role enumeration."""
    DATA_OWNER = "data_owner"
    DATA_STEWARD = "data_steward"
    DATA_CUSTODIAN = "data_custodian"
    BUSINESS_ANALYST = "business_analyst"
    COMPLIANCE_OFFICER = "compliance_officer"

class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkflowType(Enum):
    """Workflow type enumeration."""
    DATA_ACCESS_REQUEST = "data_access_request"
    DATA_CLASSIFICATION = "data_classification"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    POLICY_VIOLATION = "policy_violation"
    RETENTION_REVIEW = "retention_review"
    COMPLIANCE_AUDIT = "compliance_audit"

@dataclass
class DataSteward:
    """Represents a data steward."""
    id: str
    name: str
    email: str
    role: StewardshipRole
    department: str
    expertise_areas: Set[str] = field(default_factory=set)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    workload_capacity: int = 10
    current_workload: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert steward to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "department": self.department,
            "expertise_areas": list(self.expertise_areas),
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "workload_capacity": self.workload_capacity,
            "current_workload": self.current_workload,
            "metadata": self.metadata
        }

@dataclass
class StewardshipWorkflow:
    """Represents a data stewardship workflow."""
    id: str
    type: WorkflowType
    title: str
    description: str
    requester_id: str
    assigned_steward_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    priority: int = 5  # 1-10 scale
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    data_assets: List[str] = field(default_factory=list)
    approval_chain: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "requester_id": self.requester_id,
            "assigned_steward_id": self.assigned_steward_id,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "data_assets": self.data_assets,
            "approval_chain": self.approval_chain,
            "comments": self.comments,
            "attachments": self.attachments,
            "metadata": self.metadata
        }

class StewardshipManager:
    """Manages data stewardship workflows and processes."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.stewards: Dict[str, DataSteward] = {}
        self.workflows: Dict[str, StewardshipWorkflow] = {}
        self.lock = Lock()
        self.workflow_timeout = self.config.get("workflow_timeout", 86400)  # 24 hours
        self.auto_assignment = self.config.get("auto_assignment", True)
        self.escalation_enabled = self.config.get("escalation_enabled", True)
        self.notification_callbacks: List[Callable] = []
        self.stats = {
            "total_stewards": 0,
            "active_stewards": 0,
            "total_workflows": 0,
            "pending_workflows": 0,
            "completed_workflows": 0,
            "overdue_workflows": 0,
            "avg_completion_time": 0.0
        }
        
    async def start(self):
        """Start the stewardship manager."""
        logger.info("Starting stewardship manager")
        asyncio.create_task(self._monitor_workflows())
        asyncio.create_task(self._update_statistics())
        
    async def stop(self):
        """Stop the stewardship manager."""
        logger.info("Stopping stewardship manager")
        
    async def register_steward(self, name: str, email: str, role: StewardshipRole, 
                              department: str, expertise_areas: Set[str] = None) -> DataSteward:
        """Register a new data steward."""
        with self.lock:
            steward_id = f"steward_{uuid.uuid4().hex[:8]}"
            
            steward = DataSteward(
                id=steward_id,
                name=name,
                email=email,
                role=role,
                department=department,
                expertise_areas=expertise_areas or set()
            )
            
            self.stewards[steward_id] = steward
            self.stats["total_stewards"] += 1
            self.stats["active_stewards"] += 1
            
            logger.info(f"Registered steward: {name} ({steward_id})")
            return steward
    
    async def get_steward(self, steward_id: str) -> Optional[DataSteward]:
        """Get steward by ID."""
        return self.stewards.get(steward_id)
    
    async def update_steward(self, steward_id: str, updates: Dict[str, Any]) -> bool:
        """Update steward information."""
        with self.lock:
            steward = self.stewards.get(steward_id)
            if not steward:
                return False
            
            if "name" in updates:
                steward.name = updates["name"]
            if "email" in updates:
                steward.email = updates["email"]
            if "department" in updates:
                steward.department = updates["department"]
            if "expertise_areas" in updates:
                steward.expertise_areas = set(updates["expertise_areas"])
            if "active" in updates:
                steward.active = updates["active"]
                if updates["active"]:
                    self.stats["active_stewards"] += 1
                else:
                    self.stats["active_stewards"] -= 1
            if "workload_capacity" in updates:
                steward.workload_capacity = updates["workload_capacity"]
            
            logger.info(f"Updated steward: {steward_id}")
            return True
    
    async def create_workflow(self, workflow_type: WorkflowType, title: str, 
                             description: str, requester_id: str, 
                             data_assets: List[str] = None, priority: int = 5,
                             due_hours: int = 24) -> StewardshipWorkflow:
        """Create a new stewardship workflow."""
        with self.lock:
            workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
            
            workflow = StewardshipWorkflow(
                id=workflow_id,
                type=workflow_type,
                title=title,
                description=description,
                requester_id=requester_id,
                priority=priority,
                due_date=datetime.now() + timedelta(hours=due_hours),
                data_assets=data_assets or []
            )
            
            # Auto-assign if enabled
            if self.auto_assignment:
                assigned_steward = await self._find_best_steward(workflow)
                if assigned_steward:
                    workflow.assigned_steward_id = assigned_steward.id
                    workflow.status = WorkflowStatus.IN_PROGRESS
                    assigned_steward.current_workload += 1
                    assigned_steward.last_activity = datetime.now()
            
            self.workflows[workflow_id] = workflow
            self.stats["total_workflows"] += 1
            self.stats["pending_workflows"] += 1
            
            # Send notification
            await self._send_notification("workflow_created", workflow)
            
            logger.info(f"Created workflow: {title} ({workflow_id})")
            return workflow
    
    async def get_workflow(self, workflow_id: str) -> Optional[StewardshipWorkflow]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)
    
    async def assign_workflow(self, workflow_id: str, steward_id: str) -> bool:
        """Assign workflow to a steward."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            steward = self.stewards.get(steward_id)
            
            if not workflow or not steward:
                return False
            
            # Remove from previous steward if assigned
            if workflow.assigned_steward_id:
                prev_steward = self.stewards.get(workflow.assigned_steward_id)
                if prev_steward:
                    prev_steward.current_workload -= 1
            
            # Assign to new steward
            workflow.assigned_steward_id = steward_id
            workflow.status = WorkflowStatus.IN_PROGRESS
            workflow.updated_at = datetime.now()
            steward.current_workload += 1
            steward.last_activity = datetime.now()
            
            # Send notification
            await self._send_notification("workflow_assigned", workflow)
            
            logger.info(f"Assigned workflow {workflow_id} to steward {steward_id}")
            return True
    
    async def update_workflow_status(self, workflow_id: str, status: WorkflowStatus, 
                                   comment: str = "", user_id: str = "") -> bool:
        """Update workflow status."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return False
            
            old_status = workflow.status
            workflow.status = status
            workflow.updated_at = datetime.now()
            
            # Add comment if provided
            if comment:
                workflow.comments.append({
                    "user_id": user_id,
                    "comment": comment,
                    "timestamp": datetime.now().isoformat(),
                    "status_change": f"{old_status.value} -> {status.value}"
                })
            
            # Update completion time
            if status in [WorkflowStatus.COMPLETED, WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]:
                workflow.completed_at = datetime.now()
                self.stats["completed_workflows"] += 1
                self.stats["pending_workflows"] -= 1
                
                # Update steward workload
                if workflow.assigned_steward_id:
                    steward = self.stewards.get(workflow.assigned_steward_id)
                    if steward:
                        steward.current_workload -= 1
            
            # Send notification
            await self._send_notification("workflow_status_changed", workflow)
            
            logger.info(f"Updated workflow {workflow_id} status to {status.value}")
            return True
    
    async def add_workflow_comment(self, workflow_id: str, comment: str, user_id: str) -> bool:
        """Add comment to workflow."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return False
            
            workflow.comments.append({
                "user_id": user_id,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
            
            workflow.updated_at = datetime.now()
            
            logger.info(f"Added comment to workflow {workflow_id}")
            return True
    
    async def get_steward_workload(self, steward_id: str) -> Dict[str, Any]:
        """Get steward's current workload."""
        steward = self.stewards.get(steward_id)
        if not steward:
            return {}
        
        assigned_workflows = [
            w for w in self.workflows.values() 
            if w.assigned_steward_id == steward_id and w.status == WorkflowStatus.IN_PROGRESS
        ]
        
        return {
            "steward_id": steward_id,
            "current_workload": steward.current_workload,
            "capacity": steward.workload_capacity,
            "utilization": (steward.current_workload / steward.workload_capacity) * 100,
            "assigned_workflows": [w.to_dict() for w in assigned_workflows]
        }
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        # Calculate average completion time
        completed_workflows = [
            w for w in self.workflows.values() 
            if w.completed_at and w.created_at
        ]
        
        if completed_workflows:
            total_time = sum(
                (w.completed_at - w.created_at).total_seconds() 
                for w in completed_workflows
            )
            avg_completion_time = total_time / len(completed_workflows) / 3600  # hours
            self.stats["avg_completion_time"] = avg_completion_time
        
        # Count overdue workflows
        now = datetime.now()
        overdue_count = sum(
            1 for w in self.workflows.values() 
            if w.due_date and w.due_date < now and w.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]
        )
        self.stats["overdue_workflows"] = overdue_count
        
        return self.stats.copy()
    
    async def get_workflows_by_status(self, status: WorkflowStatus) -> List[StewardshipWorkflow]:
        """Get workflows by status."""
        return [w for w in self.workflows.values() if w.status == status]
    
    async def get_workflows_by_steward(self, steward_id: str) -> List[StewardshipWorkflow]:
        """Get workflows assigned to a steward."""
        return [w for w in self.workflows.values() if w.assigned_steward_id == steward_id]
    
    async def escalate_workflow(self, workflow_id: str, reason: str) -> bool:
        """Escalate workflow to higher authority."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return False
            
            workflow.status = WorkflowStatus.ESCALATED
            workflow.updated_at = datetime.now()
            workflow.comments.append({
                "user_id": "system",
                "comment": f"Workflow escalated: {reason}",
                "timestamp": datetime.now().isoformat(),
                "escalation": True
            })
            
            # Send escalation notification
            await self._send_notification("workflow_escalated", workflow)
            
            logger.info(f"Escalated workflow {workflow_id}: {reason}")
            return True
    
    async def add_notification_callback(self, callback: Callable):
        """Add notification callback."""
        self.notification_callbacks.append(callback)
    
    async def _find_best_steward(self, workflow: StewardshipWorkflow) -> Optional[DataSteward]:
        """Find the best steward for a workflow."""
        available_stewards = [
            s for s in self.stewards.values() 
            if s.active and s.current_workload < s.workload_capacity
        ]
        
        if not available_stewards:
            return None
        
        # Score stewards based on expertise and workload
        best_steward = None
        best_score = -1
        
        for steward in available_stewards:
            score = 0
            
            # Expertise match
            workflow_domain = workflow.metadata.get("domain", "")
            if workflow_domain in steward.expertise_areas:
                score += 10
            
            # Workload factor (prefer less loaded stewards)
            utilization = steward.current_workload / steward.workload_capacity
            score += (1 - utilization) * 5
            
            # Role match
            if workflow.type == WorkflowType.COMPLIANCE_AUDIT and steward.role == StewardshipRole.COMPLIANCE_OFFICER:
                score += 5
            elif workflow.type == WorkflowType.DATA_QUALITY_ISSUE and steward.role == StewardshipRole.DATA_STEWARD:
                score += 5
            
            if score > best_score:
                best_score = score
                best_steward = steward
        
        return best_steward
    
    async def _send_notification(self, event_type: str, workflow: StewardshipWorkflow):
        """Send notification for workflow events."""
        try:
            for callback in self.notification_callbacks:
                await callback(event_type, workflow)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _monitor_workflows(self):
        """Background task to monitor workflows."""
        while True:
            try:
                now = datetime.now()
                
                # Check for overdue workflows
                for workflow in self.workflows.values():
                    if (workflow.due_date and workflow.due_date < now and 
                        workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.IN_PROGRESS]):
                        
                        if self.escalation_enabled:
                            await self.escalate_workflow(workflow.id, "Workflow overdue")
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in workflow monitoring: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _update_statistics(self):
        """Background task to update statistics."""
        while True:
            try:
                await self.get_workflow_statistics()
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(300)
