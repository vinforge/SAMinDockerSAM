"""
Procedural Chat Handler for SAM
===============================

Handles procedural memory integration in SAM's chat interface, providing
intelligent routing and context injection for "how-to" queries.

Features:
- Automatic detection of procedural queries
- Context injection with relevant procedures
- Execution tracking and follow-up suggestions
- Seamless integration with existing chat flow

Author: SAM Development Team
Version: 2.0.0
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ProceduralChatHandler:
    """Handles procedural memory integration in SAM's chat interface."""
    
    def __init__(self):
        """Initialize the procedural chat handler."""
        self.meta_router = None
        self.integration_service = None
        self.execution_tracker = None
        self.suggestion_engine = None
        self.knowledge_enrichment = None
        self.chat_history = []

        self._init_components()

        logger.info("Procedural Chat Handler initialized with Phase 3 features")
    
    def _init_components(self):
        """Initialize required components."""
        try:
            from sam.cognition.meta_router import get_meta_router
            from sam.memory.procedural_integration import get_procedural_integration_service
            from sam.memory.execution_tracker import get_execution_tracker
            from sam.cognition.proactive_suggestions import get_proactive_suggestion_engine
            from sam.memory.knowledge_enrichment import get_knowledge_enrichment_engine

            self.meta_router = get_meta_router()
            self.integration_service = get_procedural_integration_service()
            self.execution_tracker = get_execution_tracker()
            self.suggestion_engine = get_proactive_suggestion_engine()
            self.knowledge_enrichment = get_knowledge_enrichment_engine()

            logger.info("Procedural chat components initialized with Phase 3 features")
        except Exception as e:
            logger.error(f"Failed to initialize procedural chat components: {e}")
    
    def process_user_query(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query with procedural memory integration.
        
        Args:
            query: The user's query text
            user_context: Additional context about the user and session
            
        Returns:
            Dictionary containing routing decision, context, and response guidance
        """
        if not self.meta_router or not self.integration_service:
            logger.warning("Procedural components not available")
            return self._fallback_response(query)
        
        try:
            # Phase 3: Record user action for pattern analysis
            if self.suggestion_engine:
                self.suggestion_engine.record_user_action(
                    action_type="query",
                    content=query,
                    context=user_context or {},
                    session_id=user_context.get('session_id', 'default') if user_context else 'default'
                )

            # Step 1: Route the query using Meta-Router
            routing_decision = self.meta_router.route_query(query, user_context)

            # Step 2: Handle based on routing decision
            if routing_decision.suggested_action == "search_procedural_memory":
                return self._handle_procedural_query(query, routing_decision, user_context)
            elif routing_decision.suggested_action == "search_knowledge_base":
                return self._handle_factual_query(query, routing_decision, user_context)
            else:
                return self._handle_general_chat(query, routing_decision, user_context)

        except Exception as e:
            logger.error(f"Error processing user query: {e}")
            return self._fallback_response(query)
    
    def _handle_procedural_query(self, query: str, routing_decision, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle queries that require procedural memory search."""
        logger.info(f"Handling procedural query: {query}")
        
        # Search for relevant procedures
        procedural_context = self.integration_service.search_and_format_procedures(query, user_context)

        if procedural_context:
            # Phase 3: Enhance procedures with knowledge enrichment
            enhanced_context = procedural_context
            if self.knowledge_enrichment:
                try:
                    # Get the procedure for enrichment
                    from sam.memory.procedural_memory import get_procedural_memory_store
                    store = get_procedural_memory_store()
                    search_results = store.search_procedures(query)

                    if search_results:
                        procedure, _ = search_results[0]
                        enriched_data = self.knowledge_enrichment.enrich_procedure(procedure, user_context)

                        # Add enrichment information to context
                        if enriched_data.get('contextual_information'):
                            enhanced_context += "\n\n## 🧠 Enhanced Context\n"
                            context_info = enriched_data['contextual_information']

                            if context_info.get('related_procedures'):
                                enhanced_context += "\n**Related Procedures:**\n"
                                for related in context_info['related_procedures'][:3]:
                                    enhanced_context += f"• {related['name']} (Category: {related['category']})\n"

                            if context_info.get('environment_notes'):
                                enhanced_context += "\n**Environment Notes:**\n"
                                for note in context_info['environment_notes']:
                                    enhanced_context += f"• {note}\n"

                except Exception as e:
                    logger.debug(f"Knowledge enrichment failed: {e}")

            # Procedures found - inject into LLM context
            response_data = {
                'routing_decision': routing_decision,
                'has_procedural_context': True,
                'procedural_context': enhanced_context,
                'response_type': 'procedural_guidance',
                'suggested_prompt_enhancement': self._build_procedural_prompt_enhancement(query, enhanced_context),
                'follow_up_actions': [
                    'offer_execution_tracking',
                    'suggest_procedure_customization',
                    'ask_for_clarification'
                ]
            }
            
            # Track the interaction
            self._track_procedural_interaction(query, routing_decision, True)
            
        else:
            # No procedures found - suggest creation or general help
            response_data = {
                'routing_decision': routing_decision,
                'has_procedural_context': False,
                'response_type': 'procedural_not_found',
                'suggested_response': self._build_no_procedures_response(query),
                'follow_up_actions': [
                    'offer_procedure_creation',
                    'search_general_knowledge',
                    'ask_for_more_details'
                ]
            }
            
            # Track the interaction
            self._track_procedural_interaction(query, routing_decision, False)
        
        return response_data
    
    def _handle_factual_query(self, query: str, routing_decision, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle queries that require factual knowledge search."""
        logger.info(f"Handling factual query: {query}")
        
        return {
            'routing_decision': routing_decision,
            'response_type': 'factual_search',
            'suggested_action': 'search_knowledge_base',
            'enhancement_note': 'Route to standard knowledge retrieval system',
            'follow_up_actions': [
                'provide_factual_answer',
                'offer_related_procedures'
            ]
        }
    
    def _handle_general_chat(self, query: str, routing_decision, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle general conversational queries."""
        logger.info(f"Handling general chat: {query}")

        # Check if we should offer procedural suggestions
        suggestions = self.integration_service.get_procedure_suggestions(user_context or {})

        # Phase 3: Add proactive suggestions
        proactive_suggestions = []
        if self.suggestion_engine:
            try:
                proactive_suggestions = self.suggestion_engine.get_active_suggestions()
            except Exception as e:
                logger.debug(f"Failed to get proactive suggestions: {e}")

        # Phase 3: Check for active executions
        active_executions = []
        if self.execution_tracker:
            try:
                user_id = user_context.get('user_id', 'default') if user_context else 'default'
                active_executions = self.execution_tracker.get_user_active_executions(user_id)
            except Exception as e:
                logger.debug(f"Failed to get active executions: {e}")

        return {
            'routing_decision': routing_decision,
            'response_type': 'general_chat',
            'suggested_action': 'engage_conversationally',
            'procedure_suggestions': suggestions,
            'proactive_suggestions': proactive_suggestions,
            'active_executions': active_executions,
            'follow_up_actions': [
                'engage_naturally',
                'offer_help_options',
                'show_proactive_suggestions' if proactive_suggestions else None,
                'show_execution_status' if active_executions else None
            ]
        }
    
    def _build_procedural_prompt_enhancement(self, query: str, procedural_context: str) -> str:
        """Build enhanced prompt for LLM with procedural context."""
        enhancement = f"""
PROCEDURAL MEMORY CONTEXT:
{procedural_context}

INSTRUCTIONS FOR RESPONSE:
- Use the procedural information above to provide step-by-step guidance
- Adapt the procedure to the user's specific situation if needed
- Explain each step clearly and mention expected outcomes
- If parameters are mentioned (like {{email_recipient}}), ask the user for their specific values
- Offer to track their progress through the procedure
- Be encouraging and supportive throughout the process

USER QUERY: {query}

Please provide a helpful response using the procedural information above.
"""
        return enhancement
    
    def _build_no_procedures_response(self, query: str) -> str:
        """Build response when no procedures are found."""
        return f"""I understand you're asking about "{query}", but I don't have a specific procedure for that in my procedural memory.

Here's how I can help:

1. **Create a New Procedure**: I can help you create a step-by-step procedure for this task that we can save for future use.

2. **General Guidance**: I can provide general advice and information about this topic using my knowledge base.

3. **Search Existing Procedures**: Let me check if there are related procedures that might be helpful.

Would you like me to help you create a procedure for this task, or would you prefer general guidance?"""
    
    def _track_procedural_interaction(self, query: str, routing_decision, found_procedures: bool):
        """Track procedural interactions for analytics."""
        try:
            interaction_data = {
                'timestamp': datetime.now(),
                'query': query,
                'intent': routing_decision.intent.value,
                'confidence': routing_decision.confidence,
                'found_procedures': found_procedures,
                'classification_method': routing_decision.metadata.get('classification_method', 'unknown')
            }
            
            # Add to chat history for context
            self.chat_history.append(interaction_data)
            
            # Keep only recent history (last 10 interactions)
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            logger.info(f"Tracked procedural interaction: {interaction_data}")
            
        except Exception as e:
            logger.error(f"Failed to track procedural interaction: {e}")
    
    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """Fallback response when procedural components are unavailable."""
        return {
            'routing_decision': None,
            'response_type': 'fallback',
            'suggested_action': 'engage_general_chat',
            'enhancement_note': 'Procedural memory not available - using standard chat',
            'follow_up_actions': ['engage_naturally']
        }
    
    def handle_procedure_execution_request(self, procedure_id: str, user_parameters: Dict[str, str] = None) -> Dict[str, Any]:
        """Handle user request to execute a specific procedure."""
        try:
            if not self.integration_service:
                return {'success': False, 'error': 'Procedural integration not available'}
            
            # Render procedure with user parameters
            if user_parameters:
                formatted_procedure = self.integration_service.render_procedure_with_parameters(
                    procedure_id, user_parameters
                )
            else:
                # Get the procedure and format it
                from sam.memory.procedural_memory import get_procedural_memory_store
                store = get_procedural_memory_store()
                procedure = store.get_procedure(procedure_id)
                
                if not procedure:
                    return {'success': False, 'error': 'Procedure not found'}
                
                formatted_procedure = self.integration_service._format_single_procedure(procedure, 1.0)
            
            if not formatted_procedure:
                return {'success': False, 'error': 'Failed to format procedure'}
            
            # Record execution
            from sam.memory.procedural_memory import get_procedural_memory_store
            store = get_procedural_memory_store()
            store.record_procedure_execution(procedure_id)
            
            return {
                'success': True,
                'formatted_procedure': formatted_procedure,
                'execution_tracked': True,
                'follow_up_actions': [
                    'provide_step_by_step_guidance',
                    'offer_progress_tracking',
                    'ask_for_feedback'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling procedure execution request: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_chat_context_for_llm(self) -> Dict[str, Any]:
        """Get chat context information for LLM enhancement."""
        try:
            context = {
                'has_procedural_memory': True,
                'recent_interactions': len(self.chat_history),
                'procedural_queries_count': sum(
                    1 for interaction in self.chat_history 
                    if interaction.get('intent') == 'procedural_request'
                )
            }
            
            # Add recent procedure usage
            if self.chat_history:
                recent_procedural = [
                    interaction for interaction in self.chat_history[-5:]
                    if interaction.get('intent') == 'procedural_request' and interaction.get('found_procedures')
                ]
                context['recent_procedural_success'] = len(recent_procedural)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting chat context: {e}")
            return {'has_procedural_memory': False}

# Global instance for easy access
_procedural_chat_handler = None

def get_procedural_chat_handler() -> ProceduralChatHandler:
    """Get the global procedural chat handler instance."""
    global _procedural_chat_handler
    if _procedural_chat_handler is None:
        _procedural_chat_handler = ProceduralChatHandler()
    return _procedural_chat_handler
