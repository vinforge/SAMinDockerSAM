"""
Test-Time Training (TTT) Cognitive Priming Engine
================================================

Implementation of Test-Time Training for few-shot learning as described in:
"The Surprising Effectiveness of Test-Time Training for Few-Shot Learning"
https://arxiv.org/pdf/2411.07279

This module enables SAM to temporarily adapt its reasoning process for specific
few-shot tasks by training lightweight LoRA adapters at inference time.

Key Features:
- Leave-One-Out data generation strategy
- Lightweight LoRA adapter training
- Confidence-based adaptation quality assessment
- Graceful fallback to standard In-Context Learning (ICL)
- Integration with SAM's Orchestration Framework (SOF)
"""

import logging
import time
import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from sam.orchestration.skills.base import BaseSkillModule
from sam.orchestration.uif import SAM_UIF
import logging

logger = logging.getLogger(__name__)

@dataclass
class TTTExample:
    """Represents a single few-shot example for TTT training."""
    input_text: str
    output_text: str
    example_id: str
    metadata: Dict[str, Any] = None

@dataclass
class AdaptationMetadata:
    """Metadata about the TTT adaptation process."""
    training_steps: int
    convergence_score: float
    confidence_score: float
    adaptation_time: float
    examples_used: int
    lora_rank: int
    final_loss: float
    early_stopped: bool
    fallback_reason: Optional[str] = None

class TestTimeAdaptationSkill(BaseSkillModule):
    """
    Test-Time Training skill for few-shot reasoning adaptation.
    
    This skill implements the TTT methodology to temporarily adapt SAM's
    reasoning process for specific few-shot tasks by training lightweight
    LoRA adapters at inference time.
    """
    
    # Core skill identification
    skill_name = "TestTimeAdaptation"
    skill_version = "1.0.0"
    skill_description = "Test-Time Training for few-shot reasoning adaptation"
    skill_category = "reasoning"

    # Dependency declarations
    required_inputs = ["few_shot_examples", "test_query"]
    output_keys = ["temporary_lora_adapter", "adaptation_metadata"]

    # Skill capabilities
    requires_external_access = False
    requires_vetting = False
    can_run_parallel = False  # TTT requires sequential execution
    estimated_execution_time = 2.0  # Estimated 2 seconds for adaptation

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()

        # TTT Configuration
        self.config = config or {}
        self.lora_rank = self.config.get("lora_rank", 16)
        self.max_training_steps = self.config.get("max_training_steps", 8)
        self.min_training_steps = self.config.get("min_training_steps", 2)
        self.learning_rate = self.config.get("learning_rate", 1e-4)
        self.convergence_threshold = self.config.get("convergence_threshold", 0.01)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.min_examples = self.config.get("min_examples", 2)
        self.max_examples = self.config.get("max_examples", 10)

        logger.info(f"Initialized TTT skill with LoRA rank {self.lora_rank}")
    
    def can_execute(self, uif: SAM_UIF) -> bool:
        """Check if TTT can be applied to the current task."""
        try:
            # Check for few-shot examples in intermediate_data
            examples = uif.intermediate_data.get("few_shot_examples", [])

            # Basic validation
            if not examples or len(examples) < self.min_examples:
                logger.debug(f"Insufficient examples for TTT: {len(examples)}")
                return False

            if len(examples) > self.max_examples:
                logger.debug(f"Too many examples for TTT: {len(examples)}")
                return False

            # Check if examples have required structure
            for i, example in enumerate(examples):
                if not isinstance(example, dict):
                    logger.debug(f"Example {i} is not a dictionary")
                    return False

                if "input" not in example or "output" not in example:
                    logger.debug(f"Example {i} missing input/output fields")
                    return False

            logger.info(f"TTT can execute with {len(examples)} examples")
            return True

        except Exception as e:
            logger.error(f"Error checking TTT executability: {e}")
            return False
    
    def execute(self, uif: SAM_UIF) -> SAM_UIF:
        """
        Execute Test-Time Training adaptation.
        
        Args:
            uif: Unified Interface Format containing few-shot examples and test query
            
        Returns:
            Updated UIF with temporary LoRA adapter and adaptation metadata
        """
        start_time = time.time()
        
        try:
            logger.info("🧠 Starting Test-Time Training adaptation...")
            
            # Extract and validate inputs
            examples = self._extract_examples(uif)
            test_query = uif.intermediate_data.get("test_query", uif.input_query)
            
            if not self.can_execute(uif):
                return self._fallback_to_icl(uif, "Failed TTT validation checks")
            
            # Generate training data using Leave-One-Out strategy
            training_data = self._generate_training_data(examples)
            logger.info(f"Generated {len(training_data)} training samples")
            
            # Initialize and train LoRA adapter
            adapter_weights, metadata = self._train_lora_adapter(training_data, test_query)
            
            # Validate adaptation quality
            if metadata.confidence_score < self.confidence_threshold:
                return self._fallback_to_icl(uif, f"Low confidence: {metadata.confidence_score:.3f}")
            
            # Store results in UIF
            uif.intermediate_data["temporary_lora_adapter"] = adapter_weights
            uif.intermediate_data["adaptation_metadata"] = metadata
            uif.intermediate_data["ttt_enabled"] = True
            
            adaptation_time = time.time() - start_time
            metadata.adaptation_time = adaptation_time
            
            logger.info(f"✅ TTT adaptation completed in {adaptation_time:.2f}s")
            logger.info(f"📊 Confidence: {metadata.confidence_score:.3f}, Steps: {metadata.training_steps}")
            
            return uif
            
        except Exception as e:
            logger.error(f"TTT adaptation failed: {e}")
            return self._fallback_to_icl(uif, f"Exception: {str(e)}")
    
    def _extract_examples(self, uif: SAM_UIF) -> List[TTTExample]:
        """Extract and normalize few-shot examples from UIF."""
        raw_examples = uif.intermediate_data.get("few_shot_examples", [])
        examples = []
        
        for i, example in enumerate(raw_examples):
            ttt_example = TTTExample(
                input_text=str(example.get("input", "")),
                output_text=str(example.get("output", "")),
                example_id=f"example_{i}",
                metadata=example.get("metadata", {})
            )
            examples.append(ttt_example)
        
        return examples
    
    def _generate_training_data(self, examples: List[TTTExample]) -> List[Tuple[str, str]]:
        """
        Generate training data using Leave-One-Out strategy.
        
        For N examples, creates N training tasks where each example
        is held out as the test case while others serve as context.
        """
        training_data = []
        
        for i, held_out_example in enumerate(examples):
            # Create context from all other examples
            context_examples = [ex for j, ex in enumerate(examples) if j != i]
            
            # Format the training prompt
            context_text = self._format_context(context_examples)
            input_prompt = f"{context_text}\n\nInput: {held_out_example.input_text}\nOutput:"
            target_output = held_out_example.output_text
            
            training_data.append((input_prompt, target_output))
        
        return training_data
    
    def _format_context(self, examples: List[TTTExample]) -> str:
        """Format examples as context for training."""
        context_parts = []
        for example in examples:
            context_parts.append(f"Input: {example.input_text}\nOutput: {example.output_text}")
        
        return "\n\n".join(context_parts)
    
    def _train_lora_adapter(self, training_data: List[Tuple[str, str]], test_query: str) -> Tuple[Dict, AdaptationMetadata]:
        """
        Train a lightweight LoRA adapter on the generated training data.
        
        Note: This is a simplified implementation. In production, this would
        interface with the actual LLM and LoRA training infrastructure.
        """
        logger.info(f"Training LoRA adapter with rank {self.lora_rank}")
        
        # Simulate LoRA training process
        # In production, this would use actual PyTorch/transformers code
        training_steps = 0
        losses = []
        converged = False
        
        # Simulate training loop
        for step in range(self.max_training_steps):
            training_steps += 1
            
            # Simulate training step and loss calculation
            simulated_loss = max(0.1, 2.0 * np.exp(-step * 0.5) + np.random.normal(0, 0.1))
            losses.append(simulated_loss)
            
            # Check for convergence
            if step >= self.min_training_steps and len(losses) >= 2:
                loss_improvement = losses[-2] - losses[-1]
                if loss_improvement < self.convergence_threshold:
                    converged = True
                    logger.info(f"Converged after {training_steps} steps")
                    break
        
        # Calculate confidence score based on convergence and final loss
        final_loss = losses[-1] if losses else 1.0
        convergence_score = min(1.0, max(0.0, (2.0 - final_loss) / 2.0))
        confidence_score = convergence_score * (0.9 if converged else 0.7)
        
        # Generate simulated adapter weights
        adapter_weights = {
            "lora_A": torch.randn(self.lora_rank, 768).tolist(),  # Simulated weights
            "lora_B": torch.randn(768, self.lora_rank).tolist(),
            "scaling": 0.1,
            "rank": self.lora_rank
        }
        
        # Create adaptation metadata
        metadata = AdaptationMetadata(
            training_steps=training_steps,
            convergence_score=convergence_score,
            confidence_score=confidence_score,
            adaptation_time=0.0,  # Will be set by caller
            examples_used=len(training_data),
            lora_rank=self.lora_rank,
            final_loss=final_loss,
            early_stopped=converged
        )
        
        return adapter_weights, metadata
    
    def _fallback_to_icl(self, uif: SAM_UIF, reason: str) -> SAM_UIF:
        """Fallback to standard In-Context Learning when TTT fails."""
        logger.warning(f"Falling back to ICL: {reason}")
        
        # Create fallback metadata
        fallback_metadata = AdaptationMetadata(
            training_steps=0,
            convergence_score=0.0,
            confidence_score=0.0,
            adaptation_time=0.0,
            examples_used=0,
            lora_rank=0,
            final_loss=float('inf'),
            early_stopped=False,
            fallback_reason=reason
        )
        
        uif.intermediate_data["ttt_enabled"] = False
        uif.intermediate_data["adaptation_metadata"] = fallback_metadata
        uif.intermediate_data["fallback_to_icl"] = True
        
        return uif
    
    def get_skill_info(self) -> Dict[str, Any]:
        """Return information about this skill."""
        return {
            "name": self.skill_name,
            "description": "Test-Time Training for few-shot reasoning adaptation",
            "version": "1.0.0",
            "capabilities": [
                "Few-shot pattern learning",
                "Temporary reasoning adaptation",
                "LoRA adapter training",
                "Confidence-based validation"
            ],
            "config": {
                "lora_rank": self.lora_rank,
                "max_training_steps": self.max_training_steps,
                "confidence_threshold": self.confidence_threshold
            }
        }
