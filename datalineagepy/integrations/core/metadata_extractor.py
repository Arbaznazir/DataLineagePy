"""
Metadata extractor for enterprise integrations.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Type
from datetime import datetime
from enum import Enum
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MetadataType(Enum):
    """Types of metadata."""
    TABLE = "table"
    VIEW = "view"
    COLUMN = "column"
    SCHEMA = "schema"
    DATABASE = "database"
    WAREHOUSE = "warehouse"
    WORKBOOK = "workbook"
    DASHBOARD = "dashboard"
    DATASOURCE = "datasource"
    REPORT = "report"
    DATASET = "dataset"
    PIPELINE = "pipeline"
    JOB = "job"
    FUNCTION = "function"
    PROCEDURE = "procedure"
    INDEX = "index"
    CONSTRAINT = "constraint"
    TRIGGER = "trigger"
    PARTITION = "partition"
    CLUSTER = "cluster"
    TOPIC = "topic"
    QUEUE = "queue"
    STREAM = "stream"
    BUCKET = "bucket"
    FILE = "file"
    FOLDER = "folder"


class DataType(Enum):
    """Data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    DECIMAL = "decimal"
    JSON = "json"
    ARRAY = "array"
    OBJECT = "object"
    BINARY = "binary"
    TEXT = "text"
    UUID = "uuid"
    UNKNOWN = "unknown"


@dataclass
class ColumnMetadata:
    """Column metadata information."""
    name: str
    data_type: DataType
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'data_type': self.data_type.value,
            'is_nullable': self.is_nullable,
            'is_primary_key': self.is_primary_key,
            'is_foreign_key': self.is_foreign_key,
            'default_value': self.default_value,
            'max_length': self.max_length,
            'precision': self.precision,
            'scale': self.scale,
            'description': self.description,
            'tags': self.tags,
            'constraints': self.constraints
        }


@dataclass
class MetadataSchema:
    """Metadata schema definition."""
    entity_id: str
    entity_type: MetadataType
    name: str
    system: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    owner: Optional[str] = None
    location: Optional[str] = None
    size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    columns: List[ColumnMetadata] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    classification: Optional[str] = None
    sensitivity_level: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'system': self.system,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'description': self.description,
            'owner': self.owner,
            'location': self.location,
            'size_bytes': self.size_bytes,
            'row_count': self.row_count,
            'columns': [col.to_dict() for col in self.columns],
            'properties': self.properties,
            'tags': self.tags,
            'classification': self.classification,
            'sensitivity_level': self.sensitivity_level
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class BaseMetadataExtractor(ABC):
    """Base class for metadata extractors."""
    
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.extracted_metadata: Dict[str, MetadataSchema] = {}
        self.extraction_stats = {
            'total_entities': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'extraction_time': 0.0,
            'last_extraction': None
        }
    
    @abstractmethod
    async def extract_metadata(self, entity_id: Optional[str] = None) -> List[MetadataSchema]:
        """Extract metadata from the system."""
        pass
    
    @abstractmethod
    async def extract_schema_metadata(self, schema_name: str) -> List[MetadataSchema]:
        """Extract metadata for a specific schema."""
        pass
    
    @abstractmethod
    async def extract_table_metadata(self, table_name: str) -> MetadataSchema:
        """Extract metadata for a specific table."""
        pass
    
    async def get_cached_metadata(self, entity_id: str) -> Optional[MetadataSchema]:
        """Get cached metadata."""
        return self.extracted_metadata.get(entity_id)
    
    async def cache_metadata(self, metadata: MetadataSchema):
        """Cache metadata."""
        self.extracted_metadata[metadata.entity_id] = metadata
    
    async def clear_cache(self):
        """Clear metadata cache."""
        self.extracted_metadata.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.extraction_stats.copy()


class MetadataExtractor:
    """Main metadata extractor that coordinates different extractors."""
    
    def __init__(self):
        self.extractors: Dict[str, BaseMetadataExtractor] = {}
        self.metadata_cache: Dict[str, MetadataSchema] = {}
        self.extraction_history: List[Dict[str, Any]] = []
        self.stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'systems_count': 0,
            'entities_count': 0
        }
    
    def register_extractor(self, system_name: str, extractor: BaseMetadataExtractor):
        """Register a metadata extractor for a system."""
        self.extractors[system_name] = extractor
        self.stats['systems_count'] = len(self.extractors)
        logger.info(f"Registered metadata extractor for {system_name}")
    
    def unregister_extractor(self, system_name: str):
        """Unregister a metadata extractor."""
        if system_name in self.extractors:
            del self.extractors[system_name]
            self.stats['systems_count'] = len(self.extractors)
            logger.info(f"Unregistered metadata extractor for {system_name}")
    
    async def extract_all_metadata(self) -> Dict[str, List[MetadataSchema]]:
        """Extract metadata from all registered systems."""
        results = {}
        
        for system_name, extractor in self.extractors.items():
            try:
                start_time = datetime.utcnow()
                metadata_list = await extractor.extract_metadata()
                end_time = datetime.utcnow()
                
                results[system_name] = metadata_list
                
                # Cache metadata
                for metadata in metadata_list:
                    await self.cache_metadata(metadata)
                
                # Update stats
                self.stats['total_extractions'] += 1
                self.stats['successful_extractions'] += 1
                self.stats['entities_count'] += len(metadata_list)
                
                # Record extraction history
                self.extraction_history.append({
                    'system': system_name,
                    'timestamp': start_time,
                    'duration': (end_time - start_time).total_seconds(),
                    'entities_extracted': len(metadata_list),
                    'success': True
                })
                
                logger.info(f"Extracted {len(metadata_list)} entities from {system_name}")
                
            except Exception as e:
                self.stats['total_extractions'] += 1
                self.stats['failed_extractions'] += 1
                
                self.extraction_history.append({
                    'system': system_name,
                    'timestamp': datetime.utcnow(),
                    'duration': 0,
                    'entities_extracted': 0,
                    'success': False,
                    'error': str(e)
                })
                
                logger.error(f"Failed to extract metadata from {system_name}: {e}")
                results[system_name] = []
        
        return results
    
    async def extract_system_metadata(self, system_name: str) -> List[MetadataSchema]:
        """Extract metadata from a specific system."""
        if system_name not in self.extractors:
            raise ValueError(f"No extractor registered for system: {system_name}")
        
        extractor = self.extractors[system_name]
        return await extractor.extract_metadata()
    
    async def extract_entity_metadata(self, system_name: str, entity_id: str) -> MetadataSchema:
        """Extract metadata for a specific entity."""
        if system_name not in self.extractors:
            raise ValueError(f"No extractor registered for system: {system_name}")
        
        # Check cache first
        cached_metadata = await self.get_cached_metadata(entity_id)
        if cached_metadata:
            return cached_metadata
        
        extractor = self.extractors[system_name]
        
        # Try to extract specific entity
        if hasattr(extractor, 'extract_entity_metadata'):
            metadata = await extractor.extract_entity_metadata(entity_id)
        else:
            # Fallback to extracting all and filtering
            all_metadata = await extractor.extract_metadata()
            metadata = next((m for m in all_metadata if m.entity_id == entity_id), None)
            
            if not metadata:
                raise ValueError(f"Entity {entity_id} not found in {system_name}")
        
        await self.cache_metadata(metadata)
        return metadata
    
    async def cache_metadata(self, metadata: MetadataSchema):
        """Cache metadata."""
        self.metadata_cache[metadata.entity_id] = metadata
    
    async def get_cached_metadata(self, entity_id: str) -> Optional[MetadataSchema]:
        """Get cached metadata."""
        return self.metadata_cache.get(entity_id)
    
    async def search_metadata(self, 
                            query: str,
                            entity_type: Optional[MetadataType] = None,
                            system: Optional[str] = None,
                            tags: Optional[List[str]] = None) -> List[MetadataSchema]:
        """Search metadata based on criteria."""
        results = []
        
        for metadata in self.metadata_cache.values():
            # Filter by system
            if system and metadata.system != system:
                continue
            
            # Filter by entity type
            if entity_type and metadata.entity_type != entity_type:
                continue
            
            # Filter by tags
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            # Search in name and description
            if (query.lower() in metadata.name.lower() or 
                (metadata.description and query.lower() in metadata.description.lower())):
                results.append(metadata)
                continue
            
            # Search in column names
            for column in metadata.columns:
                if query.lower() in column.name.lower():
                    results.append(metadata)
                    break
        
        return results
    
    async def get_metadata_by_system(self, system_name: str) -> List[MetadataSchema]:
        """Get all metadata for a specific system."""
        return [m for m in self.metadata_cache.values() if m.system == system_name]
    
    async def get_metadata_by_type(self, entity_type: MetadataType) -> List[MetadataSchema]:
        """Get all metadata for a specific entity type."""
        return [m for m in self.metadata_cache.values() if m.entity_type == entity_type]
    
    async def get_metadata_summary(self) -> Dict[str, Any]:
        """Get metadata summary."""
        summary = {
            'total_entities': len(self.metadata_cache),
            'systems': {},
            'entity_types': {},
            'tags': {},
            'owners': {}
        }
        
        for metadata in self.metadata_cache.values():
            # Count by system
            if metadata.system not in summary['systems']:
                summary['systems'][metadata.system] = 0
            summary['systems'][metadata.system] += 1
            
            # Count by entity type
            entity_type = metadata.entity_type.value
            if entity_type not in summary['entity_types']:
                summary['entity_types'][entity_type] = 0
            summary['entity_types'][entity_type] += 1
            
            # Count tags
            for tag in metadata.tags:
                if tag not in summary['tags']:
                    summary['tags'][tag] = 0
                summary['tags'][tag] += 1
            
            # Count owners
            if metadata.owner:
                if metadata.owner not in summary['owners']:
                    summary['owners'][metadata.owner] = 0
                summary['owners'][metadata.owner] += 1
        
        return summary
    
    async def export_metadata(self, format: str = 'json') -> str:
        """Export metadata in specified format."""
        if format.lower() == 'json':
            metadata_list = [m.to_dict() for m in self.metadata_cache.values()]
            return json.dumps(metadata_list, indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'entity_id', 'entity_type', 'name', 'system', 'description',
                'owner', 'location', 'size_bytes', 'row_count', 'tags'
            ])
            
            # Write data
            for metadata in self.metadata_cache.values():
                writer.writerow([
                    metadata.entity_id,
                    metadata.entity_type.value,
                    metadata.name,
                    metadata.system,
                    metadata.description or '',
                    metadata.owner or '',
                    metadata.location or '',
                    metadata.size_bytes or '',
                    metadata.row_count or '',
                    ','.join(metadata.tags)
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            **self.stats,
            'cached_entities': len(self.metadata_cache),
            'extraction_history_count': len(self.extraction_history)
        }
    
    def get_extraction_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get extraction history."""
        history = sorted(self.extraction_history, key=lambda x: x['timestamp'], reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    async def clear_cache(self):
        """Clear metadata cache."""
        self.metadata_cache.clear()
        logger.info("Metadata cache cleared")
    
    async def refresh_metadata(self, system_name: Optional[str] = None):
        """Refresh metadata from systems."""
        if system_name:
            if system_name in self.extractors:
                await self.extract_system_metadata(system_name)
            else:
                raise ValueError(f"No extractor registered for system: {system_name}")
        else:
            await self.extract_all_metadata()
        
        logger.info("Metadata refreshed")


def create_metadata_extractor() -> MetadataExtractor:
    """Factory function to create metadata extractor."""
    return MetadataExtractor()


def create_column_metadata(name: str, 
                          data_type: Union[DataType, str],
                          **kwargs) -> ColumnMetadata:
    """Factory function to create column metadata."""
    if isinstance(data_type, str):
        data_type = DataType(data_type.lower())
    
    return ColumnMetadata(name=name, data_type=data_type, **kwargs)


def create_metadata_schema(entity_id: str,
                          entity_type: Union[MetadataType, str],
                          name: str,
                          system: str,
                          **kwargs) -> MetadataSchema:
    """Factory function to create metadata schema."""
    if isinstance(entity_type, str):
        entity_type = MetadataType(entity_type.lower())
    
    return MetadataSchema(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        system=system,
        **kwargs
    )
