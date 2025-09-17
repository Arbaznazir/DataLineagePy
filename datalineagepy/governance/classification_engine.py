"""
Data Classification Engine for DataLineagePy

Provides automated data classification, pattern matching, and ML-based content analysis
for comprehensive data governance.
"""

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Pattern
from threading import Lock
import hashlib

logger = logging.getLogger(__name__)

class ClassificationType(Enum):
    """Data classification type enumeration."""
    PII = "PII"
    PHI = "PHI"
    FINANCIAL = "FINANCIAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"

class ClassificationMethod(Enum):
    """Classification method enumeration."""
    PATTERN_MATCHING = "pattern_matching"
    CONTENT_ANALYSIS = "content_analysis"
    METADATA_ANALYSIS = "metadata_analysis"
    ML_CLASSIFICATION = "ml_classification"
    MANUAL = "manual"

class ConfidenceLevel(Enum):
    """Confidence level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class ClassificationRule:
    """Represents a data classification rule."""
    id: str
    name: str
    classification_type: ClassificationType
    method: ClassificationMethod
    pattern: Optional[str] = None
    compiled_pattern: Optional[Pattern] = None
    keywords: List[str] = field(default_factory=list)
    metadata_fields: List[str] = field(default_factory=list)
    confidence_weight: float = 1.0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Compile regex pattern if provided."""
        if self.pattern and not self.compiled_pattern:
            try:
                self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
            except re.error as e:
                logger.error(f"Invalid regex pattern in rule {self.id}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "classification_type": self.classification_type.value,
            "method": self.method.value,
            "pattern": self.pattern,
            "keywords": self.keywords,
            "metadata_fields": self.metadata_fields,
            "confidence_weight": self.confidence_weight,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class DataClassification:
    """Represents a data classification result."""
    id: str
    data_asset_id: str
    classification_type: ClassificationType
    confidence_score: float
    confidence_level: ConfidenceLevel
    method: ClassificationMethod
    rule_id: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert classification to dictionary."""
        return {
            "id": self.id,
            "data_asset_id": self.data_asset_id,
            "classification_type": self.classification_type.value,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "method": self.method.value,
            "rule_id": self.rule_id,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "reviewed": self.reviewed,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "metadata": self.metadata
        }

class ClassificationEngine:
    """Automated data classification engine."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.rules: Dict[str, ClassificationRule] = {}
        self.classifications: Dict[str, List[DataClassification]] = {}  # data_asset_id -> classifications
        self.lock = Lock()
        self.auto_classification = self.config.get("auto_classification", True)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.8)
        self.ml_enabled = self.config.get("ml_enabled", True)
        self.stats = {
            "total_rules": 0,
            "active_rules": 0,
            "total_classifications": 0,
            "auto_classifications": 0,
            "manual_classifications": 0,
            "high_confidence_classifications": 0
        }
        
        # Initialize default rules
        self._initialize_default_rules()
        
    async def start(self):
        """Start the classification engine."""
        logger.info("Starting classification engine")
        
    async def stop(self):
        """Stop the classification engine."""
        logger.info("Stopping classification engine")
        
    async def add_rule(self, name: str, classification_type: ClassificationType,
                      method: ClassificationMethod, pattern: str = None,
                      keywords: List[str] = None, metadata_fields: List[str] = None,
                      confidence_weight: float = 1.0) -> ClassificationRule:
        """Add a new classification rule."""
        with self.lock:
            rule_id = f"rule_{uuid.uuid4().hex[:8]}"
            
            rule = ClassificationRule(
                id=rule_id,
                name=name,
                classification_type=classification_type,
                method=method,
                pattern=pattern,
                keywords=keywords or [],
                metadata_fields=metadata_fields or [],
                confidence_weight=confidence_weight
            )
            
            self.rules[rule_id] = rule
            self.stats["total_rules"] += 1
            self.stats["active_rules"] += 1
            
            logger.info(f"Added classification rule: {name} ({rule_id})")
            return rule
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a classification rule."""
        with self.lock:
            rule = self.rules.get(rule_id)
            if not rule:
                return False
            
            if "name" in updates:
                rule.name = updates["name"]
            if "pattern" in updates:
                rule.pattern = updates["pattern"]
                rule.__post_init__()  # Recompile pattern
            if "keywords" in updates:
                rule.keywords = updates["keywords"]
            if "metadata_fields" in updates:
                rule.metadata_fields = updates["metadata_fields"]
            if "confidence_weight" in updates:
                rule.confidence_weight = updates["confidence_weight"]
            if "enabled" in updates:
                rule.enabled = updates["enabled"]
                if updates["enabled"]:
                    self.stats["active_rules"] += 1
                else:
                    self.stats["active_rules"] -= 1
            
            rule.updated_at = datetime.now()
            
            logger.info(f"Updated classification rule: {rule_id}")
            return True
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a classification rule."""
        with self.lock:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                del self.rules[rule_id]
                self.stats["total_rules"] -= 1
                if rule.enabled:
                    self.stats["active_rules"] -= 1
                
                logger.info(f"Deleted classification rule: {rule_id}")
                return True
            return False
    
    async def classify_data_asset(self, data_asset_id: str, content: str = None,
                                 metadata: Dict[str, Any] = None,
                                 schema: Dict[str, Any] = None) -> List[DataClassification]:
        """Classify a data asset."""
        classifications = []
        
        # Apply all enabled rules
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            classification = await self._apply_rule(rule, data_asset_id, content, metadata, schema)
            if classification:
                classifications.append(classification)
        
        # Store classifications
        with self.lock:
            if data_asset_id not in self.classifications:
                self.classifications[data_asset_id] = []
            
            # Remove old classifications for this asset
            self.classifications[data_asset_id] = [
                c for c in self.classifications[data_asset_id] 
                if c.created_by != "system" or c.reviewed
            ]
            
            # Add new classifications
            self.classifications[data_asset_id].extend(classifications)
            
            self.stats["total_classifications"] += len(classifications)
            self.stats["auto_classifications"] += len(classifications)
            self.stats["high_confidence_classifications"] += sum(
                1 for c in classifications if c.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
            )
        
        logger.info(f"Classified data asset {data_asset_id}: {len(classifications)} classifications")
        return classifications
    
    async def get_classifications(self, data_asset_id: str) -> List[DataClassification]:
        """Get classifications for a data asset."""
        return self.classifications.get(data_asset_id, [])
    
    async def add_manual_classification(self, data_asset_id: str, classification_type: ClassificationType,
                                       confidence_score: float, user_id: str,
                                       evidence: List[str] = None) -> DataClassification:
        """Add a manual classification."""
        with self.lock:
            classification_id = f"classification_{uuid.uuid4().hex[:8]}"
            
            classification = DataClassification(
                id=classification_id,
                data_asset_id=data_asset_id,
                classification_type=classification_type,
                confidence_score=confidence_score,
                confidence_level=self._calculate_confidence_level(confidence_score),
                method=ClassificationMethod.MANUAL,
                evidence=evidence or [],
                created_by=user_id,
                reviewed=True,
                reviewed_by=user_id,
                reviewed_at=datetime.now()
            )
            
            if data_asset_id not in self.classifications:
                self.classifications[data_asset_id] = []
            
            self.classifications[data_asset_id].append(classification)
            
            self.stats["total_classifications"] += 1
            self.stats["manual_classifications"] += 1
            
            logger.info(f"Added manual classification: {data_asset_id} -> {classification_type.value}")
            return classification
    
    async def review_classification(self, classification_id: str, approved: bool,
                                   reviewer_id: str, comments: str = "") -> bool:
        """Review an automatic classification."""
        with self.lock:
            for asset_classifications in self.classifications.values():
                for classification in asset_classifications:
                    if classification.id == classification_id:
                        classification.reviewed = True
                        classification.reviewed_by = reviewer_id
                        classification.reviewed_at = datetime.now()
                        
                        if not approved:
                            # Remove classification if not approved
                            asset_classifications.remove(classification)
                        
                        if comments:
                            classification.metadata["review_comments"] = comments
                        
                        logger.info(f"Reviewed classification {classification_id}: {'approved' if approved else 'rejected'}")
                        return True
            
            return False
    
    async def get_classification_statistics(self) -> Dict[str, Any]:
        """Get classification statistics."""
        # Calculate type distribution
        type_distribution = {}
        for asset_classifications in self.classifications.values():
            for classification in asset_classifications:
                type_name = classification.classification_type.value
                type_distribution[type_name] = type_distribution.get(type_name, 0) + 1
        
        # Calculate confidence distribution
        confidence_distribution = {}
        for asset_classifications in self.classifications.values():
            for classification in asset_classifications:
                level = classification.confidence_level.value
                confidence_distribution[level] = confidence_distribution.get(level, 0) + 1
        
        return {
            **self.stats,
            "type_distribution": type_distribution,
            "confidence_distribution": confidence_distribution,
            "total_assets_classified": len(self.classifications)
        }
    
    async def export_classifications(self, data_asset_id: str = None) -> List[Dict[str, Any]]:
        """Export classifications to dictionary format."""
        if data_asset_id:
            classifications = self.classifications.get(data_asset_id, [])
        else:
            classifications = []
            for asset_classifications in self.classifications.values():
                classifications.extend(asset_classifications)
        
        return [c.to_dict() for c in classifications]
    
    async def _apply_rule(self, rule: ClassificationRule, data_asset_id: str,
                         content: str = None, metadata: Dict[str, Any] = None,
                         schema: Dict[str, Any] = None) -> Optional[DataClassification]:
        """Apply a classification rule to data."""
        evidence = []
        confidence_score = 0.0
        
        if rule.method == ClassificationMethod.PATTERN_MATCHING and content and rule.compiled_pattern:
            matches = rule.compiled_pattern.findall(content)
            if matches:
                evidence.extend([f"Pattern match: {match}" for match in matches[:5]])  # Limit evidence
                confidence_score = min(1.0, len(matches) * 0.2) * rule.confidence_weight
        
        elif rule.method == ClassificationMethod.CONTENT_ANALYSIS and content and rule.keywords:
            content_lower = content.lower()
            keyword_matches = [kw for kw in rule.keywords if kw.lower() in content_lower]
            if keyword_matches:
                evidence.extend([f"Keyword match: {kw}" for kw in keyword_matches])
                confidence_score = min(1.0, len(keyword_matches) * 0.3) * rule.confidence_weight
        
        elif rule.method == ClassificationMethod.METADATA_ANALYSIS and metadata and rule.metadata_fields:
            metadata_matches = []
            for field in rule.metadata_fields:
                if field in metadata:
                    metadata_matches.append(field)
                    evidence.append(f"Metadata field: {field}")
            
            if metadata_matches:
                confidence_score = min(1.0, len(metadata_matches) * 0.4) * rule.confidence_weight
        
        elif rule.method == ClassificationMethod.ML_CLASSIFICATION and self.ml_enabled:
            # Placeholder for ML classification
            # In a real implementation, this would call an ML model
            confidence_score = await self._ml_classify(content, metadata, schema, rule.classification_type)
            if confidence_score > 0:
                evidence.append("ML model prediction")
        
        # Only create classification if confidence meets threshold
        if confidence_score >= self.confidence_threshold:
            classification_id = f"classification_{uuid.uuid4().hex[:8]}"
            
            return DataClassification(
                id=classification_id,
                data_asset_id=data_asset_id,
                classification_type=rule.classification_type,
                confidence_score=confidence_score,
                confidence_level=self._calculate_confidence_level(confidence_score),
                method=rule.method,
                rule_id=rule.id,
                evidence=evidence
            )
        
        return None
    
    async def _ml_classify(self, content: str, metadata: Dict[str, Any],
                          schema: Dict[str, Any], classification_type: ClassificationType) -> float:
        """Placeholder for ML-based classification."""
        # In a real implementation, this would:
        # 1. Prepare features from content, metadata, and schema
        # 2. Call appropriate ML model
        # 3. Return confidence score
        
        # For now, return a simple heuristic-based score
        if not content:
            return 0.0
        
        # Simple keyword-based scoring for demonstration
        keywords = {
            ClassificationType.PII: ["name", "email", "phone", "address", "ssn"],
            ClassificationType.PHI: ["patient", "medical", "health", "diagnosis", "treatment"],
            ClassificationType.FINANCIAL: ["account", "payment", "credit", "bank", "transaction"],
            ClassificationType.CONFIDENTIAL: ["confidential", "secret", "private", "restricted"]
        }
        
        type_keywords = keywords.get(classification_type, [])
        content_lower = content.lower()
        
        matches = sum(1 for kw in type_keywords if kw in content_lower)
        return min(1.0, matches * 0.2)
    
    def _calculate_confidence_level(self, score: float) -> ConfidenceLevel:
        """Calculate confidence level from score."""
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _initialize_default_rules(self):
        """Initialize default classification rules."""
        default_rules = [
            # PII Rules
            {
                "name": "Email Address",
                "type": ClassificationType.PII,
                "method": ClassificationMethod.PATTERN_MATCHING,
                "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "weight": 0.9
            },
            {
                "name": "Phone Number",
                "type": ClassificationType.PII,
                "method": ClassificationMethod.PATTERN_MATCHING,
                "pattern": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                "weight": 0.8
            },
            {
                "name": "SSN",
                "type": ClassificationType.PII,
                "method": ClassificationMethod.PATTERN_MATCHING,
                "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
                "weight": 1.0
            },
            # Financial Rules
            {
                "name": "Credit Card",
                "type": ClassificationType.FINANCIAL,
                "method": ClassificationMethod.PATTERN_MATCHING,
                "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                "weight": 0.9
            },
            {
                "name": "Bank Account",
                "type": ClassificationType.FINANCIAL,
                "method": ClassificationMethod.PATTERN_MATCHING,
                "pattern": r"\b\d{8,17}\b",
                "weight": 0.6
            },
            # Content-based rules
            {
                "name": "PII Keywords",
                "type": ClassificationType.PII,
                "method": ClassificationMethod.CONTENT_ANALYSIS,
                "keywords": ["first_name", "last_name", "full_name", "address", "zip_code", "postal_code"],
                "weight": 0.7
            },
            {
                "name": "PHI Keywords",
                "type": ClassificationType.PHI,
                "method": ClassificationMethod.CONTENT_ANALYSIS,
                "keywords": ["patient_id", "medical_record", "diagnosis", "treatment", "medication"],
                "weight": 0.8
            }
        ]
        
        for rule_config in default_rules:
            rule_id = f"default_{hashlib.md5(rule_config['name'].encode()).hexdigest()[:8]}"
            
            rule = ClassificationRule(
                id=rule_id,
                name=rule_config["name"],
                classification_type=rule_config["type"],
                method=rule_config["method"],
                pattern=rule_config.get("pattern"),
                keywords=rule_config.get("keywords", []),
                confidence_weight=rule_config["weight"]
            )
            
            self.rules[rule_id] = rule
            self.stats["total_rules"] += 1
            self.stats["active_rules"] += 1
