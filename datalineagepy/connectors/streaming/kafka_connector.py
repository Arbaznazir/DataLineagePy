import json
from typing import Any, Dict, Optional
from kafka import KafkaConsumer, KafkaProducer


class KafkaStreamingConnector:
    """
    Production-ready Kafka connector for real-time streaming lineage tracking.
    """

    def __init__(self, topic: str, bootstrap_servers: str = 'localhost:9092', group_id: str = None):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.producer = None

    def connect_consumer(self, **kwargs):
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            **kwargs
        )
        return self.consumer

    def connect_producer(self, **kwargs):
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            **kwargs
        )
        return self.producer

    def send(self, value: Dict[str, Any]):
        if not self.producer:
            self.connect_producer()
        self.producer.send(self.topic, value=value)
        self.producer.flush()

    def receive(self, timeout_ms: int = 1000) -> Optional[Dict[str, Any]]:
        if not self.consumer:
            self.connect_consumer()
        for message in self.consumer.poll(timeout_ms=timeout_ms).values():
            for record in message:
                return record.value
        return None
