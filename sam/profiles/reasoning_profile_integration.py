"""
SAM Profile-Based Reasoning Style Integration
============================================

This module integrates reasoning styles with SAM's profile system,
automatically applying appropriate reasoning styles based on user profiles.

Author: SAM Development Team
Version: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import streamlit as st

logger = logging.getLogger(__name__)

class ProfileReasoningIntegration:
    """Manages integration between user profiles and reasoning styles."""
    
    def __init__(self, profiles_dir: str = "multimodal_processing/dimension_profiles"):
        """
        Initialize the profile reasoning integration.
        
        Args:
            profiles_dir: Directory containing profile configuration files
        """
        self.profiles_dir = Path(profiles_dir)
        self.profile_configs = {}
        self.current_profile = None
        self._load_profile_configs()
        
    def _load_profile_configs(self):
        """Load reasoning style configurations from profile files."""
        if not self.profiles_dir.exists():
            logger.warning(f"Profiles directory not found: {self.profiles_dir}")
            return
        
        profile_files = list(self.profiles_dir.glob("*.json"))
        
        for profile_file in profile_files:
            try:
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                
                profile_name = profile_data.get("name", profile_file.stem)
                
                # Extract reasoning style configuration
                reasoning_config = profile_data.get("reasoning_style_config", {})
                
                if reasoning_config:
                    self.profile_configs[profile_name] = reasoning_config
                    logger.info(f"Loaded reasoning config for profile: {profile_name}")
                else:
                    # Create default config for profiles without reasoning style config
                    default_config = self._create_default_reasoning_config(profile_name)
                    self.profile_configs[profile_name] = default_config
                    logger.info(f"Created default reasoning config for profile: {profile_name}")
                    
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
        
        logger.info(f"Loaded reasoning configurations for {len(self.profile_configs)} profiles")
    
    def _create_default_reasoning_config(self, profile_name: str) -> Dict[str, Any]:
        """Create default reasoning configuration for a profile."""
        # Profile-specific defaults
        profile_defaults = {
            "researcher": {
                "default_reasoning_style": "researcher_style",
                "default_strength": 1.2,
                "description": "Research-focused analytical reasoning"
            },
            "business": {
                "default_reasoning_style": "step_by_step_reasoning",
                "default_strength": 1.0,
                "description": "Systematic business analysis"
            },
            "legal": {
                "default_reasoning_style": "researcher_style",
                "default_strength": 1.3,
                "description": "Rigorous legal analysis"
            },
            "general": {
                "default_reasoning_style": "step_by_step_reasoning",
                "default_strength": 1.0,
                "description": "Balanced general reasoning"
            }
        }
        
        # Get profile-specific default or use general default
        default = profile_defaults.get(profile_name, profile_defaults["general"])
        
        return {
            "default_reasoning_style": default["default_reasoning_style"],
            "default_strength": default["default_strength"],
            "auto_adapt": True,
            "description": default["description"],
            "fallback_style": "step_by_step_reasoning"
        }
    
    def get_profile_reasoning_config(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get reasoning configuration for a specific profile."""
        return self.profile_configs.get(profile_name)
    
    def apply_profile_reasoning_style(self, profile_name: str) -> Tuple[str, float]:
        """
        Apply reasoning style based on profile configuration.
        
        Args:
            profile_name: Name of the profile to apply
            
        Returns:
            Tuple of (reasoning_style, strength)
        """
        config = self.get_profile_reasoning_config(profile_name)
        
        if not config:
            logger.warning(f"No reasoning config found for profile: {profile_name}")
            return "step_by_step_reasoning", 1.0
        
        style = config.get("default_reasoning_style", "step_by_step_reasoning")
        strength = config.get("default_strength", 1.0)
        
        # Update session state if using Streamlit
        try:
            if hasattr(st, 'session_state'):
                # Only update if auto_adapt is enabled and user hasn't manually overridden
                auto_adapt = config.get("auto_adapt", True)
                user_override = st.session_state.get("reasoning_style_user_override", False)
                
                if auto_adapt and not user_override:
                    st.session_state.reasoning_style = style
                    st.session_state.reasoning_strength = strength
                    st.session_state.reasoning_enabled = True
                    
                    logger.info(f"Applied profile reasoning style: {profile_name} -> {style} (strength: {strength})")
        except Exception as e:
            logger.warning(f"Could not update session state: {e}")
        
        return style, strength
    
    def set_current_profile(self, profile_name: str):
        """Set the current active profile and apply its reasoning style."""
        self.current_profile = profile_name
        
        if profile_name in self.profile_configs:
            style, strength = self.apply_profile_reasoning_style(profile_name)
            logger.info(f"Switched to profile '{profile_name}' with reasoning style '{style}'")
        else:
            logger.warning(f"Profile '{profile_name}' not found in configurations")
    
    def get_available_profiles(self) -> list:
        """Get list of available profiles with reasoning configurations."""
        return list(self.profile_configs.keys())
    
    def get_profile_description(self, profile_name: str) -> str:
        """Get description of a profile's reasoning configuration."""
        config = self.get_profile_reasoning_config(profile_name)
        if config:
            return config.get("description", f"Reasoning style for {profile_name} profile")
        return f"No reasoning configuration for {profile_name}"
    
    def update_profile_reasoning_config(self, profile_name: str, **kwargs):
        """Update reasoning configuration for a profile."""
        if profile_name not in self.profile_configs:
            self.profile_configs[profile_name] = self._create_default_reasoning_config(profile_name)
        
        config = self.profile_configs[profile_name]
        
        # Update configuration
        for key, value in kwargs.items():
            if key in ["default_reasoning_style", "default_strength", "auto_adapt", "description", "fallback_style"]:
                config[key] = value
                logger.info(f"Updated {key} for profile {profile_name}: {value}")
        
        # Apply changes if this is the current profile
        if self.current_profile == profile_name:
            self.apply_profile_reasoning_style(profile_name)
    
    def reset_to_profile_defaults(self, profile_name: str):
        """Reset reasoning style to profile defaults, clearing any user overrides."""
        try:
            if hasattr(st, 'session_state'):
                st.session_state.reasoning_style_user_override = False
                
            self.apply_profile_reasoning_style(profile_name)
            logger.info(f"Reset reasoning style to defaults for profile: {profile_name}")
            
        except Exception as e:
            logger.warning(f"Could not reset to profile defaults: {e}")

# Global instance
_profile_integration = None

def get_profile_reasoning_integration() -> ProfileReasoningIntegration:
    """Get or create a global profile reasoning integration instance."""
    global _profile_integration
    
    if _profile_integration is None:
        _profile_integration = ProfileReasoningIntegration()
    
    return _profile_integration

def apply_profile_reasoning_style(profile_name: str) -> Tuple[str, float]:
    """Convenience function to apply reasoning style based on profile."""
    integration = get_profile_reasoning_integration()
    return integration.apply_profile_reasoning_style(profile_name)

def set_current_profile(profile_name: str):
    """Convenience function to set current profile and apply reasoning style."""
    integration = get_profile_reasoning_integration()
    integration.set_current_profile(profile_name)

def get_profile_reasoning_config(profile_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get profile reasoning configuration."""
    integration = get_profile_reasoning_integration()
    return integration.get_profile_reasoning_config(profile_name)

# Streamlit integration functions
def render_profile_reasoning_controls():
    """Render profile-based reasoning controls in Streamlit."""
    try:
        integration = get_profile_reasoning_integration()
        
        st.markdown("### 👤 Profile-Based Reasoning")
        
        # Profile selector
        available_profiles = integration.get_available_profiles()
        current_profile = st.session_state.get("current_profile", "general")
        
        selected_profile = st.selectbox(
            "Active Profile:",
            options=available_profiles,
            index=available_profiles.index(current_profile) if current_profile in available_profiles else 0,
            help="Select your working profile to automatically apply appropriate reasoning styles"
        )
        
        # Update profile if changed
        if selected_profile != st.session_state.get("current_profile"):
            st.session_state.current_profile = selected_profile
            integration.set_current_profile(selected_profile)
            st.rerun()
        
        # Show profile description
        description = integration.get_profile_description(selected_profile)
        st.caption(f"📝 {description}")
        
        # Profile reasoning configuration
        config = integration.get_profile_reasoning_config(selected_profile)
        if config:
            with st.expander("⚙️ Profile Reasoning Settings", expanded=False):
                st.markdown(f"**Default Style:** {config.get('default_reasoning_style', 'N/A')}")
                st.markdown(f"**Default Strength:** {config.get('default_strength', 'N/A')}")
                st.markdown(f"**Auto-Adapt:** {'✅' if config.get('auto_adapt', False) else '❌'}")
                
                if st.button("🔄 Reset to Profile Defaults"):
                    integration.reset_to_profile_defaults(selected_profile)
                    st.success(f"Reset reasoning style to {selected_profile} profile defaults")
                    st.rerun()
        
    except Exception as e:
        logger.error(f"Error rendering profile reasoning controls: {e}")
        st.error("Profile reasoning controls unavailable")
