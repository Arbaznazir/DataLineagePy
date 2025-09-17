"""
API Security Middleware
Comprehensive security middleware for FastAPI/Flask applications.
"""

import time
import json
import re
import hashlib
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import logging
from collections import defaultdict, deque
import threading
import ipaddress
from urllib.parse import urlparse


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10


@dataclass
class SecurityConfig:
    """Security middleware configuration."""
    # Rate limiting
    default_rate_limit: RateLimitRule = field(
        default_factory=lambda: RateLimitRule(60, 1000, 10000))
    rate_limit_by_endpoint: Dict[str, RateLimitRule] = None

    # CORS
    allowed_origins: List[str] = None
    allowed_methods: List[str] = None
    allowed_headers: List[str] = None

    # Input validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 10
    blocked_patterns: List[str] = None

    # IP filtering
    blocked_ips: Set[str] = None
    allowed_ips: Set[str] = None

    # Security headers
    enable_security_headers: bool = True

    def __post_init__(self):
        if self.rate_limit_by_endpoint is None:
            self.rate_limit_by_endpoint = {}
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]
        if self.allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.allowed_headers is None:
            self.allowed_headers = ["*"]
        if self.blocked_patterns is None:
            self.blocked_patterns = [
                r'<script[^>]*>.*?</script>',  # XSS
                r'union\s+select',  # SQL injection
                r'drop\s+table',  # SQL injection
                r'exec\s*\(',  # Command injection
            ]
        if self.blocked_ips is None:
            self.blocked_ips = set()
        if self.allowed_ips is None:
            self.allowed_ips = set()


class RateLimiter:
    """Thread-safe rate limiter with sliding window."""

    def __init__(self):
        self.requests = defaultdict(lambda: {
            'minute': deque(),
            'hour': deque(),
            'day': deque()
        })
        self.lock = threading.Lock()

    def is_allowed(self, key: str, rule: RateLimitRule) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit."""
        now = time.time()

        with self.lock:
            windows = self.requests[key]

            # Clean old entries
            self._clean_window(windows['minute'], now - 60)
            self._clean_window(windows['hour'], now - 3600)
            self._clean_window(windows['day'], now - 86400)

            # Check limits
            minute_count = len(windows['minute'])
            hour_count = len(windows['hour'])
            day_count = len(windows['day'])

            if (minute_count >= rule.requests_per_minute or
                hour_count >= rule.requests_per_hour or
                    day_count >= rule.requests_per_day):

                return False, {
                    'minute_count': minute_count,
                    'hour_count': hour_count,
                    'day_count': day_count,
                    'limits': {
                        'minute': rule.requests_per_minute,
                        'hour': rule.requests_per_hour,
                        'day': rule.requests_per_day
                    }
                }

            # Add current request
            windows['minute'].append(now)
            windows['hour'].append(now)
            windows['day'].append(now)

            return True, {
                'minute_count': minute_count + 1,
                'hour_count': hour_count + 1,
                'day_count': day_count + 1
            }

    def _clean_window(self, window: deque, cutoff: float):
        """Remove old entries from sliding window."""
        while window and window[0] < cutoff:
            window.popleft()


class InputValidator:
    """Input validation and sanitization."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.blocked_patterns = [re.compile(pattern, re.IGNORECASE)
                                 for pattern in config.blocked_patterns]
        self.logger = logging.getLogger(__name__)

    def validate_request_size(self, content_length: int) -> bool:
        """Validate request size."""
        return content_length <= self.config.max_request_size

    def validate_json_depth(self, data: Any, current_depth: int = 0) -> bool:
        """Validate JSON nesting depth."""
        if current_depth > self.config.max_json_depth:
            return False

        if isinstance(data, dict):
            return all(self.validate_json_depth(v, current_depth + 1)
                       for v in data.values())
        elif isinstance(data, list):
            return all(self.validate_json_depth(item, current_depth + 1)
                       for item in data)

        return True

    def scan_for_threats(self, text: str) -> List[str]:
        """Scan text for security threats."""
        threats = []
        for pattern in self.blocked_patterns:
            if pattern.search(text):
                threats.append(pattern.pattern)
        return threats

    def validate_input(self, data: Any) -> tuple[bool, List[str]]:
        """Comprehensive input validation."""
        issues = []

        # Check JSON depth
        if not self.validate_json_depth(data):
            issues.append("JSON nesting too deep")

        # Scan for threats in string values
        def scan_recursive(obj):
            if isinstance(obj, str):
                threats = self.scan_for_threats(obj)
                if threats:
                    issues.extend(
                        [f"Threat pattern detected: {t}" for t in threats])
            elif isinstance(obj, dict):
                for value in obj.values():
                    scan_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    scan_recursive(item)

        scan_recursive(data)

        return len(issues) == 0, issues


class IPFilter:
    """IP address filtering and geolocation."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed."""
        try:
            ip = ipaddress.ip_address(ip_address)

            # Check blocked IPs
            if self.config.blocked_ips:
                for blocked_ip in self.config.blocked_ips:
                    if ip in ipaddress.ip_network(blocked_ip, strict=False):
                        return False

            # Check allowed IPs (if specified, only these are allowed)
            if self.config.allowed_ips:
                for allowed_ip in self.config.allowed_ips:
                    if ip in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                return False  # Not in allowed list

            return True  # No restrictions or not blocked

        except ValueError:
            self.logger.warning(f"Invalid IP address: {ip_address}")
            return False


class SecurityMiddleware:
    """
    Comprehensive API security middleware.

    Features:
    - Rate limiting with sliding windows
    - CORS protection
    - Input validation and sanitization
    - IP filtering
    - Security headers
    - Request/response logging
    """

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator(config)
        self.ip_filter = IPFilter(config)
        self.logger = logging.getLogger(__name__)

        # Metrics
        self.metrics = {
            "requests_processed": 0,
            "requests_blocked": 0,
            "rate_limit_violations": 0,
            "input_validation_failures": 0,
            "ip_blocks": 0,
            "cors_violations": 0
        }

    def get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        # Check common headers for real IP
        headers_to_check = [
            'X-Forwarded-For',
            'X-Real-IP',
            'X-Client-IP',
            'CF-Connecting-IP'
        ]

        for header in headers_to_check:
            if hasattr(request, 'headers') and header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip

        # Fallback to remote address
        return getattr(request, 'remote_addr', '127.0.0.1')

    def check_rate_limit(self, request, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """Check rate limiting for request."""
        client_ip = self.get_client_ip(request)

        # Get rate limit rule for endpoint
        rule = self.config.rate_limit_by_endpoint.get(
            endpoint, self.config.default_rate_limit)

        # Create rate limit key
        rate_limit_key = f"{client_ip}:{endpoint}"

        allowed, info = self.rate_limiter.is_allowed(rate_limit_key, rule)

        if not allowed:
            self.metrics["rate_limit_violations"] += 1

        return allowed, info

    def validate_cors(self, request) -> bool:
        """Validate CORS policy."""
        origin = getattr(request, 'headers', {}).get('Origin')

        if not origin:
            return True  # No CORS check needed

        if '*' in self.config.allowed_origins:
            return True

        if origin in self.config.allowed_origins:
            return True

        self.metrics["cors_violations"] += 1
        return False

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to response."""
        if not self.config.enable_security_headers:
            return {}

        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

    def process_request(self, request, endpoint: str) -> tuple[bool, Dict[str, Any]]:
        """
        Process incoming request through security checks.

        Returns:
            (allowed, response_data)
        """
        self.metrics["requests_processed"] += 1

        try:
            # IP filtering
            client_ip = self.get_client_ip(request)
            if not self.ip_filter.is_ip_allowed(client_ip):
                self.metrics["ip_blocks"] += 1
                self.metrics["requests_blocked"] += 1
                return False, {
                    "error": "Access denied",
                    "code": "IP_BLOCKED",
                    "status": 403
                }

            # Rate limiting
            rate_allowed, rate_info = self.check_rate_limit(request, endpoint)
            if not rate_allowed:
                self.metrics["requests_blocked"] += 1
                return False, {
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "status": 429,
                    "details": rate_info
                }

            # CORS validation
            if not self.validate_cors(request):
                self.metrics["requests_blocked"] += 1
                return False, {
                    "error": "CORS policy violation",
                    "code": "CORS_VIOLATION",
                    "status": 403
                }

            # Request size validation
            content_length = int(
                getattr(request, 'headers', {}).get('Content-Length', 0))
            if not self.input_validator.validate_request_size(content_length):
                self.metrics["input_validation_failures"] += 1
                self.metrics["requests_blocked"] += 1
                return False, {
                    "error": "Request too large",
                    "code": "REQUEST_TOO_LARGE",
                    "status": 413
                }

            # Input validation (for JSON requests)
            if hasattr(request, 'json') and request.json:
                valid, issues = self.input_validator.validate_input(
                    request.json)
                if not valid:
                    self.metrics["input_validation_failures"] += 1
                    self.metrics["requests_blocked"] += 1
                    return False, {
                        "error": "Input validation failed",
                        "code": "INVALID_INPUT",
                        "status": 400,
                        "details": issues
                    }

            return True, {"rate_limit_info": rate_info}

        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            return False, {
                "error": "Security check failed",
                "code": "SECURITY_ERROR",
                "status": 500
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get security metrics."""
        return self.metrics.copy()


# Decorators for Flask/FastAPI integration
def require_security(config: SecurityConfig):
    """Decorator to apply security middleware to Flask routes."""
    middleware = SecurityMiddleware(config)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request, jsonify

            endpoint = request.endpoint or func.__name__
            allowed, response_data = middleware.process_request(
                request, endpoint)

            if not allowed:
                response = jsonify(response_data)
                response.status_code = response_data.get("status", 403)
                return response

            # Execute original function
            result = func(*args, **kwargs)

            # Add security headers
            if hasattr(result, 'headers'):
                for header, value in middleware.get_security_headers().items():
                    result.headers[header] = value

            return result

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Configure security
    config = SecurityConfig(
        default_rate_limit=RateLimitRule(100, 1000, 10000),
        allowed_origins=["https://myapp.com", "https://admin.myapp.com"],
        blocked_ips={"192.168.1.100", "10.0.0.0/8"},
        max_request_size=5 * 1024 * 1024  # 5MB
    )

    # Initialize middleware
    middleware = SecurityMiddleware(config)

    # Example request processing
    class MockRequest:
        def __init__(self):
            self.headers = {"X-Forwarded-For": "203.0.113.1"}
            self.json = {"user": "test", "data": "safe content"}
            self.remote_addr = "203.0.113.1"

    request = MockRequest()
    allowed, response = middleware.process_request(request, "/api/data")

    print(f"Request allowed: {allowed}")
    print(f"Response: {response}")
    print(f"Metrics: {middleware.get_metrics()}")
