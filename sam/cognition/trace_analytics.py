#!/usr/bin/env python3
"""
SAM Introspection Dashboard - Advanced Analytics Engine
======================================================

This module provides advanced analytics capabilities for trace data including
trend analysis, performance metrics aggregation, and comparative analysis.

Features:
- Performance trend analysis
- Query pattern recognition
- Module efficiency metrics
- Comparative trace analysis
- Anomaly detection
- Optimization recommendations

Author: SAM Development Team
Version: 1.0.0
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TraceAnalytics:
    """
    Advanced analytics engine for SAM trace data.
    
    Provides comprehensive analysis capabilities including performance trends,
    pattern recognition, and optimization recommendations.
    """

    def __init__(self, trace_database=None):
        """Initialize the analytics engine."""
        if trace_database is None:
            from sam.cognition.trace_database import get_trace_database
            trace_database = get_trace_database()
        
        self.db = trace_database
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        logger.info("TraceAnalytics initialized")

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        cache_key = f"performance_trends_{days}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        try:
            # Get traces from the last N days
            start_time = time.time() - (days * 24 * 3600)
            filters = {'start_date': start_time}
            traces = self.db.get_trace_history(limit=10000, filters=filters)
            
            if not traces:
                return {'error': 'No traces found for the specified period'}

            # Group traces by day
            daily_metrics = defaultdict(list)
            for trace in traces:
                if trace['total_duration'] is not None:
                    day = datetime.fromtimestamp(trace['start_time']).strftime('%Y-%m-%d')

                    # Handle modules_involved - could be list or JSON string
                    modules_involved = trace['modules_involved']
                    if isinstance(modules_involved, str):
                        try:
                            modules_list = json.loads(modules_involved or '[]')
                        except json.JSONDecodeError:
                            modules_list = []
                    elif isinstance(modules_involved, list):
                        modules_list = modules_involved
                    else:
                        modules_list = []

                    daily_metrics[day].append({
                        'duration': trace['total_duration'],
                        'event_count': trace['event_count'],
                        'success': trace['success'],
                        'modules': len(modules_list)
                    })

            # Calculate daily aggregates
            trends = {
                'daily_performance': {},
                'overall_stats': {},
                'recommendations': []
            }

            for day, day_traces in daily_metrics.items():
                durations = [t['duration'] for t in day_traces if t['duration']]
                event_counts = [t['event_count'] for t in day_traces]
                success_rate = sum(1 for t in day_traces if t['success']) / len(day_traces) if day_traces else 0
                
                trends['daily_performance'][day] = {
                    'trace_count': len(day_traces),
                    'avg_duration': statistics.mean(durations) if durations else 0,
                    'median_duration': statistics.median(durations) if durations else 0,
                    'max_duration': max(durations) if durations else 0,
                    'min_duration': min(durations) if durations else 0,
                    'avg_events': statistics.mean(event_counts) if event_counts else 0,
                    'success_rate': success_rate
                }

            # Calculate overall statistics
            all_durations = [trace['total_duration'] for trace in traces if trace['total_duration']]
            all_events = [trace['event_count'] for trace in traces]
            overall_success = sum(1 for trace in traces if trace['success']) / len(traces) if traces else 0

            trends['overall_stats'] = {
                'total_traces': len(traces),
                'avg_duration': statistics.mean(all_durations) if all_durations else 0,
                'median_duration': statistics.median(all_durations) if all_durations else 0,
                'avg_events_per_trace': statistics.mean(all_events) if all_events else 0,
                'overall_success_rate': overall_success,
                'period_days': days
            }

            # Generate recommendations
            trends['recommendations'] = self._generate_performance_recommendations(trends)

            self._cache_result(cache_key, trends)
            return trends

        except Exception as e:
            logger.error(f"Failed to analyze performance trends: {e}")
            return {'error': str(e)}

    def get_query_patterns(self, limit: int = 100) -> Dict[str, Any]:
        """Analyze query patterns and categorize common types."""
        cache_key = f"query_patterns_{limit}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        try:
            traces = self.db.get_trace_history(limit=limit)
            
            if not traces:
                return {'error': 'No traces found'}

            patterns = {
                'query_types': defaultdict(int),
                'query_lengths': [],
                'common_keywords': Counter(),
                'performance_by_type': defaultdict(list),
                'success_by_type': defaultdict(list)
            }

            for trace in traces:
                query = trace.get('query', '').lower()
                query_length = len(query)
                patterns['query_lengths'].append(query_length)

                # Categorize query types
                query_type = self._categorize_query(query)
                patterns['query_types'][query_type] += 1

                # Extract keywords
                words = [word.strip('.,!?;:') for word in query.split() if len(word) > 3]
                patterns['common_keywords'].update(words)

                # Performance by type
                if trace['total_duration']:
                    patterns['performance_by_type'][query_type].append(trace['total_duration'])
                
                patterns['success_by_type'][query_type].append(trace['success'])

            # Calculate statistics
            result = {
                'query_type_distribution': dict(patterns['query_types']),
                'query_length_stats': {
                    'avg_length': statistics.mean(patterns['query_lengths']) if patterns['query_lengths'] else 0,
                    'median_length': statistics.median(patterns['query_lengths']) if patterns['query_lengths'] else 0,
                    'max_length': max(patterns['query_lengths']) if patterns['query_lengths'] else 0,
                    'min_length': min(patterns['query_lengths']) if patterns['query_lengths'] else 0
                },
                'top_keywords': patterns['common_keywords'].most_common(20),
                'performance_by_query_type': {},
                'success_rate_by_type': {}
            }

            # Performance by query type
            for query_type, durations in patterns['performance_by_type'].items():
                if durations:
                    result['performance_by_query_type'][query_type] = {
                        'avg_duration': statistics.mean(durations),
                        'median_duration': statistics.median(durations),
                        'count': len(durations)
                    }

            # Success rate by query type
            for query_type, successes in patterns['success_by_type'].items():
                if successes:
                    success_rate = sum(1 for s in successes if s) / len(successes)
                    result['success_rate_by_type'][query_type] = {
                        'success_rate': success_rate,
                        'count': len(successes)
                    }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to analyze query patterns: {e}")
            return {'error': str(e)}

    def get_module_efficiency(self, days: int = 7) -> Dict[str, Any]:
        """Analyze module efficiency and performance."""
        cache_key = f"module_efficiency_{days}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        try:
            start_time = time.time() - (days * 24 * 3600)
            filters = {'start_date': start_time}
            traces = self.db.get_trace_history(limit=5000, filters=filters)

            module_stats = defaultdict(lambda: {
                'usage_count': 0,
                'total_duration': 0,
                'success_count': 0,
                'error_count': 0,
                'avg_events': 0
            })

            for trace in traces:
                # Handle modules_involved - could be list or JSON string
                modules_involved = trace['modules_involved']
                if isinstance(modules_involved, str):
                    try:
                        modules = json.loads(modules_involved or '[]')
                    except json.JSONDecodeError:
                        modules = []
                elif isinstance(modules_involved, list):
                    modules = modules_involved
                else:
                    modules = []

                duration = trace['total_duration'] or 0
                success = trace['success']

                for module in modules:
                    stats = module_stats[module]
                    stats['usage_count'] += 1
                    stats['total_duration'] += duration
                    if success:
                        stats['success_count'] += 1
                    else:
                        stats['error_count'] += 1

            # Calculate efficiency metrics
            efficiency_report = {}
            for module, stats in module_stats.items():
                if stats['usage_count'] > 0:
                    efficiency_report[module] = {
                        'usage_count': stats['usage_count'],
                        'avg_duration': stats['total_duration'] / stats['usage_count'],
                        'success_rate': stats['success_count'] / stats['usage_count'],
                        'error_rate': stats['error_count'] / stats['usage_count'],
                        'efficiency_score': self._calculate_efficiency_score(stats)
                    }

            # Sort by efficiency score
            sorted_modules = sorted(
                efficiency_report.items(),
                key=lambda x: x[1]['efficiency_score'],
                reverse=True
            )

            result = {
                'module_efficiency': dict(sorted_modules),
                'top_performers': sorted_modules[:5],
                'needs_attention': [m for m in sorted_modules if m[1]['efficiency_score'] < 0.7][-5:],
                'total_modules_analyzed': len(efficiency_report),
                'analysis_period_days': days
            }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to analyze module efficiency: {e}")
            return {'error': str(e)}

    def compare_traces(self, trace_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple traces for analysis."""
        try:
            if len(trace_ids) < 2:
                return {'error': 'At least 2 traces required for comparison'}

            comparison = {
                'traces': {},
                'similarities': {},
                'differences': {},
                'recommendations': []
            }

            for trace_id in trace_ids:
                # Get trace summary from database
                traces = self.db.get_trace_history(limit=1, filters={'trace_id': trace_id})
                if traces:
                    trace = traces[0]
                    events = self.db.get_trace_events_from_db(trace_id)
                    
                    # Handle modules_involved - could be list or JSON string
                    modules_involved = trace['modules_involved']
                    if isinstance(modules_involved, str):
                        try:
                            modules = json.loads(modules_involved or '[]')
                        except json.JSONDecodeError:
                            modules = []
                    elif isinstance(modules_involved, list):
                        modules = modules_involved
                    else:
                        modules = []

                    comparison['traces'][trace_id] = {
                        'summary': trace,
                        'event_count': len(events),
                        'event_types': Counter(e['event_type'] for e in events),
                        'modules': modules,
                        'performance': {
                            'duration': trace['total_duration'],
                            'success': trace['success'],
                            'events_per_second': len(events) / trace['total_duration'] if trace['total_duration'] else 0
                        }
                    }

            # Analyze similarities and differences
            if len(comparison['traces']) >= 2:
                comparison['similarities'] = self._find_trace_similarities(comparison['traces'])
                comparison['differences'] = self._find_trace_differences(comparison['traces'])
                comparison['recommendations'] = self._generate_comparison_recommendations(comparison)

            return comparison

        except Exception as e:
            logger.error(f"Error comparing traces: {e}")
            return {'error': str(e)}

    def generate_flow_diagram(self, trace_id: str) -> Dict[str, Any]:
        """
        Generate flow diagram data for visualization.

        Args:
            trace_id: Trace identifier

        Returns:
            Flow diagram data with nodes and edges
        """
        try:
            # Get trace events
            trace_events = self.db.get_trace_events_from_db(trace_id)
            if not trace_events:
                return {"nodes": [], "edges": [], "error": "No events found"}

            nodes = []
            edges = []
            node_id_counter = 0

            # Create nodes for each event
            for event in trace_events:
                node_id = f"node_{node_id_counter}"
                node_id_counter += 1

                # Determine node type and color
                event_type = event.get('event_type', 'unknown')
                source_module = event.get('source_module', 'Unknown')

                node_color = self._get_node_color(event_type, event.get('severity', 'info'))
                node_shape = self._get_node_shape(event_type)

                node = {
                    "id": node_id,
                    "label": f"{source_module}\n{event_type}",
                    "title": event.get('message', ''),
                    "color": node_color,
                    "shape": node_shape,
                    "size": 20 + ((event.get('duration_ms') or 0) / 10),  # Size based on duration
                    "event_data": {
                        "timestamp": event.get('timestamp'),
                        "duration_ms": event.get('duration_ms'),
                        "severity": event.get('severity'),
                        "payload": event.get('payload', {})
                    }
                }
                nodes.append(node)

                # Create edges between sequential events
                if len(nodes) > 1:
                    edge = {
                        "from": f"node_{node_id_counter - 2}",
                        "to": node_id,
                        "arrows": "to",
                        "color": {"color": "#848484"},
                        "width": 2
                    }
                    edges.append(edge)

            # Add decision branches and tool calls
            self._add_decision_branches(nodes, edges, trace_events)

            return {
                "nodes": nodes,
                "edges": edges,
                "layout": {
                    "hierarchical": {
                        "enabled": True,
                        "direction": "UD",
                        "sortMethod": "directed"
                    }
                },
                "physics": {
                    "enabled": False
                },
                "metadata": {
                    "trace_id": trace_id,
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "generated_at": time.time()
                }
            }

        except Exception as e:
            logger.error(f"Error generating flow diagram for {trace_id}: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def _get_node_color(self, event_type: str, severity: str) -> str:
        """Get node color based on event type and severity."""
        if severity == 'error':
            return "#ff4444"
        elif severity == 'warning':
            return "#ffaa00"
        elif event_type == 'start':
            return "#44ff44"
        elif event_type == 'end':
            return "#4444ff"
        elif event_type == 'tool_call':
            return "#ff44ff"
        elif event_type == 'decision':
            return "#ffff44"
        else:
            return "#888888"

    def _get_node_shape(self, event_type: str) -> str:
        """Get node shape based on event type."""
        if event_type == 'start':
            return "circle"
        elif event_type == 'end':
            return "circle"
        elif event_type == 'tool_call':
            return "box"
        elif event_type == 'decision':
            return "diamond"
        elif event_type == 'error':
            return "triangle"
        else:
            return "ellipse"

    def _add_decision_branches(self, nodes: List[Dict], edges: List[Dict], events: List[Dict]) -> None:
        """Add decision branches and parallel tool execution paths."""
        # Group events by parent_event_id to identify branches
        event_groups = {}
        for i, event in enumerate(events):
            parent_id = event.get('parent_event_id')
            if parent_id:
                if parent_id not in event_groups:
                    event_groups[parent_id] = []
                event_groups[parent_id].append(i)

        # Add branch edges for grouped events
        for parent_id, child_indices in event_groups.items():
            if len(child_indices) > 1:
                # Multiple children indicate branching
                for child_idx in child_indices:
                    # Find parent node and add colored edge
                    parent_node_id = f"node_{child_idx - 1}"  # Simplified parent finding
                    child_node_id = f"node_{child_idx}"

                    edge = {
                        "from": parent_node_id,
                        "to": child_node_id,
                        "arrows": "to",
                        "color": {"color": "#ff8800"},
                        "width": 3,
                        "dashes": True
                    }
                    edges.append(edge)

    def generate_hierarchy_view(self, trace_id: str) -> Dict[str, Any]:
        """
        Generate hierarchical view of trace events with parent-child relationships.

        Args:
            trace_id: Trace identifier

        Returns:
            Hierarchical tree structure of events
        """
        try:
            # Get trace events
            trace_events = self.db.get_trace_events_from_db(trace_id)
            if not trace_events:
                return {"tree": [], "error": "No events found"}

            # Build hierarchy tree
            event_map = {}
            root_events = []

            # First pass: create event nodes
            for event in trace_events:
                event_id = event.get('event_id', str(event.get('timestamp', '')))
                event_node = {
                    "id": event_id,
                    "label": f"{event.get('source_module', 'Unknown')} - {event.get('event_type', 'unknown')}",
                    "message": event.get('message', ''),
                    "timestamp": event.get('timestamp'),
                    "duration_ms": event.get('duration_ms'),
                    "severity": event.get('severity', 'info'),
                    "payload": event.get('payload', {}),
                    "children": [],
                    "expanded": True,
                    "icon": self._get_event_icon(event.get('event_type', 'unknown')),
                    "color": self._get_severity_color(event.get('severity', 'info'))
                }
                event_map[event_id] = event_node

            # Second pass: build parent-child relationships
            for event in trace_events:
                event_id = event.get('event_id', str(event.get('timestamp', '')))
                parent_id = event.get('parent_event_id')

                if parent_id and parent_id in event_map:
                    # Add as child to parent
                    event_map[parent_id]['children'].append(event_map[event_id])
                else:
                    # Root level event
                    root_events.append(event_map[event_id])

            # Calculate tree statistics
            total_events = len(trace_events)
            max_depth = self._calculate_tree_depth(root_events)
            modules_involved = len(set(event.get('source_module', 'Unknown') for event in trace_events))

            return {
                "tree": root_events,
                "statistics": {
                    "total_events": total_events,
                    "max_depth": max_depth,
                    "modules_involved": modules_involved,
                    "root_events": len(root_events)
                },
                "metadata": {
                    "trace_id": trace_id,
                    "generated_at": time.time()
                }
            }

        except Exception as e:
            logger.error(f"Error generating hierarchy view for {trace_id}: {e}")
            return {"tree": [], "error": str(e)}

    def _get_event_icon(self, event_type: str) -> str:
        """Get icon for event type."""
        icons = {
            'start': '🚀',
            'end': '🏁',
            'tool_call': '🔧',
            'decision': '🤔',
            'data_in': '📥',
            'data_out': '📤',
            'error': '❌',
            'warning': '⚠️'
        }
        return icons.get(event_type, '📋')

    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            'debug': '#888888',
            'info': '#0066cc',
            'warning': '#ff8800',
            'error': '#cc0000',
            'critical': '#990000'
        }
        return colors.get(severity, '#888888')

    def _calculate_tree_depth(self, nodes: List[Dict], current_depth: int = 0) -> int:
        """Calculate maximum depth of tree structure."""
        if not nodes:
            return current_depth

        max_depth = current_depth
        for node in nodes:
            children = node.get('children', [])
            if children:
                depth = self._calculate_tree_depth(children, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    def get_performance_baseline(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance baseline metrics for comparison.

        Args:
            days: Number of days to analyze

        Returns:
            Performance baseline data
        """
        try:
            end_time = time.time()
            start_time = end_time - (days * 24 * 60 * 60)

            # Get traces from the specified period
            traces = self.db.get_traces_by_date_range(start_time, end_time)

            if not traces:
                return {
                    "baseline": {},
                    "message": "No traces found in the specified period"
                }

            # Calculate baseline metrics
            durations = [trace.get('total_duration', 0) for trace in traces if trace.get('total_duration')]
            success_rates = [1 if trace.get('success') else 0 for trace in traces]
            event_counts = [trace.get('event_count', 0) for trace in traces]

            baseline = {
                "performance_metrics": {
                    "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                    "median_duration_ms": sorted(durations)[len(durations)//2] if durations else 0,
                    "p95_duration_ms": sorted(durations)[int(len(durations)*0.95)] if durations else 0,
                    "success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
                    "avg_events_per_trace": sum(event_counts) / len(event_counts) if event_counts else 0
                },
                "volume_metrics": {
                    "total_traces": len(traces),
                    "traces_per_day": len(traces) / days,
                    "successful_traces": sum(success_rates),
                    "failed_traces": len(traces) - sum(success_rates)
                },
                "period_info": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "days_analyzed": days
                }
            }

            return {"baseline": baseline}

        except Exception as e:
            logger.error(f"Error getting performance baseline: {e}")
            return {"baseline": {}, "error": str(e)}

    def replay_trace(self, trace_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replay a trace with the same parameters for debugging.

        Args:
            trace_id: Original trace identifier
            options: Replay options and modifications

        Returns:
            Replay result with new trace_id
        """
        try:
            # Get original trace
            traces = self.db.get_trace_history(limit=1, filters={'trace_id': trace_id})
            if not traces:
                return {"error": "Original trace not found"}

            original_trace = traces[0]
            original_query = original_trace.get('initial_query', '')

            # For now, return replay simulation data
            # In a full implementation, this would trigger actual query re-execution
            replay_result = {
                "original_trace_id": trace_id,
                "replay_trace_id": f"replay_{trace_id}_{int(time.time())}",
                "original_query": original_query,
                "replay_options": options,
                "status": "simulated",
                "message": "Trace replay simulation - full implementation would re-execute query",
                "comparison": {
                    "original_duration": original_trace.get('total_duration', 0),
                    "original_success": original_trace.get('success', False),
                    "original_events": original_trace.get('event_count', 0)
                }
            }

            return replay_result

        except Exception as e:
            logger.error(f"Error replaying trace {trace_id}: {e}")
            return {"error": str(e)}

    def advanced_trace_comparison(self, trace_ids: List[str], comparison_type: str = 'performance') -> Dict[str, Any]:
        """
        Advanced comparison of multiple traces with detailed analysis.

        Args:
            trace_ids: List of trace identifiers
            comparison_type: Type of comparison (performance, flow, tools)

        Returns:
            Advanced comparison results
        """
        try:
            comparison_result = {
                "comparison_type": comparison_type,
                "trace_ids": trace_ids,
                "traces": {},
                "analysis": {}
            }

            # Get trace data for each trace
            for trace_id in trace_ids:
                traces = self.db.get_trace_history(limit=1, filters={'trace_id': trace_id})
                if traces:
                    trace = traces[0]
                    events = self.db.get_trace_events_from_db(trace_id)

                    comparison_result["traces"][trace_id] = {
                        "summary": trace,
                        "events": events,
                        "event_count": len(events),
                        "modules": list(set(event.get('source_module', 'Unknown') for event in events))
                    }

            # Perform comparison analysis based on type
            if comparison_type == 'performance':
                comparison_result["analysis"] = self._analyze_performance_differences(comparison_result["traces"])
            elif comparison_type == 'flow':
                comparison_result["analysis"] = self._analyze_flow_differences(comparison_result["traces"])
            elif comparison_type == 'tools':
                comparison_result["analysis"] = self._analyze_tool_differences(comparison_result["traces"])
            else:
                comparison_result["analysis"] = self._analyze_general_differences(comparison_result["traces"])

            return comparison_result

        except Exception as e:
            logger.error(f"Error in advanced trace comparison: {e}")
            return {"error": str(e)}

    def _analyze_performance_differences(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance differences between traces."""
        analysis = {
            "duration_comparison": {},
            "efficiency_metrics": {},
            "bottleneck_analysis": {}
        }

        for trace_id, trace_data in traces.items():
            summary = trace_data["summary"]
            events = trace_data["events"]

            # Duration analysis
            total_duration = summary.get('total_duration', 0)
            event_durations = [event.get('duration_ms', 0) for event in events if event.get('duration_ms')]

            analysis["duration_comparison"][trace_id] = {
                "total_duration": total_duration,
                "avg_event_duration": sum(event_durations) / len(event_durations) if event_durations else 0,
                "max_event_duration": max(event_durations) if event_durations else 0,
                "events_with_duration": len(event_durations)
            }

        return analysis

    def _analyze_flow_differences(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze flow differences between traces."""
        analysis = {
            "execution_paths": {},
            "decision_points": {},
            "module_sequences": {}
        }

        for trace_id, trace_data in traces.items():
            events = trace_data["events"]

            # Execution path analysis
            event_sequence = [f"{event.get('source_module', 'Unknown')}.{event.get('event_type', 'unknown')}" for event in events]
            decision_events = [event for event in events if event.get('event_type') == 'decision']

            analysis["execution_paths"][trace_id] = {
                "sequence": event_sequence,
                "unique_steps": len(set(event_sequence)),
                "total_steps": len(event_sequence)
            }

            analysis["decision_points"][trace_id] = {
                "count": len(decision_events),
                "decisions": [event.get('message', '') for event in decision_events]
            }

        return analysis

    def _analyze_tool_differences(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool usage differences between traces."""
        analysis = {
            "tool_usage": {},
            "tool_performance": {},
            "tool_selection": {}
        }

        for trace_id, trace_data in traces.items():
            events = trace_data["events"]

            # Tool usage analysis
            tool_events = [event for event in events if event.get('event_type') == 'tool_call']
            tools_used = [event.get('source_module', 'Unknown') for event in tool_events]

            analysis["tool_usage"][trace_id] = {
                "tools_used": list(set(tools_used)),
                "tool_calls": len(tool_events),
                "tool_distribution": {tool: tools_used.count(tool) for tool in set(tools_used)}
            }

        return analysis

    def _analyze_general_differences(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general differences between traces."""
        analysis = {
            "summary_comparison": {},
            "event_distribution": {},
            "success_analysis": {}
        }

        for trace_id, trace_data in traces.items():
            summary = trace_data["summary"]
            events = trace_data["events"]

            # Event type distribution
            event_types = [event.get('event_type', 'unknown') for event in events]
            event_distribution = {event_type: event_types.count(event_type) for event_type in set(event_types)}

            analysis["summary_comparison"][trace_id] = {
                "success": summary.get('success', False),
                "duration": summary.get('total_duration', 0),
                "event_count": len(events),
                "modules_count": len(trace_data["modules"])
            }

            analysis["event_distribution"][trace_id] = event_distribution

        return analysis

    def detect_anomalies(self, days: int = 7) -> Dict[str, Any]:
        """Detect performance anomalies and unusual patterns."""
        try:
            start_time = time.time() - (days * 24 * 3600)
            filters = {'start_date': start_time}
            traces = self.db.get_trace_history(limit=5000, filters=filters)

            if len(traces) < 10:
                return {'error': 'Insufficient data for anomaly detection'}

            anomalies = {
                'performance_outliers': [],
                'unusual_patterns': [],
                'error_spikes': [],
                'recommendations': []
            }

            # Calculate baseline metrics
            durations = [t['total_duration'] for t in traces if t['total_duration']]
            event_counts = [t['event_count'] for t in traces]
            
            if durations:
                avg_duration = statistics.mean(durations)
                duration_stdev = statistics.stdev(durations) if len(durations) > 1 else 0
                
                # Find performance outliers (> 2 standard deviations)
                threshold = avg_duration + (2 * duration_stdev)
                for trace in traces:
                    if trace['total_duration'] and trace['total_duration'] > threshold:
                        anomalies['performance_outliers'].append({
                            'trace_id': trace['trace_id'],
                            'duration': trace['total_duration'],
                            'query': trace['query'][:100],
                            'deviation': (trace['total_duration'] - avg_duration) / duration_stdev if duration_stdev else 0
                        })

            # Detect error spikes
            error_traces = [t for t in traces if not t['success']]
            if len(error_traces) / len(traces) > 0.1:  # More than 10% errors
                anomalies['error_spikes'].append({
                    'error_rate': len(error_traces) / len(traces),
                    'error_count': len(error_traces),
                    'total_traces': len(traces),
                    'period': f"Last {days} days"
                })

            # Generate recommendations
            anomalies['recommendations'] = self._generate_anomaly_recommendations(anomalies)

            return anomalies

        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return {'error': str(e)}

    def _categorize_query(self, query: str) -> str:
        """Categorize a query based on its content."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['calculate', 'math', '+', '-', '*', '/', 'sum', 'multiply']):
            return 'mathematical'
        elif any(word in query_lower for word in ['search', 'find', 'latest', 'news', 'current']):
            return 'search'
        elif any(word in query_lower for word in ['analyze', 'compare', 'evaluate', 'assess']):
            return 'analytical'
        elif any(word in query_lower for word in ['explain', 'what', 'how', 'why', 'define']):
            return 'informational'
        elif any(word in query_lower for word in ['create', 'generate', 'write', 'make']):
            return 'creative'
        else:
            return 'general'

    def _calculate_efficiency_score(self, stats: Dict[str, Any]) -> float:
        """Calculate an efficiency score for a module."""
        success_rate = stats['success_count'] / stats['usage_count'] if stats['usage_count'] else 0
        avg_duration = stats['total_duration'] / stats['usage_count'] if stats['usage_count'] else 0
        
        # Normalize duration (lower is better, assume 10s is baseline)
        duration_score = max(0, 1 - (avg_duration / 10.0))
        
        # Combine success rate and duration score
        efficiency_score = (success_rate * 0.7) + (duration_score * 0.3)
        return min(1.0, max(0.0, efficiency_score))

    def _generate_performance_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        overall = trends.get('overall_stats', {})
        avg_duration = overall.get('avg_duration', 0)
        success_rate = overall.get('overall_success_rate', 1)
        
        if avg_duration > 5.0:
            recommendations.append("Consider optimizing response generation - average duration is high")
        
        if success_rate < 0.9:
            recommendations.append("Investigate error patterns - success rate is below optimal")
        
        if overall.get('avg_events_per_trace', 0) > 50:
            recommendations.append("High event count per trace - consider reducing logging verbosity")
        
        return recommendations

    def _find_trace_similarities(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Find similarities between traces."""
        similarities = {}
        
        # Compare modules used
        all_modules = [set(trace['modules']) for trace in traces.values()]
        if len(all_modules) >= 2:
            common_modules = set.intersection(*all_modules)
            similarities['common_modules'] = list(common_modules)
        
        return similarities

    def _find_trace_differences(self, traces: Dict[str, Any]) -> Dict[str, Any]:
        """Find differences between traces."""
        differences = {}
        
        durations = [trace['performance']['duration'] for trace in traces.values() if trace['performance']['duration']]
        if durations:
            differences['duration_variance'] = max(durations) - min(durations)
        
        return differences

    def _generate_comparison_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on trace comparison."""
        recommendations = []
        
        if 'duration_variance' in comparison.get('differences', {}):
            variance = comparison['differences']['duration_variance']
            if variance > 2.0:
                recommendations.append("Significant performance variance detected - investigate slower traces")
        
        return recommendations

    def _generate_anomaly_recommendations(self, anomalies: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on anomaly detection."""
        recommendations = []
        
        if anomalies['performance_outliers']:
            recommendations.append("Performance outliers detected - review slow queries for optimization")
        
        if anomalies['error_spikes']:
            recommendations.append("Error rate spike detected - investigate recent failures")
        
        return recommendations

    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid."""
        if key in self._cache:
            cached_time, _ = self._cache[key]
            return time.time() - cached_time < self._cache_ttl
        return False

    def _get_cached(self, key: str) -> Any:
        """Get cached result."""
        if key in self._cache:
            _, result = self._cache[key]
            return result
        return None

    def _cache_result(self, key: str, result: Any):
        """Cache a result with timestamp."""
        self._cache[key] = (time.time(), result)

# Global analytics instance
_trace_analytics = None

def get_trace_analytics():
    """Get the global trace analytics instance."""
    global _trace_analytics
    if _trace_analytics is None:
        _trace_analytics = TraceAnalytics()
    return _trace_analytics
