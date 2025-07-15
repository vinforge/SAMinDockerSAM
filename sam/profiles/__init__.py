"""
SAM Profile System Integration
=============================

This module contains profile system integrations for SAM.

Author: SAM Development Team
Version: 1.0.0
"""

from .reasoning_profile_integration import (
    ProfileReasoningIntegration,
    get_profile_reasoning_integration,
    apply_profile_reasoning_style,
    set_current_profile,
    get_profile_reasoning_config,
    render_profile_reasoning_controls
)

__all__ = [
    'ProfileReasoningIntegration',
    'get_profile_reasoning_integration',
    'apply_profile_reasoning_style', 
    'set_current_profile',
    'get_profile_reasoning_config',
    'render_profile_reasoning_controls'
]
