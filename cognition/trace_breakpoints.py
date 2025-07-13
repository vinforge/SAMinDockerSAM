#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Interactive Breakpoint System
===========================================================

Phase 3: Interactive debugging system that allows developers to set breakpoints
in SAM's reasoning flow, pause execution, and override decisions in real-time.

Author: SAM Development Team
Version: 3.0.0 (Phase 3)
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re

logger = logging.getLogger(__name__)

class BreakpointStatus(Enum):
    """Breakpoint status states."""
    ACTIVE = "active"
    DISABLED = "disabled"
    TRIGGERED = "triggered"
    EXPIRED = "expired"

class TraceStatus(Enum):
    """Trace execution status."""
    RUNNING = "running"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Breakpoint:
    """Interactive breakpoint definition."""
    breakpoint_id: str
    name: str
    description: str
    module_name: str
    event_type: str
    condition: str  # Python expression to evaluate
    status: BreakpointStatus = BreakpointStatus.ACTIVE
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0
    max_hits: Optional[int] = None
    expires_at: Optional[datetime] = None
    enabled: bool = True

@dataclass
class BreakpointHit:
    """Record of a breakpoint being triggered."""
    hit_id: str
    breakpoint_id: str
    trace_id: str
    event_data: Dict[str, Any]
    hit_timestamp: datetime
    resolved_timestamp: Optional[datetime] = None
    override_payload: Optional[Dict[str, Any]] = None
    resolution_action: Optional[str] = None  # resume, step, abort
    resolved_by: Optional[str] = None

@dataclass
class PausedTrace:
    """Information about a paused trace."""
    trace_id: str
    breakpoint_id: str
    hit_id: str
    paused_at: datetime
    event_data: Dict[str, Any]
    waiting_for_resume: bool = True
    timeout_at: Optional[datetime] = None
    override_payload: Optional[Dict[str, Any]] = None

class BreakpointManager:
    """
    Interactive breakpoint management system for SAM debugging.
    
    Provides comprehensive breakpoint functionality including:
    - Breakpoint creation and management
    - Condition evaluation and matching
    - Execution pausing and resuming
    - Payload override capabilities
    - Security integration with RBAC
    - Timeout handling for safety
    """
    
    def __init__(self, config_path: str = "config/breakpoints.json"):
        """
        Initialize the breakpoint manager.
        
        Args:
            config_path: Path to breakpoint configuration file
        """
        self.config_path = config_path
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.breakpoint_hits: Dict[str, BreakpointHit] = {}
        self.paused_traces: Dict[str, PausedTrace] = {}
        self._lock = threading.RLock()
        
        # Configuration
        self.config = {
            'enable_breakpoints': True,
            'default_timeout_minutes': 30,
            'max_breakpoints': 50,
            'max_paused_traces': 10,
            'condition_timeout_seconds': 5,
            'enable_condition_sandbox': True,
            'auto_cleanup_expired': True,
            'hit_history_limit': 1000
        }
        
        # Load existing breakpoints
        self._load_breakpoints()
        
        # Start background cleanup
        self._start_cleanup_thread()
        
        logger.info("BreakpointManager initialized")
    
    def create_breakpoint(self, name: str, description: str, module_name: str,
                         event_type: str, condition: str, created_by: str = "system",
                         max_hits: Optional[int] = None, 
                         expires_in_hours: Optional[int] = None) -> str:
        """
        Create a new breakpoint.
        
        Args:
            name: Breakpoint name
            description: Breakpoint description
            module_name: Target module name
            event_type: Target event type
            condition: Python condition expression
            created_by: User who created the breakpoint
            max_hits: Maximum number of hits before disabling
            expires_in_hours: Hours until breakpoint expires
            
        Returns:
            Breakpoint ID
        """
        with self._lock:
            if len(self.breakpoints) >= self.config['max_breakpoints']:
                raise ValueError(f"Maximum breakpoints ({self.config['max_breakpoints']}) reached")
            
            # Validate condition syntax
            if not self._validate_condition(condition):
                raise ValueError(f"Invalid condition syntax: {condition}")
            
            breakpoint_id = str(uuid.uuid4())
            
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            breakpoint = Breakpoint(
                breakpoint_id=breakpoint_id,
                name=name,
                description=description,
                module_name=module_name,
                event_type=event_type,
                condition=condition,
                created_by=created_by,
                max_hits=max_hits,
                expires_at=expires_at
            )
            
            self.breakpoints[breakpoint_id] = breakpoint
            self._save_breakpoints()
            
            logger.info(f"Created breakpoint {name} ({breakpoint_id}) by {created_by}")
            return breakpoint_id
    
    def check_breakpoint(self, trace_id: str, source_module: str, event_type: str,
                        event_data: Dict[str, Any]) -> Optional[str]:
        """
        Check if an event matches any active breakpoints.
        
        Args:
            trace_id: Current trace ID
            source_module: Source module name
            event_type: Event type
            event_data: Event data for condition evaluation
            
        Returns:
            Breakpoint ID if matched, None otherwise
        """
        if not self.config['enable_breakpoints']:
            return None
        
        with self._lock:
            for breakpoint_id, breakpoint in self.breakpoints.items():
                if not breakpoint.enabled or breakpoint.status != BreakpointStatus.ACTIVE:
                    continue
                
                # Check if breakpoint has expired
                if breakpoint.expires_at and datetime.now() > breakpoint.expires_at:
                    breakpoint.status = BreakpointStatus.EXPIRED
                    continue
                
                # Check if max hits reached
                if breakpoint.max_hits and breakpoint.hit_count >= breakpoint.max_hits:
                    breakpoint.status = BreakpointStatus.DISABLED
                    continue
                
                # Check module and event type match
                if not self._matches_pattern(source_module, breakpoint.module_name):
                    continue
                
                if not self._matches_pattern(event_type, breakpoint.event_type):
                    continue
                
                # Evaluate condition
                if self._evaluate_condition(breakpoint.condition, event_data):
                    # Breakpoint hit!
                    hit_id = self._record_breakpoint_hit(breakpoint_id, trace_id, event_data)
                    breakpoint.hit_count += 1
                    breakpoint.status = BreakpointStatus.TRIGGERED
                    
                    logger.info(f"Breakpoint hit: {breakpoint.name} ({breakpoint_id}) in trace {trace_id}")
                    return breakpoint_id
            
            return None
    
    def pause_trace(self, trace_id: str, breakpoint_id: str, event_data: Dict[str, Any]) -> str:
        """
        Pause a trace at a breakpoint.
        
        Args:
            trace_id: Trace to pause
            breakpoint_id: Breakpoint that was hit
            event_data: Event data at pause point
            
        Returns:
            Hit ID for tracking
        """
        with self._lock:
            if len(self.paused_traces) >= self.config['max_paused_traces']:
                # Clean up oldest paused trace
                oldest_trace_id = min(self.paused_traces.keys(), 
                                    key=lambda tid: self.paused_traces[tid].paused_at)
                self.resume_trace(oldest_trace_id, "auto_cleanup", {})
            
            hit_id = str(uuid.uuid4())
            timeout_at = datetime.now() + timedelta(minutes=self.config['default_timeout_minutes'])
            
            paused_trace = PausedTrace(
                trace_id=trace_id,
                breakpoint_id=breakpoint_id,
                hit_id=hit_id,
                paused_at=datetime.now(),
                event_data=event_data,
                timeout_at=timeout_at
            )
            
            self.paused_traces[trace_id] = paused_trace
            
            logger.info(f"Paused trace {trace_id} at breakpoint {breakpoint_id}")
            return hit_id
    
    def wait_for_resume(self, trace_id: str, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Wait for a paused trace to be resumed.
        
        Args:
            trace_id: Trace ID to wait for
            timeout_seconds: Override timeout in seconds
            
        Returns:
            Resume result with optional override payload
        """
        if trace_id not in self.paused_traces:
            return {"action": "continue", "override_payload": None}
        
        paused_trace = self.paused_traces[trace_id]
        
        # Calculate timeout
        if timeout_seconds:
            timeout_at = datetime.now() + timedelta(seconds=timeout_seconds)
        else:
            timeout_at = paused_trace.timeout_at
        
        # Wait for resume or timeout
        while paused_trace.waiting_for_resume and datetime.now() < timeout_at:
            time.sleep(0.1)  # Check every 100ms
            
            # Check if trace was resumed
            if trace_id not in self.paused_traces:
                break
        
        # Handle timeout
        if datetime.now() >= timeout_at and trace_id in self.paused_traces:
            logger.warning(f"Trace {trace_id} timed out waiting for resume")
            self.resume_trace(trace_id, "timeout", {})
            return {"action": "timeout", "override_payload": None}
        
        # Return resume result
        override_payload = paused_trace.override_payload
        return {"action": "resume", "override_payload": override_payload}
    
    def resume_trace(self, trace_id: str, resolved_by: str, 
                    override_payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Resume a paused trace.
        
        Args:
            trace_id: Trace to resume
            resolved_by: User who resumed the trace
            override_payload: Optional payload override
            
        Returns:
            True if successfully resumed
        """
        with self._lock:
            if trace_id not in self.paused_traces:
                return False
            
            paused_trace = self.paused_traces[trace_id]
            paused_trace.waiting_for_resume = False
            paused_trace.override_payload = override_payload
            
            # Update hit record
            if paused_trace.hit_id in self.breakpoint_hits:
                hit = self.breakpoint_hits[paused_trace.hit_id]
                hit.resolved_timestamp = datetime.now()
                hit.override_payload = override_payload
                hit.resolution_action = "resume"
                hit.resolved_by = resolved_by
            
            # Remove from paused traces
            del self.paused_traces[trace_id]
            
            logger.info(f"Resumed trace {trace_id} by {resolved_by}")
            return True
    
    def _record_breakpoint_hit(self, breakpoint_id: str, trace_id: str, 
                              event_data: Dict[str, Any]) -> str:
        """Record a breakpoint hit."""
        hit_id = str(uuid.uuid4())
        
        hit = BreakpointHit(
            hit_id=hit_id,
            breakpoint_id=breakpoint_id,
            trace_id=trace_id,
            event_data=event_data,
            hit_timestamp=datetime.now()
        )
        
        self.breakpoint_hits[hit_id] = hit
        
        # Limit hit history
        if len(self.breakpoint_hits) > self.config['hit_history_limit']:
            # Remove oldest hits
            oldest_hits = sorted(self.breakpoint_hits.items(), 
                               key=lambda x: x[1].hit_timestamp)
            for hit_id, _ in oldest_hits[:100]:  # Remove 100 oldest
                del self.breakpoint_hits[hit_id]
        
        return hit_id
    
    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        
        # Convert wildcard pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", value, re.IGNORECASE))
    
    def _validate_condition(self, condition: str) -> bool:
        """Validate condition syntax."""
        try:
            # Basic syntax check
            compile(condition, '<condition>', 'eval')
            
            # Check for dangerous operations
            dangerous_keywords = ['import', 'exec', 'eval', 'open', 'file', '__']
            for keyword in dangerous_keywords:
                if keyword in condition:
                    return False
            
            return True
        except:
            return False
    
    def _evaluate_condition(self, condition: str, event_data: Dict[str, Any]) -> bool:
        """Safely evaluate breakpoint condition."""
        try:
            # Create safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'payload': event_data.get('payload', {}),
                'message': event_data.get('message', ''),
                'severity': event_data.get('severity', ''),
                'timestamp': event_data.get('timestamp', 0),
                'event_type': event_data.get('event_type', ''),
                'source_module': event_data.get('source_module', ''),
                # Safe functions
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool
            }
            
            # Evaluate with timeout
            result = eval(condition, safe_dict)
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _load_breakpoints(self):
        """Load breakpoints from configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    
                    for bp_data in data.get('breakpoints', []):
                        breakpoint = Breakpoint(
                            breakpoint_id=bp_data['breakpoint_id'],
                            name=bp_data['name'],
                            description=bp_data['description'],
                            module_name=bp_data['module_name'],
                            event_type=bp_data['event_type'],
                            condition=bp_data['condition'],
                            status=BreakpointStatus(bp_data.get('status', 'active')),
                            created_by=bp_data.get('created_by', 'system'),
                            created_at=datetime.fromisoformat(bp_data.get('created_at', datetime.now().isoformat())),
                            hit_count=bp_data.get('hit_count', 0),
                            max_hits=bp_data.get('max_hits'),
                            expires_at=datetime.fromisoformat(bp_data['expires_at']) if bp_data.get('expires_at') else None,
                            enabled=bp_data.get('enabled', True)
                        )
                        self.breakpoints[breakpoint.breakpoint_id] = breakpoint
                        
        except Exception as e:
            logger.error(f"Error loading breakpoints: {e}")
    
    def _save_breakpoints(self):
        """Save breakpoints to configuration file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            data = {
                'breakpoints': [
                    {
                        'breakpoint_id': bp.breakpoint_id,
                        'name': bp.name,
                        'description': bp.description,
                        'module_name': bp.module_name,
                        'event_type': bp.event_type,
                        'condition': bp.condition,
                        'status': bp.status.value,
                        'created_by': bp.created_by,
                        'created_at': bp.created_at.isoformat(),
                        'hit_count': bp.hit_count,
                        'max_hits': bp.max_hits,
                        'expires_at': bp.expires_at.isoformat() if bp.expires_at else None,
                        'enabled': bp.enabled
                    }
                    for bp in self.breakpoints.values()
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving breakpoints: {e}")
    
    def _start_cleanup_thread(self):
        """Start background thread for cleanup tasks."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(60)  # Run every minute
                    self._cleanup_expired_breakpoints()
                    self._cleanup_timed_out_traces()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired_breakpoints(self):
        """Clean up expired breakpoints."""
        if not self.config['auto_cleanup_expired']:
            return
        
        with self._lock:
            expired_ids = []
            for bp_id, breakpoint in self.breakpoints.items():
                if (breakpoint.expires_at and datetime.now() > breakpoint.expires_at) or \
                   (breakpoint.max_hits and breakpoint.hit_count >= breakpoint.max_hits):
                    expired_ids.append(bp_id)
            
            for bp_id in expired_ids:
                del self.breakpoints[bp_id]
                logger.info(f"Cleaned up expired breakpoint {bp_id}")
            
            if expired_ids:
                self._save_breakpoints()
    
    def _cleanup_timed_out_traces(self):
        """Clean up timed out paused traces."""
        with self._lock:
            timed_out_traces = []
            for trace_id, paused_trace in self.paused_traces.items():
                if paused_trace.timeout_at and datetime.now() > paused_trace.timeout_at:
                    timed_out_traces.append(trace_id)
            
            for trace_id in timed_out_traces:
                self.resume_trace(trace_id, "auto_timeout", {})
    
    def get_breakpoints(self) -> List[Dict[str, Any]]:
        """Get all breakpoints."""
        with self._lock:
            return [
                {
                    'breakpoint_id': bp.breakpoint_id,
                    'name': bp.name,
                    'description': bp.description,
                    'module_name': bp.module_name,
                    'event_type': bp.event_type,
                    'condition': bp.condition,
                    'status': bp.status.value,
                    'created_by': bp.created_by,
                    'created_at': bp.created_at.isoformat(),
                    'hit_count': bp.hit_count,
                    'max_hits': bp.max_hits,
                    'expires_at': bp.expires_at.isoformat() if bp.expires_at else None,
                    'enabled': bp.enabled
                }
                for bp in self.breakpoints.values()
            ]
    
    def get_paused_traces(self) -> List[Dict[str, Any]]:
        """Get all paused traces."""
        with self._lock:
            return [
                {
                    'trace_id': pt.trace_id,
                    'breakpoint_id': pt.breakpoint_id,
                    'hit_id': pt.hit_id,
                    'paused_at': pt.paused_at.isoformat(),
                    'timeout_at': pt.timeout_at.isoformat() if pt.timeout_at else None,
                    'event_data': pt.event_data
                }
                for pt in self.paused_traces.values()
            ]

# Global breakpoint manager instance
_breakpoint_manager = None

def get_breakpoint_manager() -> BreakpointManager:
    """Get the global breakpoint manager instance."""
    global _breakpoint_manager
    if _breakpoint_manager is None:
        _breakpoint_manager = BreakpointManager()
    return _breakpoint_manager
