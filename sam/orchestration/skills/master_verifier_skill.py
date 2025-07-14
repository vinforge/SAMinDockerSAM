"""
Master Verifier Skill for SAM Orchestration Framework
=====================================================

This skill implements the Master-RM based verification system to detect
superficial "master key" responses and enhance SAM's reasoning integrity.

Based on the sarosavo/Master-RM model, this skill evaluates whether responses
are substantive or superficial, helping to prevent low-quality outputs from
being accepted by SAM's reasoning pipelines.

Author: SAM Development Team
Version: 1.0.0
"""

import os
import re
import time
import yaml
import logging
import functools
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ..uif import SAM_UIF, UIFStatus
from .base import BaseSkillModule, SkillExecutionError, SkillDependencyError

logger = logging.getLogger(__name__)


class MasterVerifierSkill(BaseSkillModule):
    """
    Master Verifier Skill for detecting superficial responses.
    
    Uses the Master-RM model to evaluate response quality and detect
    "master key" patterns that indicate superficial or low-quality responses.
    """
    
    # Skill identification
    skill_name = "master_verifier_skill"
    skill_version = "1.0.0"
    skill_description = "Detects superficial responses using Master-RM model to enhance reasoning integrity"
    skill_category = "reasoning"
    
    # Dependency declarations
    required_inputs = ["verification_question", "verification_response"]
    optional_inputs = ["verification_reference", "verification_context"]
    output_keys = ["is_substantive", "verification_confidence", "verification_explanation"]
    
    # Skill capabilities
    requires_external_access = False  # Model is loaded locally
    requires_vetting = False
    can_run_parallel = True
    estimated_execution_time = 2.0
    max_execution_time = 30.0
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Master Verifier Skill."""
        super().__init__()
        
        # Load configuration
        self.config_path = config_path or "config/master_verifier_config.yaml"
        self.config = self._load_config()
        
        # Initialize model components
        self._model = None
        self._tokenizer = None
        self._model_loaded = False
        
        # Initialize caching
        self._verification_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Statistics tracking
        self._verification_count = 0
        self._substantive_count = 0
        self._superficial_count = 0
        
        logger.info(f"Master Verifier Skill initialized with config: {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                return self._get_default_config()
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded Master Verifier config from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if config file is not available."""
        return {
            'model': {
                'name': 'sarosavo/Master-RM',
                'cache_dir': './model_cache/master_rm',
                'device': 'auto',
                'max_length': 2048,
                'temperature': 0.1
            },
            'verification': {
                'confidence_threshold': 0.8,
                'master_key_patterns': [
                    'thought process:', 'let\'s solve this', 'solution:',
                    'step by step', 'let me think', 'i need to'
                ],
                'min_response_length': 10,
                'timeout_seconds': 30,
                'enable_caching': True
            },
            'integration': {
                'enable_fallback': True,
                'fallback_method': 'pattern_matching',
                'penalty_multiplier': 0.2
            },
            'logging': {
                'level': 'INFO',
                'log_verification_details': False
            }
        }
    
    @functools.lru_cache(maxsize=1)
    def _load_model(self) -> Tuple[Any, Any]:
        """Load the Master-RM model and tokenizer with caching."""
        try:
            # Import transformers here to avoid dependency issues if not installed
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            model_name = self.config['model']['name']
            cache_dir = self.config['model']['cache_dir']
            device = self.config['model']['device']
            
            logger.info(f"Loading Master-RM model: {model_name}")
            
            # Create cache directory
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                trust_remote_code=self.config['model'].get('trust_remote_code', False)
            )
            
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                trust_remote_code=self.config['model'].get('trust_remote_code', False),
                torch_dtype=torch.float16 if device != 'cpu' else torch.float32
            )
            
            # Move to appropriate device
            if device == 'auto':
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            model = model.to(device)
            model.eval()
            
            logger.info(f"Master-RM model loaded successfully on {device}")
            return model, tokenizer
            
        except ImportError:
            logger.error("transformers library not available, falling back to pattern matching")
            raise SkillExecutionError("Master-RM model requires transformers library")
        except Exception as e:
            logger.error(f"Error loading Master-RM model: {e}")
            raise SkillExecutionError(f"Failed to load Master-RM model: {e}")
    
    def execute(self, uif: SAM_UIF) -> SAM_UIF:
        """
        Execute master verification on the provided response.
        
        Args:
            uif: Universal Interface Format containing verification request
            
        Returns:
            Updated UIF with verification results
        """
        start_time = time.time()
        
        try:
            # Extract inputs
            question = uif.intermediate_data.get('verification_question', '')
            response = uif.intermediate_data.get('verification_response', '')
            reference = uif.intermediate_data.get('verification_reference', '')
            context = uif.intermediate_data.get('verification_context', {})
            
            # Validate inputs
            if not question or not response:
                raise SkillDependencyError("verification_question and verification_response are required")
            
            # Check cache first
            cache_key = self._generate_cache_key(question, response, reference)
            if self.config['verification'].get('enable_caching', True) and cache_key in self._verification_cache:
                cached_result = self._verification_cache[cache_key]
                self._cache_hits += 1
                
                # Update UIF with cached results
                uif.intermediate_data.update(cached_result)
                uif.add_log_entry(f"Used cached verification result", self.skill_name)
                return uif
            
            self._cache_misses += 1
            
            # Perform verification
            verification_result = self._verify_response(question, response, reference, context)
            
            # Cache the result
            if self.config['verification'].get('enable_caching', True):
                self._verification_cache[cache_key] = verification_result
            
            # Update statistics
            self._verification_count += 1
            if verification_result['is_substantive']:
                self._substantive_count += 1
            else:
                self._superficial_count += 1
            
            # Update UIF with results
            uif.intermediate_data.update(verification_result)
            
            execution_time = time.time() - start_time
            uif.add_log_entry(
                f"Verification completed in {execution_time:.2f}s - "
                f"Substantive: {verification_result['is_substantive']}", 
                self.skill_name
            )
            
            return uif
            
        except Exception as e:
            logger.error(f"Master verification failed: {e}")
            
            # Fallback behavior
            if self.config['integration'].get('enable_fallback', True):
                fallback_result = self._fallback_verification(
                    uif.intermediate_data.get('verification_response', ''),
                    uif.intermediate_data.get('verification_context', {})
                )
                uif.intermediate_data.update(fallback_result)
                uif.add_warning(f"Used fallback verification due to error: {e}")
            else:
                raise SkillExecutionError(f"Master verification failed: {e}")
            
            return uif

    def _verify_response(self, question: str, response: str, reference: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the actual verification using Master-RM model or fallback methods.

        Args:
            question: The original question/problem
            response: The response to verify
            reference: Reference answer (optional)
            context: Additional context information

        Returns:
            Dictionary with verification results
        """
        try:
            # Try model-based verification first
            if not self._model_loaded:
                self._model, self._tokenizer = self._load_model()
                self._model_loaded = True

            return self._model_based_verification(question, response, reference)

        except Exception as e:
            logger.warning(f"Model-based verification failed: {e}, using fallback")
            return self._fallback_verification(response, context)

    def _model_based_verification(self, question: str, response: str, reference: str) -> Dict[str, Any]:
        """
        Perform verification using the Master-RM model.

        Args:
            question: The original question
            response: The response to verify
            reference: Reference answer (can be empty)

        Returns:
            Dictionary with verification results
        """
        try:
            import torch

            # Use response as reference if no reference provided
            if not reference:
                reference = response

            # Format the prompt according to Master-RM requirements
            prompt_template = self.config.get('prompt_template', '')
            if not prompt_template:
                prompt_template = self._get_default_prompt_template()

            formatted_prompt = prompt_template.format(
                question=question,
                response=response,
                reference=reference
            )

            # Tokenize input
            max_length = self.config['model'].get('max_length', 2048)
            inputs = self._tokenizer(
                formatted_prompt,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
                padding=True
            )

            # Move to same device as model
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits

                # Get prediction (assuming binary classification: 0=superficial, 1=substantive)
                probabilities = torch.softmax(logits, dim=-1)
                prediction = torch.argmax(probabilities, dim=-1).item()
                confidence = torch.max(probabilities, dim=-1).values.item()

            is_substantive = bool(prediction)

            # Apply confidence threshold
            confidence_threshold = self.config['verification'].get('confidence_threshold', 0.8)
            if confidence < confidence_threshold:
                # Low confidence, use pattern matching as backup
                pattern_result = self._pattern_matching_verification(response)
                is_substantive = pattern_result['is_substantive']
                explanation = f"Low model confidence ({confidence:.3f}), used pattern matching"
            else:
                explanation = f"Model prediction with {confidence:.3f} confidence"

            return {
                'is_substantive': is_substantive,
                'verification_confidence': confidence,
                'verification_explanation': explanation,
                'verification_method': 'model_based'
            }

        except Exception as e:
            logger.error(f"Model-based verification error: {e}")
            raise

    def _fallback_verification(self, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback verification using pattern matching and heuristics.

        Args:
            response: The response to verify
            context: Additional context

        Returns:
            Dictionary with verification results
        """
        fallback_method = self.config['integration'].get('fallback_method', 'pattern_matching')

        if fallback_method == 'pattern_matching':
            return self._pattern_matching_verification(response)
        elif fallback_method == 'length_heuristic':
            return self._length_heuristic_verification(response)
        elif fallback_method == 'always_pass':
            return {
                'is_substantive': True,
                'verification_confidence': 0.5,
                'verification_explanation': 'Fallback: always pass',
                'verification_method': 'always_pass'
            }
        else:
            return self._pattern_matching_verification(response)

    def _pattern_matching_verification(self, response: str) -> Dict[str, Any]:
        """
        Verify response using pattern matching for known master key phrases.

        Args:
            response: The response to verify

        Returns:
            Dictionary with verification results
        """
        response_lower = response.lower().strip()

        # Check minimum length
        min_length = self.config['verification'].get('min_response_length', 10)
        if len(response_lower) < min_length:
            return {
                'is_substantive': False,
                'verification_confidence': 0.9,
                'verification_explanation': f'Response too short ({len(response)} chars)',
                'verification_method': 'pattern_matching'
            }

        # Check for master key patterns
        master_patterns = self.config['verification'].get('master_key_patterns', [])
        detected_patterns = []

        for pattern in master_patterns:
            if pattern.lower() in response_lower:
                detected_patterns.append(pattern)

        # Calculate superficiality score
        if detected_patterns:
            # Response contains master key patterns - likely superficial
            confidence = min(0.9, 0.6 + len(detected_patterns) * 0.1)
            return {
                'is_substantive': False,
                'verification_confidence': confidence,
                'verification_explanation': f'Contains master key patterns: {detected_patterns}',
                'verification_method': 'pattern_matching'
            }
        else:
            # No master key patterns detected - likely substantive
            return {
                'is_substantive': True,
                'verification_confidence': 0.7,
                'verification_explanation': 'No master key patterns detected',
                'verification_method': 'pattern_matching'
            }

    def _length_heuristic_verification(self, response: str) -> Dict[str, Any]:
        """
        Simple length-based heuristic verification.

        Args:
            response: The response to verify

        Returns:
            Dictionary with verification results
        """
        response_length = len(response.strip())

        # Very short responses are likely superficial
        if response_length < 20:
            return {
                'is_substantive': False,
                'verification_confidence': 0.8,
                'verification_explanation': f'Very short response ({response_length} chars)',
                'verification_method': 'length_heuristic'
            }
        # Medium length responses are neutral
        elif response_length < 100:
            return {
                'is_substantive': True,
                'verification_confidence': 0.5,
                'verification_explanation': f'Medium length response ({response_length} chars)',
                'verification_method': 'length_heuristic'
            }
        # Longer responses are likely substantive
        else:
            return {
                'is_substantive': True,
                'verification_confidence': 0.7,
                'verification_explanation': f'Long response ({response_length} chars)',
                'verification_method': 'length_heuristic'
            }

    def _generate_cache_key(self, question: str, response: str, reference: str) -> str:
        """Generate a cache key for the verification request."""
        import hashlib

        combined = f"{question}|{response}|{reference}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template for Master-RM."""
        return """system:
You are a helpful assistant.
user:
Given a problem, determine whether the final answer in the provided solution process matches the reference answer.

**Question:**
{question}
**Solution Process (Final Step Only):**
{response}
**Reference Answer:**
{reference}
**Output:**"""

    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics."""
        return {
            'total_verifications': self._verification_count,
            'substantive_responses': self._substantive_count,
            'superficial_responses': self._superficial_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'model_loaded': self._model_loaded
        }

    def can_handle_query(self, query: str) -> bool:
        """
        Check if this skill can handle verification requests.

        Args:
            query: Query to check

        Returns:
            True if query contains verification keywords
        """
        verification_keywords = [
            'verify', 'check', 'validate', 'substantive', 'superficial',
            'master key', 'quality', 'assessment'
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in verification_keywords)
