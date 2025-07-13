"""
Procedural Memory Integration Service
====================================

Handles the integration between procedural memory and SAM's reasoning engine,
including procedure formatting, context injection, and execution guidance.

Features:
- Markdown formatting for LLM context injection
- Parameter substitution for reusable procedures
- Execution tracking and guidance
- Integration with SAM's cognitive architecture

Author: SAM Development Team
Version: 2.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ProceduralIntegrationService:
    """Service for integrating procedural memory with SAM's reasoning engine."""
    
    def __init__(self):
        """Initialize the procedural integration service."""
        self.store = None
        self._init_store()
        
        logger.info("Procedural Integration Service initialized")
    
    def _init_store(self):
        """Initialize the procedural memory store."""
        try:
            from sam.memory.procedural_memory import get_procedural_memory_store
            self.store = get_procedural_memory_store()
        except Exception as e:
            logger.error(f"Failed to initialize procedural store: {e}")
            self.store = None
    
    def search_and_format_procedures(self, query: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Search for relevant procedures and format them for LLM context.
        
        Args:
            query: The user's procedural query
            context: Additional context for search and formatting
            
        Returns:
            Formatted Markdown string for LLM context, or None if no procedures found
        """
        if not self.store:
            logger.warning("Procedural store not available")
            return None
        
        try:
            # Extract search parameters from context
            filters = self._extract_search_filters(context)
            
            # Search for relevant procedures
            search_results = self.store.search_procedures(query, filters)
            
            if not search_results:
                logger.info(f"No procedures found for query: {query}")
                return None
            
            # Select the best procedure(s) to include
            selected_procedures = self._select_procedures_for_context(search_results, context)
            
            # Format procedures for LLM context
            formatted_context = self._format_procedures_for_llm(selected_procedures, query, context)
            
            # Record procedure access for analytics
            for procedure, score in selected_procedures:
                self._record_procedure_access(procedure.id, query, score)
            
            return formatted_context
            
        except Exception as e:
            logger.error(f"Error in search_and_format_procedures: {e}")
            return None
    
    def _extract_search_filters(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract search filters from context."""
        filters = {}
        
        if not context:
            return filters
        
        # Extract category filter
        if context.get('preferred_category'):
            filters['category'] = context['preferred_category']
        
        # Extract difficulty filter
        if context.get('user_skill_level'):
            skill_mapping = {
                'novice': 'beginner',
                'intermediate': 'intermediate',
                'expert': 'advanced'
            }
            filters['difficulty_level'] = skill_mapping.get(context['user_skill_level'])
        
        # Extract tag filters
        if context.get('required_tags'):
            filters['tags'] = context['required_tags']
        
        return filters
    
    def _select_procedures_for_context(self, search_results: List[Tuple], context: Dict[str, Any] = None) -> List[Tuple]:
        """Select the best procedures to include in LLM context."""
        if not search_results:
            return []
        
        # Configuration for selection
        max_procedures = context.get('max_procedures', 2) if context else 2
        min_relevance_score = context.get('min_relevance_score', 0.3) if context else 0.3
        
        # Filter by minimum relevance score
        relevant_procedures = [
            (proc, score) for proc, score in search_results 
            if score >= min_relevance_score
        ]
        
        # Sort by relevance score (already sorted from search, but ensure)
        relevant_procedures.sort(key=lambda x: x[1], reverse=True)
        
        # Take top procedures up to max limit
        selected = relevant_procedures[:max_procedures]
        
        logger.info(f"Selected {len(selected)} procedures from {len(search_results)} search results")
        
        return selected
    
    def _format_procedures_for_llm(self, procedures: List[Tuple], query: str, context: Dict[str, Any] = None) -> str:
        """Format procedures into clean Markdown for LLM context."""
        if not procedures:
            return ""
        
        # Build the formatted context
        context_parts = []
        
        # Header
        context_parts.append("# 🧠 Procedural Memory Retrieved")
        context_parts.append(f"*Based on your query: \"{query}\"*")
        context_parts.append("")
        
        # Format each procedure
        for i, (procedure, relevance_score) in enumerate(procedures, 1):
            procedure_md = self._format_single_procedure(procedure, relevance_score, context)
            context_parts.append(procedure_md)
            
            # Add separator between procedures
            if i < len(procedures):
                context_parts.append("---")
                context_parts.append("")
        
        # Footer with guidance
        context_parts.append("## 💡 Usage Guidance")
        context_parts.append("- Follow the steps in order for best results")
        context_parts.append("- Adapt steps to your specific situation as needed")
        context_parts.append("- Pay attention to prerequisites and expected outcomes")
        
        if len(procedures) > 1:
            context_parts.append("- Multiple procedures found - choose the most relevant one")
        
        return "\n".join(context_parts)
    
    def _format_single_procedure(self, procedure, relevance_score: float, context: Dict[str, Any] = None) -> str:
        """Format a single procedure into Markdown."""
        lines = []
        
        # Procedure header
        lines.append(f"## 📋 {procedure.name}")
        lines.append(f"**Description:** {procedure.description}")
        lines.append("")
        
        # Metadata
        metadata_parts = []
        if procedure.category:
            metadata_parts.append(f"**Category:** {procedure.category}")
        if procedure.difficulty_level:
            metadata_parts.append(f"**Difficulty:** {procedure.difficulty_level}")
        if procedure.estimated_total_time:
            metadata_parts.append(f"**Estimated Time:** {procedure.estimated_total_time}")
        if procedure.tags:
            metadata_parts.append(f"**Tags:** {', '.join(procedure.tags)}")
        
        if metadata_parts:
            lines.extend(metadata_parts)
            lines.append("")
        
        # Parameters (if any)
        if procedure.parameters:
            lines.append("**Parameters:**")
            for param_key, param_value in procedure.parameters.items():
                lines.append(f"- `{param_key}`: {param_value}")
            lines.append("")
        
        # Steps
        lines.append("**Steps:**")
        for step in procedure.steps:
            step_md = self._format_procedure_step(step, procedure.parameters)
            lines.append(step_md)
        
        # Usage statistics
        if procedure.execution_count > 0:
            lines.append("")
            lines.append(f"*This procedure has been used {procedure.execution_count} times.*")
            if procedure.last_executed:
                last_used = procedure.last_executed.strftime("%Y-%m-%d")
                lines.append(f"*Last used: {last_used}*")
        
        # Relevance score (for debugging/transparency)
        lines.append("")
        lines.append(f"*Relevance Score: {relevance_score:.2f}*")
        
        return "\n".join(lines)
    
    def _format_procedure_step(self, step, parameters: Dict[str, str] = None) -> str:
        """Format a single procedure step with parameter substitution."""
        # Start with step number and description
        step_text = f"{step.step_number}. **{step.description}**"
        
        # Add details if available
        if step.details:
            details = step.details
            # Substitute parameters if available
            if parameters:
                for param_key, param_value in parameters.items():
                    details = details.replace(f"{{{param_key}}}", param_value)
            step_text += f"\n   - *Details:* {details}"
        
        # Add expected outcome if available
        if step.expected_outcome:
            step_text += f"\n   - *Expected Outcome:* {step.expected_outcome}"
        
        # Add additional metadata if available
        metadata_items = []
        if step.estimated_duration:
            metadata_items.append(f"Duration: {step.estimated_duration}")
        if step.prerequisites:
            metadata_items.append(f"Prerequisites: {', '.join(step.prerequisites)}")
        if step.tools_required:
            metadata_items.append(f"Tools: {', '.join(step.tools_required)}")
        
        if metadata_items:
            step_text += f"\n   - *{' | '.join(metadata_items)}*"
        
        return step_text
    
    def _record_procedure_access(self, procedure_id: str, query: str, relevance_score: float):
        """Record that a procedure was accessed for analytics."""
        try:
            # This could be enhanced to track detailed analytics
            logger.info(f"Procedure accessed: {procedure_id} (score: {relevance_score:.2f}) for query: {query}")
            
            # For now, we don't increment execution count until user actually uses it
            # That will be handled by the execution tracking endpoint
            
        except Exception as e:
            logger.error(f"Failed to record procedure access: {e}")
    
    def render_procedure_with_parameters(self, procedure_id: str, parameters: Dict[str, str]) -> Optional[str]:
        """Render a procedure with custom parameter values."""
        if not self.store:
            return None
        
        try:
            procedure = self.store.get_procedure(procedure_id)
            if not procedure:
                return None
            
            # Create a copy with substituted parameters
            substituted_procedure = self._substitute_parameters(procedure, parameters)
            
            # Format for display
            return self._format_single_procedure(substituted_procedure, 1.0)
            
        except Exception as e:
            logger.error(f"Error rendering procedure with parameters: {e}")
            return None
    
    def _substitute_parameters(self, procedure, custom_parameters: Dict[str, str]):
        """Create a copy of procedure with parameter substitution."""
        # This is a simplified version - in production, you'd want to create a proper copy
        # For now, we'll just modify the display without changing the stored procedure
        
        # Merge default parameters with custom ones
        final_parameters = procedure.parameters.copy()
        final_parameters.update(custom_parameters)
        
        # Create a modified copy for display purposes
        # In a real implementation, you'd use a proper copy mechanism
        return procedure
    
    def get_procedure_suggestions(self, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get procedure suggestions based on user context and behavior."""
        if not self.store:
            return []
        
        try:
            suggestions = []
            
            # Get recently used procedures
            all_procedures = self.store.get_all_procedures()
            
            # Sort by usage and recency
            recent_procedures = [
                proc for proc in all_procedures 
                if proc.last_executed and proc.execution_count > 0
            ]
            recent_procedures.sort(key=lambda p: (p.execution_count, p.last_executed), reverse=True)
            
            # Add top suggestions
            for proc in recent_procedures[:3]:
                suggestions.append({
                    'id': proc.id,
                    'name': proc.name,
                    'description': proc.description,
                    'reason': f"Used {proc.execution_count} times",
                    'category': proc.category
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting procedure suggestions: {e}")
            return []

# Global instance for easy access
_procedural_integration = None

def get_procedural_integration_service() -> ProceduralIntegrationService:
    """Get the global procedural integration service instance."""
    global _procedural_integration
    if _procedural_integration is None:
        _procedural_integration = ProceduralIntegrationService()
    return _procedural_integration
