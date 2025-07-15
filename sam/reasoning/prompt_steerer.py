"""
Prompt-Based Steering for SAM Reasoning Styles
==============================================

This module implements prompt-based steering that approximates the effects of 
KV cache steering within SAM's existing Ollama-based architecture.

The PromptSteerer transforms user prompts by adding style-specific instructions
and reasoning patterns that guide the model toward desired cognitive behaviors.

Author: SAM Development Team
Version: 1.0.0
"""

import json
import logging
import os
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ReasoningStyle:
    """Configuration for a reasoning style."""
    name: str
    description: str
    system_instruction: str
    reasoning_pattern: str
    strength_modulation: Dict[str, float]
    example_phrases: List[str]
    cognitive_markers: List[str]

class PromptSteerer:
    """
    Prompt-based steering system that approximates KV cache steering effects
    by transforming prompts with style-specific instructions and patterns.
    """
    
    def __init__(self, assets_dir: str = None):
        """
        Initialize the prompt steerer.
        
        Args:
            assets_dir: Directory containing steering vector assets and templates
        """
        if assets_dir is None:
            # Default to SAM's assets directory
            current_dir = Path(__file__).parent
            assets_dir = current_dir.parent / "assets" / "steering_vectors"
        
        self.assets_dir = Path(assets_dir)
        self.reasoning_styles: Dict[str, ReasoningStyle] = {}
        self.default_style = "step_by_step_reasoning"
        
        # Load reasoning styles from templates
        self._load_reasoning_styles()
        
        logger.info(f"PromptSteerer initialized with {len(self.reasoning_styles)} styles")
    
    def _load_reasoning_styles(self):
        """Load reasoning styles from template files."""
        if not self.assets_dir.exists():
            logger.warning(f"Assets directory not found: {self.assets_dir}")
            self._create_default_styles()
            return
        
        # Load from template files
        template_files = list(self.assets_dir.glob("*_template.json"))
        
        for template_file in template_files:
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                
                style = ReasoningStyle(
                    name=template_data["style_name"],
                    description=template_data["description"],
                    system_instruction=template_data["system_instruction"],
                    reasoning_pattern=template_data["reasoning_pattern"],
                    strength_modulation=template_data.get("strength_modulation", {"low": 0.5, "medium": 1.0, "high": 1.5}),
                    example_phrases=template_data.get("example_phrases", []),
                    cognitive_markers=template_data.get("cognitive_markers", [])
                )
                
                self.reasoning_styles[style.name] = style
                logger.info(f"Loaded reasoning style: {style.name}")
                
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
        
        # Create default styles if none were loaded
        if not self.reasoning_styles:
            self._create_default_styles()
    
    def _create_default_styles(self):
        """Create default reasoning styles if templates are not available."""
        logger.info("Creating default reasoning styles")
        
        # Researcher Style
        self.reasoning_styles["researcher_style"] = ReasoningStyle(
            name="researcher_style",
            description="Detailed analytical reasoning with research methodology",
            system_instruction="""Adopt the mindset of a meticulous researcher. Approach this query with systematic analysis, consider multiple perspectives, cite relevant principles, and show your analytical methodology clearly. Break down complex problems into components and examine each thoroughly.""",
            reasoning_pattern="systematic analysis → evidence gathering → perspective consideration → methodical conclusion",
            strength_modulation={"low": 0.5, "medium": 1.0, "high": 1.5},
            example_phrases=[
                "Let me analyze this systematically...",
                "From a research perspective...",
                "The evidence suggests...",
                "Multiple factors need consideration..."
            ],
            cognitive_markers=["analysis", "evidence", "methodology", "systematic", "research"]
        )
        
        # Step-by-Step Reasoning
        self.reasoning_styles["step_by_step_reasoning"] = ReasoningStyle(
            name="step_by_step_reasoning",
            description="Systematic step-by-step logical progression",
            system_instruction="""Think through this problem using clear, numbered steps. Break down your reasoning process systematically, showing each logical step and explaining how you move from one step to the next. Make your thought process transparent and easy to follow.""",
            reasoning_pattern="problem breakdown → step 1 → step 2 → ... → logical conclusion",
            strength_modulation={"low": 0.5, "medium": 1.0, "high": 1.5},
            example_phrases=[
                "Let me break this down step by step:",
                "Step 1:",
                "Following from the previous step...",
                "Therefore, we can conclude..."
            ],
            cognitive_markers=["step", "systematic", "logical", "breakdown", "process"]
        )
        
        # Creative Explorer
        self.reasoning_styles["creative_explorer"] = ReasoningStyle(
            name="creative_explorer",
            description="Creative and exploratory thinking patterns",
            system_instruction="""Approach this question with creative exploration and innovative thinking. Consider unconventional perspectives, explore alternative possibilities, think outside traditional boundaries, and generate novel insights. Embrace creative problem-solving approaches.""",
            reasoning_pattern="creative exploration → alternative perspectives → innovative connections → novel insights",
            strength_modulation={"low": 0.5, "medium": 1.0, "high": 1.5},
            example_phrases=[
                "Let me explore this creatively...",
                "What if we consider...",
                "An alternative perspective might be...",
                "This opens up interesting possibilities..."
            ],
            cognitive_markers=["creative", "innovative", "alternative", "explore", "possibilities"]
        )
    
    def apply_style(self, base_prompt: str, style_name: str, strength: float = 1.0) -> str:
        """
        Apply reasoning style steering to a base prompt.
        
        Args:
            base_prompt: The original user prompt
            style_name: Name of the reasoning style to apply
            strength: Strength multiplier for the steering effect (0.1 to 3.0)
            
        Returns:
            Enhanced prompt with style-specific steering
        """
        if style_name == "default" or style_name not in self.reasoning_styles:
            return base_prompt
        
        style = self.reasoning_styles[style_name]
        
        # Determine strength level
        strength_level = self._determine_strength_level(strength)
        modulation_factor = style.strength_modulation.get(strength_level, 1.0)
        
        # Apply strength modulation to the steering
        if modulation_factor < 0.8:
            # Low strength: subtle guidance
            enhanced_prompt = self._apply_subtle_steering(base_prompt, style)
        elif modulation_factor > 1.2:
            # High strength: strong guidance
            enhanced_prompt = self._apply_strong_steering(base_prompt, style)
        else:
            # Medium strength: standard guidance
            enhanced_prompt = self._apply_standard_steering(base_prompt, style)
        
        logger.debug(f"Applied {style_name} steering with strength {strength} to prompt")
        return enhanced_prompt
    
    def _determine_strength_level(self, strength: float) -> str:
        """Determine strength level category from numeric value."""
        if strength < 0.8:
            return "low"
        elif strength > 1.2:
            return "high"
        else:
            return "medium"
    
    def _apply_subtle_steering(self, base_prompt: str, style: ReasoningStyle) -> str:
        """Apply subtle steering for low strength."""
        # Add a brief hint about the reasoning approach
        hint = f"Consider approaching this with {style.reasoning_pattern.split(' → ')[0]}."
        return f"{hint}\n\n{base_prompt}"
    
    def _apply_standard_steering(self, base_prompt: str, style: ReasoningStyle) -> str:
        """Apply standard steering for medium strength."""
        # Add system instruction and reasoning pattern guidance
        instruction = style.system_instruction
        
        enhanced_prompt = f"""System: {instruction}

User Query: {base_prompt}

Please respond following the {style.description.lower()} approach."""
        
        return enhanced_prompt
    
    def _apply_strong_steering(self, base_prompt: str, style: ReasoningStyle) -> str:
        """Apply strong steering for high strength."""
        # Add comprehensive guidance with examples and cognitive markers
        instruction = style.system_instruction
        pattern = style.reasoning_pattern
        
        # Include example phrases if available
        examples_text = ""
        if style.example_phrases:
            examples_text = f"\n\nExample phrases to guide your response: {', '.join(style.example_phrases[:3])}"
        
        enhanced_prompt = f"""System: {instruction}

Reasoning Pattern: {pattern}

Cognitive Focus: Emphasize {', '.join(style.cognitive_markers[:3])} in your response.{examples_text}

User Query: {base_prompt}

Please provide a comprehensive response that fully embodies the {style.description.lower()} approach, demonstrating clear adherence to the specified reasoning pattern."""
        
        return enhanced_prompt
    
    def get_available_styles(self) -> List[str]:
        """Get list of available reasoning styles."""
        return list(self.reasoning_styles.keys())
    
    def get_style_description(self, style_name: str) -> Optional[str]:
        """Get description of a specific reasoning style."""
        style = self.reasoning_styles.get(style_name)
        return style.description if style else None
    
    def get_style_info(self, style_name: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a reasoning style."""
        style = self.reasoning_styles.get(style_name)
        if not style:
            return None
        
        return {
            "name": style.name,
            "description": style.description,
            "reasoning_pattern": style.reasoning_pattern,
            "cognitive_markers": style.cognitive_markers,
            "example_phrases": style.example_phrases
        }
    
    def set_default_style(self, style_name: str):
        """Set the default reasoning style."""
        if style_name in self.reasoning_styles:
            self.default_style = style_name
            logger.info(f"Default reasoning style set to: {style_name}")
        else:
            logger.warning(f"Unknown style: {style_name}")

# Utility functions for integration
def get_prompt_steerer() -> PromptSteerer:
    """Get a singleton instance of the PromptSteerer."""
    if not hasattr(get_prompt_steerer, '_instance'):
        get_prompt_steerer._instance = PromptSteerer()
    return get_prompt_steerer._instance

def apply_reasoning_style(prompt: str, style: str = "default", strength: float = 1.0) -> str:
    """
    Convenience function to apply reasoning style steering to a prompt.
    
    Args:
        prompt: Original prompt
        style: Reasoning style name
        strength: Steering strength (0.1 to 3.0)
        
    Returns:
        Enhanced prompt with reasoning style applied
    """
    steerer = get_prompt_steerer()
    return steerer.apply_style(prompt, style, strength)
