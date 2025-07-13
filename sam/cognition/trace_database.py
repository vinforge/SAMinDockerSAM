#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Database Persistence Layer
=======================================================

This module provides database persistence for trace data with efficient
indexing, query optimization, and historical trace management.

Features:
- SQLite database with optimized schema
- Efficient indexing for fast queries
- Batch operations for performance
- Data retention and archival
- Migration support for schema updates

Author: SAM Development Team
Version: 1.0.0
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TraceDatabase:
    """
    Database persistence layer for SAM trace data.
    
    Provides efficient storage, retrieval, and management of trace events
    with support for historical analysis and performance optimization.
    """

    def __init__(self, db_path: str = "data/trace_history.db"):
        """Initialize the trace database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection_pool = {}
        
        # Initialize database schema
        self._init_database()
        logger.info(f"TraceDatabase initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        thread_id = threading.get_ident()
        
        if thread_id not in self._connection_pool:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and performance
            conn.execute("PRAGMA cache_size=10000")  # Increase cache size
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp storage
            self._connection_pool[thread_id] = conn
        
        return self._connection_pool[thread_id]

    def _init_database(self):
        """Initialize database schema with optimized indexes."""
        with self._lock:
            conn = self._get_connection()
            
            # Create traces table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    status TEXT NOT NULL DEFAULT 'active',
                    total_duration REAL,
                    event_count INTEGER DEFAULT 0,
                    modules_involved TEXT,  -- JSON array
                    success BOOLEAN,
                    final_response_length INTEGER,
                    created_at REAL NOT NULL DEFAULT (julianday('now')),
                    metadata TEXT  -- JSON object
                )
            """)
            
            # Create events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    source_module TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    duration_ms REAL,
                    parent_event_id TEXT,
                    payload TEXT,  -- JSON object
                    metadata TEXT,  -- JSON object
                    sequence_number INTEGER,
                    created_at REAL NOT NULL DEFAULT (julianday('now')),
                    FOREIGN KEY (trace_id) REFERENCES traces (trace_id) ON DELETE CASCADE
                )
            """)
            
            # Create performance metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    timestamp REAL NOT NULL,
                    source_module TEXT,
                    metadata TEXT,  -- JSON object
                    FOREIGN KEY (trace_id) REFERENCES traces (trace_id) ON DELETE CASCADE
                )
            """)
            
            # Create analytics cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_data TEXT NOT NULL,  -- JSON object
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            
            # Create optimized indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces (start_time)",
                "CREATE INDEX IF NOT EXISTS idx_traces_status ON traces (status)",
                "CREATE INDEX IF NOT EXISTS idx_traces_user_id ON traces (user_id)",
                "CREATE INDEX IF NOT EXISTS idx_traces_session_id ON traces (session_id)",
                "CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events (trace_id)",
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_events_source_module ON events (source_module)",
                "CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type)",
                "CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity)",
                "CREATE INDEX IF NOT EXISTS idx_performance_trace_id ON performance_metrics (trace_id)",
                "CREATE INDEX IF NOT EXISTS idx_performance_metric_name ON performance_metrics (metric_name)",
                "CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics (timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_expires ON analytics_cache (expires_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            logger.info("Database schema initialized with optimized indexes")

    def store_trace(self, trace_summary: Dict[str, Any]) -> bool:
        """Store a complete trace in the database."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                # Prepare trace data
                trace_data = (
                    trace_summary['trace_id'],
                    trace_summary.get('query', ''),
                    trace_summary.get('user_id'),
                    trace_summary.get('session_id'),
                    trace_summary.get('start_time', time.time()),
                    trace_summary.get('end_time'),
                    trace_summary.get('status', 'completed'),
                    trace_summary.get('total_duration'),
                    trace_summary.get('event_count', 0),
                    json.dumps(trace_summary.get('modules_involved', [])),
                    trace_summary.get('success'),
                    trace_summary.get('final_response_length'),
                    time.time(),
                    json.dumps(trace_summary.get('metadata', {}))
                )
                
                # Insert trace
                conn.execute("""
                    INSERT OR REPLACE INTO traces 
                    (trace_id, query, user_id, session_id, start_time, end_time, status, 
                     total_duration, event_count, modules_involved, success, 
                     final_response_length, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, trace_data)
                
                conn.commit()
                logger.debug(f"Stored trace: {trace_summary['trace_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store trace: {e}")
            return False

    def store_events(self, trace_id: str, events: List[Dict[str, Any]]) -> bool:
        """Store trace events in batch for performance."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                # Prepare event data
                event_data = []
                for i, event in enumerate(events):
                    event_tuple = (
                        event.get('event_id'),
                        trace_id,
                        self._parse_timestamp(event.get('timestamp')),
                        event.get('source_module', ''),
                        event.get('event_type', ''),
                        event.get('severity', ''),
                        event.get('message', ''),
                        event.get('duration_ms'),
                        event.get('parent_event_id'),
                        json.dumps(event.get('payload', {})),
                        json.dumps(event.get('metadata', {})),
                        i,  # sequence_number
                        time.time()
                    )
                    event_data.append(event_tuple)
                
                # Batch insert events
                conn.executemany("""
                    INSERT OR REPLACE INTO events 
                    (event_id, trace_id, timestamp, source_module, event_type, severity, 
                     message, duration_ms, parent_event_id, payload, metadata, 
                     sequence_number, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, event_data)
                
                conn.commit()
                logger.debug(f"Stored {len(events)} events for trace: {trace_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store events: {e}")
            return False

    def get_trace_history(self, limit: int = 100, offset: int = 0, 
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get historical traces with filtering and pagination."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                # Build query with filters
                where_clauses = []
                params = []
                
                if filters:
                    if 'start_date' in filters:
                        where_clauses.append("start_time >= ?")
                        params.append(self._parse_timestamp(filters['start_date']))
                    
                    if 'end_date' in filters:
                        where_clauses.append("start_time <= ?")
                        params.append(self._parse_timestamp(filters['end_date']))
                    
                    if 'user_id' in filters:
                        where_clauses.append("user_id = ?")
                        params.append(filters['user_id'])
                    
                    if 'status' in filters:
                        where_clauses.append("status = ?")
                        params.append(filters['status'])
                    
                    if 'success' in filters:
                        where_clauses.append("success = ?")
                        params.append(filters['success'])
                    
                    if 'query_contains' in filters:
                        where_clauses.append("query LIKE ?")
                        params.append(f"%{filters['query_contains']}%")
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                # Add pagination
                params.extend([limit, offset])
                
                query = f"""
                    SELECT * FROM traces 
                    {where_sql}
                    ORDER BY start_time DESC 
                    LIMIT ? OFFSET ?
                """
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dictionaries and parse JSON fields
                traces = []
                for row in rows:
                    trace = dict(row)
                    trace['modules_involved'] = json.loads(trace['modules_involved'] or '[]')
                    trace['metadata'] = json.loads(trace['metadata'] or '{}')
                    traces.append(trace)
                
                return traces
                
        except Exception as e:
            logger.error(f"Failed to get trace history: {e}")
            return []

    def get_trace_events_from_db(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific trace from database."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                cursor = conn.execute("""
                    SELECT * FROM events 
                    WHERE trace_id = ? 
                    ORDER BY sequence_number ASC
                """, (trace_id,))
                
                rows = cursor.fetchall()
                
                # Convert to dictionaries and parse JSON fields
                events = []
                for row in rows:
                    event = dict(row)
                    event['payload'] = json.loads(event['payload'] or '{}')
                    event['metadata'] = json.loads(event['metadata'] or '{}')
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get trace events: {e}")
            return []

    def _parse_timestamp(self, timestamp: Any) -> float:
        """Parse various timestamp formats to float."""
        if isinstance(timestamp, (int, float)):
            return float(timestamp)
        elif isinstance(timestamp, str):
            try:
                # Try ISO format first
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.timestamp()
            except:
                # Try as float string
                return float(timestamp)
        elif isinstance(timestamp, datetime):
            return timestamp.timestamp()
        else:
            return time.time()

    def cleanup_old_traces(self, max_age_days: int = 30) -> int:
        """Clean up traces older than specified days."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                cutoff_time = time.time() - (max_age_days * 24 * 3600)
                
                # Count traces to be deleted
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM traces WHERE start_time < ?", 
                    (cutoff_time,)
                )
                count = cursor.fetchone()[0]
                
                # Delete old traces (events will be deleted by CASCADE)
                conn.execute(
                    "DELETE FROM traces WHERE start_time < ?", 
                    (cutoff_time,)
                )
                
                # Clean up analytics cache
                conn.execute(
                    "DELETE FROM analytics_cache WHERE expires_at < ?", 
                    (time.time(),)
                )
                
                conn.commit()
                logger.info(f"Cleaned up {count} old traces (older than {max_age_days} days)")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old traces: {e}")
            return 0

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._lock:
                conn = self._get_connection()
                
                stats = {}
                
                # Count traces
                cursor = conn.execute("SELECT COUNT(*) FROM traces")
                stats['total_traces'] = cursor.fetchone()[0]
                
                # Count events
                cursor = conn.execute("SELECT COUNT(*) FROM events")
                stats['total_events'] = cursor.fetchone()[0]
                
                # Count performance metrics
                cursor = conn.execute("SELECT COUNT(*) FROM performance_metrics")
                stats['total_metrics'] = cursor.fetchone()[0]
                
                # Database size
                stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
                
                # Date range
                cursor = conn.execute("SELECT MIN(start_time), MAX(start_time) FROM traces")
                min_time, max_time = cursor.fetchone()
                if min_time and max_time:
                    stats['date_range'] = {
                        'earliest': datetime.fromtimestamp(min_time).isoformat(),
                        'latest': datetime.fromtimestamp(max_time).isoformat()
                    }
                
                return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def get_traces_by_date_range(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        Get traces within a specific date range.

        Args:
            start_time: Start timestamp (Unix time)
            end_time: End timestamp (Unix time)

        Returns:
            List of traces within the date range
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT trace_id, start_time, end_time, initial_query, final_response,
                           termination_reason, total_duration, success, event_count,
                           modules_involved, metadata
                    FROM traces
                    WHERE start_time >= ? AND start_time <= ?
                    ORDER BY start_time DESC
                """, (start_time, end_time))

                rows = cursor.fetchall()
                traces = []

                for row in rows:
                    trace = {
                        'trace_id': row[0],
                        'start_time': row[1],
                        'end_time': row[2],
                        'initial_query': row[3],
                        'final_response': row[4],
                        'termination_reason': row[5],
                        'total_duration': row[6],
                        'success': bool(row[7]),
                        'event_count': row[8],
                        'modules_involved': row[9],
                        'metadata': json.loads(row[10]) if row[10] else {},
                        'query': row[3]  # Alias for compatibility
                    }
                    traces.append(trace)

                return traces

        except Exception as e:
            logger.error(f"Error getting traces by date range: {e}")
            return []

    def close(self):
        """Close all database connections."""
        with self._lock:
            for conn in self._connection_pool.values():
                conn.close()
            self._connection_pool.clear()
            logger.info("Database connections closed")

# Global database instance
_trace_database = None
_database_lock = threading.Lock()

def get_trace_database() -> TraceDatabase:
    """Get the global trace database instance."""
    global _trace_database
    
    if _trace_database is None:
        with _database_lock:
            if _trace_database is None:
                _trace_database = TraceDatabase()
    
    return _trace_database
