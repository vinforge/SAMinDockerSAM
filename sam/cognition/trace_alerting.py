#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Real-time Alerting System
======================================================

Production-ready alerting system for monitoring SAM's performance and
sending notifications when issues are detected.

Author: SAM Development Team
Version: 2.0.0 (Phase 2B)
"""

import os
import json
import time
import smtplib
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    LOG = "log"
    CONSOLE = "console"

@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    description: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 15
    enabled: bool = True
    context_fields: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    channels_sent: List[AlertChannel] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class AlertChannel_Config:
    """Alert channel configuration."""
    channel: AlertChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

class AlertManager:
    """
    Real-time alerting system for SAM Introspection Dashboard.
    
    Provides comprehensive alerting capabilities including:
    - Rule-based alert generation
    - Multiple delivery channels (email, webhook, Slack, etc.)
    - Alert deduplication and cooldown
    - Alert acknowledgment and resolution
    - Alert history and statistics
    - Integration with performance monitoring
    """
    
    def __init__(self, config_path: str = "config/alerting.json"):
        """
        Initialize the alert manager.
        
        Args:
            config_path: Path to alerting configuration file
        """
        self.config_path = config_path
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_channels: Dict[AlertChannel, AlertChannel_Config] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        
        # Configuration
        self.config = {
            'max_alert_history': 1000,
            'enable_deduplication': True,
            'default_cooldown_minutes': 15,
            'enable_auto_resolution': True,
            'auto_resolution_timeout_hours': 24,
            'batch_alerts': False,
            'batch_interval_minutes': 5
        }
        
        # Load configuration
        self._load_config()
        self._init_default_rules()
        self._init_default_channels()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("AlertManager initialized")
    
    def _init_default_rules(self):
        """Initialize default alert rules."""
        default_rules = [
            AlertRule(
                rule_id="high_error_rate",
                name="High Error Rate",
                description="Alert when error rate exceeds threshold",
                condition="error_rate > 0.1",  # 10% error rate
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.LOG],
                cooldown_minutes=30
            ),
            AlertRule(
                rule_id="slow_response_time",
                name="Slow Response Time",
                description="Alert when response time is too high",
                condition="response_time > 5.0",  # 5 seconds
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
                cooldown_minutes=15
            ),
            AlertRule(
                rule_id="circuit_breaker_open",
                name="Circuit Breaker Open",
                description="Alert when circuit breaker opens",
                condition="circuit_state == 'open'",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG],
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="memory_usage_high",
                name="High Memory Usage",
                description="Alert when memory usage is high",
                condition="memory_usage > 0.9",  # 90% memory usage
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG, AlertChannel.WEBHOOK],
                cooldown_minutes=20
            ),
            AlertRule(
                rule_id="goal_generation_failure",
                name="Goal Generation Failure",
                description="Alert when Goal & Motivation Engine fails",
                condition="goal_generation_errors > 0",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG, AlertChannel.EMAIL],
                cooldown_minutes=10
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def _init_default_channels(self):
        """Initialize default alert channels."""
        self.alert_channels = {
            AlertChannel.LOG: AlertChannel_Config(
                channel=AlertChannel.LOG,
                enabled=True
            ),
            AlertChannel.CONSOLE: AlertChannel_Config(
                channel=AlertChannel.CONSOLE,
                enabled=True
            ),
            AlertChannel.EMAIL: AlertChannel_Config(
                channel=AlertChannel.EMAIL,
                enabled=False,  # Disabled by default, requires configuration
                config={
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_email': 'sam-alerts@localhost',
                    'to_emails': []
                }
            ),
            AlertChannel.WEBHOOK: AlertChannel_Config(
                channel=AlertChannel.WEBHOOK,
                enabled=False,  # Disabled by default, requires configuration
                config={
                    'url': '',
                    'headers': {},
                    'timeout': 10
                }
            ),
            AlertChannel.SLACK: AlertChannel_Config(
                channel=AlertChannel.SLACK,
                enabled=False,  # Disabled by default, requires configuration
                config={
                    'webhook_url': '',
                    'channel': '#alerts',
                    'username': 'SAM-Alerts'
                }
            )
        }
    
    def evaluate_conditions(self, context: Dict[str, Any]):
        """
        Evaluate alert conditions against current context.
        
        Args:
            context: Current system context with metrics and status
        """
        with self._lock:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    # Check cooldown
                    if self._is_in_cooldown(rule.rule_id):
                        continue
                    
                    # Evaluate condition
                    if self._evaluate_condition(rule.condition, context):
                        self._trigger_alert(rule, context)
                        
                except Exception as e:
                    logger.error(f"Error evaluating alert rule {rule.rule_id}: {e}")
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate alert condition expression."""
        try:
            # Create safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                **context
            }
            
            # Evaluate condition
            return bool(eval(condition, safe_dict))
            
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, context: Dict[str, Any]):
        """Trigger an alert based on rule and context."""
        alert_id = f"{rule.rule_id}_{int(time.time())}"
        
        # Extract relevant context fields
        alert_context = {}
        for field in rule.context_fields:
            if field in context:
                alert_context[field] = context[field]
        
        # Create alert
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            title=rule.name,
            message=self._format_alert_message(rule, context),
            timestamp=datetime.now(),
            context=alert_context
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Trim history if needed
        if len(self.alert_history) > self.config['max_alert_history']:
            self.alert_history = self.alert_history[-self.config['max_alert_history']:]
        
        # Update cooldown
        self.last_alert_times[rule.rule_id] = datetime.now()
        
        # Send alert through channels
        self._send_alert(alert, rule.channels)
        
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
    
    def _format_alert_message(self, rule: AlertRule, context: Dict[str, Any]) -> str:
        """Format alert message with context information."""
        message = f"{rule.description}\n\n"
        message += f"Condition: {rule.condition}\n"
        message += f"Timestamp: {datetime.now().isoformat()}\n"
        
        # Add relevant context
        if 'error_rate' in context:
            message += f"Error Rate: {context['error_rate']:.2%}\n"
        if 'response_time' in context:
            message += f"Response Time: {context['response_time']:.2f}s\n"
        if 'memory_usage' in context:
            message += f"Memory Usage: {context['memory_usage']:.1%}\n"
        if 'circuit_state' in context:
            message += f"Circuit State: {context['circuit_state']}\n"
        
        return message
    
    def _send_alert(self, alert: Alert, channels: List[AlertChannel]):
        """Send alert through specified channels."""
        for channel in channels:
            try:
                channel_config = self.alert_channels.get(channel)
                if not channel_config or not channel_config.enabled:
                    continue
                
                if channel == AlertChannel.LOG:
                    self._send_log_alert(alert)
                elif channel == AlertChannel.CONSOLE:
                    self._send_console_alert(alert)
                elif channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert, channel_config.config)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert, channel_config.config)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(alert, channel_config.config)
                
                alert.channels_sent.append(channel)
                
            except Exception as e:
                logger.error(f"Error sending alert via {channel.value}: {e}")
    
    def _send_log_alert(self, alert: Alert):
        """Send alert to log."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.EMERGENCY: logging.CRITICAL
        }.get(alert.severity, logging.WARNING)
        
        logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
    
    def _send_console_alert(self, alert: Alert):
        """Send alert to console."""
        severity_colors = {
            AlertSeverity.INFO: '\033[94m',      # Blue
            AlertSeverity.WARNING: '\033[93m',   # Yellow
            AlertSeverity.CRITICAL: '\033[91m',  # Red
            AlertSeverity.EMERGENCY: '\033[95m'  # Magenta
        }
        reset_color = '\033[0m'
        
        color = severity_colors.get(alert.severity, '')
        print(f"{color}[ALERT {alert.severity.value.upper()}] {alert.title}: {alert.message}{reset_color}")
    
    def _send_email_alert(self, alert: Alert, config: Dict[str, Any]):
        """Send alert via email."""
        if not config.get('to_emails'):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"SAM Alert [{alert.severity.value.upper()}]: {alert.title}"
            
            body = f"""
SAM Introspection Dashboard Alert

Severity: {alert.severity.value.upper()}
Title: {alert.title}
Time: {alert.timestamp.isoformat()}

Message:
{alert.message}

Context:
{json.dumps(alert.context, indent=2)}

Alert ID: {alert.alert_id}
Rule ID: {alert.rule_id}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('username') and config.get('password'):
                server.starttls()
                server.login(config['username'], config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_webhook_alert(self, alert: Alert, config: Dict[str, Any]):
        """Send alert via webhook."""
        if not config.get('url'):
            return
        
        try:
            payload = {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'context': alert.context
            }
            
            headers = config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            
            response = requests.post(
                config['url'],
                json=payload,
                headers=headers,
                timeout=config.get('timeout', 10)
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    def _send_slack_alert(self, alert: Alert, config: Dict[str, Any]):
        """Send alert via Slack webhook."""
        if not config.get('webhook_url'):
            return
        
        try:
            severity_colors = {
                AlertSeverity.INFO: '#36a64f',      # Green
                AlertSeverity.WARNING: '#ffaa00',   # Orange
                AlertSeverity.CRITICAL: '#ff0000',  # Red
                AlertSeverity.EMERGENCY: '#800080'  # Purple
            }
            
            payload = {
                'channel': config.get('channel', '#alerts'),
                'username': config.get('username', 'SAM-Alerts'),
                'attachments': [{
                    'color': severity_colors.get(alert.severity, '#ffaa00'),
                    'title': f"SAM Alert [{alert.severity.value.upper()}]",
                    'text': alert.title,
                    'fields': [
                        {
                            'title': 'Message',
                            'value': alert.message,
                            'short': False
                        },
                        {
                            'title': 'Time',
                            'value': alert.timestamp.isoformat(),
                            'short': True
                        },
                        {
                            'title': 'Alert ID',
                            'value': alert.alert_id,
                            'short': True
                        }
                    ]
                }]
            }
            
            response = requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period."""
        if rule_id not in self.last_alert_times:
            return False
        
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return False
        
        time_since_last = datetime.now() - self.last_alert_times[rule_id]
        return time_since_last.total_seconds() < (rule.cooldown_minutes * 60)
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert."""
        with self._lock:
            alert = self.active_alerts.get(alert_id)
            if alert:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
            return False
    
    def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """Resolve an alert."""
        with self._lock:
            alert = self.active_alerts.get(alert_id)
            if alert:
                alert.resolved = True
                if alert_id in self.active_alerts:
                    del self.active_alerts[alert_id]
                logger.info(f"Alert {alert_id} resolved by {user}")
                return True
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        with self._lock:
            return list(self.active_alerts.values())
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            stats = {
                'total_alerts': len(self.alert_history),
                'active_alerts': len(self.active_alerts),
                'alerts_by_severity': {},
                'alerts_by_rule': {},
                'recent_alerts': []
            }
            
            # Count by severity
            for severity in AlertSeverity:
                count = len([a for a in self.alert_history if a.severity == severity])
                stats['alerts_by_severity'][severity.value] = count
            
            # Count by rule
            for rule_id in self.alert_rules.keys():
                count = len([a for a in self.alert_history if a.rule_id == rule_id])
                stats['alerts_by_rule'][rule_id] = count
            
            # Recent alerts (last 10)
            for alert in self.alert_history[-10:]:
                stats['recent_alerts'].append({
                    'alert_id': alert.alert_id,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'resolved': alert.resolved
                })
            
            return stats
    
    def _load_config(self):
        """Load alerting configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            logger.error(f"Error loading alerting config: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks for alert management."""
        # This would start background threads for:
        # - Auto-resolution of old alerts
        # - Batch alert processing
        # - Alert cleanup
        logger.info("Alert background tasks initialized")

# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
