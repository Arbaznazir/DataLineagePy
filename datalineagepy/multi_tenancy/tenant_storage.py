"""
Tenant Storage for Multi-Tenant DataLineagePy

Provides isolated storage capabilities for multi-tenant environments.
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StorageConfig:
    """Configuration for tenant storage."""
    base_path: str = "data/tenants"
    database_type: str = "sqlite"  # sqlite, postgresql, mysql
    max_storage_mb: int = 1000
    backup_enabled: bool = True
    encryption_enabled: bool = False
    compression_enabled: bool = True


class TenantStorage:
    """Manages isolated storage for tenants."""
    
    def __init__(self, tenant_id: str, config: Optional[StorageConfig] = None):
        self.tenant_id = tenant_id
        self.config = config or StorageConfig()
        self._lock = threading.RLock()
        
        # Setup tenant directory
        self.tenant_path = Path(self.config.base_path) / tenant_id
        self.tenant_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_path = self.tenant_path / "tenant.db"
        self._init_database()
        
        logger.info(f"TenantStorage initialized for tenant {tenant_id}")
    
    def _init_database(self) -> None:
        """Initialize the tenant database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lineage_nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lineage_edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES lineage_nodes (id),
                    FOREIGN KEY (target_id) REFERENCES lineage_nodes (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    input_nodes TEXT,
                    output_nodes TEXT,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS storage_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON lineage_nodes(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON lineage_edges(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON lineage_edges(target_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(operation_type)")
            
            conn.commit()
    
    def store_node(self, node_id: str, name: str, node_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a lineage node."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    metadata_json = json.dumps(metadata) if metadata else None
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO lineage_nodes 
                        (id, name, type, metadata, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (node_id, name, node_type, metadata_json))
                    
                    conn.commit()
                    logger.debug(f"Stored node {node_id} for tenant {self.tenant_id}")
                    return True
            
            except Exception as e:
                logger.error(f"Error storing node {node_id}: {e}")
                return False
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a lineage node."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT id, name, type, metadata, created_at, updated_at
                        FROM lineage_nodes WHERE id = ?
                    """, (node_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'id': row[0],
                            'name': row[1],
                            'type': row[2],
                            'metadata': json.loads(row[3]) if row[3] else {},
                            'created_at': row[4],
                            'updated_at': row[5]
                        }
                    
                    return None
            
            except Exception as e:
                logger.error(f"Error retrieving node {node_id}: {e}")
                return None
    
    def store_edge(self, edge_id: str, source_id: str, target_id: str, 
                   relationship_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store a lineage edge."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    metadata_json = json.dumps(metadata) if metadata else None
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO lineage_edges 
                        (id, source_id, target_id, relationship_type, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (edge_id, source_id, target_id, relationship_type, metadata_json))
                    
                    conn.commit()
                    logger.debug(f"Stored edge {edge_id} for tenant {self.tenant_id}")
                    return True
            
            except Exception as e:
                logger.error(f"Error storing edge {edge_id}: {e}")
                return False
    
    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a lineage edge."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT id, source_id, target_id, relationship_type, metadata, created_at
                        FROM lineage_edges WHERE id = ?
                    """, (edge_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'id': row[0],
                            'source_id': row[1],
                            'target_id': row[2],
                            'relationship_type': row[3],
                            'metadata': json.loads(row[4]) if row[4] else {},
                            'created_at': row[5]
                        }
                    
                    return None
            
            except Exception as e:
                logger.error(f"Error retrieving edge {edge_id}: {e}")
                return None
    
    def store_operation(self, operation_id: str, operation_type: str, 
                       input_nodes: List[str], output_nodes: List[str],
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store an operation."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    input_json = json.dumps(input_nodes)
                    output_json = json.dumps(output_nodes)
                    metadata_json = json.dumps(metadata) if metadata else None
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO operations 
                        (id, operation_type, input_nodes, output_nodes, metadata)
                        VALUES (?, ?, ?, ?, ?)
                    """, (operation_id, operation_type, input_json, output_json, metadata_json))
                    
                    conn.commit()
                    logger.debug(f"Stored operation {operation_id} for tenant {self.tenant_id}")
                    return True
            
            except Exception as e:
                logger.error(f"Error storing operation {operation_id}: {e}")
                return False
    
    def query_nodes(self, node_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Query lineage nodes."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    if node_type:
                        cursor.execute("""
                            SELECT id, name, type, metadata, created_at, updated_at
                            FROM lineage_nodes WHERE type = ?
                            ORDER BY created_at DESC LIMIT ?
                        """, (node_type, limit))
                    else:
                        cursor.execute("""
                            SELECT id, name, type, metadata, created_at, updated_at
                            FROM lineage_nodes
                            ORDER BY created_at DESC LIMIT ?
                        """, (limit,))
                    
                    rows = cursor.fetchall()
                    return [
                        {
                            'id': row[0],
                            'name': row[1],
                            'type': row[2],
                            'metadata': json.loads(row[3]) if row[3] else {},
                            'created_at': row[4],
                            'updated_at': row[5]
                        }
                        for row in rows
                    ]
            
            except Exception as e:
                logger.error(f"Error querying nodes: {e}")
                return []
    
    def query_edges(self, source_id: Optional[str] = None, target_id: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Query lineage edges."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    if source_id and target_id:
                        cursor.execute("""
                            SELECT id, source_id, target_id, relationship_type, metadata, created_at
                            FROM lineage_edges WHERE source_id = ? AND target_id = ?
                            ORDER BY created_at DESC LIMIT ?
                        """, (source_id, target_id, limit))
                    elif source_id:
                        cursor.execute("""
                            SELECT id, source_id, target_id, relationship_type, metadata, created_at
                            FROM lineage_edges WHERE source_id = ?
                            ORDER BY created_at DESC LIMIT ?
                        """, (source_id, limit))
                    elif target_id:
                        cursor.execute("""
                            SELECT id, source_id, target_id, relationship_type, metadata, created_at
                            FROM lineage_edges WHERE target_id = ?
                            ORDER BY created_at DESC LIMIT ?
                        """, (target_id, limit))
                    else:
                        cursor.execute("""
                            SELECT id, source_id, target_id, relationship_type, metadata, created_at
                            FROM lineage_edges
                            ORDER BY created_at DESC LIMIT ?
                        """, (limit,))
                    
                    rows = cursor.fetchall()
                    return [
                        {
                            'id': row[0],
                            'source_id': row[1],
                            'target_id': row[2],
                            'relationship_type': row[3],
                            'metadata': json.loads(row[4]) if row[4] else {},
                            'created_at': row[5]
                        }
                        for row in rows
                    ]
            
            except Exception as e:
                logger.error(f"Error querying edges: {e}")
                return []
    
    def store_file(self, filename: str, content: Union[str, bytes]) -> bool:
        """Store a file in tenant storage."""
        with self._lock:
            try:
                file_path = self.tenant_path / "files" / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if isinstance(content, str):
                    file_path.write_text(content, encoding='utf-8')
                else:
                    file_path.write_bytes(content)
                
                logger.debug(f"Stored file {filename} for tenant {self.tenant_id}")
                return True
            
            except Exception as e:
                logger.error(f"Error storing file {filename}: {e}")
                return False
    
    def get_file(self, filename: str) -> Optional[Union[str, bytes]]:
        """Retrieve a file from tenant storage."""
        with self._lock:
            try:
                file_path = self.tenant_path / "files" / filename
                if not file_path.exists():
                    return None
                
                # Try to read as text first
                try:
                    return file_path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    # If text fails, read as bytes
                    return file_path.read_bytes()
            
            except Exception as e:
                logger.error(f"Error retrieving file {filename}: {e}")
                return None
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from tenant storage."""
        with self._lock:
            try:
                file_path = self.tenant_path / "files" / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted file {filename} for tenant {self.tenant_id}")
                    return True
                return False
            
            except Exception as e:
                logger.error(f"Error deleting file {filename}: {e}")
                return False
    
    def list_files(self) -> List[str]:
        """List all files in tenant storage."""
        with self._lock:
            try:
                files_path = self.tenant_path / "files"
                if not files_path.exists():
                    return []
                
                return [f.name for f in files_path.iterdir() if f.is_file()]
            
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for the tenant."""
        with self._lock:
            try:
                # Database stats
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM lineage_nodes")
                    node_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM lineage_edges")
                    edge_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM operations")
                    operation_count = cursor.fetchone()[0]
                
                # File stats
                files_path = self.tenant_path / "files"
                file_count = len(list(files_path.glob("*"))) if files_path.exists() else 0
                
                # Storage size
                total_size = sum(f.stat().st_size for f in self.tenant_path.rglob("*") if f.is_file())
                
                return {
                    'tenant_id': self.tenant_id,
                    'node_count': node_count,
                    'edge_count': edge_count,
                    'operation_count': operation_count,
                    'file_count': file_count,
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'storage_limit_mb': self.config.max_storage_mb
                }
            
            except Exception as e:
                logger.error(f"Error getting storage stats: {e}")
                return {}
    
    def backup_tenant_data(self, backup_path: Optional[str] = None) -> bool:
        """Create a backup of tenant data."""
        if not self.config.backup_enabled:
            return False
        
        with self._lock:
            try:
                import shutil
                
                if not backup_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"backups/{self.tenant_id}_{timestamp}"
                
                backup_dir = Path(backup_path)
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy tenant directory
                shutil.copytree(self.tenant_path, backup_dir / "data", dirs_exist_ok=True)
                
                # Create backup metadata
                metadata = {
                    'tenant_id': self.tenant_id,
                    'backup_timestamp': datetime.now().isoformat(),
                    'stats': self.get_storage_stats()
                }
                
                (backup_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
                
                logger.info(f"Created backup for tenant {self.tenant_id} at {backup_path}")
                return True
            
            except Exception as e:
                logger.error(f"Error creating backup: {e}")
                return False
    
    def cleanup_tenant_data(self) -> bool:
        """Clean up all tenant data."""
        with self._lock:
            try:
                import shutil
                
                if self.tenant_path.exists():
                    shutil.rmtree(self.tenant_path)
                    logger.info(f"Cleaned up data for tenant {self.tenant_id}")
                    return True
                
                return False
            
            except Exception as e:
                logger.error(f"Error cleaning up tenant data: {e}")
                return False


class TenantDatabase:
    """Manages database connections for multi-tenant environments."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tenant_storages: Dict[str, TenantStorage] = {}
        self._lock = threading.RLock()
        
        logger.info("TenantDatabase initialized")
    
    def get_tenant_storage(self, tenant_id: str) -> TenantStorage:
        """Get or create tenant storage."""
        with self._lock:
            if tenant_id not in self.tenant_storages:
                storage_config = StorageConfig(**self.config.get('storage', {}))
                self.tenant_storages[tenant_id] = TenantStorage(tenant_id, storage_config)
            
            return self.tenant_storages[tenant_id]
    
    def remove_tenant_storage(self, tenant_id: str) -> bool:
        """Remove tenant storage."""
        with self._lock:
            if tenant_id in self.tenant_storages:
                storage = self.tenant_storages.pop(tenant_id)
                return storage.cleanup_tenant_data()
            
            return False
    
    def get_all_tenant_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get storage statistics for all tenants."""
        with self._lock:
            return {
                tenant_id: storage.get_storage_stats()
                for tenant_id, storage in self.tenant_storages.items()
            }


def create_tenant_storage(tenant_id: str, config: Optional[StorageConfig] = None) -> TenantStorage:
    """Factory function to create tenant storage."""
    return TenantStorage(tenant_id, config)


def create_tenant_database(config: Optional[Dict[str, Any]] = None) -> TenantDatabase:
    """Factory function to create tenant database."""
    return TenantDatabase(config)
