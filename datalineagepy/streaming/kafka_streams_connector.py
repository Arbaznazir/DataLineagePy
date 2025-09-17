"""
Kafka Streams connector for real-time data lineage tracking.
Provides integration with Kafka Streams applications for lineage extraction.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import threading
from abc import ABC, abstractmethod

try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    KafkaConsumer = None
    KafkaProducer = None
    KafkaError = Exception

logger = logging.getLogger(__name__)


class StreamingEventType(Enum):
    """Types of streaming events."""
    DATA_INGESTION = "data_ingestion"
    DATA_TRANSFORMATION = "data_transformation"
    DATA_OUTPUT = "data_output"
    SCHEMA_CHANGE = "schema_change"
    PARTITION_CHANGE = "partition_change"
    CONSUMER_LAG = "consumer_lag"
    PROCESSING_ERROR = "processing_error"
    THROUGHPUT_ALERT = "throughput_alert"


@dataclass
class KafkaStreamsConfig:
    """Configuration for Kafka Streams connector."""
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "datalineage-consumer"
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    lineage_topic: str = "datalineage-events"
    metadata_topic: str = "datalineage-metadata"


@dataclass
class StreamingEvent:
    """Represents a streaming event for lineage tracking."""
    event_id: str
    event_type: StreamingEventType
    source_topic: str
    target_topic: Optional[str] = None
    application_id: str = ""
    processor_name: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    partition: Optional[int] = None
    offset: Optional[int] = None
    key: Optional[str] = None
    headers: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    schema_info: Dict[str, Any] = field(default_factory=dict)
    lineage_info: Dict[str, Any] = field(default_factory=dict)
    processing_time: Optional[float] = None
    lag_ms: Optional[int] = None
    error_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'source_topic': self.source_topic,
            'target_topic': self.target_topic,
            'application_id': self.application_id,
            'processor_name': self.processor_name,
            'timestamp': self.timestamp.isoformat(),
            'partition': self.partition,
            'offset': self.offset,
            'key': self.key,
            'headers': self.headers,
            'payload': self.payload,
            'schema_info': self.schema_info,
            'lineage_info': self.lineage_info,
            'processing_time': self.processing_time,
            'lag_ms': self.lag_ms,
            'error_info': self.error_info,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingEvent':
        """Create from dictionary."""
        return cls(
            event_id=data['event_id'],
            event_type=StreamingEventType(data['event_type']),
            source_topic=data['source_topic'],
            target_topic=data.get('target_topic'),
            application_id=data.get('application_id', ''),
            processor_name=data.get('processor_name', ''),
            timestamp=datetime.fromisoformat(data['timestamp']),
            partition=data.get('partition'),
            offset=data.get('offset'),
            key=data.get('key'),
            headers=data.get('headers', {}),
            payload=data.get('payload', {}),
            schema_info=data.get('schema_info', {}),
            lineage_info=data.get('lineage_info', {}),
            processing_time=data.get('processing_time'),
            lag_ms=data.get('lag_ms'),
            error_info=data.get('error_info'),
        )


class BaseStreamingConnector(ABC):
    """Base class for streaming connectors."""
    
    @abstractmethod
    async def start(self):
        """Start the connector."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the connector."""
        pass
    
    @abstractmethod
    async def consume_events(self) -> AsyncGenerator[StreamingEvent, None]:
        """Consume streaming events."""
        pass
    
    @abstractmethod
    async def publish_lineage(self, event: StreamingEvent):
        """Publish lineage event."""
        pass


class KafkaStreamsConnector(BaseStreamingConnector):
    """Kafka Streams connector for real-time lineage tracking."""
    
    def __init__(self, config: KafkaStreamsConfig):
        self.config = config
        self.consumer: Optional[KafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None
        self.running = False
        self.event_handlers: Dict[StreamingEventType, List[Callable]] = {}
        self.stats = {
            'events_consumed': 0,
            'events_published': 0,
            'errors': 0,
            'last_event_time': None,
            'consumer_lag': 0,
        }
        self._consumer_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        if KafkaConsumer is None:
            raise ImportError("kafka-python is required for Kafka Streams connector")
    
    async def start(self):
        """Start the Kafka Streams connector."""
        try:
            # Create consumer
            consumer_config = {
                'bootstrap_servers': self.config.bootstrap_servers,
                'group_id': self.config.group_id,
                'auto_offset_reset': self.config.auto_offset_reset,
                'enable_auto_commit': self.config.enable_auto_commit,
                'session_timeout_ms': self.config.session_timeout_ms,
                'heartbeat_interval_ms': self.config.heartbeat_interval_ms,
                'max_poll_records': self.config.max_poll_records,
                'max_poll_interval_ms': self.config.max_poll_interval_ms,
                'security_protocol': self.config.security_protocol,
                'value_deserializer': lambda x: json.loads(x.decode('utf-8')) if x else None,
                'key_deserializer': lambda x: x.decode('utf-8') if x else None,
            }
            
            # Add authentication if configured
            if self.config.sasl_mechanism:
                consumer_config.update({
                    'sasl_mechanism': self.config.sasl_mechanism,
                    'sasl_plain_username': self.config.sasl_username,
                    'sasl_plain_password': self.config.sasl_password,
                })
            
            # Add SSL if configured
            if self.config.ssl_cafile:
                consumer_config.update({
                    'ssl_cafile': self.config.ssl_cafile,
                    'ssl_certfile': self.config.ssl_certfile,
                    'ssl_keyfile': self.config.ssl_keyfile,
                })
            
            self.consumer = KafkaConsumer(**consumer_config)
            
            # Create producer
            producer_config = {
                'bootstrap_servers': self.config.bootstrap_servers,
                'security_protocol': self.config.security_protocol,
                'value_serializer': lambda x: json.dumps(x).encode('utf-8'),
                'key_serializer': lambda x: x.encode('utf-8') if x else None,
            }
            
            if self.config.sasl_mechanism:
                producer_config.update({
                    'sasl_mechanism': self.config.sasl_mechanism,
                    'sasl_plain_username': self.config.sasl_username,
                    'sasl_plain_password': self.config.sasl_password,
                })
            
            if self.config.ssl_cafile:
                producer_config.update({
                    'ssl_cafile': self.config.ssl_cafile,
                    'ssl_certfile': self.config.ssl_certfile,
                    'ssl_keyfile': self.config.ssl_keyfile,
                })
            
            self.producer = KafkaProducer(**producer_config)
            
            # Subscribe to topics
            if self.config.topics:
                self.consumer.subscribe(self.config.topics)
            
            self.running = True
            logger.info(f"Kafka Streams connector started, subscribed to topics: {self.config.topics}")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka Streams connector: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka Streams connector."""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
            self.consumer = None
        
        if self.producer:
            self.producer.close()
            self.producer = None
        
        logger.info("Kafka Streams connector stopped")
    
    async def consume_events(self) -> AsyncGenerator[StreamingEvent, None]:
        """Consume streaming events from Kafka."""
        if not self.consumer:
            raise RuntimeError("Connector not started")
        
        try:
            while self.running:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Create streaming event from Kafka message
                            event = self._create_event_from_message(message, topic_partition)
                            
                            # Update stats
                            with self._lock:
                                self.stats['events_consumed'] += 1
                                self.stats['last_event_time'] = datetime.utcnow()
                            
                            # Process event handlers
                            await self._process_event_handlers(event)
                            
                            yield event
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            with self._lock:
                                self.stats['errors'] += 1
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error consuming events: {e}")
            with self._lock:
                self.stats['errors'] += 1
    
    async def publish_lineage(self, event: StreamingEvent):
        """Publish lineage event to Kafka."""
        if not self.producer:
            raise RuntimeError("Connector not started")
        
        try:
            # Serialize event
            event_data = event.to_dict()
            
            # Send to lineage topic
            future = self.producer.send(
                self.config.lineage_topic,
                key=event.event_id,
                value=event_data,
                headers=[(k, v.encode('utf-8') if isinstance(v, str) else str(v).encode('utf-8')) 
                        for k, v in event.headers.items()]
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            # Update stats
            with self._lock:
                self.stats['events_published'] += 1
            
            logger.debug(f"Published lineage event {event.event_id} to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            
        except Exception as e:
            logger.error(f"Error publishing lineage event: {e}")
            with self._lock:
                self.stats['errors'] += 1
            raise
    
    def add_event_handler(self, event_type: StreamingEventType, handler: Callable):
        """Add event handler for specific event type."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: StreamingEventType, handler: Callable):
        """Remove event handler."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics."""
        with self._lock:
            return self.stats.copy()
    
    def get_consumer_lag(self) -> Dict[str, int]:
        """Get consumer lag information."""
        if not self.consumer:
            return {}
        
        try:
            # Get partition assignments
            partitions = self.consumer.assignment()
            lag_info = {}
            
            for partition in partitions:
                # Get current position
                position = self.consumer.position(partition)
                
                # Get high water mark
                high_water_marks = self.consumer.end_offsets([partition])
                high_water_mark = high_water_marks.get(partition, 0)
                
                # Calculate lag
                lag = high_water_mark - position
                lag_info[f"{partition.topic}:{partition.partition}"] = lag
            
            return lag_info
            
        except Exception as e:
            logger.error(f"Error getting consumer lag: {e}")
            return {}
    
    def _create_event_from_message(self, message, topic_partition) -> StreamingEvent:
        """Create streaming event from Kafka message."""
        # Extract event type from message or headers
        event_type = StreamingEventType.DATA_INGESTION
        if message.headers:
            for key, value in message.headers:
                if key == 'event_type':
                    try:
                        event_type = StreamingEventType(value.decode('utf-8'))
                    except (ValueError, UnicodeDecodeError):
                        pass
        
        # Create event
        event = StreamingEvent(
            event_id=f"{topic_partition.topic}:{topic_partition.partition}:{message.offset}",
            event_type=event_type,
            source_topic=topic_partition.topic,
            timestamp=datetime.fromtimestamp(message.timestamp / 1000) if message.timestamp else datetime.utcnow(),
            partition=topic_partition.partition,
            offset=message.offset,
            key=message.key,
            headers={k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in (message.headers or [])},
            payload=message.value or {},
        )
        
        return event
    
    async def _process_event_handlers(self, event: StreamingEvent):
        """Process event handlers for the given event."""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")


def create_kafka_streams_connector(
    bootstrap_servers: str = "localhost:9092",
    group_id: str = "datalineage-consumer",
    topics: Optional[List[str]] = None,
    **kwargs
) -> KafkaStreamsConnector:
    """Factory function to create Kafka Streams connector."""
    config = KafkaStreamsConfig(
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        topics=topics or [],
        **kwargs
    )
    return KafkaStreamsConnector(config)
