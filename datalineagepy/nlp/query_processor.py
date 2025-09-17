"""
Natural Language Query Processor for DataLineagePy

Processes natural language queries and converts them to structured data lineage queries.
"""

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from threading import Lock
import difflib

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Query type enumeration."""
    LINEAGE_SEARCH = "lineage_search"
    DATA_DISCOVERY = "data_discovery"
    IMPACT_ANALYSIS = "impact_analysis"
    SCHEMA_SEARCH = "schema_search"
    METADATA_SEARCH = "metadata_search"
    RELATIONSHIP_SEARCH = "relationship_search"
    QUALITY_SEARCH = "quality_search"
    USAGE_SEARCH = "usage_search"

class EntityType(Enum):
    """Entity type enumeration."""
    TABLE = "table"
    COLUMN = "column"
    DATABASE = "database"
    SCHEMA = "schema"
    PIPELINE = "pipeline"
    JOB = "job"
    USER = "user"
    APPLICATION = "application"
    SYSTEM = "system"
    METRIC = "metric"

@dataclass
class QueryEntity:
    """Represents an entity extracted from a query."""
    text: str
    entity_type: EntityType
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryIntent:
    """Represents the intent of a query."""
    intent_type: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NLQuery:
    """Represents a natural language query."""
    id: str
    text: str
    language: str = "en"
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert query to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "language": self.language,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "metadata": self.metadata
        }

@dataclass
class QueryResult:
    """Represents the result of query processing."""
    query_id: str
    query_type: QueryType
    intent: QueryIntent
    entities: List[QueryEntity]
    structured_query: Dict[str, Any]
    confidence: float
    suggestions: List[str] = field(default_factory=list)
    corrections: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "query_id": self.query_id,
            "query_type": self.query_type.value,
            "intent": {
                "intent_type": self.intent.intent_type,
                "confidence": self.intent.confidence,
                "parameters": self.intent.parameters
            },
            "entities": [
                {
                    "text": e.text,
                    "entity_type": e.entity_type.value,
                    "confidence": e.confidence,
                    "start_pos": e.start_pos,
                    "end_pos": e.end_pos,
                    "metadata": e.metadata
                }
                for e in self.entities
            ],
            "structured_query": self.structured_query,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
            "corrections": self.corrections,
            "execution_time": self.execution_time,
            "metadata": self.metadata
        }

class QueryProcessor:
    """Natural language query processor."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.lock = Lock()
        
        # Configuration
        self.max_query_length = self.config.get("max_query_length", 500)
        self.supported_languages = self.config.get("supported_languages", ["en"])
        self.enable_spell_check = self.config.get("enable_spell_check", True)
        self.enable_autocomplete = self.config.get("enable_autocomplete", True)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_results = self.config.get("max_results", 50)
        self.enable_caching = self.config.get("enable_caching", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)
        
        # Query cache
        self.query_cache: Dict[str, QueryResult] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cached_queries": 0,
            "average_confidence": 0.0,
            "average_execution_time": 0.0
        }
        
        # Initialize patterns and vocabularies
        self._initialize_patterns()
        self._initialize_vocabulary()
        
    async def start(self):
        """Start the query processor."""
        logger.info("Starting query processor")
        
    async def stop(self):
        """Stop the query processor."""
        logger.info("Stopping query processor")
        
    async def process_query(self, query_text: str, user_id: str = None,
                           language: str = "en") -> QueryResult:
        """Process a natural language query."""
        start_time = datetime.now()
        
        # Create query object
        query_id = f"query_{uuid.uuid4().hex[:8]}"
        query = NLQuery(
            id=query_id,
            text=query_text.strip(),
            language=language,
            user_id=user_id
        )
        
        # Check cache
        if self.enable_caching:
            cache_key = self._get_cache_key(query_text, language)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.stats["cached_queries"] += 1
                return cached_result
        
        try:
            # Validate query
            validation_result = await self._validate_query(query)
            if not validation_result["valid"]:
                raise ValueError(validation_result["error"])
            
            # Preprocess query
            preprocessed_text = await self._preprocess_query(query.text)
            
            # Extract entities
            entities = await self._extract_entities(preprocessed_text)
            
            # Classify intent
            intent = await self._classify_intent(preprocessed_text, entities)
            
            # Determine query type
            query_type = await self._determine_query_type(intent, entities)
            
            # Build structured query
            structured_query = await self._build_structured_query(
                query_type, intent, entities, preprocessed_text
            )
            
            # Calculate confidence
            confidence = await self._calculate_confidence(intent, entities, structured_query)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(query_text, entities, intent)
            
            # Create result
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = QueryResult(
                query_id=query_id,
                query_type=query_type,
                intent=intent,
                entities=entities,
                structured_query=structured_query,
                confidence=confidence,
                suggestions=suggestions,
                execution_time=execution_time
            )
            
            # Cache result
            if self.enable_caching and confidence >= self.confidence_threshold:
                self._cache_result(cache_key, result)
            
            # Update statistics
            self.stats["total_queries"] += 1
            self.stats["successful_queries"] += 1
            self._update_average_stats(confidence, execution_time)
            
            query.processed = True
            
            logger.info(f"Processed query {query_id} with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            
            # Return error result
            return QueryResult(
                query_id=query_id,
                query_type=QueryType.DATA_DISCOVERY,
                intent=QueryIntent("error", 0.0, {"error": str(e)}),
                entities=[],
                structured_query={},
                confidence=0.0,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )
    
    async def get_autocomplete_suggestions(self, partial_query: str,
                                         limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for partial query."""
        if not self.enable_autocomplete or len(partial_query) < 2:
            return []
        
        suggestions = []
        
        # Entity-based suggestions
        for entity_type in EntityType:
            if entity_type.value.startswith(partial_query.lower()):
                suggestions.append(f"Find all {entity_type.value}s")
        
        # Pattern-based suggestions
        for pattern in self.query_patterns:
            if pattern.lower().startswith(partial_query.lower()):
                suggestions.append(pattern)
        
        # Common query templates
        templates = [
            "Show me the lineage of {table}",
            "What tables are downstream from {table}",
            "Find all columns containing {keyword}",
            "Show data quality issues for {table}",
            "What is the impact of changing {column}",
            "Find all pipelines using {table}",
            "Show me recent changes to {schema}",
            "What systems connect to {database}"
        ]
        
        for template in templates:
            if template.lower().startswith(partial_query.lower()):
                suggestions.append(template)
        
        return suggestions[:limit]
    
    async def spell_check(self, query_text: str) -> List[str]:
        """Check spelling and suggest corrections."""
        if not self.enable_spell_check:
            return []
        
        corrections = []
        words = query_text.split()
        
        for word in words:
            if word.lower() not in self.vocabulary:
                # Find closest matches
                matches = difflib.get_close_matches(
                    word.lower(), self.vocabulary, n=3, cutoff=0.6
                )
                if matches:
                    corrections.append(f"Did you mean '{matches[0]}' instead of '{word}'?")
        
        return corrections
    
    async def get_query_statistics(self) -> Dict[str, Any]:
        """Get query processing statistics."""
        return {
            **self.stats,
            "cache_size": len(self.query_cache),
            "supported_languages": self.supported_languages,
            "confidence_threshold": self.confidence_threshold
        }
    
    async def clear_cache(self):
        """Clear the query cache."""
        with self.lock:
            self.query_cache.clear()
            self.cache_timestamps.clear()
        
        logger.info("Query cache cleared")
    
    async def _validate_query(self, query: NLQuery) -> Dict[str, Any]:
        """Validate a query."""
        if not query.text:
            return {"valid": False, "error": "Empty query"}
        
        if len(query.text) > self.max_query_length:
            return {"valid": False, "error": f"Query too long (max {self.max_query_length} characters)"}
        
        if query.language not in self.supported_languages:
            return {"valid": False, "error": f"Unsupported language: {query.language}"}
        
        return {"valid": True}
    
    async def _preprocess_query(self, query_text: str) -> str:
        """Preprocess query text."""
        # Convert to lowercase
        text = query_text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Expand contractions
        contractions = {
            "what's": "what is",
            "where's": "where is",
            "how's": "how is",
            "who's": "who is",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "couldn't": "could not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    async def _extract_entities(self, text: str) -> List[QueryEntity]:
        """Extract entities from query text."""
        entities = []
        
        # Simple pattern-based entity extraction
        entity_patterns = {
            EntityType.TABLE: [
                r'\btable\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+table'
            ],
            EntityType.COLUMN: [
                r'\bcolumn\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\bfield\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+column'
            ],
            EntityType.DATABASE: [
                r'\bdatabase\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\bdb\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+database'
            ],
            EntityType.SCHEMA: [
                r'\bschema\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+schema'
            ],
            EntityType.PIPELINE: [
                r'\bpipeline\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\bjob\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s+pipeline'
            ]
        }
        
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1)
                    entities.append(QueryEntity(
                        text=entity_text,
                        entity_type=entity_type,
                        confidence=0.8,
                        start_pos=match.start(1),
                        end_pos=match.end(1)
                    ))
        
        return entities
    
    async def _classify_intent(self, text: str, entities: List[QueryEntity]) -> QueryIntent:
        """Classify the intent of the query."""
        # Simple rule-based intent classification
        intent_patterns = {
            "find_data": [
                r'\bfind\b', r'\bsearch\b', r'\bshow\b', r'\blist\b', r'\bget\b'
            ],
            "trace_lineage": [
                r'\blineage\b', r'\btrace\b', r'\btrack\b', r'\bfollow\b'
            ],
            "analyze_impact": [
                r'\bimpact\b', r'\baffect\b', r'\bdownstream\b', r'\bupstream\b'
            ],
            "check_quality": [
                r'\bquality\b', r'\bissue\b', r'\berror\b', r'\bproblem\b'
            ],
            "get_metadata": [
                r'\bmetadata\b', r'\binfo\b', r'\binformation\b', r'\bdetails\b'
            ]
        }
        
        intent_scores = {}
        
        for intent_type, patterns in intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                intent_scores[intent_type] = score / len(patterns)
        
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[best_intent])
        else:
            best_intent = "find_data"
            confidence = 0.5
        
        return QueryIntent(
            intent_type=best_intent,
            confidence=confidence,
            parameters={"entities": [e.text for e in entities]}
        )
    
    async def _determine_query_type(self, intent: QueryIntent,
                                   entities: List[QueryEntity]) -> QueryType:
        """Determine the query type based on intent and entities."""
        intent_to_type = {
            "find_data": QueryType.DATA_DISCOVERY,
            "trace_lineage": QueryType.LINEAGE_SEARCH,
            "analyze_impact": QueryType.IMPACT_ANALYSIS,
            "check_quality": QueryType.QUALITY_SEARCH,
            "get_metadata": QueryType.METADATA_SEARCH
        }
        
        return intent_to_type.get(intent.intent_type, QueryType.DATA_DISCOVERY)
    
    async def _build_structured_query(self, query_type: QueryType, intent: QueryIntent,
                                     entities: List[QueryEntity], text: str) -> Dict[str, Any]:
        """Build structured query from natural language components."""
        structured_query = {
            "type": query_type.value,
            "intent": intent.intent_type,
            "entities": {},
            "filters": {},
            "options": {}
        }
        
        # Group entities by type
        for entity in entities:
            entity_type = entity.entity_type.value
            if entity_type not in structured_query["entities"]:
                structured_query["entities"][entity_type] = []
            structured_query["entities"][entity_type].append(entity.text)
        
        # Extract filters from text
        if "recent" in text or "latest" in text:
            structured_query["filters"]["time_range"] = "recent"
        
        if "all" in text:
            structured_query["options"]["include_all"] = True
        
        return structured_query
    
    async def _calculate_confidence(self, intent: QueryIntent, entities: List[QueryEntity],
                                   structured_query: Dict[str, Any]) -> float:
        """Calculate overall confidence score."""
        scores = [intent.confidence]
        
        # Entity confidence
        if entities:
            entity_confidence = sum(e.confidence for e in entities) / len(entities)
            scores.append(entity_confidence)
        
        # Structured query completeness
        completeness = 0.0
        if structured_query.get("entities"):
            completeness += 0.5
        if structured_query.get("filters"):
            completeness += 0.3
        if structured_query.get("options"):
            completeness += 0.2
        
        scores.append(completeness)
        
        return sum(scores) / len(scores)
    
    async def _generate_suggestions(self, query_text: str, entities: List[QueryEntity],
                                   intent: QueryIntent) -> List[str]:
        """Generate query suggestions."""
        suggestions = []
        
        # Entity-based suggestions
        for entity in entities:
            if entity.entity_type == EntityType.TABLE:
                suggestions.append(f"Show lineage for table {entity.text}")
                suggestions.append(f"Find columns in table {entity.text}")
        
        # Intent-based suggestions
        if intent.intent_type == "find_data":
            suggestions.append("Show me all tables")
            suggestions.append("Find tables with quality issues")
        
        return suggestions[:5]
    
    def _get_cache_key(self, query_text: str, language: str) -> str:
        """Generate cache key for query."""
        import hashlib
        content = f"{query_text}:{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[QueryResult]:
        """Get cached query result."""
        if cache_key not in self.query_cache:
            return None
        
        # Check if cache is expired
        cache_time = self.cache_timestamps.get(cache_key)
        if cache_time and (datetime.now() - cache_time).total_seconds() > self.cache_ttl:
            del self.query_cache[cache_key]
            del self.cache_timestamps[cache_key]
            return None
        
        return self.query_cache[cache_key]
    
    def _cache_result(self, cache_key: str, result: QueryResult):
        """Cache query result."""
        with self.lock:
            self.query_cache[cache_key] = result
            self.cache_timestamps[cache_key] = datetime.now()
    
    def _update_average_stats(self, confidence: float, execution_time: float):
        """Update average statistics."""
        total = self.stats["successful_queries"]
        
        # Update average confidence
        current_avg_conf = self.stats["average_confidence"]
        self.stats["average_confidence"] = (
            (current_avg_conf * (total - 1) + confidence) / total
        )
        
        # Update average execution time
        current_avg_time = self.stats["average_execution_time"]
        self.stats["average_execution_time"] = (
            (current_avg_time * (total - 1) + execution_time) / total
        )
    
    def _initialize_patterns(self):
        """Initialize query patterns."""
        self.query_patterns = [
            "Show me the lineage of",
            "Find all tables",
            "What is the impact of",
            "Show data quality issues",
            "Find columns containing",
            "What tables are downstream",
            "Show me recent changes",
            "Find all pipelines using",
            "What systems connect to",
            "Show metadata for"
        ]
    
    def _initialize_vocabulary(self):
        """Initialize vocabulary for spell checking."""
        self.vocabulary = {
            # Data terms
            "table", "column", "database", "schema", "pipeline", "job", "data",
            "lineage", "metadata", "quality", "impact", "downstream", "upstream",
            "transformation", "source", "target", "system", "application",
            
            # Query terms
            "find", "show", "search", "get", "list", "trace", "track", "follow",
            "analyze", "check", "what", "where", "how", "when", "who", "which",
            "all", "recent", "latest", "new", "old", "containing", "using",
            
            # Common words
            "the", "of", "in", "to", "for", "with", "by", "from", "on", "at",
            "is", "are", "was", "were", "be", "been", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "can",
            "may", "might", "must", "shall", "and", "or", "but", "not", "no"
        }
