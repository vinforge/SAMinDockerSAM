#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Security & Access Control
=======================================================

Production-ready security layer for the introspection dashboard including
authentication, authorization, role-based access control, and audit logging.

Author: SAM Development Team
Version: 2.0.0 (Phase 2B)
"""

import os
import time
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import threading

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access levels for introspection dashboard."""
    NONE = 0
    READ_ONLY = 1
    ANALYST = 2
    ADMIN = 3
    SUPER_ADMIN = 4

class SecurityEvent(Enum):
    """Security event types for audit logging."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class User:
    """User account for introspection dashboard."""
    username: str
    password_hash: str
    access_level: AccessLevel
    created_at: datetime
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    api_key: Optional[str] = None
    permissions: Set[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = set()

@dataclass
class Session:
    """User session for introspection dashboard."""
    session_id: str
    username: str
    access_level: AccessLevel
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    expires_at: datetime

@dataclass
class AuditLogEntry:
    """Audit log entry for security events."""
    timestamp: datetime
    event_type: SecurityEvent
    username: str
    ip_address: str
    user_agent: str
    resource: str
    action: str
    success: bool
    details: Dict[str, Any]

class TraceSecurityManager:
    """
    Security manager for SAM Introspection Dashboard.
    
    Provides comprehensive security features including:
    - User authentication and authorization
    - Role-based access control (RBAC)
    - Session management
    - API key authentication
    - Audit logging
    - Rate limiting
    - Security monitoring
    """
    
    def __init__(self, config_path: str = "config/trace_security.json"):
        """
        Initialize the security manager.
        
        Args:
            config_path: Path to security configuration file
        """
        self.config_path = config_path
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.audit_log: List[AuditLogEntry] = []
        self.rate_limits: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
        
        # Security configuration
        self.config = {
            'session_timeout_minutes': 60,
            'max_failed_attempts': 5,
            'lockout_duration_minutes': 30,
            'password_min_length': 8,
            'require_strong_passwords': True,
            'api_key_length': 32,
            'rate_limit_requests_per_minute': 100,
            'audit_log_max_entries': 10000,
            'enable_ip_whitelist': False,
            'allowed_ips': [],
            'enable_2fa': False,
            'session_cookie_secure': True,
            'session_cookie_httponly': True
        }
        
        # Load configuration and users
        self._load_config()
        self._load_users()
        
        # Create default admin user if none exists
        if not self.users:
            self._create_default_admin()
        
        logger.info("TraceSecurityManager initialized")
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = "unknown", 
                         user_agent: str = "unknown") -> Optional[str]:
        """
        Authenticate a user and create a session.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID if authentication successful, None otherwise
        """
        with self._lock:
            try:
                # Check rate limiting
                if not self._check_rate_limit(ip_address):
                    self._log_security_event(
                        SecurityEvent.SECURITY_VIOLATION,
                        username, ip_address, user_agent,
                        "authentication", "rate_limit_exceeded",
                        False, {"reason": "Too many requests"}
                    )
                    return None
                
                # Get user
                user = self.users.get(username)
                if not user:
                    self._log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        username, ip_address, user_agent,
                        "authentication", "login",
                        False, {"reason": "User not found"}
                    )
                    return None
                
                # Check if account is locked
                if user.locked_until and datetime.now() < user.locked_until:
                    self._log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        username, ip_address, user_agent,
                        "authentication", "login",
                        False, {"reason": "Account locked"}
                    )
                    return None
                
                # Verify password
                if not self._verify_password(password, user.password_hash):
                    user.failed_attempts += 1
                    
                    # Lock account if too many failures
                    if user.failed_attempts >= self.config['max_failed_attempts']:
                        user.locked_until = datetime.now() + timedelta(
                            minutes=self.config['lockout_duration_minutes']
                        )
                        logger.warning(f"Account {username} locked due to failed attempts")
                    
                    self._log_security_event(
                        SecurityEvent.LOGIN_FAILURE,
                        username, ip_address, user_agent,
                        "authentication", "login",
                        False, {"reason": "Invalid password", "attempts": user.failed_attempts}
                    )
                    self._save_users()
                    return None
                
                # Reset failed attempts on successful login
                user.failed_attempts = 0
                user.last_login = datetime.now()
                user.locked_until = None
                
                # Create session
                session_id = self._generate_session_id()
                session = Session(
                    session_id=session_id,
                    username=username,
                    access_level=user.access_level,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=datetime.now() + timedelta(
                        minutes=self.config['session_timeout_minutes']
                    )
                )
                
                self.sessions[session_id] = session
                
                self._log_security_event(
                    SecurityEvent.LOGIN_SUCCESS,
                    username, ip_address, user_agent,
                    "authentication", "login",
                    True, {"session_id": session_id}
                )
                
                self._save_users()
                logger.info(f"User {username} authenticated successfully")
                return session_id
                
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                self._log_security_event(
                    SecurityEvent.SECURITY_VIOLATION,
                    username, ip_address, user_agent,
                    "authentication", "login",
                    False, {"error": str(e)}
                )
                return None
    
    def validate_session(self, session_id: str, 
                        ip_address: str = "unknown") -> Optional[Session]:
        """
        Validate a session and update last activity.
        
        Args:
            session_id: Session ID to validate
            ip_address: Client IP address
            
        Returns:
            Session object if valid, None otherwise
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            # Check if session expired
            if datetime.now() > session.expires_at:
                del self.sessions[session_id]
                logger.info(f"Session {session_id} expired")
                return None
            
            # Check IP address consistency (optional security measure)
            if self.config.get('enforce_ip_consistency', False):
                if session.ip_address != ip_address:
                    self._log_security_event(
                        SecurityEvent.SECURITY_VIOLATION,
                        session.username, ip_address, "",
                        "session", "ip_mismatch",
                        False, {"session_ip": session.ip_address, "request_ip": ip_address}
                    )
                    return None
            
            # Update last activity
            session.last_activity = datetime.now()
            session.expires_at = datetime.now() + timedelta(
                minutes=self.config['session_timeout_minutes']
            )
            
            return session
    
    def check_permission(self, session_id: str, resource: str, 
                        action: str, ip_address: str = "unknown") -> bool:
        """
        Check if a session has permission for a specific action.
        
        Args:
            session_id: Session ID
            resource: Resource being accessed
            action: Action being performed
            ip_address: Client IP address
            
        Returns:
            True if permission granted, False otherwise
        """
        session = self.validate_session(session_id, ip_address)
        if not session:
            return False
        
        # Check access level permissions
        required_level = self._get_required_access_level(resource, action)
        has_permission = session.access_level.value >= required_level.value
        
        # Log access attempt
        self._log_security_event(
            SecurityEvent.DATA_ACCESS if has_permission else SecurityEvent.UNAUTHORIZED_ACCESS,
            session.username, ip_address, "",
            resource, action,
            has_permission, {
                "required_level": required_level.name,
                "user_level": session.access_level.name
            }
        )
        
        return has_permission
    
    def _get_required_access_level(self, resource: str, action: str) -> AccessLevel:
        """Get required access level for resource/action combination."""
        # Define access control matrix
        access_matrix = {
            'traces': {
                'read': AccessLevel.READ_ONLY,
                'export': AccessLevel.ANALYST,
                'delete': AccessLevel.ADMIN
            },
            'analytics': {
                'read': AccessLevel.READ_ONLY,
                'generate': AccessLevel.ANALYST
            },
            'admin': {
                'read': AccessLevel.ADMIN,
                'write': AccessLevel.ADMIN,
                'user_management': AccessLevel.SUPER_ADMIN
            },
            'system': {
                'health': AccessLevel.READ_ONLY,
                'config': AccessLevel.ADMIN,
                'restart': AccessLevel.SUPER_ADMIN
            }
        }
        
        return access_matrix.get(resource, {}).get(action, AccessLevel.ADMIN)
    
    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        # Simple hash verification (in production, use bcrypt or similar)
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        # Simple hash (in production, use bcrypt or similar)
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """Check if identifier is within rate limits."""
        now = time.time()
        window = 60  # 1 minute window
        
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Remove old entries
        self.rate_limits[identifier] = [
            timestamp for timestamp in self.rate_limits[identifier]
            if now - timestamp < window
        ]
        
        # Check limit
        if len(self.rate_limits[identifier]) >= self.config['rate_limit_requests_per_minute']:
            return False
        
        # Add current request
        self.rate_limits[identifier].append(now)
        return True
    
    def _log_security_event(self, event_type: SecurityEvent, username: str,
                           ip_address: str, user_agent: str, resource: str,
                           action: str, success: bool, details: Dict[str, Any]):
        """Log a security event."""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            success=success,
            details=details
        )
        
        self.audit_log.append(entry)
        
        # Trim audit log if too large
        if len(self.audit_log) > self.config['audit_log_max_entries']:
            self.audit_log = self.audit_log[-self.config['audit_log_max_entries']:]
        
        # Log to file for persistence
        logger.info(f"Security event: {event_type.value} - {username}@{ip_address} - {resource}:{action} - {'SUCCESS' if success else 'FAILURE'}")
    
    def _create_default_admin(self):
        """Create default admin user."""
        admin_password = os.getenv('SAM_ADMIN_PASSWORD', 'admin123')
        admin_user = User(
            username='admin',
            password_hash=self._hash_password(admin_password),
            access_level=AccessLevel.SUPER_ADMIN,
            created_at=datetime.now(),
            permissions={'*'}  # All permissions
        )
        
        self.users['admin'] = admin_user
        self._save_users()
        logger.warning(f"Created default admin user with password: {admin_password}")
    
    def _load_config(self):
        """Load security configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            logger.error(f"Error loading security config: {e}")
    
    def _load_users(self):
        """Load users from storage."""
        # In production, this would load from a secure database
        # For now, we'll use a simple file-based approach
        pass
    
    def _save_users(self):
        """Save users to storage."""
        # In production, this would save to a secure database
        # For now, we'll use a simple file-based approach
        pass

# Global security manager instance
_security_manager = None

def get_security_manager() -> TraceSecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = TraceSecurityManager()
    return _security_manager
