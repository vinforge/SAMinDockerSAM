"""
Proactive Suggestion Engine for SAM
===================================

Advanced cognitive system that analyzes user behavior patterns, identifies
repetitive workflows, and proactively suggests procedure creation or optimization.

Features:
- Behavioral pattern analysis
- Workflow repetition detection
- Intelligent procedure suggestions
- Optimization recommendations
- Integration with SAM's cognitive architecture

Author: SAM Development Team
Version: 2.0.0 (Phase 3 - Advanced Cognitive Features)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class UserAction:
    """Represents a single user action for pattern analysis."""
    timestamp: datetime
    action_type: str  # "query", "procedure_execution", "document_access", etc.
    content: str
    context: Dict[str, Any]
    session_id: str

@dataclass
class WorkflowPattern:
    """Represents a detected workflow pattern."""
    pattern_id: str
    name: str
    description: str
    actions: List[str]
    frequency: int
    confidence: float
    suggested_procedure_name: str
    estimated_time_savings: str
    last_detected: datetime

@dataclass
class ProactiveSuggestion:
    """Represents a proactive suggestion for the user."""
    suggestion_id: str
    type: str  # "create_procedure", "optimize_procedure", "workflow_automation"
    title: str
    description: str
    rationale: str
    confidence: float
    potential_benefit: str
    suggested_actions: List[str]
    created_at: datetime
    priority: int  # 1-5, 5 being highest

class ProactiveSuggestionEngine:
    """Advanced engine for analyzing behavior and generating proactive suggestions."""
    
    def __init__(self, storage_path: str = "sam/data/proactive_suggestions.json"):
        """Initialize the proactive suggestion engine."""
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Data storage
        self.user_actions: List[UserAction] = []
        self.detected_patterns: List[WorkflowPattern] = []
        self.active_suggestions: List[ProactiveSuggestion] = []
        self.dismissed_suggestions: List[ProactiveSuggestion] = []
        
        # Configuration
        self.min_pattern_frequency = 3  # Minimum occurrences to suggest a pattern
        self.analysis_window_days = 30  # Days to look back for pattern analysis
        self.max_suggestions = 5  # Maximum active suggestions at once
        
        # Load existing data
        self.load_data()
        
        logger.info("Proactive Suggestion Engine initialized")
    
    def record_user_action(self, action_type: str, content: str, context: Dict[str, Any] = None, 
                          session_id: str = "default") -> bool:
        """Record a user action for pattern analysis."""
        try:
            action = UserAction(
                timestamp=datetime.now(),
                action_type=action_type,
                content=content,
                context=context or {},
                session_id=session_id
            )
            
            self.user_actions.append(action)
            
            # Keep only recent actions (within analysis window)
            cutoff_date = datetime.now() - timedelta(days=self.analysis_window_days)
            self.user_actions = [a for a in self.user_actions if a.timestamp >= cutoff_date]
            
            # Trigger pattern analysis if we have enough actions
            if len(self.user_actions) % 10 == 0:  # Analyze every 10 actions
                self.analyze_patterns()
            
            self.save_data()
            
            logger.debug(f"Recorded user action: {action_type} - {content[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record user action: {e}")
            return False
    
    def analyze_patterns(self) -> List[WorkflowPattern]:
        """Analyze user actions to detect workflow patterns."""
        try:
            logger.info("Analyzing user behavior patterns...")
            
            # Group actions by session and time proximity
            sessions = self._group_actions_by_session()
            
            # Detect repetitive sequences
            patterns = []
            for session_id, session_actions in sessions.items():
                session_patterns = self._detect_session_patterns(session_actions)
                patterns.extend(session_patterns)
            
            # Filter and rank patterns
            significant_patterns = self._filter_significant_patterns(patterns)
            
            # Update detected patterns
            self.detected_patterns = significant_patterns
            
            # Generate suggestions based on patterns
            self._generate_pattern_suggestions()
            
            logger.info(f"Detected {len(significant_patterns)} significant workflow patterns")
            return significant_patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            return []
    
    def _group_actions_by_session(self) -> Dict[str, List[UserAction]]:
        """Group actions by session and time proximity."""
        sessions = defaultdict(list)
        
        # Group by session_id first
        for action in self.user_actions:
            sessions[action.session_id].append(action)
        
        # Further group by time proximity within sessions
        refined_sessions = {}
        for session_id, actions in sessions.items():
            # Sort by timestamp
            actions.sort(key=lambda a: a.timestamp)
            
            # Group actions within 1 hour of each other
            time_groups = []
            current_group = []
            
            for action in actions:
                if not current_group:
                    current_group.append(action)
                else:
                    time_diff = action.timestamp - current_group[-1].timestamp
                    if time_diff <= timedelta(hours=1):
                        current_group.append(action)
                    else:
                        if len(current_group) >= 2:  # Only keep groups with multiple actions
                            time_groups.append(current_group)
                        current_group = [action]
            
            if len(current_group) >= 2:
                time_groups.append(current_group)
            
            # Create unique session IDs for each time group
            for i, group in enumerate(time_groups):
                refined_sessions[f"{session_id}_{i}"] = group
        
        return refined_sessions
    
    def _detect_session_patterns(self, actions: List[UserAction]) -> List[WorkflowPattern]:
        """Detect patterns within a single session."""
        patterns = []
        
        if len(actions) < 3:  # Need at least 3 actions for a pattern
            return patterns
        
        # Extract action sequences
        action_sequence = [self._normalize_action(action) for action in actions]
        
        # Look for repeated subsequences
        for length in range(3, min(8, len(action_sequence) + 1)):  # Patterns of 3-7 steps
            for start in range(len(action_sequence) - length + 1):
                subsequence = action_sequence[start:start + length]
                
                # Check if this subsequence appears elsewhere
                occurrences = self._count_subsequence_occurrences(action_sequence, subsequence)
                
                if occurrences >= 2:  # Found a repeated pattern
                    pattern = self._create_workflow_pattern(subsequence, actions, occurrences)
                    if pattern:
                        patterns.append(pattern)
        
        return patterns
    
    def _normalize_action(self, action: UserAction) -> str:
        """Normalize an action for pattern matching."""
        # Simplify action content for pattern detection
        content_lower = action.content.lower()
        
        # Extract key terms
        if action.action_type == "query":
            # Extract intent from queries
            if any(word in content_lower for word in ["how", "steps", "procedure", "workflow"]):
                return "procedural_query"
            elif any(word in content_lower for word in ["what", "who", "when", "where", "define"]):
                return "factual_query"
            else:
                return "general_query"
        elif action.action_type == "procedure_execution":
            return f"execute_procedure:{action.context.get('procedure_category', 'unknown')}"
        elif action.action_type == "document_access":
            return f"access_document:{action.context.get('document_type', 'unknown')}"
        else:
            return action.action_type
    
    def _count_subsequence_occurrences(self, sequence: List[str], subsequence: List[str]) -> int:
        """Count how many times a subsequence appears in a sequence."""
        count = 0
        for i in range(len(sequence) - len(subsequence) + 1):
            if sequence[i:i + len(subsequence)] == subsequence:
                count += 1
        return count
    
    def _create_workflow_pattern(self, subsequence: List[str], original_actions: List[UserAction], 
                                frequency: int) -> Optional[WorkflowPattern]:
        """Create a workflow pattern from a detected subsequence."""
        try:
            # Generate pattern description
            pattern_description = " → ".join(subsequence)
            
            # Suggest a procedure name
            if "procedural_query" in subsequence and "execute_procedure" in subsequence:
                suggested_name = "Custom Workflow Procedure"
            elif "document_access" in pattern_description:
                suggested_name = "Document Processing Workflow"
            elif "query" in pattern_description:
                suggested_name = "Information Gathering Workflow"
            else:
                suggested_name = "Repeated Task Procedure"
            
            # Estimate time savings
            estimated_savings = f"{frequency * 2}-{frequency * 5} minutes per execution"
            
            pattern = WorkflowPattern(
                pattern_id=f"pattern_{hash(pattern_description)}",
                name=f"Workflow Pattern: {pattern_description[:30]}...",
                description=f"Detected pattern: {pattern_description}",
                actions=subsequence,
                frequency=frequency,
                confidence=min(0.9, 0.5 + (frequency * 0.1)),
                suggested_procedure_name=suggested_name,
                estimated_time_savings=estimated_savings,
                last_detected=datetime.now()
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Failed to create workflow pattern: {e}")
            return None
    
    def _filter_significant_patterns(self, patterns: List[WorkflowPattern]) -> List[WorkflowPattern]:
        """Filter patterns to keep only significant ones."""
        # Remove duplicates and low-confidence patterns
        unique_patterns = {}
        for pattern in patterns:
            key = tuple(pattern.actions)
            if key not in unique_patterns or pattern.confidence > unique_patterns[key].confidence:
                unique_patterns[key] = pattern
        
        # Filter by minimum frequency and confidence
        significant = [
            p for p in unique_patterns.values()
            if p.frequency >= self.min_pattern_frequency and p.confidence >= 0.6
        ]
        
        # Sort by confidence and frequency
        significant.sort(key=lambda p: (p.confidence, p.frequency), reverse=True)
        
        return significant[:10]  # Keep top 10 patterns
    
    def _generate_pattern_suggestions(self):
        """Generate proactive suggestions based on detected patterns."""
        try:
            new_suggestions = []
            
            for pattern in self.detected_patterns:
                # Check if we already have a suggestion for this pattern
                existing = any(s.title.startswith(pattern.suggested_procedure_name) 
                             for s in self.active_suggestions)
                
                if not existing:
                    suggestion = ProactiveSuggestion(
                        suggestion_id=f"suggest_{pattern.pattern_id}",
                        type="create_procedure",
                        title=f"Create Procedure: {pattern.suggested_procedure_name}",
                        description=f"I've noticed you frequently perform this workflow: {pattern.description}",
                        rationale=f"This pattern has occurred {pattern.frequency} times with {pattern.confidence:.0%} confidence. Creating a procedure could save you {pattern.estimated_time_savings}.",
                        confidence=pattern.confidence,
                        potential_benefit=f"Time savings: {pattern.estimated_time_savings}",
                        suggested_actions=[
                            "Create a new procedure based on this workflow",
                            "Document the steps for future reference",
                            "Set up automation where possible"
                        ],
                        created_at=datetime.now(),
                        priority=min(5, int(pattern.frequency))
                    )
                    
                    new_suggestions.append(suggestion)
            
            # Add new suggestions to active list
            self.active_suggestions.extend(new_suggestions)
            
            # Limit active suggestions
            self.active_suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)
            self.active_suggestions = self.active_suggestions[:self.max_suggestions]
            
            if new_suggestions:
                logger.info(f"Generated {len(new_suggestions)} new proactive suggestions")
            
        except Exception as e:
            logger.error(f"Failed to generate pattern suggestions: {e}")
    
    def get_active_suggestions(self, user_id: str = "default") -> List[ProactiveSuggestion]:
        """Get active suggestions for a user."""
        # For now, return all active suggestions
        # In a multi-user system, filter by user_id
        return self.active_suggestions.copy()
    
    def dismiss_suggestion(self, suggestion_id: str) -> bool:
        """Dismiss a suggestion."""
        try:
            suggestion = None
            for i, s in enumerate(self.active_suggestions):
                if s.suggestion_id == suggestion_id:
                    suggestion = self.active_suggestions.pop(i)
                    break
            
            if suggestion:
                self.dismissed_suggestions.append(suggestion)
                self.save_data()
                logger.info(f"Dismissed suggestion: {suggestion.title}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to dismiss suggestion: {e}")
            return False
    
    def accept_suggestion(self, suggestion_id: str) -> bool:
        """Mark a suggestion as accepted."""
        try:
            suggestion = None
            for i, s in enumerate(self.active_suggestions):
                if s.suggestion_id == suggestion_id:
                    suggestion = self.active_suggestions.pop(i)
                    break
            
            if suggestion:
                # In a full implementation, this would trigger procedure creation
                logger.info(f"Accepted suggestion: {suggestion.title}")
                self.save_data()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to accept suggestion: {e}")
            return False
    
    def get_suggestion_analytics(self) -> Dict[str, Any]:
        """Get analytics about suggestions and user behavior."""
        try:
            total_actions = len(self.user_actions)
            total_patterns = len(self.detected_patterns)
            active_suggestions_count = len(self.active_suggestions)
            dismissed_suggestions_count = len(self.dismissed_suggestions)
            
            # Action type distribution
            action_types = Counter(action.action_type for action in self.user_actions)
            
            # Pattern confidence distribution
            if self.detected_patterns:
                avg_pattern_confidence = sum(p.confidence for p in self.detected_patterns) / len(self.detected_patterns)
                max_pattern_frequency = max(p.frequency for p in self.detected_patterns)
            else:
                avg_pattern_confidence = 0
                max_pattern_frequency = 0
            
            return {
                'total_user_actions': total_actions,
                'detected_patterns': total_patterns,
                'active_suggestions': active_suggestions_count,
                'dismissed_suggestions': dismissed_suggestions_count,
                'action_type_distribution': dict(action_types),
                'average_pattern_confidence': avg_pattern_confidence,
                'max_pattern_frequency': max_pattern_frequency,
                'analysis_window_days': self.analysis_window_days
            }
            
        except Exception as e:
            logger.error(f"Failed to get suggestion analytics: {e}")
            return {}
    
    def save_data(self) -> bool:
        """Save suggestion engine data."""
        try:
            data = {
                'user_actions': [asdict(action) for action in self.user_actions],
                'detected_patterns': [asdict(pattern) for pattern in self.detected_patterns],
                'active_suggestions': [asdict(suggestion) for suggestion in self.active_suggestions],
                'dismissed_suggestions': [asdict(suggestion) for suggestion in self.dismissed_suggestions],
                'metadata': {
                    'version': '2.0.0',
                    'last_saved': datetime.now().isoformat(),
                    'total_actions': len(self.user_actions),
                    'total_patterns': len(self.detected_patterns)
                }
            }
            
            # Convert datetime objects to ISO format
            for action_data in data['user_actions']:
                action_data['timestamp'] = action_data['timestamp'].isoformat() if isinstance(action_data['timestamp'], datetime) else action_data['timestamp']
            
            for pattern_data in data['detected_patterns']:
                pattern_data['last_detected'] = pattern_data['last_detected'].isoformat() if isinstance(pattern_data['last_detected'], datetime) else pattern_data['last_detected']
            
            for suggestion_data in data['active_suggestions'] + data['dismissed_suggestions']:
                suggestion_data['created_at'] = suggestion_data['created_at'].isoformat() if isinstance(suggestion_data['created_at'], datetime) else suggestion_data['created_at']
            
            # Write to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug("Saved proactive suggestion data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save suggestion data: {e}")
            return False
    
    def load_data(self) -> bool:
        """Load suggestion engine data."""
        try:
            if not self.storage_path.exists():
                logger.info("No existing suggestion data found - starting fresh")
                return True
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load user actions
            self.user_actions = []
            for action_data in data.get('user_actions', []):
                action_data['timestamp'] = datetime.fromisoformat(action_data['timestamp'])
                self.user_actions.append(UserAction(**action_data))
            
            # Load detected patterns
            self.detected_patterns = []
            for pattern_data in data.get('detected_patterns', []):
                pattern_data['last_detected'] = datetime.fromisoformat(pattern_data['last_detected'])
                self.detected_patterns.append(WorkflowPattern(**pattern_data))
            
            # Load active suggestions
            self.active_suggestions = []
            for suggestion_data in data.get('active_suggestions', []):
                suggestion_data['created_at'] = datetime.fromisoformat(suggestion_data['created_at'])
                self.active_suggestions.append(ProactiveSuggestion(**suggestion_data))
            
            # Load dismissed suggestions
            self.dismissed_suggestions = []
            for suggestion_data in data.get('dismissed_suggestions', []):
                suggestion_data['created_at'] = datetime.fromisoformat(suggestion_data['created_at'])
                self.dismissed_suggestions.append(ProactiveSuggestion(**suggestion_data))
            
            logger.info(f"Loaded suggestion data: {len(self.user_actions)} actions, {len(self.detected_patterns)} patterns")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load suggestion data: {e}")
            return False

# Global instance for easy access
_proactive_engine = None

def get_proactive_suggestion_engine() -> ProactiveSuggestionEngine:
    """Get the global proactive suggestion engine instance."""
    global _proactive_engine
    if _proactive_engine is None:
        _proactive_engine = ProactiveSuggestionEngine()
    return _proactive_engine
