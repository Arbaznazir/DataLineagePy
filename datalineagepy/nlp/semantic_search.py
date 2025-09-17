"""
Semantic Search Module for DataLineagePy

Provides semantic search capabilities for data lineage exploration using
natural language queries and vector embeddings.
"""

import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
# import numpy as np  # Removed to avoid external dependency

logger = logging.getLogger(__name__)


@dataclass
class SemanticResult:
    """Represents a semantic search result."""
    id: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    highlights: List[str] = field(default_factory=list)


@dataclass
class SearchIndex:
    """Represents a search index entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    title: str = ""
    node_id: str = ""
    node_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SemanticSearch:
    """Provides semantic search capabilities for data lineage."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.index: Dict[str, SearchIndex] = {}
        self.embeddings: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
        
        # Configuration
        self.max_results = self.config.get('max_results', 10)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.embedding_dimension = self.config.get('embedding_dimension', 384)
        
        logger.info("SemanticSearch initialized")
    
    def add_to_index(self, node_id: str, title: str, content: str, 
                    node_type: str = "unknown", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add content to the search index."""
        with self._lock:
            index_entry = SearchIndex(
                content=content,
                title=title,
                node_id=node_id,
                node_type=node_type,
                metadata=metadata or {}
            )
            
            # Generate embedding (simplified - in production use proper embedding model)
            embedding = self._generate_embedding(content + " " + title)
            index_entry.embedding = embedding
            self.embeddings[index_entry.id] = embedding
            
            self.index[index_entry.id] = index_entry
            logger.debug(f"Added to index: {node_id} - {title}")
            return index_entry.id
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SemanticResult]:
        """Perform semantic search."""
        with self._lock:
            if not self.index:
                return []
            
            max_results = max_results or self.max_results
            query_embedding = self._generate_embedding(query)
            
            # Calculate similarities
            similarities = []
            for index_id, index_entry in self.index.items():
                if index_entry.embedding:
                    similarity = self._cosine_similarity(query_embedding, index_entry.embedding)
                    if similarity >= self.similarity_threshold:
                        similarities.append((index_id, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Create results
            results = []
            for index_id, score in similarities[:max_results]:
                index_entry = self.index[index_id]
                
                result = SemanticResult(
                    id=index_entry.id,
                    title=index_entry.title,
                    content=index_entry.content,
                    score=score,
                    metadata=index_entry.metadata,
                    node_id=index_entry.node_id,
                    node_type=index_entry.node_type,
                    highlights=self._extract_highlights(query, index_entry.content)
                )
                results.append(result)
            
            logger.info(f"Semantic search for '{query}' returned {len(results)} results")
            return results
    
    def search_by_node_type(self, node_type: str, query: Optional[str] = None) -> List[SemanticResult]:
        """Search for nodes of a specific type."""
        with self._lock:
            filtered_entries = [
                entry for entry in self.index.values()
                if entry.node_type == node_type
            ]
            
            if not query:
                # Return all entries of this type
                results = []
                for entry in filtered_entries:
                    result = SemanticResult(
                        id=entry.id,
                        title=entry.title,
                        content=entry.content,
                        score=1.0,
                        metadata=entry.metadata,
                        node_id=entry.node_id,
                        node_type=entry.node_type
                    )
                    results.append(result)
                return results
            
            # Perform semantic search within filtered entries
            query_embedding = self._generate_embedding(query)
            similarities = []
            
            for entry in filtered_entries:
                if entry.embedding:
                    similarity = self._cosine_similarity(query_embedding, entry.embedding)
                    if similarity >= self.similarity_threshold:
                        similarities.append((entry, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for entry, score in similarities[:self.max_results]:
                result = SemanticResult(
                    id=entry.id,
                    title=entry.title,
                    content=entry.content,
                    score=score,
                    metadata=entry.metadata,
                    node_id=entry.node_id,
                    node_type=entry.node_type,
                    highlights=self._extract_highlights(query, entry.content)
                )
                results.append(result)
            
            return results
    
    def update_index_entry(self, index_id: str, title: Optional[str] = None, 
                          content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update an existing index entry."""
        with self._lock:
            if index_id not in self.index:
                return False
            
            entry = self.index[index_id]
            
            if title is not None:
                entry.title = title
            if content is not None:
                entry.content = content
            if metadata is not None:
                entry.metadata.update(metadata)
            
            # Regenerate embedding if content changed
            if title is not None or content is not None:
                embedding = self._generate_embedding(entry.content + " " + entry.title)
                entry.embedding = embedding
                self.embeddings[index_id] = embedding
            
            entry.updated_at = datetime.now()
            logger.debug(f"Updated index entry: {index_id}")
            return True
    
    def remove_from_index(self, index_id: str) -> bool:
        """Remove an entry from the search index."""
        with self._lock:
            if index_id in self.index:
                del self.index[index_id]
                self.embeddings.pop(index_id, None)
                logger.debug(f"Removed from index: {index_id}")
                return True
            return False
    
    def remove_by_node_id(self, node_id: str) -> int:
        """Remove all entries for a specific node ID."""
        with self._lock:
            entries_to_remove = [
                index_id for index_id, entry in self.index.items()
                if entry.node_id == node_id
            ]
            
            for index_id in entries_to_remove:
                del self.index[index_id]
                self.embeddings.pop(index_id, None)
            
            logger.debug(f"Removed {len(entries_to_remove)} entries for node {node_id}")
            return len(entries_to_remove)
    
    def get_similar_nodes(self, node_id: str, max_results: Optional[int] = None) -> List[SemanticResult]:
        """Find nodes similar to a given node."""
        with self._lock:
            # Find the node in the index
            target_entry = None
            for entry in self.index.values():
                if entry.node_id == node_id:
                    target_entry = entry
                    break
            
            if not target_entry or not target_entry.embedding:
                return []
            
            max_results = max_results or self.max_results
            similarities = []
            
            for index_id, entry in self.index.items():
                if entry.node_id != node_id and entry.embedding:
                    similarity = self._cosine_similarity(target_entry.embedding, entry.embedding)
                    if similarity >= self.similarity_threshold:
                        similarities.append((entry, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for entry, score in similarities[:max_results]:
                result = SemanticResult(
                    id=entry.id,
                    title=entry.title,
                    content=entry.content,
                    score=score,
                    metadata=entry.metadata,
                    node_id=entry.node_id,
                    node_type=entry.node_type
                )
                results.append(result)
            
            return results
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (simplified implementation)."""
        # In production, use proper embedding models like sentence-transformers
        # This is a simplified hash-based approach for demonstration
        import hashlib
        
        # Simple hash-based embedding
        hash_obj = hashlib.md5(text.lower().encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to normalized vector
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                value = int.from_bytes(chunk, 'big') / (2**32)
                embedding.append(value)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.embedding_dimension:
            embedding.append(0.0)
        embedding = embedding[:self.embedding_dimension]
        
        # Normalize
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _extract_highlights(self, query: str, content: str, max_highlights: int = 3) -> List[str]:
        """Extract highlighted snippets from content."""
        query_words = query.lower().split()
        content_lower = content.lower()
        
        highlights = []
        for word in query_words:
            if word in content_lower:
                # Find the position and extract surrounding context
                pos = content_lower.find(word)
                start = max(0, pos - 50)
                end = min(len(content), pos + len(word) + 50)
                
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                
                highlights.append(snippet)
                
                if len(highlights) >= max_highlights:
                    break
        
        return highlights
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index."""
        with self._lock:
            node_types = {}
            for entry in self.index.values():
                node_type = entry.node_type
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            return {
                'total_entries': len(self.index),
                'node_types': node_types,
                'embedding_dimension': self.embedding_dimension,
                'similarity_threshold': self.similarity_threshold
            }
    
    def clear_index(self) -> None:
        """Clear the entire search index."""
        with self._lock:
            self.index.clear()
            self.embeddings.clear()
            logger.info("Search index cleared")


def create_semantic_search(config: Optional[Dict[str, Any]] = None) -> SemanticSearch:
    """Factory function to create a semantic search instance."""
    return SemanticSearch(config)
