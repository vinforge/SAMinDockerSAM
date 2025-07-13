#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Performance Monitoring & Circuit Breaker
======================================================================

Production-ready performance monitoring system with circuit breaker pattern
to prevent tracing overhead from impacting SAM's core functionality.

Author: SAM Development Team
Version: 2.0.0 (Phase 2B)
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker tripped, blocking requests
    HALF_OPEN = "half_open"  # Testing if service has recovered

class PerformanceMetric(Enum):
    """Performance metrics to monitor."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    TRACE_OVERHEAD = "trace_overhead"

@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    metric: PerformanceMetric
    warning_threshold: float
    critical_threshold: float
    measurement_window_seconds: int = 60
    min_samples: int = 10

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Number of failures to trip circuit
    recovery_timeout_seconds: int = 60  # Time before trying half-open
    success_threshold: int = 3  # Successes needed to close circuit
    timeout_seconds: float = 5.0  # Request timeout
    monitoring_window_seconds: int = 300  # 5 minutes

@dataclass
class PerformanceSample:
    """Single performance measurement."""
    timestamp: datetime
    metric: PerformanceMetric
    value: float
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AlertEvent:
    """Performance alert event."""
    timestamp: datetime
    metric: PerformanceMetric
    severity: str  # warning, critical
    current_value: float
    threshold: float
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """
    Performance monitoring system for SAM Introspection Dashboard.
    
    Monitors key performance metrics and provides:
    - Real-time performance tracking
    - Threshold-based alerting
    - Performance trend analysis
    - Resource usage monitoring
    - Automatic performance degradation detection
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self._lock = threading.RLock()
        self.samples: Dict[PerformanceMetric, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: List[AlertEvent] = []
        self.alert_callbacks: List[Callable[[AlertEvent], None]] = []
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                metric=PerformanceMetric.RESPONSE_TIME,
                warning_threshold=1.0,  # 1 second
                critical_threshold=5.0,  # 5 seconds
                measurement_window_seconds=60
            ),
            PerformanceMetric.THROUGHPUT: PerformanceThreshold(
                metric=PerformanceMetric.THROUGHPUT,
                warning_threshold=10.0,  # 10 requests/second minimum
                critical_threshold=5.0,   # 5 requests/second minimum
                measurement_window_seconds=60
            ),
            PerformanceMetric.ERROR_RATE: PerformanceThreshold(
                metric=PerformanceMetric.ERROR_RATE,
                warning_threshold=0.05,  # 5% error rate
                critical_threshold=0.10,  # 10% error rate
                measurement_window_seconds=300
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.MEMORY_USAGE,
                warning_threshold=0.80,  # 80% memory usage
                critical_threshold=0.90,  # 90% memory usage
                measurement_window_seconds=60
            ),
            PerformanceMetric.TRACE_OVERHEAD: PerformanceThreshold(
                metric=PerformanceMetric.TRACE_OVERHEAD,
                warning_threshold=0.05,  # 5% overhead
                critical_threshold=0.10,  # 10% overhead
                measurement_window_seconds=60
            )
        }
        
        # Configuration
        self.config = {
            'enable_monitoring': True,
            'enable_alerting': True,
            'max_alerts': 1000,
            'alert_cooldown_seconds': 300,  # 5 minutes between same alerts
            'performance_sampling_interval': 10,  # seconds
            'enable_auto_recovery': True
        }
        
        # Alert cooldown tracking
        self.last_alert_times: Dict[str, datetime] = {}
        
        logger.info("PerformanceMonitor initialized")
    
    def record_metric(self, metric: PerformanceMetric, value: float, 
                     context: Dict[str, Any] = None):
        """
        Record a performance metric sample.
        
        Args:
            metric: Performance metric type
            value: Metric value
            context: Additional context information
        """
        if not self.config['enable_monitoring']:
            return
        
        with self._lock:
            sample = PerformanceSample(
                timestamp=datetime.now(),
                metric=metric,
                value=value,
                context=context or {}
            )
            
            self.samples[metric].append(sample)
            
            # Check thresholds
            if self.config['enable_alerting']:
                self._check_thresholds(metric)
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric has exceeded thresholds."""
        threshold = self.thresholds.get(metric)
        if not threshold:
            return
        
        # Get recent samples within measurement window
        cutoff_time = datetime.now() - timedelta(seconds=threshold.measurement_window_seconds)
        recent_samples = [
            s for s in self.samples[metric]
            if s.timestamp >= cutoff_time
        ]
        
        if len(recent_samples) < threshold.min_samples:
            return
        
        # Calculate current metric value
        values = [s.value for s in recent_samples]
        
        if metric == PerformanceMetric.THROUGHPUT:
            # For throughput, we want higher values
            current_value = len(values) / threshold.measurement_window_seconds
            is_warning = current_value < threshold.warning_threshold
            is_critical = current_value < threshold.critical_threshold
        elif metric == PerformanceMetric.ERROR_RATE:
            # Error rate is calculated as percentage
            current_value = statistics.mean(values)
            is_warning = current_value > threshold.warning_threshold
            is_critical = current_value > threshold.critical_threshold
        else:
            # For other metrics, higher values are worse
            current_value = statistics.mean(values)
            is_warning = current_value > threshold.warning_threshold
            is_critical = current_value > threshold.critical_threshold
        
        # Generate alerts
        if is_critical:
            self._generate_alert(metric, "critical", current_value, threshold.critical_threshold)
        elif is_warning:
            self._generate_alert(metric, "warning", current_value, threshold.warning_threshold)
    
    def _generate_alert(self, metric: PerformanceMetric, severity: str, 
                       current_value: float, threshold: float):
        """Generate a performance alert."""
        alert_key = f"{metric.value}_{severity}"
        
        # Check cooldown
        if alert_key in self.last_alert_times:
            time_since_last = datetime.now() - self.last_alert_times[alert_key]
            if time_since_last.total_seconds() < self.config['alert_cooldown_seconds']:
                return
        
        # Create alert
        alert = AlertEvent(
            timestamp=datetime.now(),
            metric=metric,
            severity=severity,
            current_value=current_value,
            threshold=threshold,
            message=f"{metric.value} {severity}: {current_value:.3f} exceeds threshold {threshold:.3f}",
            context={}
        )
        
        self.alerts.append(alert)
        self.last_alert_times[alert_key] = alert.timestamp
        
        # Trim alerts if too many
        if len(self.alerts) > self.config['max_alerts']:
            self.alerts = self.alerts[-self.config['max_alerts']:]
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.warning(f"Performance alert: {alert.message}")
    
    def add_alert_callback(self, callback: Callable[[AlertEvent], None]):
        """Add a callback for performance alerts."""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics summary."""
        with self._lock:
            metrics = {}
            
            for metric_type in PerformanceMetric:
                samples = list(self.samples[metric_type])
                if not samples:
                    continue
                
                # Get recent samples (last 5 minutes)
                cutoff_time = datetime.now() - timedelta(minutes=5)
                recent_samples = [s for s in samples if s.timestamp >= cutoff_time]
                
                if recent_samples:
                    values = [s.value for s in recent_samples]
                    metrics[metric_type.value] = {
                        'current': values[-1] if values else 0,
                        'average': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'samples': len(values),
                        'last_updated': recent_samples[-1].timestamp.isoformat()
                    }
            
            return metrics
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance trends over specified time period."""
        with self._lock:
            trends = {}
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for metric_type in PerformanceMetric:
                samples = [
                    s for s in self.samples[metric_type]
                    if s.timestamp >= cutoff_time
                ]
                
                if samples:
                    trends[metric_type.value] = [
                        {
                            'timestamp': s.timestamp.isoformat(),
                            'value': s.value,
                            'context': s.context
                        }
                        for s in samples
                    ]
            
            return trends

class CircuitBreaker:
    """
    Circuit breaker for tracing operations.
    
    Implements the circuit breaker pattern to prevent tracing overhead
    from impacting SAM's core functionality when performance degrades.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'circuit_trips': 0,
            'last_trip_time': None,
            'total_blocked_requests': 0
        }
        
        logger.info(f"CircuitBreaker '{name}' initialized")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            self.stats['total_requests'] += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    self.stats['total_blocked_requests'] += 1
                    raise Exception(f"Circuit breaker '{self.name}' is OPEN")
            
            # Execute function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Check for timeout
                if execution_time > self.config.timeout_seconds:
                    self._record_failure()
                    raise Exception(f"Function timeout: {execution_time:.3f}s > {self.config.timeout_seconds}s")
                
                self._record_success()
                return result
                
            except Exception as e:
                self._record_failure()
                raise e
    
    def _record_success(self):
        """Record a successful operation."""
        self.success_count += 1
        self.last_success_time = datetime.now()
        self.stats['successful_requests'] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' CLOSED after recovery")
    
    def _record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.stats['failed_requests'] += 1
        
        if self.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.stats['circuit_trips'] += 1
                self.stats['last_trip_time'] = datetime.now().isoformat()
                logger.warning(f"Circuit breaker '{self.name}' OPENED due to failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if not self.last_failure_time:
            return False
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout_seconds
    
    def force_open(self):
        """Force circuit breaker to open state."""
        with self._lock:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' forced OPEN")
    
    def force_close(self):
        """Force circuit breaker to closed state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            logger.info(f"Circuit breaker '{self.name}' forced CLOSED")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
                'stats': self.stats.copy(),
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout_seconds': self.config.recovery_timeout_seconds,
                    'success_threshold': self.config.success_threshold,
                    'timeout_seconds': self.config.timeout_seconds
                }
            }

class TracePerformanceManager:
    """
    Performance management system for SAM Introspection Dashboard.
    
    Combines performance monitoring with circuit breaker protection
    to ensure tracing operations don't impact core SAM functionality.
    """
    
    def __init__(self):
        """Initialize the performance manager."""
        self.monitor = PerformanceMonitor()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Create default circuit breakers
        self._init_circuit_breakers()
        
        # Set up alert callbacks
        self.monitor.add_alert_callback(self._handle_performance_alert)
        
        logger.info("TracePerformanceManager initialized")
    
    def _init_circuit_breakers(self):
        """Initialize default circuit breakers."""
        # Main tracing circuit breaker
        self.circuit_breakers['tracing'] = CircuitBreaker(
            'tracing',
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout_seconds=30,
                success_threshold=2,
                timeout_seconds=2.0
            )
        )
        
        # Analytics circuit breaker
        self.circuit_breakers['analytics'] = CircuitBreaker(
            'analytics',
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout_seconds=60,
                success_threshold=3,
                timeout_seconds=10.0
            )
        )
        
        # Database circuit breaker
        self.circuit_breakers['database'] = CircuitBreaker(
            'database',
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout_seconds=15,
                success_threshold=2,
                timeout_seconds=5.0
            )
        )
    
    def _handle_performance_alert(self, alert: AlertEvent):
        """Handle performance alerts by adjusting circuit breakers."""
        if alert.severity == 'critical':
            # Open relevant circuit breakers for critical alerts
            if alert.metric in [PerformanceMetric.RESPONSE_TIME, PerformanceMetric.TRACE_OVERHEAD]:
                self.circuit_breakers['tracing'].force_open()
                logger.warning("Opened tracing circuit breaker due to critical performance alert")
    
    def execute_with_protection(self, operation_type: str, func: Callable, 
                               *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            operation_type: Type of operation (tracing, analytics, database)
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        circuit_breaker = self.circuit_breakers.get(operation_type)
        if not circuit_breaker:
            # No circuit breaker, execute directly
            return func(*args, **kwargs)
        
        return circuit_breaker.call(func, *args, **kwargs)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        current_metrics = self.monitor.get_current_metrics()
        circuit_stats = {
            name: cb.get_stats()
            for name, cb in self.circuit_breakers.items()
        }
        
        # Calculate overall health score
        health_score = self._calculate_health_score(current_metrics, circuit_stats)
        
        return {
            'health_score': health_score,
            'status': self._get_health_status(health_score),
            'metrics': current_metrics,
            'circuit_breakers': circuit_stats,
            'recent_alerts': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'metric': alert.metric.value,
                    'severity': alert.severity,
                    'message': alert.message
                }
                for alert in self.monitor.alerts[-10:]
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any], 
                               circuit_stats: Dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0
        
        # Deduct points for circuit breaker issues
        for cb_stats in circuit_stats.values():
            if cb_stats['state'] == 'open':
                score -= 20
            elif cb_stats['state'] == 'half_open':
                score -= 10
        
        # Deduct points for performance issues
        for metric_name, metric_data in metrics.items():
            if metric_name == 'error_rate':
                if metric_data['current'] > 0.1:  # 10% error rate
                    score -= 15
                elif metric_data['current'] > 0.05:  # 5% error rate
                    score -= 5
            elif metric_name == 'response_time':
                if metric_data['current'] > 5.0:  # 5 seconds
                    score -= 15
                elif metric_data['current'] > 1.0:  # 1 second
                    score -= 5
        
        return max(0.0, min(100.0, score))
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score."""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 50:
            return "fair"
        elif health_score >= 25:
            return "poor"
        else:
            return "critical"

# Global performance manager instance
_performance_manager = None

def get_performance_manager() -> TracePerformanceManager:
    """Get the global performance manager instance."""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = TracePerformanceManager()
    return _performance_manager
