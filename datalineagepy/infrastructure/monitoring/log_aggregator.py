"""
Log Aggregator Implementation
Centralized log collection, processing, and analysis system.
"""

import time
import threading
import logging
import json
import re
import gzip
import os
from typing import Dict, List, Optional, Callable, Any, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import queue

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0


class LogSource(Enum):
    """Log sources."""
    APPLICATION = "application"
    SYSTEM = "system"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


@dataclass
class LogEntry:
    """Individual log entry."""
    timestamp: float
    level: LogLevel
    source: LogSource
    logger_name: str
    message: str
    
    # Optional fields
    thread_id: Optional[str] = None
    process_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Structured data
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Exception information
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            "timestamp": self.timestamp,
            "level": self.level.name,
            "source": self.source.value,
            "logger_name": self.logger_name,
            "message": self.message,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "labels": self.labels,
            "metadata": self.metadata,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "stack_trace": self.stack_trace
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create log entry from dictionary."""
        return cls(
            timestamp=data.get("timestamp", time.time()),
            level=LogLevel[data.get("level", "INFO")],
            source=LogSource(data.get("source", "application")),
            logger_name=data.get("logger_name", ""),
            message=data.get("message", ""),
            thread_id=data.get("thread_id"),
            process_id=data.get("process_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            labels=data.get("labels", {}),
            metadata=data.get("metadata", {}),
            exception_type=data.get("exception_type"),
            exception_message=data.get("exception_message"),
            stack_trace=data.get("stack_trace")
        )


@dataclass
class LogFilter:
    """Log filtering configuration."""
    min_level: Optional[LogLevel] = None
    max_level: Optional[LogLevel] = None
    sources: Optional[List[LogSource]] = None
    logger_names: Optional[List[str]] = None
    time_range: Optional[tuple] = None  # (start_time, end_time)
    
    # Text filters
    message_contains: Optional[str] = None
    message_regex: Optional[str] = None
    
    # Label filters
    required_labels: Optional[Dict[str, str]] = None
    excluded_labels: Optional[Dict[str, str]] = None
    
    # User/session filters
    user_ids: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None
    request_ids: Optional[List[str]] = None


@dataclass
class LogAggregation:
    """Log aggregation result."""
    time_bucket: str
    count: int
    levels: Dict[str, int]
    sources: Dict[str, int]
    top_loggers: Dict[str, int]
    error_count: int
    warning_count: int
    
    # Time range
    start_time: float
    end_time: float


class LogHandler(logging.Handler):
    """Custom log handler for log aggregator."""
    
    def __init__(self, aggregator: 'LogAggregator', source: LogSource = LogSource.APPLICATION):
        """
        Initialize log handler.
        
        Args:
            aggregator: Log aggregator instance
            source: Log source type
        """
        super().__init__()
        self.aggregator = aggregator
        self.source = source
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record."""
        try:
            # Convert logging record to LogEntry
            log_entry = LogEntry(
                timestamp=record.created,
                level=LogLevel(record.levelno),
                source=self.source,
                logger_name=record.name,
                message=record.getMessage(),
                thread_id=str(record.thread),
                process_id=str(record.process),
                labels={
                    "module": record.module,
                    "function": record.funcName,
                    "line": str(record.lineno)
                }
            )
            
            # Add exception information if present
            if record.exc_info:
                log_entry.exception_type = record.exc_info[0].__name__
                log_entry.exception_message = str(record.exc_info[1])
                log_entry.stack_trace = self.format(record)
            
            # Send to aggregator
            self.aggregator.add_log_entry(log_entry)
            
        except Exception:
            self.handleError(record)


class LogAggregator:
    """
    Enterprise-grade log aggregation system.
    
    Features:
    - Centralized log collection from multiple sources
    - Real-time log processing and indexing
    - Advanced filtering and search capabilities
    - Log aggregation and analytics
    - Configurable retention policies
    - Export to external systems (ELK, Splunk, etc.)
    - Performance monitoring and alerting integration
    """
    
    def __init__(self, max_entries: int = 1000000, retention_days: int = 30):
        """
        Initialize log aggregator.
        
        Args:
            max_entries: Maximum number of log entries to keep in memory
            retention_days: Log retention period in days
        """
        self.max_entries = max_entries
        self.retention_days = retention_days
        
        # Log storage
        self.log_entries: deque = deque(maxlen=max_entries)
        self.log_index: Dict[str, List[int]] = defaultdict(list)  # Index for fast searching
        
        # Processing queue
        self.processing_queue: queue.Queue = queue.Queue(maxsize=10000)
        
        # Threading
        self.lock = threading.RLock()
        self.processing_thread = None
        self.cleanup_thread = None
        self.running = False
        
        # Export backends
        self.export_backends: List[Callable[[List[LogEntry]], None]] = []
        
        # Statistics
        self.total_logs_processed = 0
        self.total_logs_exported = 0
        self.processing_errors = 0
        self.start_time = time.time()
        
        # Aggregation cache
        self.aggregation_cache: Dict[str, LogAggregation] = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("Log aggregator initialized")
    
    def add_log_entry(self, entry: LogEntry) -> bool:
        """
        Add a log entry for processing.
        
        Args:
            entry: Log entry to add
            
        Returns:
            True if entry was queued successfully
        """
        try:
            self.processing_queue.put(entry, timeout=1)
            return True
        except queue.Full:
            logger.warning("Log processing queue is full, dropping entry")
            return False
        except Exception as e:
            logger.error(f"Failed to queue log entry: {str(e)}")
            return False
    
    def start_processing(self):
        """Start log processing threads."""
        if self.running:
            logger.warning("Log processing already running")
            return
        
        self.running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
            name="log-processing"
        )
        self.processing_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="log-cleanup"
        )
        self.cleanup_thread.start()
        
        logger.info("Started log processing")
    
    def stop_processing(self):
        """Stop log processing threads."""
        self.running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        logger.info("Stopped log processing")
    
    def _processing_loop(self):
        """Main log processing loop."""
        while self.running:
            try:
                # Get log entry from queue
                try:
                    entry = self.processing_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process the entry
                self._process_log_entry(entry)
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Log processing error: {str(e)}")
                self.processing_errors += 1
                time.sleep(1)
    
    def _process_log_entry(self, entry: LogEntry):
        """Process a single log entry."""
        try:
            with self.lock:
                # Add to storage
                entry_index = len(self.log_entries)
                self.log_entries.append(entry)
                
                # Update indexes
                self._update_indexes(entry, entry_index)
                
                # Update statistics
                self.total_logs_processed += 1
                
                # Export to backends
                if self.export_backends:
                    self._export_log_entry(entry)
                
                # Clear aggregation cache if needed
                self._invalidate_aggregation_cache()
                
        except Exception as e:
            logger.error(f"Failed to process log entry: {str(e)}")
            self.processing_errors += 1
    
    def _update_indexes(self, entry: LogEntry, entry_index: int):
        """Update search indexes for fast retrieval."""
        try:
            # Index by level
            self.log_index[f"level:{entry.level.name}"].append(entry_index)
            
            # Index by source
            self.log_index[f"source:{entry.source.value}"].append(entry_index)
            
            # Index by logger name
            self.log_index[f"logger:{entry.logger_name}"].append(entry_index)
            
            # Index by user/session/request IDs
            if entry.user_id:
                self.log_index[f"user:{entry.user_id}"].append(entry_index)
            if entry.session_id:
                self.log_index[f"session:{entry.session_id}"].append(entry_index)
            if entry.request_id:
                self.log_index[f"request:{entry.request_id}"].append(entry_index)
            
            # Index by labels
            for key, value in entry.labels.items():
                self.log_index[f"label:{key}:{value}"].append(entry_index)
            
        except Exception as e:
            logger.error(f"Failed to update indexes: {str(e)}")
    
    def _export_log_entry(self, entry: LogEntry):
        """Export log entry to configured backends."""
        try:
            for backend in self.export_backends:
                backend([entry])
            self.total_logs_exported += 1
        except Exception as e:
            logger.error(f"Failed to export log entry: {str(e)}")
    
    def _invalidate_aggregation_cache(self):
        """Invalidate aggregation cache."""
        current_time = time.time()
        expired_keys = [
            key for key, agg in self.aggregation_cache.items()
            if current_time - agg.end_time > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.aggregation_cache[key]
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.running:
            try:
                self._cleanup_old_logs()
                self._cleanup_indexes()
                time.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Log cleanup error: {str(e)}")
                time.sleep(300)
    
    def _cleanup_old_logs(self):
        """Clean up old log entries."""
        try:
            if self.retention_days <= 0:
                return
            
            cutoff_time = time.time() - (self.retention_days * 24 * 3600)
            
            with self.lock:
                # Count entries to remove
                remove_count = 0
                for entry in self.log_entries:
                    if entry.timestamp < cutoff_time:
                        remove_count += 1
                    else:
                        break
                
                # Remove old entries
                for _ in range(remove_count):
                    if self.log_entries:
                        self.log_entries.popleft()
                
                if remove_count > 0:
                    logger.info(f"Cleaned up {remove_count} old log entries")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")
    
    def _cleanup_indexes(self):
        """Clean up search indexes."""
        try:
            with self.lock:
                # Rebuild indexes periodically to remove stale references
                if len(self.log_entries) > 0:
                    self.log_index.clear()
                    
                    for i, entry in enumerate(self.log_entries):
                        self._update_indexes(entry, i)
                    
                    logger.debug("Rebuilt log search indexes")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup indexes: {str(e)}")
    
    def search_logs(self, log_filter: LogFilter, limit: int = 1000) -> List[LogEntry]:
        """
        Search logs with filtering.
        
        Args:
            log_filter: Filter criteria
            limit: Maximum number of results
            
        Returns:
            List of matching log entries
        """
        try:
            with self.lock:
                # Start with all entries
                candidate_indices = set(range(len(self.log_entries)))
                
                # Apply index-based filters
                candidate_indices = self._apply_indexed_filters(log_filter, candidate_indices)
                
                # Apply remaining filters
                results = []
                for index in sorted(candidate_indices, reverse=True):  # Most recent first
                    if len(results) >= limit:
                        break
                    
                    if index < len(self.log_entries):
                        entry = self.log_entries[index]
                        if self._matches_filter(entry, log_filter):
                            results.append(entry)
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to search logs: {str(e)}")
            return []
    
    def _apply_indexed_filters(self, log_filter: LogFilter, candidate_indices: set) -> set:
        """Apply filters that can use indexes."""
        try:
            # Filter by level
            if log_filter.min_level or log_filter.max_level:
                level_indices = set()
                for level in LogLevel:
                    if log_filter.min_level and level.value < log_filter.min_level.value:
                        continue
                    if log_filter.max_level and level.value > log_filter.max_level.value:
                        continue
                    level_indices.update(self.log_index.get(f"level:{level.name}", []))
                candidate_indices &= level_indices
            
            # Filter by sources
            if log_filter.sources:
                source_indices = set()
                for source in log_filter.sources:
                    source_indices.update(self.log_index.get(f"source:{source.value}", []))
                candidate_indices &= source_indices
            
            # Filter by logger names
            if log_filter.logger_names:
                logger_indices = set()
                for logger_name in log_filter.logger_names:
                    logger_indices.update(self.log_index.get(f"logger:{logger_name}", []))
                candidate_indices &= logger_indices
            
            # Filter by user IDs
            if log_filter.user_ids:
                user_indices = set()
                for user_id in log_filter.user_ids:
                    user_indices.update(self.log_index.get(f"user:{user_id}", []))
                candidate_indices &= user_indices
            
            # Filter by required labels
            if log_filter.required_labels:
                for key, value in log_filter.required_labels.items():
                    label_indices = set(self.log_index.get(f"label:{key}:{value}", []))
                    candidate_indices &= label_indices
            
            return candidate_indices
            
        except Exception as e:
            logger.error(f"Failed to apply indexed filters: {str(e)}")
            return candidate_indices
    
    def _matches_filter(self, entry: LogEntry, log_filter: LogFilter) -> bool:
        """Check if log entry matches filter criteria."""
        try:
            # Time range filter
            if log_filter.time_range:
                start_time, end_time = log_filter.time_range
                if not (start_time <= entry.timestamp <= end_time):
                    return False
            
            # Message content filters
            if log_filter.message_contains:
                if log_filter.message_contains.lower() not in entry.message.lower():
                    return False
            
            if log_filter.message_regex:
                if not re.search(log_filter.message_regex, entry.message, re.IGNORECASE):
                    return False
            
            # Session/request ID filters
            if log_filter.session_ids and entry.session_id not in log_filter.session_ids:
                return False
            
            if log_filter.request_ids and entry.request_id not in log_filter.request_ids:
                return False
            
            # Excluded labels
            if log_filter.excluded_labels:
                for key, value in log_filter.excluded_labels.items():
                    if entry.labels.get(key) == value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to match filter: {str(e)}")
            return False
    
    def aggregate_logs(self, time_bucket: str = "1h", 
                      time_range: Optional[tuple] = None) -> List[LogAggregation]:
        """
        Aggregate logs by time buckets.
        
        Args:
            time_bucket: Time bucket size (e.g., "1m", "5m", "1h", "1d")
            time_range: Optional time range filter
            
        Returns:
            List of log aggregations
        """
        try:
            # Parse time bucket
            bucket_seconds = self._parse_time_bucket(time_bucket)
            if bucket_seconds <= 0:
                logger.error(f"Invalid time bucket: {time_bucket}")
                return []
            
            # Check cache
            cache_key = f"{time_bucket}_{time_range}"
            if cache_key in self.aggregation_cache:
                cached_agg = self.aggregation_cache[cache_key]
                if time.time() - cached_agg.end_time < self.cache_ttl:
                    return [cached_agg]
            
            with self.lock:
                # Determine time range
                if not time_range:
                    if not self.log_entries:
                        return []
                    start_time = self.log_entries[0].timestamp
                    end_time = self.log_entries[-1].timestamp
                else:
                    start_time, end_time = time_range
                
                # Create time buckets
                buckets = {}
                current_time = start_time
                
                while current_time < end_time:
                    bucket_end = current_time + bucket_seconds
                    bucket_key = datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
                    
                    buckets[bucket_key] = LogAggregation(
                        time_bucket=bucket_key,
                        count=0,
                        levels=defaultdict(int),
                        sources=defaultdict(int),
                        top_loggers=defaultdict(int),
                        error_count=0,
                        warning_count=0,
                        start_time=current_time,
                        end_time=bucket_end
                    )
                    
                    current_time = bucket_end
                
                # Aggregate log entries
                for entry in self.log_entries:
                    if time_range and not (start_time <= entry.timestamp <= end_time):
                        continue
                    
                    # Find appropriate bucket
                    bucket_start = int(entry.timestamp // bucket_seconds) * bucket_seconds
                    bucket_key = datetime.fromtimestamp(bucket_start).strftime("%Y-%m-%d %H:%M:%S")
                    
                    if bucket_key in buckets:
                        agg = buckets[bucket_key]
                        agg.count += 1
                        agg.levels[entry.level.name] += 1
                        agg.sources[entry.source.value] += 1
                        agg.top_loggers[entry.logger_name] += 1
                        
                        if entry.level.value >= LogLevel.ERROR.value:
                            agg.error_count += 1
                        elif entry.level.value >= LogLevel.WARNING.value:
                            agg.warning_count += 1
                
                # Convert to list and cache
                result = list(buckets.values())
                if len(result) == 1:
                    self.aggregation_cache[cache_key] = result[0]
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to aggregate logs: {str(e)}")
            return []
    
    def _parse_time_bucket(self, time_bucket: str) -> int:
        """Parse time bucket string to seconds."""
        try:
            if time_bucket.endswith('s'):
                return int(time_bucket[:-1])
            elif time_bucket.endswith('m'):
                return int(time_bucket[:-1]) * 60
            elif time_bucket.endswith('h'):
                return int(time_bucket[:-1]) * 3600
            elif time_bucket.endswith('d'):
                return int(time_bucket[:-1]) * 86400
            else:
                return int(time_bucket)
        except ValueError:
            return 0
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get log aggregator statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            
            # Count by level
            level_counts = defaultdict(int)
            source_counts = defaultdict(int)
            
            for entry in self.log_entries:
                level_counts[entry.level.name] += 1
                source_counts[entry.source.value] += 1
            
            return {
                "uptime_seconds": uptime,
                "total_logs_stored": len(self.log_entries),
                "total_logs_processed": self.total_logs_processed,
                "total_logs_exported": self.total_logs_exported,
                "processing_errors": self.processing_errors,
                "queue_size": self.processing_queue.qsize(),
                "logs_by_level": dict(level_counts),
                "logs_by_source": dict(source_counts),
                "index_size": len(self.log_index),
                "cache_size": len(self.aggregation_cache),
                "processing_running": self.running
            }
    
    def add_export_backend(self, backend: Callable[[List[LogEntry]], None]):
        """
        Add an export backend.
        
        Args:
            backend: Function to export log entries
        """
        self.export_backends.append(backend)
        logger.info("Added log export backend")
    
    def create_log_handler(self, source: LogSource = LogSource.APPLICATION) -> LogHandler:
        """
        Create a log handler for this aggregator.
        
        Args:
            source: Log source type
            
        Returns:
            Log handler instance
        """
        return LogHandler(self, source)
    
    def export_logs_json(self, file_path: str, log_filter: Optional[LogFilter] = None) -> bool:
        """
        Export logs to JSON file.
        
        Args:
            file_path: Output file path
            log_filter: Optional filter criteria
            
        Returns:
            True if exported successfully
        """
        try:
            # Get logs to export
            if log_filter:
                logs = self.search_logs(log_filter, limit=0)  # No limit
            else:
                with self.lock:
                    logs = list(self.log_entries)
            
            # Prepare export data
            export_data = {
                "timestamp": time.time(),
                "stats": self.get_log_stats(),
                "logs": [log.to_dict() for log in logs]
            }
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(logs)} logs to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export logs to JSON: {str(e)}")
            return False
    
    def shutdown(self):
        """Gracefully shutdown log aggregator."""
        logger.info("Shutting down log aggregator")
        self.stop_processing()
        
        with self.lock:
            self.log_entries.clear()
            self.log_index.clear()
            self.aggregation_cache.clear()
            self.export_backends.clear()
        
        logger.info("Log aggregator shutdown complete")
