"""
SAM Reasoning Module
===================

This module contains SAM's advanced reasoning capabilities including:
- Prompt-based steering for different reasoning styles
- Integration with steering vectors and cognitive patterns
- Profile-aware reasoning adaptation

Author: SAM Development Team
Version: 1.0.0
"""

from .prompt_steerer import PromptSteerer, ReasoningStyle

__all__ = ['PromptSteerer', 'ReasoningStyle']
