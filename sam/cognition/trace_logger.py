#!/usr/bin/env python3
"""
SAM Introspection Dashboard - TraceLogger Core System
====================================================

This module provides the central TraceLogger class for SAM's introspection
and debugging system. It enables real-time tracing of SAM's cognitive
processes with structured event logging and UUID-based trace identification.

Features:
- Thread-safe trace event logging
- UUID-based trace identification
- Structured event format with metadata
- Performance metrics tracking
- Hierarchical event relationships
- Real-time event streaming

Author: SAM Development Team
Version: 1.0.0
"""

import uuid
import time
import threading
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for trace logging."""
    START = "start"
    END = "end"
    DECISION = "decision"
    TOOL_CALL = "tool_call"
    ERROR = "error"
    DATA_IN = "data_in"
    DATA_OUT = "data_out"
    PERFORMANCE = "performance"

class Severity(Enum):
    """Severity levels for trace events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class TraceEvent:
    """Structured trace event with comprehensive metadata."""
    timestamp: str
    trace_id: str
    source_module: str
    event_type: EventType
    severity: Severity
    message: str
    duration_ms: Optional[float] = None
    parent_event_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    event_id: Optional[str] = None

    def __post_init__(self):
        """Generate event ID if not provided."""
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Convert enums to strings (handle both enum and string values)
        result['event_type'] = self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type)
        result['severity'] = self.severity.value if hasattr(self.severity, 'value') else str(self.severity)
        return result

class TraceLogger:
    """
    Central trace logging system for SAM's introspection dashboard.
    
    Provides thread-safe logging of trace events with real-time streaming
    capabilities and comprehensive metadata tracking.
    """

    def __init__(self):
        """Initialize the trace logger."""
        self._traces: Dict[str, List[TraceEvent]] = {}
        self._active_traces: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._performance_metrics: Dict[str, Dict[str, float]] = {}
        
        logger.info("TraceLogger initialized")

    def start_trace(self, query: str, user_id: Optional[str] = None, 
                   session_id: Optional[str] = None) -> str:
        """
        Start a new trace session.
        
        Args:
            query: The query being traced
            user_id: Optional user identifier
            session_id: Optional session identifier
            
        Returns:
            trace_id: Unique identifier for this trace
        """
        trace_id = str(uuid.uuid4())
        
        with self._lock:
            self._traces[trace_id] = []
            self._active_traces[trace_id] = {
                'query': query,
                'user_id': user_id,
                'session_id': session_id,
                'start_time': time.time(),
                'status': 'active'
            }
            self._performance_metrics[trace_id] = {
                'start_time': time.time(),
                'events_logged': 0,
                'modules_involved': set()
            }

        # Log the initial trace start event
        self.log_event(
            trace_id=trace_id,
            source_module="TraceLogger",
            event_type=EventType.START,
            severity=Severity.INFO,
            message=f"Trace started for query: {query[:50]}{'...' if len(query) > 50 else ''}",
            payload={
                'query': query,
                'query_length': len(query),
                'user_id': user_id,
                'session_id': session_id
            },
            metadata={
                'sam_version': '2.1.0',
                'trace_version': '1.0.0'
            }
        )

        logger.info(f"Started trace {trace_id} for query: {query[:50]}...")
        return trace_id

    def log_event(self, trace_id: str, source_module: str, event_type: EventType,
                  severity: Severity, message: str, duration_ms: Optional[float] = None,
                  parent_event_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a trace event.
        
        Args:
            trace_id: Trace identifier
            source_module: Module generating the event
            event_type: Type of event
            severity: Event severity level
            message: Human-readable event message
            duration_ms: Optional duration in milliseconds
            parent_event_id: Optional parent event for hierarchical tracing
            payload: Optional event-specific data
            metadata: Optional additional metadata
            
        Returns:
            event_id: Unique identifier for this event
        """
        if trace_id not in self._traces:
            logger.warning(f"Attempted to log event for unknown trace: {trace_id}")
            return ""

        # Create the trace event
        event = TraceEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
            source_module=source_module,
            event_type=event_type,
            severity=severity,
            message=message,
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
            payload=payload or {},
            metadata=metadata or {}
        )

        # Phase 3: Check for breakpoints before processing
        breakpoint_hit = self._check_breakpoints(trace_id, source_module, event_type, event)

        if breakpoint_hit:
            # Pause execution and wait for resume
            resume_result = self._handle_breakpoint_pause(trace_id, breakpoint_hit, event)

            # Apply payload override if provided
            if resume_result.get('override_payload'):
                event.payload.update(resume_result['override_payload'])
                event.message += f" [OVERRIDE APPLIED]"
                logger.info(f"Applied payload override to event {event.event_id}")

        # Add performance tracking metadata
        if trace_id in self._performance_metrics:
            event.metadata.update({
                'memory_usage_mb': self._get_memory_usage(),
                'cpu_usage_percent': self._get_cpu_usage(),
                'event_sequence': self._performance_metrics[trace_id]['events_logged'] + 1
            })

        with self._lock:
            self._traces[trace_id].append(event)
            
            # Update performance metrics
            if trace_id in self._performance_metrics:
                self._performance_metrics[trace_id]['events_logged'] += 1
                self._performance_metrics[trace_id]['modules_involved'].add(source_module)

        # Handle both EventType enum and string values
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        logger.debug(f"Logged {event_type_str} event for trace {trace_id}: {message}")
        return event.event_id

    def end_trace(self, trace_id: str, success: bool = True,
                  final_response: Optional[str] = None) -> None:
        """
        End a trace session.

        Args:
            trace_id: Trace identifier
            success: Whether the trace completed successfully
            final_response: Optional final response content
        """
        if trace_id not in self._active_traces:
            logger.warning(f"Attempted to end unknown trace: {trace_id}")
            return

        with self._lock:
            trace_info = self._active_traces[trace_id]
            total_time = time.time() - trace_info['start_time']

            # Update trace status
            trace_info['status'] = 'completed' if success else 'failed'
            trace_info['end_time'] = time.time()
            trace_info['total_duration'] = total_time
            trace_info['success'] = success
            trace_info['final_response_length'] = len(final_response) if final_response else 0

        # Log the final trace end event
        self.log_event(
            trace_id=trace_id,
            source_module="TraceLogger",
            event_type=EventType.END,
            severity=Severity.INFO if success else Severity.ERROR,
            message=f"Trace {'completed' if success else 'failed'} in {total_time:.2f}s",
            duration_ms=total_time * 1000,
            payload={
                'success': success,
                'total_duration_ms': total_time * 1000,
                'final_response_length': len(final_response) if final_response else 0,
                'events_logged': self._performance_metrics.get(trace_id, {}).get('events_logged', 0),
                'modules_involved': len(self._performance_metrics.get(trace_id, {}).get('modules_involved', set()))
            }
        )

        # Store trace in database for historical analysis
        self._store_trace_in_database(trace_id)

        logger.info(f"Ended trace {trace_id} ({'success' if success else 'failure'}) in {total_time:.2f}s")

    def get_trace_events(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a trace.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            List of trace events as dictionaries
        """
        with self._lock:
            if trace_id not in self._traces:
                return []
            
            return [event.to_dict() for event in self._traces[trace_id]]

    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """
        Get a summary of a trace.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Trace summary with performance metrics
        """
        with self._lock:
            if trace_id not in self._active_traces:
                return {}

            trace_info = self._active_traces[trace_id].copy()
            events = self._traces.get(trace_id, [])
            perf_metrics = self._performance_metrics.get(trace_id, {})

            return {
                'trace_id': trace_id,
                'query': trace_info.get('query', ''),
                'status': trace_info.get('status', 'unknown'),
                'start_time': trace_info.get('start_time'),
                'end_time': trace_info.get('end_time'),
                'total_duration': trace_info.get('total_duration'),
                'event_count': len(events),
                'modules_involved': list(perf_metrics.get('modules_involved', set())),
                'user_id': trace_info.get('user_id'),
                'session_id': trace_info.get('session_id')
            }

    def get_active_traces(self) -> List[str]:
        """Get list of currently active trace IDs."""
        with self._lock:
            return [tid for tid, info in self._active_traces.items() 
                   if info.get('status') == 'active']

    def cleanup_old_traces(self, max_age_hours: int = 24) -> int:
        """
        Clean up old trace data.
        
        Args:
            max_age_hours: Maximum age of traces to keep
            
        Returns:
            Number of traces cleaned up
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned_count = 0

        with self._lock:
            traces_to_remove = []
            
            for trace_id, trace_info in self._active_traces.items():
                if trace_info.get('start_time', 0) < cutoff_time:
                    traces_to_remove.append(trace_id)

            for trace_id in traces_to_remove:
                if trace_id in self._traces:
                    del self._traces[trace_id]
                if trace_id in self._active_traces:
                    del self._active_traces[trace_id]
                if trace_id in self._performance_metrics:
                    del self._performance_metrics[trace_id]
                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} old traces")
        return cleaned_count

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=None)
        except ImportError:
            return 0.0

    def _store_trace_in_database(self, trace_id: str) -> None:
        """Store completed trace in database for historical analysis."""
        try:
            # Import database here to avoid circular imports
            from sam.cognition.trace_database import get_trace_database

            db = get_trace_database()

            # Get trace summary and events
            trace_summary = self.get_trace_summary(trace_id)
            trace_events = self.get_trace_events(trace_id)

            if trace_summary and trace_events:
                # Store trace summary
                success = db.store_trace(trace_summary)

                if success:
                    # Store trace events
                    db.store_events(trace_id, trace_events)
                    logger.debug(f"Stored trace {trace_id} in database with {len(trace_events)} events")
                else:
                    logger.warning(f"Failed to store trace {trace_id} in database")

        except Exception as e:
            logger.warning(f"Failed to store trace {trace_id} in database: {e}")
            # Don't raise exception - database storage is optional

    def _check_breakpoints(self, trace_id: str, source_module: str, event_type, event: TraceEvent) -> Optional[str]:
        """
        Phase 3: Check if event matches any active breakpoints.

        Args:
            trace_id: Current trace ID
            source_module: Source module name
            event_type: Event type
            event: Event data

        Returns:
            Breakpoint ID if matched, None otherwise
        """
        try:
            from sam.cognition.trace_breakpoints import get_breakpoint_manager
            breakpoint_manager = get_breakpoint_manager()

            # Convert event type to string for comparison
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)

            # Prepare event data for condition evaluation
            event_data = {
                'trace_id': trace_id,
                'source_module': source_module,
                'event_type': event_type_str,
                'message': event.message,
                'severity': event.severity.value if hasattr(event.severity, 'value') else str(event.severity),
                'payload': event.payload,
                'metadata': event.metadata,
                'timestamp': event.timestamp
            }

            return breakpoint_manager.check_breakpoint(trace_id, source_module, event_type_str, event_data)

        except Exception as e:
            logger.warning(f"Error checking breakpoints: {e}")
            return None

    def _handle_breakpoint_pause(self, trace_id: str, breakpoint_id: str, event: TraceEvent) -> Dict[str, Any]:
        """
        Phase 3: Handle breakpoint pause and wait for resume.

        Args:
            trace_id: Trace ID that hit breakpoint
            breakpoint_id: Breakpoint that was triggered
            event: Event data at pause point

        Returns:
            Resume result with optional override payload
        """
        try:
            from sam.cognition.trace_breakpoints import get_breakpoint_manager
            breakpoint_manager = get_breakpoint_manager()

            # Prepare event data for pause
            event_data = {
                'trace_id': trace_id,
                'source_module': event.source_module,
                'event_type': event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                'message': event.message,
                'severity': event.severity.value if hasattr(event.severity, 'value') else str(event.severity),
                'payload': event.payload,
                'metadata': event.metadata,
                'timestamp': event.timestamp,
                'event_id': event.event_id
            }

            # Pause the trace
            hit_id = breakpoint_manager.pause_trace(trace_id, breakpoint_id, event_data)

            logger.info(f"Trace {trace_id} paused at breakpoint {breakpoint_id}, waiting for resume...")

            # Wait for resume with timeout
            resume_result = breakpoint_manager.wait_for_resume(trace_id, timeout_seconds=1800)  # 30 minutes

            logger.info(f"Trace {trace_id} resumed with action: {resume_result.get('action')}")

            return resume_result

        except Exception as e:
            logger.error(f"Error handling breakpoint pause: {e}")
            return {"action": "continue", "override_payload": None}

# Global trace logger instance
_trace_logger = None
_logger_lock = threading.Lock()

def get_trace_logger() -> TraceLogger:
    """Get the global trace logger instance."""
    global _trace_logger
    
    if _trace_logger is None:
        with _logger_lock:
            if _trace_logger is None:
                _trace_logger = TraceLogger()
    
    return _trace_logger

def start_trace(query: str, user_id: Optional[str] = None, 
               session_id: Optional[str] = None) -> str:
    """Convenience function to start a trace."""
    return get_trace_logger().start_trace(query, user_id, session_id)

def log_event(trace_id: str, source_module: str, event_type,
              severity, message: str, **kwargs) -> str:
    """Convenience function to log an event."""
    # Convert string event types to EventType enum if needed
    if isinstance(event_type, str):
        try:
            event_type = EventType(event_type)
        except ValueError:
            # If string doesn't match enum, create a basic enum-like object
            class StringEventType:
                def __init__(self, value):
                    self.value = value
            event_type = StringEventType(event_type)

    # Convert string severity to Severity enum if needed
    if isinstance(severity, str):
        try:
            severity = Severity(severity)
        except ValueError:
            # If string doesn't match enum, create a basic enum-like object
            class StringSeverity:
                def __init__(self, value):
                    self.value = value
            severity = StringSeverity(severity)

    return get_trace_logger().log_event(
        trace_id, source_module, event_type, severity, message, **kwargs
    )

def end_trace(trace_id: str, success: bool = True, 
              final_response: Optional[str] = None) -> None:
    """Convenience function to end a trace."""
    get_trace_logger().end_trace(trace_id, success, final_response)
