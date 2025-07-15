"""
SAM Meta-Router with LLM-Powered Query Classification
====================================================

Intelligent query routing system that determines whether user queries should be
directed to procedural memory, factual knowledge, or general chat capabilities.

Features:
- LLM-powered query classification for robust intent detection
- Context-aware routing decisions
- Integration with SAM's cognitive architecture
- Fallback mechanisms for reliable operation

Author: SAM Development Team
Version: 2.0.0 (Enhanced with Procedural Memory)
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Enumeration of possible query intents."""
    PROCEDURAL_REQUEST = "procedural_request"  # How-to questions, workflow requests
    FACTUAL_QUESTION = "factual_question"     # Information retrieval
    GENERAL_CHAT = "general_chat"             # Conversational interaction
    UNKNOWN = "unknown"                       # Unable to classify

class QueryComplexity(Enum):
    """Enumeration of query complexity levels for routing decisions."""
    SIMPLE = "simple"          # Fast path: Direct tool use, minimal processing
    MODERATE = "moderate"      # Standard path: Normal confidence assessment
    COMPLEX = "complex"        # Full path: Complete reasoning pipeline

@dataclass
class RoutingDecision:
    """Result of query routing analysis."""
    intent: QueryIntent
    complexity: QueryComplexity
    confidence: float
    reasoning: str
    suggested_action: str
    metadata: Dict[str, Any]
    fast_path_eligible: bool = False

class MetaRouter:
    """Enhanced Meta-Router with LLM-powered query classification."""
    
    def __init__(self):
        """Initialize the Meta-Router with LLM integration."""
        self.llm_client = None
        self.fallback_patterns = self._init_fallback_patterns()
        self._init_llm_client()
        
        logger.info("Meta-Router initialized with LLM classification")
    
    def _init_llm_client(self):
        """Initialize LLM client for query classification."""
        try:
            from sam.core.sam_model_client import get_sam_model_client
            self.llm_client = get_sam_model_client()
            logger.info("LLM client initialized for Meta-Router")
        except Exception as e:
            logger.warning(f"LLM client not available for Meta-Router: {e}")
            self.llm_client = None
    
    def _init_fallback_patterns(self) -> Dict[str, list]:
        """Initialize fallback keyword patterns for when LLM is unavailable."""
        return {
            'procedural_indicators': [
                r'how (do|can) i',
                r'steps? (to|for)',
                r'workflow (for|to)',
                r'procedure (for|to)',
                r'guide (for|to)',
                r'process (for|to)',
                r'checklist (for|to)',
                r'walk me through',
                r'show me how',
                r'teach me',
                r'instructions for'
            ],
            'factual_indicators': [
                r'what is',
                r'who is',
                r'when did',
                r'where is',
                r'why does',
                r'define',
                r'explain',
                r'tell me about',
                r'information about'
            ]
        }

    def _init_complexity_patterns(self) -> Dict[str, list]:
        """Initialize patterns for query complexity classification."""
        return {
            'simple_factual': [
                r'\bwhat\s+is\s+the\s+(latest|current|price|stock|weather)\b',
                r'\b(latest|current|today\'?s)\s+(price|stock|weather|news)\b',
                r'\bstock\s+price\s+for\b', r'\bweather\s+in\b',
                r'\btime\s+in\b', r'\bdate\s+today\b', r'\bcurrent\s+time\b'
            ],
            'simple_temporal': [
                r'\b(latest|current|recent|today|now)\s+\w+\b',
                r'\bwhat\'?s\s+the\s+(latest|current)\b',
                r'\btoday\'?s\s+\w+\b', r'\brecent\s+\w+\b'
            ],
            'simple_lookup': [
                r'\bwhat\s+is\s+\w+\b', r'\bwho\s+is\s+\w+\b',
                r'\bdefine\s+\w+\b', r'\bmeaning\s+of\s+\w+\b'
            ],
            'complex_analytical': [
                r'\banalyze\b', r'\bcompare\b', r'\bevaluate\b', r'\bassess\b',
                r'\bexamine\b', r'\binvestigate\b', r'\bstrategic\b', r'\bimplications\b',
                r'\bpros\s+and\s+cons\b', r'\badvantages\s+and\s+disadvantages\b',
                r'\bimpact\s+of\b', r'\beffects\s+of\b'
            ],
            'complex_creative': [
                r'\bwrite\s+a\b', r'\bcreate\s+a\b', r'\bgenerate\s+a\b',
                r'\bbrainstorm\b', r'\bdesign\s+a\b', r'\bdevelop\s+a\b',
                r'\bplan\s+for\b', r'\bstrategy\s+for\b'
            ],
            'complex_procedural': [
                r'\bhow\s+to\s+\w+\s+\w+\s+\w+', # Multi-word how-to (complex)
                r'\bstep\s+by\s+step\s+guide\b', r'\bdetailed\s+instructions\b',
                r'\bcomplete\s+process\b', r'\bfull\s+workflow\b'
            ]
        }

    def classify_query_complexity(self, query: str, intent: QueryIntent = None) -> QueryComplexity:
        """
        Classify query complexity to determine processing path.

        Args:
            query: The user's query text
            intent: Optional pre-classified intent

        Returns:
            QueryComplexity level for routing decisions
        """
        query_lower = query.lower()
        complexity_patterns = self._init_complexity_patterns()

        # Check for simple patterns first (fast path candidates)
        simple_indicators = 0
        for pattern_type in ['simple_factual', 'simple_temporal', 'simple_lookup']:
            for pattern in complexity_patterns[pattern_type]:
                if re.search(pattern, query_lower):
                    simple_indicators += 1

        # Check for complex patterns
        complex_indicators = 0
        for pattern_type in ['complex_analytical', 'complex_creative', 'complex_procedural']:
            for pattern in complexity_patterns[pattern_type]:
                if re.search(pattern, query_lower):
                    complex_indicators += 1

        # Additional complexity factors
        word_count = len(query.split())
        has_multiple_questions = query.count('?') > 1
        has_conjunctions = any(word in query_lower for word in ['and', 'but', 'however', 'also', 'additionally'])

        # Classification logic
        if complex_indicators > 0:
            return QueryComplexity.COMPLEX
        elif simple_indicators > 0 and word_count <= 10 and not has_multiple_questions:
            return QueryComplexity.SIMPLE
        elif word_count > 20 or has_multiple_questions or has_conjunctions:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.MODERATE

    def route_query(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """
        Route a user query to the appropriate SAM subsystem.
        
        Args:
            query: The user's query text
            context: Optional context information (user history, current session, etc.)
            
        Returns:
            RoutingDecision with intent classification and routing information
        """
        if not query or not query.strip():
            return RoutingDecision(
                intent=QueryIntent.GENERAL_CHAT,
                complexity=QueryComplexity.SIMPLE,
                confidence=1.0,
                reasoning="Empty query defaults to general chat",
                suggested_action="engage_general_chat",
                metadata={},
                fast_path_eligible=True
            )
        
        # Try LLM classification first
        if self.llm_client:
            try:
                return self._llm_classify_query(query, context)
            except Exception as e:
                logger.warning(f"LLM classification failed, using fallback: {e}")
        
        # Fallback to pattern-based classification
        return self._fallback_classify_query(query, context)
    
    def _llm_classify_query(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """Use LLM to classify query intent with high accuracy."""
        
        # Prepare classification prompt
        classification_prompt = self._build_classification_prompt(query, context)
        
        try:
            # Call LLM for classification
            response = self.llm_client.generate(
                prompt=classification_prompt,
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent classification
                stop_sequences=["```", "---"]
            )
            
            # Parse LLM response
            classification_result = self._parse_llm_response(response)
            
            # Validate and enhance result
            return self._validate_classification_result(classification_result, query)
            
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            raise
    
    def _build_classification_prompt(self, query: str, context: Dict[str, Any] = None) -> str:
        """Build the classification prompt for the LLM."""
        
        context_info = ""
        if context:
            if context.get('has_procedures'):
                context_info += f"- User has {context.get('procedure_count', 0)} stored procedures\n"
            if context.get('recent_procedures'):
                recent = ", ".join(context['recent_procedures'][:3])
                context_info += f"- Recently used procedures: {recent}\n"
        
        prompt = f"""You are SAM's query classification system. Analyze the user's query and classify its primary intent.

QUERY: "{query}"

CONTEXT:
{context_info if context_info else "- No additional context available"}

CLASSIFICATION TASK:
Determine the user's primary intent from these categories:

1. **procedural_request**: User wants to know HOW to do something, asking for step-by-step instructions, workflows, or procedures
   - Examples: "How do I backup the database?", "Steps to deploy code", "Walk me through the sales report process"

2. **factual_question**: User wants to know WHAT something is, seeking information, facts, or explanations
   - Examples: "What is Docker?", "Who is the project manager?", "When was this feature released?"

3. **general_chat**: User wants to have a conversation, get help, or discuss something casually
   - Examples: "Hello", "How are you?", "Can you help me?", "Thanks for the information"

RESPONSE FORMAT (JSON only):
{{
    "intent": "procedural_request|factual_question|general_chat",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this classification was chosen",
    "keywords": ["key", "words", "that", "influenced", "decision"]
}}

Respond with JSON only:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM's JSON response."""
        try:
            # Clean the response
            response = response.strip()
            
            # Find JSON content
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['intent', 'confidence', 'reasoning']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field: {field}")
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response}")
            raise
    
    def _validate_classification_result(self, result: Dict[str, Any], query: str) -> RoutingDecision:
        """Validate and enhance the LLM classification result."""
        
        # Map intent string to enum
        intent_mapping = {
            'procedural_request': QueryIntent.PROCEDURAL_REQUEST,
            'factual_question': QueryIntent.FACTUAL_QUESTION,
            'general_chat': QueryIntent.GENERAL_CHAT
        }
        
        intent_str = result.get('intent', 'unknown')
        intent = intent_mapping.get(intent_str, QueryIntent.UNKNOWN)
        
        # Validate confidence
        confidence = float(result.get('confidence', 0.0))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        # Determine suggested action
        action_mapping = {
            QueryIntent.PROCEDURAL_REQUEST: "search_procedural_memory",
            QueryIntent.FACTUAL_QUESTION: "search_knowledge_base",
            QueryIntent.GENERAL_CHAT: "engage_general_chat",
            QueryIntent.UNKNOWN: "engage_general_chat"
        }
        
        suggested_action = action_mapping[intent]

        # Classify query complexity
        complexity = self.classify_query_complexity(query, intent)

        # Determine if eligible for fast path
        fast_path_eligible = (
            complexity == QueryComplexity.SIMPLE and
            intent == QueryIntent.FACTUAL_QUESTION and
            confidence > 0.7
        )

        # Enhance suggested action based on complexity
        if fast_path_eligible:
            suggested_action = "fast_path_" + suggested_action

        # Build metadata
        metadata = {
            'classification_method': 'llm',
            'keywords': result.get('keywords', []),
            'query_length': len(query),
            'complexity_level': complexity.value,
            'fast_path_eligible': fast_path_eligible,
            'llm_raw_response': result
        }

        return RoutingDecision(
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            reasoning=result.get('reasoning', 'LLM classification'),
            suggested_action=suggested_action,
            metadata=metadata,
            fast_path_eligible=fast_path_eligible
        )
    
    def _fallback_classify_query(self, query: str, context: Dict[str, Any] = None) -> RoutingDecision:
        """Fallback pattern-based classification when LLM is unavailable."""
        import re
        
        query_lower = query.lower()
        
        # Check for procedural patterns
        procedural_score = 0
        for pattern in self.fallback_patterns['procedural_indicators']:
            if re.search(pattern, query_lower):
                procedural_score += 1
        
        # Check for factual patterns
        factual_score = 0
        for pattern in self.fallback_patterns['factual_indicators']:
            if re.search(pattern, query_lower):
                factual_score += 1
        
        # Determine intent based on scores
        if procedural_score > factual_score and procedural_score > 0:
            intent = QueryIntent.PROCEDURAL_REQUEST
            confidence = min(0.8, 0.5 + (procedural_score * 0.1))
            reasoning = f"Pattern-based: Found {procedural_score} procedural indicators"
            action = "search_procedural_memory"
        elif factual_score > 0:
            intent = QueryIntent.FACTUAL_QUESTION
            confidence = min(0.8, 0.5 + (factual_score * 0.1))
            reasoning = f"Pattern-based: Found {factual_score} factual indicators"
            action = "search_knowledge_base"
        else:
            intent = QueryIntent.GENERAL_CHAT
            confidence = 0.6
            reasoning = "Pattern-based: No specific indicators found, defaulting to general chat"
            action = "engage_general_chat"
        
        # Classify query complexity
        complexity = self.classify_query_complexity(query, intent)

        # Determine if eligible for fast path
        fast_path_eligible = (
            complexity == QueryComplexity.SIMPLE and
            intent == QueryIntent.FACTUAL_QUESTION and
            confidence > 0.6
        )

        # Enhance suggested action based on complexity
        if fast_path_eligible:
            action = "fast_path_" + action

        metadata = {
            'classification_method': 'pattern_fallback',
            'procedural_score': procedural_score,
            'factual_score': factual_score,
            'query_length': len(query),
            'complexity_level': complexity.value,
            'fast_path_eligible': fast_path_eligible
        }

        return RoutingDecision(
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            reasoning=reasoning,
            suggested_action=action,
            metadata=metadata,
            fast_path_eligible=fast_path_eligible
        )
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions (for analytics)."""
        # This would be enhanced with actual tracking in a production system
        return {
            'total_queries_routed': 0,
            'intent_distribution': {
                'procedural_request': 0,
                'factual_question': 0,
                'general_chat': 0,
                'unknown': 0
            },
            'average_confidence': 0.0,
            'llm_availability': self.llm_client is not None,
            'fallback_usage_rate': 0.0
        }

# Global instance for easy access
_meta_router = None

def get_meta_router() -> MetaRouter:
    """Get the global Meta-Router instance."""
    global _meta_router
    if _meta_router is None:
        _meta_router = MetaRouter()
    return _meta_router
