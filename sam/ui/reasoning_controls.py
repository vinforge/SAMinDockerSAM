"""
SAM Reasoning Style Controls for Streamlit UI
=============================================

This module provides Streamlit UI components for controlling SAM's
reasoning style steering functionality.

Author: SAM Development Team
Version: 1.0.0
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, Tuple
from sam.reasoning.prompt_steerer import get_prompt_steerer
from sam.core.sam_model_client import get_sam_model_client

logger = logging.getLogger(__name__)

class ReasoningStyleControls:
    """Streamlit UI controls for reasoning style management."""
    
    def __init__(self):
        """Initialize the reasoning style controls."""
        self.steerer = None
        self.model_client = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize the reasoning components."""
        try:
            self.steerer = get_prompt_steerer()
            self.model_client = get_sam_model_client()
            logger.info("Reasoning style controls initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize reasoning components: {e}")
    
    def render_reasoning_style_sidebar(self):
        """Render reasoning style controls in the sidebar."""
        if not self.steerer:
            return
        
        st.markdown("### 🧠 Reasoning Style")
        
        # Get available styles
        available_styles = self.steerer.get_available_styles()
        style_options = ["default"] + available_styles
        
        # Style descriptions for display
        style_descriptions = {
            "default": "Standard reasoning",
            "researcher_style": "🔬 Research Analysis",
            "step_by_step_reasoning": "📝 Step-by-Step",
            "creative_explorer": "🎨 Creative Explorer"
        }
        
        # Current style selection
        current_style = st.session_state.get('reasoning_style', 'default')
        
        # Style selector
        selected_style = st.selectbox(
            "Select reasoning approach:",
            options=style_options,
            index=style_options.index(current_style) if current_style in style_options else 0,
            format_func=lambda x: style_descriptions.get(x, x),
            help="Choose how SAM should approach reasoning and problem-solving"
        )
        
        # Update session state
        st.session_state.reasoning_style = selected_style
        
        # Show style information
        if selected_style != "default":
            style_info = self.steerer.get_style_info(selected_style)
            if style_info:
                with st.expander("ℹ️ Style Details", expanded=False):
                    st.markdown(f"**Description:** {style_info['description']}")
                    st.markdown(f"**Pattern:** {style_info['reasoning_pattern']}")
                    
                    if style_info.get('cognitive_markers'):
                        markers = ", ".join(style_info['cognitive_markers'][:3])
                        st.markdown(f"**Focus:** {markers}")
        
        # Strength control
        if selected_style != "default":
            strength = st.slider(
                "Reasoning intensity:",
                min_value=0.1,
                max_value=3.0,
                value=st.session_state.get('reasoning_strength', 1.0),
                step=0.1,
                help="Higher values apply stronger reasoning style guidance"
            )
            st.session_state.reasoning_strength = strength
            
            # Visual indicator
            if strength < 0.8:
                st.caption("🔹 Subtle guidance")
            elif strength > 1.5:
                st.caption("🔸 Strong guidance")
            else:
                st.caption("🔹 Balanced guidance")
        
        # Enable/disable toggle
        reasoning_enabled = st.checkbox(
            "Enable reasoning styles",
            value=st.session_state.get('reasoning_enabled', True),
            help="Toggle reasoning style steering on/off"
        )
        st.session_state.reasoning_enabled = reasoning_enabled
        
        # Update model client
        if self.model_client:
            self.model_client.enable_reasoning_styles(reasoning_enabled)
    
    def render_reasoning_style_compact(self):
        """Render a compact version of reasoning style controls."""
        if not self.steerer:
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Quick style selector
            available_styles = ["default"] + self.steerer.get_available_styles()
            style_icons = {
                "default": "🤖",
                "researcher_style": "🔬",
                "step_by_step_reasoning": "📝",
                "creative_explorer": "🎨"
            }
            
            current_style = st.session_state.get('reasoning_style', 'default')
            
            selected_style = st.selectbox(
                "Reasoning:",
                options=available_styles,
                index=available_styles.index(current_style) if current_style in available_styles else 0,
                format_func=lambda x: f"{style_icons.get(x, '🧠')} {x.replace('_', ' ').title()}",
                label_visibility="collapsed"
            )
            st.session_state.reasoning_style = selected_style
        
        with col2:
            # Quick enable/disable
            enabled = st.checkbox(
                "On",
                value=st.session_state.get('reasoning_enabled', True),
                help="Enable reasoning styles"
            )
            st.session_state.reasoning_enabled = enabled
            
            if self.model_client:
                self.model_client.enable_reasoning_styles(enabled)
    
    def get_current_reasoning_config(self) -> Dict[str, Any]:
        """Get the current reasoning configuration."""
        return {
            'style': st.session_state.get('reasoning_style', 'default'),
            'strength': st.session_state.get('reasoning_strength', 1.0),
            'enabled': st.session_state.get('reasoning_enabled', True)
        }
    
    def apply_reasoning_to_prompt(self, prompt: str) -> str:
        """Apply current reasoning style to a prompt."""
        if not self.steerer or not st.session_state.get('reasoning_enabled', True):
            return prompt
        
        style = st.session_state.get('reasoning_style', 'default')
        strength = st.session_state.get('reasoning_strength', 1.0)
        
        if style == 'default':
            return prompt
        
        try:
            return self.steerer.apply_style(prompt, style, strength)
        except Exception as e:
            logger.warning(f"Failed to apply reasoning style: {e}")
            return prompt

def render_reasoning_style_status():
    """Render a status indicator for the current reasoning style."""
    try:
        current_style = st.session_state.get('reasoning_style', 'default')
        enabled = st.session_state.get('reasoning_enabled', True)
        
        if not enabled:
            st.caption("🤖 Standard reasoning")
            return
        
        if current_style == 'default':
            st.caption("🤖 Standard reasoning")
        else:
            style_icons = {
                "researcher_style": "🔬",
                "step_by_step_reasoning": "📝", 
                "creative_explorer": "🎨"
            }
            
            icon = style_icons.get(current_style, "🧠")
            style_name = current_style.replace('_', ' ').title()
            strength = st.session_state.get('reasoning_strength', 1.0)
            
            if strength < 0.8:
                intensity = "Subtle"
            elif strength > 1.5:
                intensity = "Strong"
            else:
                intensity = "Balanced"
            
            st.caption(f"{icon} {style_name} ({intensity})")
    
    except Exception as e:
        logger.warning(f"Error rendering reasoning style status: {e}")
        st.caption("🤖 Standard reasoning")

def get_reasoning_controls() -> ReasoningStyleControls:
    """Get a singleton instance of reasoning style controls."""
    if 'reasoning_controls' not in st.session_state:
        st.session_state.reasoning_controls = ReasoningStyleControls()
    return st.session_state.reasoning_controls

# Convenience functions for integration
def render_reasoning_sidebar():
    """Convenience function to render reasoning controls in sidebar."""
    controls = get_reasoning_controls()
    controls.render_reasoning_style_sidebar()

def render_reasoning_compact():
    """Convenience function to render compact reasoning controls."""
    controls = get_reasoning_controls()
    controls.render_reasoning_style_compact()

def apply_current_reasoning_style(prompt: str) -> str:
    """Convenience function to apply current reasoning style to a prompt."""
    controls = get_reasoning_controls()
    return controls.apply_reasoning_to_prompt(prompt)
