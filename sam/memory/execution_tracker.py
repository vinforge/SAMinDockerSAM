"""
Procedure Execution Tracking Engine
===================================

Advanced execution tracking system for monitoring user progress through procedures,
providing real-time guidance, and collecting analytics for procedure optimization.

Features:
- Real-time execution state management
- Step-by-step progress tracking
- Intelligent guidance and suggestions
- Performance analytics and optimization
- Integration with SAM's cognitive architecture

Author: SAM Development Team
Version: 2.0.0 (Phase 3 - Advanced Cognitive Features)
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Enumeration of execution states."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Enumeration of step completion states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"

@dataclass
class StepExecution:
    """Tracks execution state of a single procedure step."""
    step_number: int
    status: StepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    user_notes: str = ""
    issues_encountered: List[str] = None
    verification_result: Optional[bool] = None
    
    def __post_init__(self):
        if self.issues_encountered is None:
            self.issues_encountered = []

@dataclass
class ProcedureExecution:
    """Tracks complete execution of a procedure."""
    execution_id: str
    procedure_id: str
    procedure_name: str
    user_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    current_step: int = 0
    steps: Dict[int, StepExecution] = None
    user_parameters: Dict[str, str] = None
    overall_notes: str = ""
    success_rating: Optional[int] = None  # 1-5 scale
    difficulty_rating: Optional[int] = None  # 1-5 scale
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = {}
        if self.user_parameters is None:
            self.user_parameters = {}

class ExecutionTracker:
    """Advanced execution tracking engine for procedures."""
    
    def __init__(self, storage_path: str = "sam/data/execution_tracking.json"):
        """Initialize the execution tracker."""
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_executions: Dict[str, ProcedureExecution] = {}
        self.completed_executions: List[ProcedureExecution] = []
        self._security_manager = None
        
        # Initialize security integration
        self._init_security()
        
        # Load existing executions
        self.load_executions()
        
        logger.info(f"Execution Tracker initialized with {len(self.active_executions)} active executions")
    
    def _init_security(self):
        """Initialize SAM Secure Enclave integration."""
        try:
            from security import get_security_manager
            self._security_manager = get_security_manager()
            logger.info("Execution tracking integrated with SAM Secure Enclave")
        except ImportError:
            logger.warning("SAM Secure Enclave not available - using unencrypted storage")
            self._security_manager = None
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using SAM Secure Enclave."""
        if self._security_manager and hasattr(self._security_manager, 'encrypt_data'):
            return self._security_manager.encrypt_data(data)
        return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using SAM Secure Enclave."""
        if self._security_manager and hasattr(self._security_manager, 'decrypt_data'):
            return self._security_manager.decrypt_data(encrypted_data)
        return encrypted_data
    
    def start_execution(self, procedure_id: str, procedure_name: str, user_id: str = "default", 
                       user_parameters: Dict[str, str] = None) -> str:
        """Start tracking execution of a procedure."""
        try:
            execution_id = f"exec_{uuid.uuid4().hex[:8]}"
            
            execution = ProcedureExecution(
                execution_id=execution_id,
                procedure_id=procedure_id,
                procedure_name=procedure_name,
                user_id=user_id,
                status=ExecutionStatus.IN_PROGRESS,
                started_at=datetime.now(),
                current_step=1,
                user_parameters=user_parameters or {}
            )
            
            self.active_executions[execution_id] = execution
            self.save_executions()
            
            logger.info(f"Started execution tracking: {procedure_name} ({execution_id})")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to start execution tracking: {e}")
            return None
    
    def update_step_status(self, execution_id: str, step_number: int, status: StepStatus, 
                          user_notes: str = "", issues: List[str] = None) -> bool:
        """Update the status of a specific step."""
        try:
            if execution_id not in self.active_executions:
                logger.warning(f"Execution not found: {execution_id}")
                return False
            
            execution = self.active_executions[execution_id]
            
            # Initialize step if not exists
            if step_number not in execution.steps:
                execution.steps[step_number] = StepExecution(
                    step_number=step_number,
                    status=StepStatus.PENDING
                )
            
            step = execution.steps[step_number]
            old_status = step.status
            step.status = status
            step.user_notes = user_notes
            
            if issues:
                step.issues_encountered.extend(issues)
            
            # Update timestamps
            now = datetime.now()
            if status == StepStatus.IN_PROGRESS and old_status == StepStatus.PENDING:
                step.started_at = now
            elif status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
                if step.started_at:
                    step.completed_at = now
                    step.duration_seconds = (now - step.started_at).total_seconds()
                else:
                    step.completed_at = now
                    step.duration_seconds = 0
            
            # Update current step
            if status == StepStatus.COMPLETED:
                execution.current_step = step_number + 1
            
            self.save_executions()
            
            logger.info(f"Updated step {step_number} to {status.value} for execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update step status: {e}")
            return False
    
    def complete_execution(self, execution_id: str, success_rating: int = None, 
                          difficulty_rating: int = None, overall_notes: str = "") -> bool:
        """Mark an execution as completed."""
        try:
            if execution_id not in self.active_executions:
                logger.warning(f"Execution not found: {execution_id}")
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.total_duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            execution.success_rating = success_rating
            execution.difficulty_rating = difficulty_rating
            execution.overall_notes = overall_notes
            
            # Move to completed executions
            self.completed_executions.append(execution)
            del self.active_executions[execution_id]
            
            self.save_executions()
            
            logger.info(f"Completed execution: {execution.procedure_name} ({execution_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete execution: {e}")
            return False
    
    def pause_execution(self, execution_id: str) -> bool:
        """Pause an active execution."""
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.PAUSED
            
            self.save_executions()
            
            logger.info(f"Paused execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause execution: {e}")
            return False
    
    def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution."""
        try:
            if execution_id not in self.active_executions:
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.IN_PROGRESS
            
            self.save_executions()
            
            logger.info(f"Resumed execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume execution: {e}")
            return False
    
    def get_execution_status(self, execution_id: str) -> Optional[ProcedureExecution]:
        """Get current status of an execution."""
        return self.active_executions.get(execution_id)
    
    def get_user_active_executions(self, user_id: str = "default") -> List[ProcedureExecution]:
        """Get all active executions for a user."""
        return [exec for exec in self.active_executions.values() if exec.user_id == user_id]
    
    def get_execution_analytics(self, procedure_id: str = None) -> Dict[str, Any]:
        """Get analytics for executions."""
        try:
            # Filter executions
            if procedure_id:
                executions = [exec for exec in self.completed_executions if exec.procedure_id == procedure_id]
            else:
                executions = self.completed_executions
            
            if not executions:
                return {
                    'total_executions': 0,
                    'average_duration': 0,
                    'success_rate': 0,
                    'average_difficulty': 0,
                    'common_issues': []
                }
            
            # Calculate metrics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
            
            durations = [e.total_duration_seconds for e in executions if e.total_duration_seconds]
            average_duration = sum(durations) / len(durations) if durations else 0
            
            success_ratings = [e.success_rating for e in executions if e.success_rating]
            average_success = sum(success_ratings) / len(success_ratings) if success_ratings else 0
            
            difficulty_ratings = [e.difficulty_rating for e in executions if e.difficulty_rating]
            average_difficulty = sum(difficulty_ratings) / len(difficulty_ratings) if difficulty_ratings else 0
            
            # Collect common issues
            all_issues = []
            for execution in executions:
                for step in execution.steps.values():
                    all_issues.extend(step.issues_encountered)
            
            # Count issue frequency
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
                'average_duration_minutes': average_duration / 60 if average_duration > 0 else 0,
                'average_success_rating': average_success,
                'average_difficulty_rating': average_difficulty,
                'common_issues': common_issues
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution analytics: {e}")
            return {}
    
    def save_executions(self) -> bool:
        """Save execution data to secure storage."""
        try:
            # Convert to serializable format
            data = {
                'active_executions': {},
                'completed_executions': [],
                'metadata': {
                    'version': '2.0.0',
                    'last_saved': datetime.now().isoformat(),
                    'total_active': len(self.active_executions),
                    'total_completed': len(self.completed_executions)
                }
            }
            
            # Convert active executions
            for exec_id, execution in self.active_executions.items():
                exec_dict = asdict(execution)
                # Convert datetime objects
                exec_dict['started_at'] = execution.started_at.isoformat()
                if execution.completed_at:
                    exec_dict['completed_at'] = execution.completed_at.isoformat()
                
                # Convert step datetimes
                for step_num, step in exec_dict['steps'].items():
                    if step['started_at']:
                        step['started_at'] = step['started_at'].isoformat() if isinstance(step['started_at'], datetime) else step['started_at']
                    if step['completed_at']:
                        step['completed_at'] = step['completed_at'].isoformat() if isinstance(step['completed_at'], datetime) else step['completed_at']
                
                data['active_executions'][exec_id] = exec_dict
            
            # Convert completed executions
            for execution in self.completed_executions:
                exec_dict = asdict(execution)
                exec_dict['started_at'] = execution.started_at.isoformat()
                if execution.completed_at:
                    exec_dict['completed_at'] = execution.completed_at.isoformat()
                
                # Convert step datetimes
                for step_num, step in exec_dict['steps'].items():
                    if step['started_at']:
                        step['started_at'] = step['started_at'].isoformat() if isinstance(step['started_at'], datetime) else step['started_at']
                    if step['completed_at']:
                        step['completed_at'] = step['completed_at'].isoformat() if isinstance(step['completed_at'], datetime) else step['completed_at']
                
                data['completed_executions'].append(exec_dict)
            
            # Serialize to JSON
            json_data = json.dumps(data, indent=2, default=str)
            
            # Encrypt if security is available
            encrypted_data = self._encrypt_data(json_data)
            
            # Write to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            logger.info(f"Saved execution data: {len(self.active_executions)} active, {len(self.completed_executions)} completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save execution data: {e}")
            return False
    
    def load_executions(self) -> bool:
        """Load execution data from secure storage."""
        try:
            if not self.storage_path.exists():
                logger.info("No existing execution data found - starting fresh")
                return True
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # Decrypt if security is available
            decrypted_data = self._decrypt_data(encrypted_data)
            
            if not decrypted_data.strip():
                logger.info("Empty execution data file - starting fresh")
                return True
            
            data = json.loads(decrypted_data)
            
            # Load active executions
            for exec_id, exec_data in data.get('active_executions', {}).items():
                # Parse datetime fields
                exec_data['started_at'] = datetime.fromisoformat(exec_data['started_at'])
                if exec_data.get('completed_at'):
                    exec_data['completed_at'] = datetime.fromisoformat(exec_data['completed_at'])
                
                # Parse step data
                steps = {}
                for step_num, step_data in exec_data.get('steps', {}).items():
                    if step_data.get('started_at'):
                        step_data['started_at'] = datetime.fromisoformat(step_data['started_at'])
                    if step_data.get('completed_at'):
                        step_data['completed_at'] = datetime.fromisoformat(step_data['completed_at'])
                    
                    steps[int(step_num)] = StepExecution(**step_data)
                
                exec_data['steps'] = steps
                exec_data['status'] = ExecutionStatus(exec_data['status'])
                
                self.active_executions[exec_id] = ProcedureExecution(**exec_data)
            
            # Load completed executions
            for exec_data in data.get('completed_executions', []):
                # Parse datetime fields
                exec_data['started_at'] = datetime.fromisoformat(exec_data['started_at'])
                if exec_data.get('completed_at'):
                    exec_data['completed_at'] = datetime.fromisoformat(exec_data['completed_at'])
                
                # Parse step data
                steps = {}
                for step_num, step_data in exec_data.get('steps', {}).items():
                    if step_data.get('started_at'):
                        step_data['started_at'] = datetime.fromisoformat(step_data['started_at'])
                    if step_data.get('completed_at'):
                        step_data['completed_at'] = datetime.fromisoformat(step_data['completed_at'])
                    
                    steps[int(step_num)] = StepExecution(**step_data)
                
                exec_data['steps'] = steps
                exec_data['status'] = ExecutionStatus(exec_data['status'])
                
                self.completed_executions.append(ProcedureExecution(**exec_data))
            
            logger.info(f"Loaded execution data: {len(self.active_executions)} active, {len(self.completed_executions)} completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load execution data: {e}")
            return False

# Global instance for easy access
_execution_tracker = None

def get_execution_tracker() -> ExecutionTracker:
    """Get the global execution tracker instance."""
    global _execution_tracker
    if _execution_tracker is None:
        _execution_tracker = ExecutionTracker()
    return _execution_tracker
