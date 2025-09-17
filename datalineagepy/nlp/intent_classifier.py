"""
Intent Classifier for DataLineagePy

Classifies user intents in natural language queries for data lineage exploration.
"""

import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
from enum import Enum
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Supported intent types."""
    SEARCH = "search"
    TRACE_UPSTREAM = "trace_upstream"
    TRACE_DOWNSTREAM = "trace_downstream"
    ANALYZE_IMPACT = "analyze_impact"
    DOCUMENT = "document"
    MONITOR = "monitor"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    COMPARE = "compare"
    VALIDATE = "validate"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Result of intent classification."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent: Intent = Intent.UNKNOWN
    confidence: float = 0.0
    entities: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    query: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentClassifier:
    """Classifies user intents in natural language queries."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._lock = threading.RLock()
        
        # Intent patterns and keywords
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        
        # Training data for improved classification
        self.training_data: List[Tuple[str, Intent]] = []
        self.classification_history: List[IntentResult] = []
        
        # Configuration
        self.min_confidence_threshold = self.config.get('min_confidence', 0.3)
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        logger.info("IntentClassifier initialized")
    
    def _initialize_intent_patterns(self) -> Dict[Intent, Dict[str, Any]]:
        """Initialize intent patterns and keywords."""
        return {
            Intent.SEARCH: {
                'keywords': [
                    'find', 'search', 'look for', 'show me', 'get', 'list',
                    'where is', 'what is', 'display', 'retrieve', 'fetch'
                ],
                'patterns': [
                    r'\b(?:find|search|look for|show me|get|list)\b',
                    r'\bwhere is\b',
                    r'\bwhat is\b'
                ],
                'weight': 1.0
            },
            Intent.TRACE_UPSTREAM: {
                'keywords': [
                    'upstream', 'source', 'origin', 'comes from', 'derived from',
                    'parent', 'input', 'dependency', 'trace back', 'backward'
                ],
                'patterns': [
                    r'\bupstream\b',
                    r'\bsource\b',
                    r'\bcomes from\b',
                    r'\btrace back\b'
                ],
                'weight': 1.2
            },
            Intent.TRACE_DOWNSTREAM: {
                'keywords': [
                    'downstream', 'destination', 'goes to', 'used by', 'child',
                    'output', 'consumer', 'trace forward', 'forward', 'impact'
                ],
                'patterns': [
                    r'\bdownstream\b',
                    r'\bgoes to\b',
                    r'\bused by\b',
                    r'\btrace forward\b'
                ],
                'weight': 1.2
            },
            Intent.ANALYZE_IMPACT: {
                'keywords': [
                    'impact', 'effect', 'affect', 'influence', 'consequence',
                    'analyze', 'analysis', 'relationship', 'dependency'
                ],
                'patterns': [
                    r'\bimpact\b',
                    r'\beffect\b',
                    r'\banalyze\b',
                    r'\banalysis\b'
                ],
                'weight': 1.1
            },
            Intent.DOCUMENT: {
                'keywords': [
                    'document', 'describe', 'explain', 'documentation',
                    'tell me about', 'what does', 'how does', 'definition'
                ],
                'patterns': [
                    r'\bdocument\b',
                    r'\bdescribe\b',
                    r'\bexplain\b',
                    r'\btell me about\b'
                ],
                'weight': 1.0
            },
            Intent.MONITOR: {
                'keywords': [
                    'status', 'health', 'monitor', 'check', 'alert',
                    'running', 'failed', 'error', 'warning', 'performance'
                ],
                'patterns': [
                    r'\bstatus\b',
                    r'\bhealth\b',
                    r'\bmonitor\b',
                    r'\bcheck\b'
                ],
                'weight': 1.0
            },
            Intent.CREATE: {
                'keywords': [
                    'create', 'add', 'new', 'insert', 'build', 'generate',
                    'make', 'establish', 'set up'
                ],
                'patterns': [
                    r'\bcreate\b',
                    r'\badd\b',
                    r'\bnew\b',
                    r'\binsert\b'
                ],
                'weight': 1.0
            },
            Intent.UPDATE: {
                'keywords': [
                    'update', 'modify', 'change', 'edit', 'alter',
                    'revise', 'adjust', 'correct'
                ],
                'patterns': [
                    r'\bupdate\b',
                    r'\bmodify\b',
                    r'\bchange\b',
                    r'\bedit\b'
                ],
                'weight': 1.0
            },
            Intent.DELETE: {
                'keywords': [
                    'delete', 'remove', 'drop', 'destroy', 'eliminate',
                    'clear', 'purge', 'erase'
                ],
                'patterns': [
                    r'\bdelete\b',
                    r'\bremove\b',
                    r'\bdrop\b',
                    r'\bdestroy\b'
                ],
                'weight': 1.0
            },
            Intent.COMPARE: {
                'keywords': [
                    'compare', 'difference', 'diff', 'versus', 'vs',
                    'contrast', 'similar', 'different'
                ],
                'patterns': [
                    r'\bcompare\b',
                    r'\bdifference\b',
                    r'\bversus\b',
                    r'\bvs\b'
                ],
                'weight': 1.0
            },
            Intent.VALIDATE: {
                'keywords': [
                    'validate', 'verify', 'test', 'quality', 'check',
                    'ensure', 'confirm', 'audit'
                ],
                'patterns': [
                    r'\bvalidate\b',
                    r'\bverify\b',
                    r'\btest\b',
                    r'\bquality\b'
                ],
                'weight': 1.0
            }
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, str]:
        """Initialize entity extraction patterns."""
        return {
            'table': r'\b(?:table|tbl)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\b',
            'column': r'\b(?:column|col|field)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'database': r'\b(?:database|db|schema)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'file': r'\b(?:file|dataset)\s+([a-zA-Z0-9_./\\-]+)\b',
            'pipeline': r'\b(?:pipeline|workflow)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'job': r'\b(?:job|task)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
            'quoted_entity': r'"([^"]+)"',
            'sql_table': r'\b(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\b',
            'sql_column': r'\bSELECT\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\s+FROM\b'
        }
    
    def classify_intent(self, query: str) -> IntentResult:
        """Classify the intent of a natural language query."""
        with self._lock:
            query_lower = query.lower().strip()
            
            if not query_lower:
                return IntentResult(
                    intent=Intent.UNKNOWN,
                    confidence=0.0,
                    query=query
                )
            
            # Calculate scores for each intent
            intent_scores = self._calculate_intent_scores(query_lower)
            
            # Find the best intent
            best_intent = Intent.UNKNOWN
            best_score = 0.0
            
            for intent, score in intent_scores.items():
                if score > best_score:
                    best_score = score
                    best_intent = intent
            
            # Normalize confidence score
            confidence = min(1.0, best_score)
            
            # If confidence is too low, mark as unknown
            if confidence < self.min_confidence_threshold:
                best_intent = Intent.UNKNOWN
                confidence = 0.0
            
            # Extract entities
            entities = self._extract_entities(query)
            
            # Extract parameters
            parameters = self._extract_parameters(query, best_intent)
            
            # Create result
            result = IntentResult(
                intent=best_intent,
                confidence=confidence,
                entities=entities,
                parameters=parameters,
                query=query,
                metadata={
                    'all_scores': {intent.value: score for intent, score in intent_scores.items()},
                    'query_length': len(query),
                    'word_count': len(query.split())
                }
            )
            
            # Add to history
            self._add_to_history(result)
            
            logger.debug(f"Classified intent: {best_intent.value} (confidence: {confidence:.2f})")
            return result
    
    def _calculate_intent_scores(self, query: str) -> Dict[Intent, float]:
        """Calculate scores for each intent based on patterns and keywords."""
        scores = defaultdict(float)
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            
            # Keyword matching
            keywords = config.get('keywords', [])
            for keyword in keywords:
                if keyword in query:
                    score += 1.0
            
            # Pattern matching
            patterns = config.get('patterns', [])
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                score += len(matches) * 1.5
            
            # Apply weight
            weight = config.get('weight', 1.0)
            score *= weight
            
            scores[intent] = score
        
        return scores
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from the query."""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if tuple
                
                entities.append({
                    'type': entity_type,
                    'value': match.strip(),
                    'start_pos': query.lower().find(match.lower()),
                    'end_pos': query.lower().find(match.lower()) + len(match)
                })
        
        # Remove duplicates
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity['type'], entity['value'].lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _extract_parameters(self, query: str, intent: Intent) -> Dict[str, Any]:
        """Extract parameters specific to the intent."""
        parameters = {}
        query_lower = query.lower()
        
        # Common parameters
        if 'limit' in query_lower:
            limit_match = re.search(r'limit\s+(\d+)', query_lower)
            if limit_match:
                parameters['limit'] = int(limit_match.group(1))
        
        if 'top' in query_lower:
            top_match = re.search(r'top\s+(\d+)', query_lower)
            if top_match:
                parameters['limit'] = int(top_match.group(1))
        
        # Intent-specific parameters
        if intent == Intent.TRACE_UPSTREAM:
            parameters['direction'] = 'upstream'
            if 'levels' in query_lower:
                levels_match = re.search(r'(\d+)\s+levels?', query_lower)
                if levels_match:
                    parameters['max_levels'] = int(levels_match.group(1))
        
        elif intent == Intent.TRACE_DOWNSTREAM:
            parameters['direction'] = 'downstream'
            if 'levels' in query_lower:
                levels_match = re.search(r'(\d+)\s+levels?', query_lower)
                if levels_match:
                    parameters['max_levels'] = int(levels_match.group(1))
        
        elif intent == Intent.SEARCH:
            if 'type' in query_lower:
                type_match = re.search(r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_lower)
                if type_match:
                    parameters['node_type'] = type_match.group(1)
        
        elif intent == Intent.MONITOR:
            if 'status' in query_lower:
                parameters['check_type'] = 'status'
            elif 'health' in query_lower:
                parameters['check_type'] = 'health'
            elif 'performance' in query_lower:
                parameters['check_type'] = 'performance'
        
        # Time-related parameters
        time_patterns = {
            'today': r'\btoday\b',
            'yesterday': r'\byesterday\b',
            'last_week': r'\blast\s+week\b',
            'last_month': r'\blast\s+month\b'
        }
        
        for time_key, pattern in time_patterns.items():
            if re.search(pattern, query_lower):
                parameters['time_filter'] = time_key
                break
        
        return parameters
    
    def _add_to_history(self, result: IntentResult) -> None:
        """Add classification result to history."""
        self.classification_history.append(result)
        
        # Maintain history size limit
        if len(self.classification_history) > self.max_history_size:
            self.classification_history = self.classification_history[-self.max_history_size:]
    
    def add_training_data(self, query: str, intent: Intent) -> None:
        """Add training data for improved classification."""
        with self._lock:
            self.training_data.append((query.lower().strip(), intent))
            logger.debug(f"Added training data: {intent.value}")
    
    def retrain_classifier(self) -> None:
        """Retrain the classifier using training data."""
        with self._lock:
            if not self.training_data:
                logger.warning("No training data available for retraining")
                return
            
            # Analyze training data to improve patterns
            intent_examples = defaultdict(list)
            for query, intent in self.training_data:
                intent_examples[intent].append(query)
            
            # Update patterns based on training data
            for intent, examples in intent_examples.items():
                if intent in self.intent_patterns:
                    # Extract common words from examples
                    all_words = []
                    for example in examples:
                        all_words.extend(example.split())
                    
                    # Find frequent words not already in keywords
                    word_counts = defaultdict(int)
                    for word in all_words:
                        word_counts[word] += 1
                    
                    current_keywords = set(self.intent_patterns[intent]['keywords'])
                    for word, count in word_counts.items():
                        if count >= 2 and word not in current_keywords and len(word) > 2:
                            self.intent_patterns[intent]['keywords'].append(word)
            
            logger.info(f"Retrained classifier with {len(self.training_data)} examples")
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        with self._lock:
            if not self.classification_history:
                return {'total_classifications': 0}
            
            intent_counts = defaultdict(int)
            confidence_sum = 0.0
            
            for result in self.classification_history:
                intent_counts[result.intent.value] += 1
                confidence_sum += result.confidence
            
            avg_confidence = confidence_sum / len(self.classification_history)
            
            return {
                'total_classifications': len(self.classification_history),
                'intent_distribution': dict(intent_counts),
                'average_confidence': avg_confidence,
                'training_data_size': len(self.training_data)
            }
    
    def clear_history(self) -> None:
        """Clear classification history."""
        with self._lock:
            self.classification_history.clear()
            logger.info("Classification history cleared")
    
    def export_training_data(self) -> List[Dict[str, str]]:
        """Export training data for external use."""
        with self._lock:
            return [
                {'query': query, 'intent': intent.value}
                for query, intent in self.training_data
            ]
    
    def import_training_data(self, data: List[Dict[str, str]]) -> int:
        """Import training data from external source."""
        with self._lock:
            imported_count = 0
            
            for item in data:
                query = item.get('query', '').strip()
                intent_str = item.get('intent', '').strip()
                
                try:
                    intent = Intent(intent_str)
                    if query:
                        self.training_data.append((query.lower(), intent))
                        imported_count += 1
                except ValueError:
                    logger.warning(f"Invalid intent value: {intent_str}")
            
            logger.info(f"Imported {imported_count} training examples")
            return imported_count


def create_intent_classifier(config: Optional[Dict[str, Any]] = None) -> IntentClassifier:
    """Factory function to create an intent classifier."""
    return IntentClassifier(config)
