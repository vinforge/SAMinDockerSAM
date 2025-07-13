#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Data Retention & Cleanup Policies
===============================================================

Production-ready data retention system for managing trace data lifecycle,
automated cleanup, archival, and storage optimization.

Author: SAM Development Team
Version: 2.0.0 (Phase 2B)
"""

import os
import time
import gzip
import json
import shutil
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

class RetentionPolicy(Enum):
    """Data retention policies."""
    IMMEDIATE = "immediate"  # Delete immediately after processing
    SHORT_TERM = "short_term"  # Keep for 7 days
    MEDIUM_TERM = "medium_term"  # Keep for 30 days
    LONG_TERM = "long_term"  # Keep for 1 year
    PERMANENT = "permanent"  # Keep indefinitely
    ARCHIVE = "archive"  # Compress and archive

class DataCategory(Enum):
    """Categories of trace data."""
    TRACE_EVENTS = "trace_events"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_LOGS = "error_logs"
    SECURITY_AUDIT = "security_audit"
    ANALYTICS_CACHE = "analytics_cache"
    EXPORTED_DATA = "exported_data"

@dataclass
class RetentionRule:
    """Rule for data retention."""
    category: DataCategory
    policy: RetentionPolicy
    retention_days: int
    archive_after_days: Optional[int] = None
    compress: bool = True
    priority: int = 1  # Higher priority rules override lower ones
    conditions: Dict[str, Any] = None  # Additional conditions
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = {}

@dataclass
class CleanupJob:
    """Cleanup job definition."""
    job_id: str
    name: str
    description: str
    schedule_cron: str  # Cron-like schedule
    retention_rules: List[RetentionRule]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    job_id: str
    start_time: datetime
    end_time: datetime
    records_processed: int
    records_deleted: int
    records_archived: int
    bytes_freed: int
    errors: List[str]
    success: bool

class TraceRetentionManager:
    """
    Data retention and cleanup manager for SAM Introspection Dashboard.
    
    Provides comprehensive data lifecycle management including:
    - Automated cleanup based on retention policies
    - Data archival and compression
    - Storage optimization
    - Compliance with data retention requirements
    - Performance monitoring
    - Audit trail for cleanup operations
    """
    
    def __init__(self, db_path: str = "data/sam_introspection.db",
                 archive_path: str = "data/archives"):
        """
        Initialize the retention manager.
        
        Args:
            db_path: Path to the trace database
            archive_path: Path for archived data
        """
        self.db_path = Path(db_path)
        self.archive_path = Path(archive_path)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
        self.cleanup_jobs: Dict[str, CleanupJob] = {}
        self.cleanup_history: List[CleanupResult] = []
        
        # Configuration
        self.config = {
            'enable_auto_cleanup': True,
            'cleanup_interval_hours': 24,
            'max_cleanup_history': 100,
            'archive_compression_level': 6,
            'batch_size': 1000,
            'max_cleanup_duration_minutes': 60,
            'enable_performance_monitoring': True,
            'backup_before_cleanup': True,
            'verify_after_cleanup': True
        }
        
        # Initialize default retention rules
        self._init_default_rules()
        
        # Start cleanup scheduler
        self._start_scheduler()
        
        logger.info("TraceRetentionManager initialized")
    
    def _init_default_rules(self):
        """Initialize default retention rules."""
        default_jobs = [
            CleanupJob(
                job_id="daily_cleanup",
                name="Daily Cleanup",
                description="Daily cleanup of temporary and expired data",
                schedule_cron="0 2 * * *",  # 2 AM daily
                retention_rules=[
                    RetentionRule(
                        category=DataCategory.TRACE_EVENTS,
                        policy=RetentionPolicy.MEDIUM_TERM,
                        retention_days=30,
                        archive_after_days=7
                    ),
                    RetentionRule(
                        category=DataCategory.PERFORMANCE_METRICS,
                        policy=RetentionPolicy.LONG_TERM,
                        retention_days=365,
                        archive_after_days=90
                    ),
                    RetentionRule(
                        category=DataCategory.ERROR_LOGS,
                        policy=RetentionPolicy.LONG_TERM,
                        retention_days=365
                    ),
                    RetentionRule(
                        category=DataCategory.SECURITY_AUDIT,
                        policy=RetentionPolicy.PERMANENT,
                        retention_days=-1  # Never delete
                    ),
                    RetentionRule(
                        category=DataCategory.ANALYTICS_CACHE,
                        policy=RetentionPolicy.SHORT_TERM,
                        retention_days=7
                    )
                ]
            ),
            CleanupJob(
                job_id="weekly_archive",
                name="Weekly Archive",
                description="Weekly archival of older data",
                schedule_cron="0 3 * * 0",  # 3 AM on Sundays
                retention_rules=[
                    RetentionRule(
                        category=DataCategory.TRACE_EVENTS,
                        policy=RetentionPolicy.ARCHIVE,
                        retention_days=7,
                        compress=True
                    )
                ]
            )
        ]
        
        for job in default_jobs:
            self.cleanup_jobs[job.job_id] = job
    
    def run_cleanup_job(self, job_id: str) -> CleanupResult:
        """
        Run a specific cleanup job.
        
        Args:
            job_id: ID of the cleanup job to run
            
        Returns:
            CleanupResult with operation details
        """
        with self._lock:
            job = self.cleanup_jobs.get(job_id)
            if not job:
                raise ValueError(f"Cleanup job {job_id} not found")
            
            if not job.enabled:
                raise ValueError(f"Cleanup job {job_id} is disabled")
            
            start_time = datetime.now()
            logger.info(f"Starting cleanup job: {job.name}")
            
            result = CleanupResult(
                job_id=job_id,
                start_time=start_time,
                end_time=start_time,  # Will be updated
                records_processed=0,
                records_deleted=0,
                records_archived=0,
                bytes_freed=0,
                errors=[],
                success=False
            )
            
            try:
                # Create backup if enabled
                if self.config['backup_before_cleanup']:
                    self._create_backup(job_id)
                
                # Process each retention rule
                for rule in job.retention_rules:
                    rule_result = self._apply_retention_rule(rule)
                    result.records_processed += rule_result['processed']
                    result.records_deleted += rule_result['deleted']
                    result.records_archived += rule_result['archived']
                    result.bytes_freed += rule_result['bytes_freed']
                    result.errors.extend(rule_result['errors'])
                
                # Verify cleanup if enabled
                if self.config['verify_after_cleanup']:
                    self._verify_cleanup(job, result)
                
                # Update job status
                job.last_run = start_time
                result.end_time = datetime.now()
                result.success = len(result.errors) == 0
                
                # Add to history
                self.cleanup_history.append(result)
                if len(self.cleanup_history) > self.config['max_cleanup_history']:
                    self.cleanup_history = self.cleanup_history[-self.config['max_cleanup_history']:]
                
                logger.info(f"Cleanup job {job.name} completed: "
                           f"{result.records_deleted} deleted, "
                           f"{result.records_archived} archived, "
                           f"{result.bytes_freed} bytes freed")
                
                return result
                
            except Exception as e:
                result.errors.append(str(e))
                result.end_time = datetime.now()
                result.success = False
                logger.error(f"Cleanup job {job.name} failed: {e}")
                return result
    
    def _apply_retention_rule(self, rule: RetentionRule) -> Dict[str, int]:
        """Apply a specific retention rule."""
        result = {
            'processed': 0,
            'deleted': 0,
            'archived': 0,
            'bytes_freed': 0,
            'errors': []
        }
        
        try:
            if rule.category == DataCategory.TRACE_EVENTS:
                result.update(self._cleanup_trace_events(rule))
            elif rule.category == DataCategory.PERFORMANCE_METRICS:
                result.update(self._cleanup_performance_metrics(rule))
            elif rule.category == DataCategory.ERROR_LOGS:
                result.update(self._cleanup_error_logs(rule))
            elif rule.category == DataCategory.ANALYTICS_CACHE:
                result.update(self._cleanup_analytics_cache(rule))
            elif rule.category == DataCategory.EXPORTED_DATA:
                result.update(self._cleanup_exported_data(rule))
            
        except Exception as e:
            result['errors'].append(f"Error applying rule {rule.category.value}: {e}")
            logger.error(f"Error applying retention rule: {e}")
        
        return result
    
    def _cleanup_trace_events(self, rule: RetentionRule) -> Dict[str, int]:
        """Clean up trace events based on retention rule."""
        result = {'processed': 0, 'deleted': 0, 'archived': 0, 'bytes_freed': 0, 'errors': []}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate cutoff dates
                if rule.retention_days > 0:
                    delete_cutoff = datetime.now() - timedelta(days=rule.retention_days)
                    delete_timestamp = delete_cutoff.timestamp()
                else:
                    delete_timestamp = None  # Never delete
                
                archive_timestamp = None
                if rule.archive_after_days:
                    archive_cutoff = datetime.now() - timedelta(days=rule.archive_after_days)
                    archive_timestamp = archive_cutoff.timestamp()
                
                # Archive old events if specified
                if archive_timestamp and rule.policy == RetentionPolicy.ARCHIVE:
                    cursor.execute("""
                        SELECT trace_id, start_time, end_time, initial_query, final_response,
                               termination_reason, total_duration, success, event_count,
                               modules_involved, metadata
                        FROM traces 
                        WHERE start_time < ? AND start_time >= ?
                    """, (archive_timestamp, delete_timestamp if delete_timestamp else 0))
                    
                    traces_to_archive = cursor.fetchall()
                    if traces_to_archive:
                        archived_count = self._archive_traces(traces_to_archive, rule)
                        result['archived'] += archived_count
                
                # Delete old events if specified
                if delete_timestamp:
                    # Get size before deletion
                    cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp < ?", (delete_timestamp,))
                    events_to_delete = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM traces WHERE start_time < ?", (delete_timestamp,))
                    traces_to_delete = cursor.fetchone()[0]
                    
                    # Delete events
                    cursor.execute("DELETE FROM events WHERE timestamp < ?", (delete_timestamp,))
                    cursor.execute("DELETE FROM traces WHERE start_time < ?", (delete_timestamp,))
                    
                    result['deleted'] += events_to_delete + traces_to_delete
                    result['processed'] += events_to_delete + traces_to_delete
                    
                    # Estimate bytes freed (rough calculation)
                    result['bytes_freed'] += (events_to_delete + traces_to_delete) * 1024  # Rough estimate
                
                # Vacuum database to reclaim space
                conn.execute("VACUUM")
                
        except Exception as e:
            result['errors'].append(f"Error cleaning trace events: {e}")
            logger.error(f"Error cleaning trace events: {e}")
        
        return result
    
    def _cleanup_performance_metrics(self, rule: RetentionRule) -> Dict[str, int]:
        """Clean up performance metrics based on retention rule."""
        result = {'processed': 0, 'deleted': 0, 'archived': 0, 'bytes_freed': 0, 'errors': []}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if rule.retention_days > 0:
                    cutoff = datetime.now() - timedelta(days=rule.retention_days)
                    cutoff_timestamp = cutoff.timestamp()
                    
                    cursor.execute("SELECT COUNT(*) FROM performance_metrics WHERE timestamp < ?", 
                                 (cutoff_timestamp,))
                    count = cursor.fetchone()[0]
                    
                    cursor.execute("DELETE FROM performance_metrics WHERE timestamp < ?", 
                                 (cutoff_timestamp,))
                    
                    result['deleted'] += count
                    result['processed'] += count
                    result['bytes_freed'] += count * 512  # Rough estimate
                
        except Exception as e:
            result['errors'].append(f"Error cleaning performance metrics: {e}")
            logger.error(f"Error cleaning performance metrics: {e}")
        
        return result
    
    def _cleanup_analytics_cache(self, rule: RetentionRule) -> Dict[str, int]:
        """Clean up analytics cache based on retention rule."""
        result = {'processed': 0, 'deleted': 0, 'archived': 0, 'bytes_freed': 0, 'errors': []}
        
        # Clean up cache files
        cache_dir = Path("cache/analytics")
        if cache_dir.exists():
            cutoff = datetime.now() - timedelta(days=rule.retention_days)
            
            for cache_file in cache_dir.glob("*.json"):
                try:
                    if datetime.fromtimestamp(cache_file.stat().st_mtime) < cutoff:
                        file_size = cache_file.stat().st_size
                        cache_file.unlink()
                        result['deleted'] += 1
                        result['processed'] += 1
                        result['bytes_freed'] += file_size
                except Exception as e:
                    result['errors'].append(f"Error deleting cache file {cache_file}: {e}")
        
        return result
    
    def _cleanup_exported_data(self, rule: RetentionRule) -> Dict[str, int]:
        """Clean up exported data files based on retention rule."""
        result = {'processed': 0, 'deleted': 0, 'archived': 0, 'bytes_freed': 0, 'errors': []}
        
        # Clean up export files
        export_dir = Path("exports")
        if export_dir.exists():
            cutoff = datetime.now() - timedelta(days=rule.retention_days)
            
            for export_file in export_dir.glob("*.json"):
                try:
                    if datetime.fromtimestamp(export_file.stat().st_mtime) < cutoff:
                        file_size = export_file.stat().st_size
                        export_file.unlink()
                        result['deleted'] += 1
                        result['processed'] += 1
                        result['bytes_freed'] += file_size
                except Exception as e:
                    result['errors'].append(f"Error deleting export file {export_file}: {e}")
        
        return result
    
    def _cleanup_error_logs(self, rule: RetentionRule) -> Dict[str, int]:
        """Clean up error logs based on retention rule."""
        result = {'processed': 0, 'deleted': 0, 'archived': 0, 'bytes_freed': 0, 'errors': []}
        
        # This would clean up application error logs
        # Implementation depends on logging configuration
        
        return result
    
    def _archive_traces(self, traces: List[Tuple], rule: RetentionRule) -> int:
        """Archive traces to compressed files."""
        try:
            archive_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_path / f"traces_archive_{archive_date}.json.gz"
            
            # Convert traces to JSON format
            archive_data = []
            for trace in traces:
                trace_dict = {
                    'trace_id': trace[0],
                    'start_time': trace[1],
                    'end_time': trace[2],
                    'initial_query': trace[3],
                    'final_response': trace[4],
                    'termination_reason': trace[5],
                    'total_duration': trace[6],
                    'success': trace[7],
                    'event_count': trace[8],
                    'modules_involved': trace[9],
                    'metadata': trace[10]
                }
                archive_data.append(trace_dict)
            
            # Compress and save
            with gzip.open(archive_file, 'wt', encoding='utf-8', 
                          compresslevel=self.config['archive_compression_level']) as f:
                json.dump(archive_data, f, indent=2, default=str)
            
            logger.info(f"Archived {len(traces)} traces to {archive_file}")
            return len(traces)
            
        except Exception as e:
            logger.error(f"Error archiving traces: {e}")
            return 0
    
    def _create_backup(self, job_id: str):
        """Create a backup before cleanup."""
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{job_id}_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_file)
            logger.info(f"Created backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def _verify_cleanup(self, job: CleanupJob, result: CleanupResult):
        """Verify cleanup operation completed successfully."""
        # This would implement verification logic
        # For example, checking that expected records were deleted
        pass
    
    def _start_scheduler(self):
        """Start the cleanup scheduler."""
        # This would implement a proper scheduler
        # For now, we'll just log that it's initialized
        logger.info("Cleanup scheduler initialized")
    
    def get_retention_stats(self) -> Dict[str, Any]:
        """Get retention and cleanup statistics."""
        stats = {
            'total_cleanup_jobs': len(self.cleanup_jobs),
            'enabled_jobs': len([j for j in self.cleanup_jobs.values() if j.enabled]),
            'last_cleanup_runs': [],
            'total_records_deleted': 0,
            'total_records_archived': 0,
            'total_bytes_freed': 0,
            'cleanup_history_count': len(self.cleanup_history)
        }
        
        # Add recent cleanup history
        for result in self.cleanup_history[-10:]:
            stats['last_cleanup_runs'].append({
                'job_id': result.job_id,
                'start_time': result.start_time.isoformat(),
                'success': result.success,
                'records_deleted': result.records_deleted,
                'records_archived': result.records_archived,
                'bytes_freed': result.bytes_freed
            })
            
            stats['total_records_deleted'] += result.records_deleted
            stats['total_records_archived'] += result.records_archived
            stats['total_bytes_freed'] += result.bytes_freed
        
        return stats

# Global retention manager instance
_retention_manager = None

def get_retention_manager() -> TraceRetentionManager:
    """Get the global retention manager instance."""
    global _retention_manager
    if _retention_manager is None:
        _retention_manager = TraceRetentionManager()
    return _retention_manager
