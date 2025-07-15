"""
Procedural Memory Engine for SAM
===============================

Provides secure storage and management of user-defined multi-step procedures,
workflows, and "how-to" guides with deep integration into SAM's cognitive architecture.

Features:
- Secure encrypted storage with SAM Secure Enclave integration
- Enhanced data models with parameters and versioning
- Usage tracking and analytics
- Advanced search and ranking capabilities

Author: SAM Development Team
Version: 2.0.0 (Enhanced Implementation)
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ProcedureStep(BaseModel):
    """Enhanced procedure step with detailed metadata."""
    step_number: int
    description: str  # e.g., "Open the weekly sales report spreadsheet"
    details: Optional[str] = None  # e.g., "The file is located at /reports/sales.xlsx"
    expected_outcome: Optional[str] = None  # e.g., "The spreadsheet is open and visible"
    estimated_duration: Optional[str] = None  # e.g., "5 minutes"
    prerequisites: List[str] = []  # Dependencies for this step
    tools_required: List[str] = []  # Software, files, etc. needed
    verification_criteria: Optional[str] = None  # How to verify completion
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Procedure(BaseModel):
    """Enhanced procedure model with cognitive features."""
    id: str = Field(default_factory=lambda: f"proc_{uuid.uuid4().hex[:8]}")
    name: str  # e.g., "Weekly Sales Report Workflow"
    description: str  # e.g., "A step-by-step guide to compile and send the weekly sales report"
    tags: List[str] = []  # e.g., ["reporting", "sales", "weekly"]
    steps: List[ProcedureStep]
    
    # Enhanced metadata
    category: Optional[str] = None  # "business", "personal", "technical"
    difficulty_level: Optional[str] = None  # "beginner", "intermediate", "advanced"
    estimated_total_time: Optional[str] = None
    version: float = 1.0  # Enable procedure versioning
    parameters: Dict[str, str] = {}  # Dynamic parameters for reusable procedures
    
    # Usage tracking
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProceduralMemoryStore:
    """Secure storage and management system for procedures."""
    
    def __init__(self, storage_path: str = "sam/data/procedural_memory.json"):
        """Initialize the procedural memory store with secure storage."""
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.procedures: Dict[str, Procedure] = {}
        self._security_manager = None
        
        # Initialize security integration
        self._init_security()
        
        # Load existing procedures
        self.load_procedures()
        
        logger.info(f"ProceduralMemoryStore initialized with {len(self.procedures)} procedures")
    
    def _init_security(self):
        """Initialize SAM Secure Enclave integration."""
        try:
            from security import get_security_manager
            self._security_manager = get_security_manager()
            logger.info("Procedural memory integrated with SAM Secure Enclave")
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
    
    def load_procedures(self) -> bool:
        """Load procedures from secure storage."""
        try:
            if not self.storage_path.exists():
                logger.info("No existing procedural memory file found - starting fresh")
                return True
            
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
            
            # Decrypt if security is available
            decrypted_data = self._decrypt_data(encrypted_data)
            
            if not decrypted_data.strip():
                logger.info("Empty procedural memory file - starting fresh")
                return True
            
            data = json.loads(decrypted_data)
            
            # Load procedures with datetime parsing
            for proc_id, proc_data in data.get('procedures', {}).items():
                # Parse datetime fields
                for date_field in ['created_date', 'last_modified', 'last_executed']:
                    if proc_data.get(date_field):
                        proc_data[date_field] = datetime.fromisoformat(proc_data[date_field])
                
                # Parse step data
                steps = []
                for step_data in proc_data.get('steps', []):
                    steps.append(ProcedureStep(**step_data))
                proc_data['steps'] = steps
                
                self.procedures[proc_id] = Procedure(**proc_data)
            
            logger.info(f"Loaded {len(self.procedures)} procedures from secure storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load procedures: {e}")
            return False
    
    def save_procedures(self) -> bool:
        """Save procedures to secure storage."""
        try:
            # Convert procedures to serializable format
            data = {
                'procedures': {},
                'metadata': {
                    'version': '2.0.0',
                    'last_saved': datetime.now().isoformat(),
                    'total_procedures': len(self.procedures)
                }
            }
            
            for proc_id, procedure in self.procedures.items():
                data['procedures'][proc_id] = procedure.dict()
            
            # Serialize to JSON
            json_data = json.dumps(data, indent=2, default=str)
            
            # Encrypt if security is available
            encrypted_data = self._encrypt_data(json_data)
            
            # Write to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
            
            logger.info(f"Saved {len(self.procedures)} procedures to secure storage")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save procedures: {e}")
            return False
    
    def add_procedure(self, procedure: Procedure) -> bool:
        """Add a new procedure to the store."""
        try:
            procedure.created_date = datetime.now()
            procedure.last_modified = datetime.now()
            
            self.procedures[procedure.id] = procedure
            success = self.save_procedures()
            
            if success:
                logger.info(f"Added procedure: {procedure.name} ({procedure.id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add procedure: {e}")
            return False
    
    def get_procedure(self, procedure_id: str) -> Optional[Procedure]:
        """Retrieve a procedure by its unique ID."""
        return self.procedures.get(procedure_id)
    
    def update_procedure(self, procedure_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update an existing procedure."""
        try:
            if procedure_id not in self.procedures:
                logger.warning(f"Procedure not found: {procedure_id}")
                return False
            
            procedure = self.procedures[procedure_id]
            
            # Update fields
            for field, value in updated_data.items():
                if hasattr(procedure, field):
                    setattr(procedure, field, value)
            
            # Update modification timestamp
            procedure.last_modified = datetime.now()
            
            success = self.save_procedures()
            
            if success:
                logger.info(f"Updated procedure: {procedure.name} ({procedure_id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update procedure: {e}")
            return False
    
    def delete_procedure(self, procedure_id: str) -> bool:
        """Remove a procedure from the store."""
        try:
            if procedure_id not in self.procedures:
                logger.warning(f"Procedure not found: {procedure_id}")
                return False
            
            procedure_name = self.procedures[procedure_id].name
            del self.procedures[procedure_id]
            
            success = self.save_procedures()
            
            if success:
                logger.info(f"Deleted procedure: {procedure_name} ({procedure_id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete procedure: {e}")
            return False
    
    def get_all_procedures(self) -> List[Procedure]:
        """Get all procedures sorted by last modified date."""
        procedures = list(self.procedures.values())
        procedures.sort(key=lambda p: p.last_modified, reverse=True)
        return procedures
    
    def search_procedures(self, query: str, filters: Dict[str, Any] = None) -> List[Tuple[Procedure, float]]:
        """Enhanced search with hybrid scoring and filtering."""
        results = []

        if not query.strip():
            # No query - return all procedures with default score
            results = [(proc, 1.0) for proc in self.procedures.values()]
        else:
            # Query provided - calculate relevance scores
            query_lower = query.lower()
            for procedure in self.procedures.values():
                score = self._calculate_relevance_score(procedure, query_lower)
                # Increased relevance threshold to reduce irrelevant matches
                if score > 2.0:  # Higher threshold for better relevance
                    results.append((procedure, score))

        # Apply filters if provided
        if filters:
            results = self._apply_filters(results, filters)

        # Sort by relevance score (or last modified for equal scores)
        results.sort(key=lambda x: (x[1], x[0].last_modified), reverse=True)
        return results

    def _calculate_relevance_score(self, procedure: Procedure, query_lower: str) -> float:
        """Calculate relevance score using hybrid scoring model with stricter matching."""
        score = 0.0
        query_words = [word for word in query_lower.split() if len(word) > 2]  # Filter short words

        # Skip common words that don't add meaning
        stop_words = {'the', 'and', 'for', 'with', 'how', 'what', 'when', 'where', 'why', 'lets', 'let'}
        meaningful_words = [word for word in query_words if word not in stop_words]

        if not meaningful_words:
            return 0.0  # No meaningful words to match

        # Name match (highest weight) - check both full query and individual words
        procedure_name_lower = procedure.name.lower()
        if query_lower in procedure_name_lower:
            score += 5.0  # Increased for exact phrase match
        else:
            # Check meaningful words only
            name_word_matches = 0
            for word in meaningful_words:
                if word in procedure_name_lower:
                    score += 2.0  # Increased weight for name matches
                    name_word_matches += 1

            # Bonus for multiple word matches in name
            if name_word_matches > 1:
                score += name_word_matches * 0.5

        # Tag matches (high weight)
        for tag in procedure.tags:
            tag_lower = tag.lower()
            if query_lower in tag_lower:
                score += 3.0  # Increased for exact phrase match
            else:
                # Check meaningful words only
                for word in meaningful_words:
                    if word in tag_lower:
                        score += 1.5  # Increased weight for tag matches

        # Description match (medium weight)
        description_lower = procedure.description.lower()
        if query_lower in description_lower:
            score += 2.0  # Increased for exact phrase match
        else:
            # Check meaningful words only
            for word in meaningful_words:
                if word in description_lower:
                    score += 1.0

        # Step description matches (lower weight, meaningful words only)
        for step in procedure.steps:
            step_desc_lower = step.description.lower()
            if query_lower in step_desc_lower:
                score += 1.0
            else:
                # Check meaningful words only
                for word in meaningful_words:
                    if word in step_desc_lower:
                        score += 0.3  # Reduced weight

            if step.details:
                step_details_lower = step.details.lower()
                if query_lower in step_details_lower:
                    score += 0.5
                else:
                    # Check meaningful words only
                    for word in meaningful_words:
                        if word in step_details_lower:
                            score += 0.2  # Reduced weight

        # Category match (low weight, meaningful words only)
        if procedure.category:
            category_lower = procedure.category.lower()
            if query_lower in category_lower:
                score += 1.0  # Increased for exact category match
            else:
                # Check meaningful words only
                for word in meaningful_words:
                    if word in category_lower:
                        score += 0.5

        # Boost based on usage (recency and popularity)
        if procedure.execution_count > 0:
            score += min(procedure.execution_count * 0.1, 1.0)  # Cap at 1.0

        if procedure.last_executed:
            days_since_used = (datetime.now() - procedure.last_executed).days
            if days_since_used < 7:
                score += 0.5  # Recently used boost

        return score

    def _apply_filters(self, results: List[Tuple[Procedure, float]], filters: Dict[str, Any]) -> List[Tuple[Procedure, float]]:
        """Apply filters to search results."""
        filtered_results = []

        for procedure, score in results:
            # Category filter
            if 'category' in filters and filters['category']:
                if procedure.category != filters['category']:
                    continue

            # Difficulty filter
            if 'difficulty_level' in filters and filters['difficulty_level']:
                if procedure.difficulty_level != filters['difficulty_level']:
                    continue

            # Tags filter
            if 'tags' in filters and filters['tags']:
                required_tags = set(filters['tags'])
                procedure_tags = set(procedure.tags)
                if not required_tags.intersection(procedure_tags):
                    continue

            filtered_results.append((procedure, score))

        return filtered_results

    def record_procedure_execution(self, procedure_id: str) -> bool:
        """Record that a procedure was executed (usage tracking)."""
        try:
            if procedure_id not in self.procedures:
                return False

            procedure = self.procedures[procedure_id]
            procedure.last_executed = datetime.now()
            procedure.execution_count += 1

            success = self.save_procedures()

            if success:
                logger.info(f"Recorded execution of procedure: {procedure.name}")

            return success

        except Exception as e:
            logger.error(f"Failed to record procedure execution: {e}")
            return False

    def get_procedure_stats(self) -> Dict[str, Any]:
        """Get statistics about the procedural memory store."""
        if not self.procedures:
            return {
                'total_procedures': 0,
                'categories': {},
                'most_used': None,
                'recently_created': []
            }

        procedures = list(self.procedures.values())

        # Category distribution
        categories = {}
        for proc in procedures:
            cat = proc.category or 'uncategorized'
            categories[cat] = categories.get(cat, 0) + 1

        # Most used procedure
        most_used = max(procedures, key=lambda p: p.execution_count, default=None)

        # Recently created (last 5)
        recently_created = sorted(procedures, key=lambda p: p.created_date, reverse=True)[:5]

        return {
            'total_procedures': len(procedures),
            'categories': categories,
            'most_used': {
                'name': most_used.name,
                'execution_count': most_used.execution_count
            } if most_used else None,
            'recently_created': [
                {'name': p.name, 'created_date': p.created_date.isoformat()}
                for p in recently_created
            ]
        }

# Global instance for easy access
_procedural_store = None

def get_procedural_memory_store() -> ProceduralMemoryStore:
    """Get the global procedural memory store instance."""
    global _procedural_store
    if _procedural_store is None:
        _procedural_store = ProceduralMemoryStore()
    return _procedural_store
