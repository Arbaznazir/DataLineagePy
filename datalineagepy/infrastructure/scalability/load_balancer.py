"""
Load Balancer Implementation
Enterprise-grade load balancing with multiple algorithms and health checking.
"""

import time
import random
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib
import logging

logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"


@dataclass
class ServerInstance:
    """Represents a backend server instance."""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 1000
    current_connections: int = 0
    is_healthy: bool = True
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_health_check: float = 0
    total_requests: int = 0
    failed_requests: int = 0
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return ((self.total_requests - self.failed_requests) / self.total_requests) * 100
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement."""
        self.response_times.append(response_time)
    
    def increment_connections(self):
        """Increment current connection count."""
        self.current_connections += 1
    
    def decrement_connections(self):
        """Decrement current connection count."""
        self.current_connections = max(0, self.current_connections - 1)
    
    def record_request(self, success: bool = True):
        """Record a request outcome."""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1


class LoadBalancer:
    """
    Enterprise-grade load balancer with multiple algorithms and health checking.
    
    Features:
    - Multiple load balancing algorithms
    - Health checking with automatic failover
    - Connection tracking and limits
    - Response time monitoring
    - Weighted distribution
    - Session affinity (sticky sessions)
    - Circuit breaker integration
    """
    
    def __init__(self, algorithm: str = "round_robin", health_check_interval: int = 30):
        """
        Initialize load balancer.
        
        Args:
            algorithm: Load balancing algorithm to use
            health_check_interval: Health check interval in seconds
        """
        self.algorithm = LoadBalancingAlgorithm(algorithm)
        self.health_check_interval = health_check_interval
        
        # Server management
        self.servers: Dict[str, ServerInstance] = {}
        self.healthy_servers: List[str] = []
        self.unhealthy_servers: List[str] = []
        
        # Algorithm state
        self.round_robin_index = 0
        self.session_affinity: Dict[str, str] = {}  # session_id -> server_id
        
        # Monitoring
        self.total_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
        
        # Threading
        self.lock = threading.RLock()
        self.health_check_thread = None
        self.running = False
        
        # Health check callback
        self.health_check_callback: Optional[Callable[[ServerInstance], bool]] = None
        
        logger.info(f"Load balancer initialized with {algorithm} algorithm")
    
    def add_server(self, server_id: str, host: str, port: int, weight: int = 1, 
                   max_connections: int = 1000) -> bool:
        """
        Add a server to the load balancer pool.
        
        Args:
            server_id: Unique server identifier
            host: Server hostname or IP
            port: Server port
            weight: Server weight for weighted algorithms
            max_connections: Maximum concurrent connections
            
        Returns:
            True if server was added successfully
        """
        try:
            with self.lock:
                if server_id in self.servers:
                    logger.warning(f"Server {server_id} already exists")
                    return False
                
                server = ServerInstance(
                    id=server_id,
                    host=host,
                    port=port,
                    weight=weight,
                    max_connections=max_connections
                )
                
                self.servers[server_id] = server
                self.healthy_servers.append(server_id)
                
                logger.info(f"Added server {server_id} ({host}:{port}) with weight {weight}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add server {server_id}: {str(e)}")
            return False
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server from the load balancer pool.
        
        Args:
            server_id: Server identifier to remove
            
        Returns:
            True if server was removed successfully
        """
        try:
            with self.lock:
                if server_id not in self.servers:
                    logger.warning(f"Server {server_id} not found")
                    return False
                
                # Remove from all lists
                if server_id in self.healthy_servers:
                    self.healthy_servers.remove(server_id)
                if server_id in self.unhealthy_servers:
                    self.unhealthy_servers.remove(server_id)
                
                # Remove server
                del self.servers[server_id]
                
                # Clean up session affinity
                sessions_to_remove = [
                    session_id for session_id, srv_id in self.session_affinity.items()
                    if srv_id == server_id
                ]
                for session_id in sessions_to_remove:
                    del self.session_affinity[session_id]
                
                logger.info(f"Removed server {server_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove server {server_id}: {str(e)}")
            return False
    
    def get_server(self, client_ip: Optional[str] = None, 
                   session_id: Optional[str] = None) -> Optional[ServerInstance]:
        """
        Get the next server based on the configured algorithm.
        
        Args:
            client_ip: Client IP for IP hash algorithm
            session_id: Session ID for sticky sessions
            
        Returns:
            Selected server instance or None if no healthy servers
        """
        try:
            with self.lock:
                # Check for session affinity first
                if session_id and session_id in self.session_affinity:
                    server_id = self.session_affinity[session_id]
                    if server_id in self.healthy_servers:
                        server = self.servers[server_id]
                        if server.current_connections < server.max_connections:
                            return server
                
                # No healthy servers available
                if not self.healthy_servers:
                    logger.warning("No healthy servers available")
                    return None
                
                # Select server based on algorithm
                server = self._select_server_by_algorithm(client_ip)
                
                # Set session affinity if session_id provided
                if session_id and server:
                    self.session_affinity[session_id] = server.id
                
                return server
                
        except Exception as e:
            logger.error(f"Failed to get server: {str(e)}")
            return None
    
    def _select_server_by_algorithm(self, client_ip: Optional[str] = None) -> Optional[ServerInstance]:
        """Select server based on the configured algorithm."""
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_select()
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_select()
        
        elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select()
        
        elif self.algorithm == LoadBalancingAlgorithm.IP_HASH:
            return self._ip_hash_select(client_ip)
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_select()
        
        elif self.algorithm == LoadBalancingAlgorithm.RANDOM:
            return self._random_select()
        
        else:
            return self._round_robin_select()
    
    def _round_robin_select(self) -> Optional[ServerInstance]:
        """Round robin server selection."""
        if not self.healthy_servers:
            return None
        
        server_id = self.healthy_servers[self.round_robin_index]
        self.round_robin_index = (self.round_robin_index + 1) % len(self.healthy_servers)
        
        server = self.servers[server_id]
        if server.current_connections < server.max_connections:
            return server
        
        # Try next servers if current is at capacity
        for _ in range(len(self.healthy_servers) - 1):
            server_id = self.healthy_servers[self.round_robin_index]
            self.round_robin_index = (self.round_robin_index + 1) % len(self.healthy_servers)
            server = self.servers[server_id]
            if server.current_connections < server.max_connections:
                return server
        
        return None
    
    def _least_connections_select(self) -> Optional[ServerInstance]:
        """Least connections server selection."""
        available_servers = [
            self.servers[server_id] for server_id in self.healthy_servers
            if self.servers[server_id].current_connections < self.servers[server_id].max_connections
        ]
        
        if not available_servers:
            return None
        
        return min(available_servers, key=lambda s: s.current_connections)
    
    def _weighted_round_robin_select(self) -> Optional[ServerInstance]:
        """Weighted round robin server selection."""
        if not self.healthy_servers:
            return None
        
        # Create weighted list
        weighted_servers = []
        for server_id in self.healthy_servers:
            server = self.servers[server_id]
            if server.current_connections < server.max_connections:
                weighted_servers.extend([server_id] * server.weight)
        
        if not weighted_servers:
            return None
        
        server_id = weighted_servers[self.round_robin_index % len(weighted_servers)]
        self.round_robin_index += 1
        
        return self.servers[server_id]
    
    def _ip_hash_select(self, client_ip: Optional[str] = None) -> Optional[ServerInstance]:
        """IP hash server selection for session affinity."""
        if not client_ip or not self.healthy_servers:
            return self._round_robin_select()
        
        # Hash client IP to select server
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        server_index = hash_value % len(self.healthy_servers)
        server_id = self.healthy_servers[server_index]
        
        server = self.servers[server_id]
        if server.current_connections < server.max_connections:
            return server
        
        # Fallback to round robin if selected server is at capacity
        return self._round_robin_select()
    
    def _least_response_time_select(self) -> Optional[ServerInstance]:
        """Least response time server selection."""
        available_servers = [
            self.servers[server_id] for server_id in self.healthy_servers
            if self.servers[server_id].current_connections < self.servers[server_id].max_connections
        ]
        
        if not available_servers:
            return None
        
        return min(available_servers, key=lambda s: s.average_response_time)
    
    def _random_select(self) -> Optional[ServerInstance]:
        """Random server selection."""
        available_servers = [
            server_id for server_id in self.healthy_servers
            if self.servers[server_id].current_connections < self.servers[server_id].max_connections
        ]
        
        if not available_servers:
            return None
        
        server_id = random.choice(available_servers)
        return self.servers[server_id]
    
    def record_request(self, server_id: str, response_time: float, success: bool = True):
        """
        Record request metrics for a server.
        
        Args:
            server_id: Server that handled the request
            response_time: Request response time in seconds
            success: Whether the request was successful
        """
        try:
            with self.lock:
                self.total_requests += 1
                if not success:
                    self.failed_requests += 1
                
                if server_id in self.servers:
                    server = self.servers[server_id]
                    server.add_response_time(response_time)
                    server.record_request(success)
                    
        except Exception as e:
            logger.error(f"Failed to record request for server {server_id}: {str(e)}")
    
    def start_health_checks(self, health_check_callback: Callable[[ServerInstance], bool]):
        """
        Start health checking for all servers.
        
        Args:
            health_check_callback: Function to check server health
        """
        self.health_check_callback = health_check_callback
        self.running = True
        
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()
        
        logger.info("Health checking started")
    
    def stop_health_checks(self):
        """Stop health checking."""
        self.running = False
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        
        logger.info("Health checking stopped")
    
    def _health_check_loop(self):
        """Health check loop running in background thread."""
        while self.running:
            try:
                self._perform_health_checks()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                time.sleep(5)  # Short delay on error
    
    def _perform_health_checks(self):
        """Perform health checks on all servers."""
        if not self.health_check_callback:
            return
        
        current_time = time.time()
        
        with self.lock:
            servers_to_check = list(self.servers.values())
        
        for server in servers_to_check:
            try:
                # Perform health check
                is_healthy = self.health_check_callback(server)
                server.last_health_check = current_time
                
                with self.lock:
                    if is_healthy and not server.is_healthy:
                        # Server recovered
                        server.is_healthy = True
                        if server.id in self.unhealthy_servers:
                            self.unhealthy_servers.remove(server.id)
                        if server.id not in self.healthy_servers:
                            self.healthy_servers.append(server.id)
                        logger.info(f"Server {server.id} recovered")
                    
                    elif not is_healthy and server.is_healthy:
                        # Server failed
                        server.is_healthy = False
                        if server.id in self.healthy_servers:
                            self.healthy_servers.remove(server.id)
                        if server.id not in self.unhealthy_servers:
                            self.unhealthy_servers.append(server.id)
                        logger.warning(f"Server {server.id} failed health check")
                        
            except Exception as e:
                logger.error(f"Health check failed for server {server.id}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        with self.lock:
            uptime = time.time() - self.start_time
            
            server_stats = {}
            for server_id, server in self.servers.items():
                server_stats[server_id] = {
                    "host": f"{server.host}:{server.port}",
                    "healthy": server.is_healthy,
                    "current_connections": server.current_connections,
                    "max_connections": server.max_connections,
                    "total_requests": server.total_requests,
                    "failed_requests": server.failed_requests,
                    "success_rate": server.success_rate,
                    "average_response_time": server.average_response_time,
                    "weight": server.weight
                }
            
            return {
                "algorithm": self.algorithm.value,
                "uptime_seconds": uptime,
                "total_requests": self.total_requests,
                "failed_requests": self.failed_requests,
                "success_rate": ((self.total_requests - self.failed_requests) / max(self.total_requests, 1)) * 100,
                "healthy_servers": len(self.healthy_servers),
                "unhealthy_servers": len(self.unhealthy_servers),
                "total_servers": len(self.servers),
                "active_sessions": len(self.session_affinity),
                "servers": server_stats
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the load balancer."""
        with self.lock:
            return {
                "status": "healthy" if self.healthy_servers else "unhealthy",
                "healthy_servers": len(self.healthy_servers),
                "unhealthy_servers": len(self.unhealthy_servers),
                "total_servers": len(self.servers),
                "health_check_enabled": self.running,
                "last_health_check": max(
                    [server.last_health_check for server in self.servers.values()],
                    default=0
                )
            }
    
    def shutdown(self):
        """Gracefully shutdown the load balancer."""
        logger.info("Shutting down load balancer")
        self.stop_health_checks()
        
        with self.lock:
            self.servers.clear()
            self.healthy_servers.clear()
            self.unhealthy_servers.clear()
            self.session_affinity.clear()
        
        logger.info("Load balancer shutdown complete")
