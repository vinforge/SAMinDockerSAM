"""
Knowledge Enrichment Engine for Procedural Memory
=================================================

Advanced system that enriches procedure steps with contextual information
from SAM's knowledge base, providing dynamic context injection and
intelligent step enhancement.

Features:
- Dynamic context injection from knowledge base
- Step-specific information enrichment
- Real-time parameter resolution
- Integration with SAM's memory systems
- Intelligent content suggestions

Author: SAM Development Team
Version: 2.0.0 (Phase 3 - Advanced Cognitive Features)
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeEnrichmentEngine:
    """Engine for enriching procedures with contextual knowledge."""
    
    def __init__(self):
        """Initialize the knowledge enrichment engine."""
        self.memory_store = None
        self.llm_client = None
        self.enrichment_cache = {}
        
        self._init_components()
        
        logger.info("Knowledge Enrichment Engine initialized")
    
    def _init_components(self):
        """Initialize required components."""
        try:
            # Initialize memory store
            from memory.memory_vectorstore import get_memory_store
            self.memory_store = get_memory_store()
            
            # Initialize LLM client
            from sam.core.sam_model_client import get_sam_model_client
            self.llm_client = get_sam_model_client()
            
            logger.info("Knowledge enrichment components initialized")
        except Exception as e:
            logger.warning(f"Some knowledge enrichment components not available: {e}")
    
    def enrich_procedure(self, procedure, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enrich a procedure with contextual knowledge and dynamic information.
        
        Args:
            procedure: The procedure object to enrich
            user_context: Additional context about the user and environment
            
        Returns:
            Dictionary containing enriched procedure data and metadata
        """
        try:
            enriched_data = {
                'original_procedure': procedure,
                'enriched_steps': [],
                'dynamic_parameters': {},
                'contextual_information': {},
                'enrichment_metadata': {
                    'enriched_at': datetime.now(),
                    'enrichment_version': '2.0.0',
                    'user_context': user_context or {}
                }
            }
            
            # Enrich each step
            for step in procedure.steps:
                enriched_step = self._enrich_step(step, procedure, user_context)
                enriched_data['enriched_steps'].append(enriched_step)
            
            # Resolve dynamic parameters
            enriched_data['dynamic_parameters'] = self._resolve_dynamic_parameters(
                procedure.parameters, user_context
            )
            
            # Add contextual information
            enriched_data['contextual_information'] = self._gather_contextual_information(
                procedure, user_context
            )
            
            logger.info(f"Enriched procedure: {procedure.name}")
            return enriched_data
            
        except Exception as e:
            logger.error(f"Failed to enrich procedure: {e}")
            return {'original_procedure': procedure, 'enrichment_error': str(e)}
    
    def _enrich_step(self, step, procedure, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enrich a single procedure step with contextual information."""
        try:
            enriched_step = {
                'original_step': step,
                'enhanced_description': step.description,
                'enhanced_details': step.details or "",
                'contextual_notes': [],
                'related_information': [],
                'dynamic_content': {},
                'enrichment_confidence': 0.0
            }
            
            # Extract entities and concepts from step
            entities = self._extract_entities(step.description, step.details)
            
            # Enrich with knowledge base information
            for entity in entities:
                knowledge = self._lookup_knowledge(entity, procedure.category)
                if knowledge:
                    enriched_step['related_information'].append(knowledge)
            
            # Add dynamic content based on context
            dynamic_content = self._generate_dynamic_content(step, user_context)
            if dynamic_content:
                enriched_step['dynamic_content'] = dynamic_content
            
            # Enhance step description with context
            enhanced_description = self._enhance_step_description(
                step, entities, enriched_step['related_information']
            )
            if enhanced_description != step.description:
                enriched_step['enhanced_description'] = enhanced_description
                enriched_step['enrichment_confidence'] = 0.8
            
            # Add contextual notes
            contextual_notes = self._generate_contextual_notes(step, procedure, user_context)
            enriched_step['contextual_notes'] = contextual_notes
            
            return enriched_step
            
        except Exception as e:
            logger.error(f"Failed to enrich step: {e}")
            return {'original_step': step, 'enrichment_error': str(e)}
    
    def _extract_entities(self, description: str, details: str = None) -> List[str]:
        """Extract entities and concepts from step text."""
        try:
            text = f"{description} {details or ''}"
            
            # Simple entity extraction patterns
            entities = []
            
            # File paths
            file_patterns = [
                r'/[a-zA-Z0-9_/.-]+',  # Unix paths
                r'[A-Z]:\\[a-zA-Z0-9_\\.-]+',  # Windows paths
                r'[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,4}'  # Files with extensions
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, text)
                entities.extend(matches)
            
            # Email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            entities.extend(emails)
            
            # URLs
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, text)
            entities.extend(urls)
            
            # Commands (words starting with specific prefixes)
            command_patterns = [
                r'\b(mysql|git|npm|pip|docker|kubectl)\s+[a-zA-Z-]+',
                r'\b[a-zA-Z]+\s*-[a-zA-Z]+'  # Command line flags
            ]
            
            for pattern in command_patterns:
                matches = re.findall(pattern, text)
                entities.extend(matches)
            
            # Technical terms (capitalized words, acronyms)
            tech_pattern = r'\b[A-Z]{2,}[A-Z0-9]*\b'  # Acronyms like SQL, API, etc.
            tech_terms = re.findall(tech_pattern, text)
            entities.extend(tech_terms)
            
            # Remove duplicates and filter
            unique_entities = list(set(entities))
            filtered_entities = [e for e in unique_entities if len(e) > 2]
            
            return filtered_entities[:10]  # Limit to top 10 entities
            
        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            return []
    
    def _lookup_knowledge(self, entity: str, category: str = None) -> Optional[Dict[str, Any]]:
        """Look up information about an entity in the knowledge base."""
        try:
            if not self.memory_store:
                return None
            
            # Check cache first
            cache_key = f"{entity}_{category}"
            if cache_key in self.enrichment_cache:
                return self.enrichment_cache[cache_key]
            
            # Search memory store for relevant information
            search_results = self.memory_store.search_memories(entity, limit=3)
            
            if search_results:
                knowledge = {
                    'entity': entity,
                    'type': self._classify_entity_type(entity),
                    'information': [],
                    'confidence': 0.7
                }
                
                for memory in search_results:
                    if hasattr(memory, 'content') and entity.lower() in memory.content.lower():
                        knowledge['information'].append({
                            'content': memory.content[:200] + "..." if len(memory.content) > 200 else memory.content,
                            'source': getattr(memory, 'source', 'knowledge_base'),
                            'relevance': 0.8
                        })
                
                if knowledge['information']:
                    # Cache the result
                    self.enrichment_cache[cache_key] = knowledge
                    return knowledge
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to lookup knowledge for {entity}: {e}")
            return None
    
    def _classify_entity_type(self, entity: str) -> str:
        """Classify the type of an entity."""
        if '@' in entity:
            return 'email'
        elif entity.startswith(('http://', 'https://')):
            return 'url'
        elif '/' in entity or '\\' in entity or '.' in entity:
            return 'file_path'
        elif entity.isupper() and len(entity) > 1:
            return 'acronym'
        elif any(cmd in entity.lower() for cmd in ['mysql', 'git', 'npm', 'docker']):
            return 'command'
        else:
            return 'concept'
    
    def _generate_dynamic_content(self, step, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate dynamic content based on user context."""
        try:
            dynamic_content = {}
            
            if not user_context:
                return dynamic_content
            
            # Add environment-specific information
            if user_context.get('operating_system'):
                os_info = user_context['operating_system']
                if 'windows' in os_info.lower():
                    dynamic_content['os_specific_note'] = "Note: On Windows, use backslashes (\\) for file paths"
                elif 'mac' in os_info.lower() or 'darwin' in os_info.lower():
                    dynamic_content['os_specific_note'] = "Note: On macOS, use forward slashes (/) for file paths"
                elif 'linux' in os_info.lower():
                    dynamic_content['os_specific_note'] = "Note: On Linux, use forward slashes (/) for file paths"
            
            # Add time-sensitive information
            current_time = datetime.now()
            if 'backup' in step.description.lower():
                dynamic_content['timestamp_suggestion'] = f"Suggested timestamp: {current_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Add user-specific customizations
            if user_context.get('user_preferences'):
                prefs = user_context['user_preferences']
                if prefs.get('default_editor'):
                    dynamic_content['editor_suggestion'] = f"Use your preferred editor: {prefs['default_editor']}"
            
            return dynamic_content
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic content: {e}")
            return {}
    
    def _enhance_step_description(self, step, entities: List[str], related_info: List[Dict]) -> str:
        """Enhance step description with contextual information."""
        try:
            enhanced = step.description
            
            # Add clarifications for technical terms
            for entity in entities:
                if self._classify_entity_type(entity) == 'acronym':
                    # Find related information for this entity
                    for info in related_info:
                        if info['entity'] == entity and info['information']:
                            # Add a brief explanation
                            explanation = info['information'][0]['content'][:50] + "..."
                            enhanced = enhanced.replace(entity, f"{entity} ({explanation})")
                            break
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Failed to enhance step description: {e}")
            return step.description
    
    def _generate_contextual_notes(self, step, procedure, user_context: Dict[str, Any] = None) -> List[str]:
        """Generate contextual notes for a step."""
        try:
            notes = []
            
            # Add safety warnings for potentially dangerous operations
            dangerous_keywords = ['delete', 'remove', 'drop', 'truncate', 'format', 'rm -rf']
            if any(keyword in step.description.lower() for keyword in dangerous_keywords):
                notes.append("⚠️ Warning: This operation is potentially destructive. Make sure you have backups.")
            
            # Add performance notes
            if 'backup' in step.description.lower():
                notes.append("💡 Tip: Large backups may take significant time. Consider running during off-peak hours.")
            
            # Add security notes
            if 'password' in step.description.lower() or 'credential' in step.description.lower():
                notes.append("🔒 Security: Never share credentials or store them in plain text.")
            
            # Add efficiency tips
            if 'manual' in step.description.lower():
                notes.append("🚀 Optimization: Consider automating this step for future executions.")
            
            return notes
            
        except Exception as e:
            logger.error(f"Failed to generate contextual notes: {e}")
            return []
    
    def _resolve_dynamic_parameters(self, parameters: Dict[str, str], 
                                   user_context: Dict[str, Any] = None) -> Dict[str, str]:
        """Resolve dynamic parameters with current context."""
        try:
            resolved = parameters.copy()
            
            if not user_context:
                return resolved
            
            # Resolve time-based parameters
            current_time = datetime.now()
            time_replacements = {
                '$(date +%Y%m%d)': current_time.strftime('%Y%m%d'),
                '$(date +%Y-%m-%d)': current_time.strftime('%Y-%m-%d'),
                '$(date +%H%M%S)': current_time.strftime('%H%M%S'),
                '{current_date}': current_time.strftime('%Y-%m-%d'),
                '{current_time}': current_time.strftime('%H:%M:%S'),
                '{timestamp}': current_time.strftime('%Y%m%d_%H%M%S')
            }
            
            for param_key, param_value in resolved.items():
                for pattern, replacement in time_replacements.items():
                    if pattern in param_value:
                        resolved[param_key] = param_value.replace(pattern, replacement)
            
            # Resolve user-specific parameters
            if user_context.get('user_info'):
                user_info = user_context['user_info']
                user_replacements = {
                    '{user_name}': user_info.get('name', 'user'),
                    '{user_email}': user_info.get('email', 'user@example.com'),
                    '{user_id}': user_info.get('id', 'default')
                }
                
                for param_key, param_value in resolved.items():
                    for pattern, replacement in user_replacements.items():
                        if pattern in param_value:
                            resolved[param_key] = param_value.replace(pattern, replacement)
            
            return resolved
            
        except Exception as e:
            logger.error(f"Failed to resolve dynamic parameters: {e}")
            return parameters
    
    def _gather_contextual_information(self, procedure, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gather additional contextual information for the procedure."""
        try:
            context_info = {
                'related_procedures': [],
                'prerequisites_check': [],
                'environment_notes': [],
                'optimization_suggestions': []
            }
            
            # Find related procedures
            if self.memory_store:
                try:
                    from sam.memory.procedural_memory import get_procedural_memory_store
                    proc_store = get_procedural_memory_store()
                    
                    # Search for procedures with similar tags
                    for tag in procedure.tags:
                        related = proc_store.search_procedures(tag)
                        for related_proc, score in related[:3]:  # Top 3 related
                            if related_proc.id != procedure.id:
                                context_info['related_procedures'].append({
                                    'name': related_proc.name,
                                    'relevance': score,
                                    'category': related_proc.category
                                })
                except Exception as e:
                    logger.debug(f"Could not find related procedures: {e}")
            
            # Add environment-specific notes
            if user_context and user_context.get('environment'):
                env = user_context['environment']
                if env.get('is_production'):
                    context_info['environment_notes'].append(
                        "🏭 Production Environment: Extra caution required"
                    )
                if env.get('has_monitoring'):
                    context_info['environment_notes'].append(
                        "📊 Monitoring Available: Check dashboards during execution"
                    )
            
            # Add optimization suggestions
            if procedure.execution_count > 5:
                context_info['optimization_suggestions'].append(
                    "🔄 Frequently Used: Consider creating shortcuts or automation"
                )
            
            return context_info
            
        except Exception as e:
            logger.error(f"Failed to gather contextual information: {e}")
            return {}

# Global instance for easy access
_knowledge_enrichment_engine = None

def get_knowledge_enrichment_engine() -> KnowledgeEnrichmentEngine:
    """Get the global knowledge enrichment engine instance."""
    global _knowledge_enrichment_engine
    if _knowledge_enrichment_engine is None:
        _knowledge_enrichment_engine = KnowledgeEnrichmentEngine()
    return _knowledge_enrichment_engine
