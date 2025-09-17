"""
Real-time streaming support for DataLineagePy.
Provides integration with major streaming platforms and real-time lineage tracking.
"""

from .kafka_streams_connector import KafkaStreamsConnector, KafkaStreamsConfig
from .flink_connector import FlinkConnector, FlinkConfig
from .pulsar_connector import PulsarConnector, PulsarConfig
from .kinesis_connector import KinesisConnector, KinesisConfig
from .realtime_tracker import RealtimeTracker, StreamingEvent
from .stream_processor import StreamProcessor, ProcessingRule
from .event_processor import EventProcessor, EventType

# Factory functions
from .kafka_streams_connector import create_kafka_streams_connector
from .flink_connector import create_flink_connector
from .pulsar_connector import create_pulsar_connector
from .kinesis_connector import create_kinesis_connector
from .realtime_tracker import create_realtime_tracker
from .stream_processor import create_stream_processor
from .event_processor import create_event_processor

__all__ = [
    # Core streaming connectors
    'KafkaStreamsConnector',
    'FlinkConnector', 
    'PulsarConnector',
    'KinesisConnector',
    
    # Configuration classes
    'KafkaStreamsConfig',
    'FlinkConfig',
    'PulsarConfig', 
    'KinesisConfig',
    
    # Real-time processing
    'RealtimeTracker',
    'StreamProcessor',
    'EventProcessor',
    
    # Data classes
    'StreamingEvent',
    'ProcessingRule',
    'EventType',
    
    # Factory functions
    'create_kafka_streams_connector',
    'create_flink_connector',
    'create_pulsar_connector', 
    'create_kinesis_connector',
    'create_realtime_tracker',
    'create_stream_processor',
    'create_event_processor',
]

# Default configurations
DEFAULT_KAFKA_CONFIG = {
    'bootstrap_servers': 'localhost:9092',
    'group_id': 'datalineage-consumer',
    'auto_offset_reset': 'latest',
    'enable_auto_commit': True,
    'session_timeout_ms': 30000,
    'heartbeat_interval_ms': 3000,
}

DEFAULT_FLINK_CONFIG = {
    'job_manager_host': 'localhost',
    'job_manager_port': 8081,
    'parallelism': 1,
    'checkpoint_interval': 5000,
    'restart_strategy': 'fixed-delay',
}

DEFAULT_PULSAR_CONFIG = {
    'service_url': 'pulsar://localhost:6650',
    'subscription_name': 'datalineage-subscription',
    'consumer_type': 'Shared',
    'subscription_type': 'Shared',
}

DEFAULT_KINESIS_CONFIG = {
    'region_name': 'us-east-1',
    'stream_name': 'datalineage-stream',
    'shard_iterator_type': 'LATEST',
    'polling_interval': 1.0,
}

# Supported streaming platforms
SUPPORTED_PLATFORMS = [
    'kafka',
    'flink', 
    'pulsar',
    'kinesis',
    'kafka_streams',
    'storm',
    'spark_streaming',
]

# Event types for streaming
STREAMING_EVENT_TYPES = [
    'data_ingestion',
    'data_transformation',
    'data_output',
    'schema_change',
    'partition_change',
    'consumer_lag',
    'processing_error',
    'throughput_alert',
]
