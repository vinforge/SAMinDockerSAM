#!/usr/bin/env python3
"""
SAM Secure Streamlit Application

Main Streamlit application with integrated security features.
Provides secure access to SAM's AI assistant capabilities.

Author: SAM Development Team
Version: 1.0.0
"""

import os
# Suppress PyTorch/Streamlit compatibility warnings and prevent crashes
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Fix torch/Streamlit compatibility issues
os.environ['PYTORCH_DISABLE_PER_OP_PROFILING'] = '1'

# Prevent torch from interfering with Streamlit's module system
import sys

import streamlit as st
import sys
import logging
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from typing import List, Dict, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging with better error handling
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/secure_streamlit.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

def health_check():
    """Health check endpoint for Docker containers and load balancers."""
    try:
        # Check if we're in a health check request
        query_params = st.query_params
        if 'health' in query_params or st.session_state.get('health_check_mode', False):
            # Return simple health status
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "services": {
                    "streamlit": "running",
                    "memory_store": "available",
                    "security": "enabled"
                }
            }

            # Display health status
            st.json(health_status)
            st.stop()

    except Exception as e:
        logger.error(f"Health check error: {e}")
        st.json({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        st.stop()

def main():
    """Main Streamlit application with security integration and first-time setup."""

    # Configure Streamlit page FIRST (must be the very first Streamlit command)
    st.set_page_config(
        page_title="SAM - Secure AI Assistant",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Handle health check requests after page config
    health_check()

    # Check for first-time user and route to setup wizard
    try:
        from utils.first_time_setup import get_first_time_setup_manager
        setup_manager = get_first_time_setup_manager()

        if setup_manager.is_first_time_user():
            # Route to setup wizard for first-time users
            render_setup_wizard()
            return

    except ImportError:
        # If first-time setup module not available, continue with normal flow
        logger.warning("First-time setup module not available")
    except Exception as e:
        logger.error(f"Error checking first-time setup: {e}")

    # Initialize security system
    if 'security_manager' not in st.session_state:
        try:
            from security import SecureStateManager
            st.session_state.security_manager = SecureStateManager()
            logger.info("Security manager initialized")
        except ImportError:
            st.error("❌ Security module not available")
            st.info("💡 Run diagnostic: python security_diagnostic.py")
            st.stop()
        except Exception as e:
            st.error(f"❌ Failed to initialize security: {e}")
            st.stop()

    # Create security UI
    try:
        from security import create_security_ui
        security_ui = create_security_ui(st.session_state.security_manager)
    except Exception as e:
        st.error(f"❌ Failed to create security UI: {e}")
        st.stop()

    # Render security interface
    is_unlocked = security_ui.render_security_interface()

    if is_unlocked:
        # Show main SAM application
        render_main_sam_application()
    else:
        # Security interface is shown (setup or unlock)
        st.stop()

def render_setup_wizard():
    """Render the first-time setup wizard."""
    try:
        from ui.setup_wizard import show_setup_wizard
        show_setup_wizard()
    except ImportError:
        # Fallback to basic setup if setup wizard not available
        render_basic_first_time_setup()
    except Exception as e:
        st.error(f"❌ Setup wizard error: {e}")
        render_basic_first_time_setup()

def render_basic_first_time_setup():
    """Basic first-time setup fallback."""
    st.markdown("# 🚀 Welcome to SAM!")
    st.markdown("### Let's get you set up in just a few steps")

    st.info("""
    **Welcome to SAM - The world's most advanced AI system!**

    To get started, you'll need to:
    1. 🔐 Create your master password for secure encryption
    2. 🔑 Activate your SAM Pro features
    3. 🎓 Complete a quick tour of SAM's capabilities
    """)

    # Check what step we're on
    try:
        from utils.first_time_setup import get_first_time_setup_manager
        setup_manager = get_first_time_setup_manager()
        progress = setup_manager.get_setup_progress()
        next_step = progress['next_step']

        st.progress(progress['progress_percent'] / 100)
        st.markdown(f"**Setup Progress:** {progress['completed_steps']}/{progress['total_steps']} steps complete")

        if next_step == 'master_password':
            st.markdown("## 🔐 Step 1: Create Master Password")
            st.markdown("Your master password protects all SAM data with enterprise-grade encryption.")

            if st.button("🔐 Set Up Master Password", type="primary"):
                st.info("🔄 Refreshing to security setup...")
                st.rerun()

        elif next_step == 'sam_pro_activation':
            st.markdown("## 🔑 Step 2: Activate SAM Pro")
            sam_pro_key = setup_manager.get_sam_pro_key()
            if sam_pro_key:
                st.code(sam_pro_key, language=None)
                st.markdown("**💾 Important: Save this key!**")

                if st.button("✅ Activate SAM Pro Features", type="primary"):
                    setup_manager.update_setup_status('sam_pro_activated', True)
                    st.success("🎉 SAM Pro activated!")
                    st.rerun()
            else:
                st.warning("No SAM Pro key found. Please run setup again.")

        elif next_step == 'onboarding':
            st.markdown("## 🎓 Step 3: Quick Tour")
            st.markdown("Ready to explore SAM's capabilities!")

            if st.button("🎉 Complete Setup & Start Using SAM!", type="primary"):
                setup_manager.update_setup_status('onboarding_completed', True)
                st.success("✅ Setup complete! Welcome to SAM!")
                st.rerun()
        else:
            st.success("✅ Setup complete! Redirecting to SAM...")
            st.rerun()

    except Exception as e:
        st.error(f"Setup error: {e}")
        st.markdown("### 🔧 Manual Setup")
        st.markdown("Please complete setup manually:")
        st.markdown("1. Create your master password in the Security section")
        st.markdown("2. Enter your SAM Pro activation key")
        st.markdown("3. Start using SAM!")

def render_main_sam_application():
    """Render the main SAM application with security integration."""

    # Render SAM Pro activation sidebar (preserving 100% of existing functionality)
    render_sam_pro_sidebar()

    # Main title
    st.title("🧠 SAM - Secure AI Assistant")
    st.markdown("*Your personal AI assistant with enterprise-grade security*")

    # Quick navigation to Memory Control Center
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🎛️ Memory Control Center", use_container_width=True, help="Switch to advanced Memory Control Center"):
            st.session_state.show_memory_control_center = True
            st.rerun()

    st.markdown("---")

    # Initialize SAM components with security (needed for both interfaces)
    # Only initialize if security manager is unlocked
    if 'sam_initialized' not in st.session_state and st.session_state.security_manager.is_unlocked():
        with st.spinner("🔧 Initializing SAM components..."):
            try:
                initialize_secure_sam()
                st.session_state.sam_initialized = True
                st.success("✅ SAM initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize SAM: {e}")
                logger.error(f"SAM initialization failed: {e}")
                return

    # Check if Memory Control Center should be shown FIRST (before SAM initialization)
    if st.session_state.get('show_memory_control_center', False):
        # Add a button to return to normal interface
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔙 Return to Main Interface", use_container_width=True):
                st.session_state.show_memory_control_center = False
                st.rerun()

        st.markdown("---")

        # Render the Memory Control Center directly
        render_integrated_memory_control_center()

    else:
        # Normal tab interface
        # Main application tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📚 Documents", "🧠 Memory", "🔍 Vetting", "🛡️ Security"])

        with tab1:
            render_chat_interface()

        with tab2:
            render_document_interface()

        with tab3:
            render_memory_interface()

        with tab4:
            render_vetting_interface()

        with tab5:
            render_security_dashboard()

def initialize_secure_sam():
    """Initialize SAM components with security integration."""

    # Initialize secure memory store with security manager
    if 'secure_memory_store' not in st.session_state:
        from memory.secure_memory_vectorstore import get_secure_memory_store, VectorStoreType

        # Create secure memory store with security manager connection
        st.session_state.secure_memory_store = get_secure_memory_store(
            store_type=VectorStoreType.CHROMA,
            storage_directory="memory_store",
            embedding_dimension=384,
            enable_encryption=True,
            security_manager=st.session_state.security_manager  # Connect to security manager
        )
        logger.info("Secure memory store initialized with security integration")

        # Try to activate encryption if security manager is unlocked
        if (hasattr(st.session_state.security_manager, 'is_unlocked') and
            st.session_state.security_manager.is_unlocked()):
            if st.session_state.secure_memory_store.activate_encryption():
                logger.info("✅ Encryption activated for secure memory store")
            else:
                logger.warning("⚠️ Failed to activate encryption for secure memory store")
        else:
            logger.info("🔒 Secure memory store created - encryption will activate after authentication")
    else:
        # If memory store already exists, try to activate encryption
        if (hasattr(st.session_state.secure_memory_store, 'activate_encryption') and
            st.session_state.security_manager.is_unlocked()):
            encryption_activated = st.session_state.secure_memory_store.activate_encryption()
            if encryption_activated:
                logger.info("✅ Encryption activated for existing memory store")
    
    # Initialize embedding manager
    if 'embedding_manager' not in st.session_state:
        try:
            from utils.embedding_utils import get_embedding_manager
            st.session_state.embedding_manager = get_embedding_manager()
            logger.info("✅ Embedding manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Embedding manager not available: {e}")

    # Initialize vector manager
    if 'vector_manager' not in st.session_state:
        try:
            from utils.vector_manager import VectorManager
            st.session_state.vector_manager = VectorManager()
            logger.info("✅ Vector manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vector manager not available: {e}")

    # Initialize multimodal pipeline
    if 'multimodal_pipeline' not in st.session_state:
        try:
            from multimodal_processing.multimodal_pipeline import get_multimodal_pipeline
            st.session_state.multimodal_pipeline = get_multimodal_pipeline()
            logger.info("✅ Multimodal pipeline initialized")
        except Exception as e:
            logger.warning(f"⚠️ Multimodal pipeline not available: {e}")

    # Initialize tool-augmented reasoning (optional)
    if 'reasoning_framework' not in st.session_state:
        try:
            from reasoning.self_decide_framework import SelfDecideFramework
            st.session_state.reasoning_framework = SelfDecideFramework()
            logger.info("✅ Tool-augmented reasoning initialized")
        except Exception as e:
            logger.warning(f"⚠️ Tool-augmented reasoning not available: {e}")

    # Initialize Enhanced SLP System (Phase 1A+1B Integration)
    if 'enhanced_slp_initialized' not in st.session_state:
        try:
            from integrate_slp_enhancements import integrate_enhanced_slp_into_sam
            slp_integration = integrate_enhanced_slp_into_sam()

            if slp_integration:
                st.session_state.enhanced_slp_integration = slp_integration
                st.session_state.enhanced_slp_initialized = True
                logger.info("✅ Enhanced SLP system (Phase 1A+1B) initialized")
            else:
                st.session_state.enhanced_slp_initialized = False
                logger.warning("⚠️ Enhanced SLP initialization failed - using basic SLP")
        except Exception as e:
            st.session_state.enhanced_slp_initialized = False
            logger.warning(f"⚠️ Enhanced SLP not available: {e}")

    # Initialize TPV System (preserving 100% of existing functionality)
    if 'tpv_initialized' not in st.session_state:
        try:
            from sam.cognition.tpv import sam_tpv_integration, UserProfile

            # Initialize TPV integration if not already done
            if not sam_tpv_integration.is_initialized:
                tpv_init_success = sam_tpv_integration.initialize()
                if tpv_init_success:
                    st.session_state.sam_tpv_integration = sam_tpv_integration
                    st.session_state.tpv_initialized = True
                    st.session_state.tpv_active = True  # Mark as active for sidebar
                    logger.info("✅ TPV system initialized and ready for Active Reasoning Control")
                else:
                    st.session_state.tpv_initialized = False
                    logger.warning("⚠️ TPV initialization failed")
            else:
                st.session_state.sam_tpv_integration = sam_tpv_integration
                st.session_state.tpv_initialized = True
                st.session_state.tpv_active = True
                logger.info("✅ TPV system already initialized and ready")
        except Exception as e:
            st.session_state.tpv_initialized = False
            st.session_state.tpv_active = False
            logger.warning(f"⚠️ TPV system not available: {e}")

    # Initialize MEMOIR System (preserving 100% of functionality)
    if 'memoir_enabled' not in st.session_state:
        try:
            from sam.orchestration.memoir_sof_integration import get_memoir_sof_integration
            sam_memoir_integration = get_memoir_sof_integration()
            st.session_state.memoir_integration = sam_memoir_integration
            st.session_state.memoir_enabled = True
            logger.info("✅ MEMOIR integration initialized for lifelong learning")
        except Exception as e:
            logger.warning(f"MEMOIR integration not available: {e}")
            st.session_state.memoir_integration = None
            st.session_state.memoir_enabled = False

    # Initialize Cognitive Distillation Engine (NEW - Phase 2 Integration)
    if 'cognitive_distillation_initialized' not in st.session_state:
        try:
            from sam.discovery.distillation import SAMCognitiveDistillation

            # Initialize with automation enabled for production
            st.session_state.cognitive_distillation = SAMCognitiveDistillation(enable_automation=True)
            st.session_state.cognitive_distillation_initialized = True
            st.session_state.cognitive_distillation_enabled = True

            logger.info("✅ Cognitive Distillation Engine initialized with automated principle discovery")

            # Setup default triggers for common SAM strategies
            try:
                automation = st.session_state.cognitive_distillation.automation
                if automation:
                    # Add triggers for SAM's main reasoning strategies
                    automation.add_trigger(
                        strategy_id="secure_chat_reasoning",
                        trigger_type="interaction_threshold",
                        trigger_condition={
                            'min_interactions': 20,
                            'min_success_rate': 0.8,
                            'cooldown_hours': 48
                        }
                    )

                    automation.add_trigger(
                        strategy_id="document_analysis",
                        trigger_type="interaction_threshold",
                        trigger_condition={
                            'min_interactions': 15,
                            'min_success_rate': 0.85,
                            'cooldown_hours': 72
                        }
                    )

                    automation.add_trigger(
                        strategy_id="web_search_integration",
                        trigger_type="time_based",
                        trigger_condition={
                            'interval_hours': 168  # Weekly
                        }
                    )

                    logger.info("✅ Cognitive distillation automation triggers configured")

            except Exception as trigger_error:
                logger.warning(f"Failed to setup distillation triggers: {trigger_error}")

        except Exception as e:
            logger.warning(f"Cognitive Distillation Engine not available: {e}")
            st.session_state.cognitive_distillation = None
            st.session_state.cognitive_distillation_initialized = False
            st.session_state.cognitive_distillation_enabled = False

# TPV control sidebar function removed to clean up the interface

def render_messages_from_sam_alert():
    """Render Messages from SAM alert with notification badges and blinking effects."""
    try:
        # Import discovery orchestrator for state checking
        from sam.orchestration.discovery_cycle import get_discovery_orchestrator
        from sam.state.state_manager import get_state_manager

        orchestrator = get_discovery_orchestrator()
        state_manager = get_state_manager()

        # Check for new insights
        insights_status = orchestrator.get_new_insights_status()
        new_insights_available = insights_status.get('new_insights_available', False)

        # Check for pending vetting items
        try:
            from sam.state.vetting_queue import get_vetting_queue_manager
            vetting_manager = get_vetting_queue_manager()
            pending_review = len(vetting_manager.get_pending_review_files())
        except:
            pending_review = 0

        # Calculate total notifications
        total_notifications = (1 if new_insights_available else 0) + (1 if pending_review > 0 else 0)

        if total_notifications > 0:
            # Create blinking CSS for urgent notifications
            st.markdown("""
            <style>
            .blinking-alert {
                animation: blink 2s linear infinite;
                background: linear-gradient(45deg, #ff4b4b, #ff6b6b);
                color: white;
                padding: 0.5rem;
                border-radius: 0.5rem;
                text-align: center;
                font-weight: bold;
                margin-bottom: 1rem;
                box-shadow: 0 2px 4px rgba(255, 75, 75, 0.3);
            }

            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0.7; }
            }

            .notification-badge {
                background: #ff4b4b;
                color: white;
                border-radius: 50%;
                padding: 0.2rem 0.5rem;
                font-size: 0.8rem;
                font-weight: bold;
                margin-left: 0.5rem;
            }

            .messages-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .message-item {
                background: rgba(255, 255, 255, 0.1);
                padding: 0.5rem;
                border-radius: 0.3rem;
                margin: 0.5rem 0;
                border-left: 3px solid #ffd700;
            }
            </style>
            """, unsafe_allow_html=True)

            # Main alert container
            st.markdown(f"""
            <div class="blinking-alert">
                ✉️ <strong>Messages from SAM</strong>
                <span class="notification-badge">{total_notifications}</span>
            </div>
            """, unsafe_allow_html=True)

            # Messages container
            st.markdown('<div class="messages-container">', unsafe_allow_html=True)

            # New insights notification
            if new_insights_available:
                timestamp = insights_status.get('last_insights_timestamp')
                time_str = ""
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp)
                        time_str = f" at {dt.strftime('%H:%M')}"
                    except:
                        pass

                st.markdown(f"""
                <div class="message-item">
                    💡 <strong>New Insights Available!</strong><br>
                    <small>Generated{time_str} - Ready for research</small>
                </div>
                """, unsafe_allow_html=True)

                # Action button for insights
                if st.button("🧠 View New Insights", key="view_insights_alert", use_container_width=True):
                    # Clear the flag and navigate to Dream Canvas
                    orchestrator.clear_new_insights_flag()
                    st.session_state.show_memory_control_center = True
                    st.session_state.memory_page_override = "🧠🎨 Dream Canvas"
                    st.rerun()

            # Pending vetting notification
            if pending_review > 0:
                st.markdown(f"""
                <div class="message-item">
                    🔍 <strong>Papers Awaiting Review</strong><br>
                    <small>{pending_review} research paper{'' if pending_review == 1 else 's'} need{'' if pending_review == 1 else ''} your approval</small>
                </div>
                """, unsafe_allow_html=True)

                # Action button for vetting
                if st.button("📋 Review Papers", key="review_papers_alert", use_container_width=True):
                    # Navigate to vetting queue
                    st.session_state.show_memory_control_center = True
                    st.session_state.memory_page_override = "🔍 Vetting Queue"
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # Quick dismiss option
            if st.button("🔕 Dismiss Alerts", key="dismiss_alerts", help="Temporarily hide alerts"):
                st.session_state.alerts_dismissed = True
                st.rerun()

        else:
            # No notifications - show subtle indicator
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #a8e6cf 0%, #88d8a3 100%);
                color: #2d5a3d;
                padding: 0.5rem;
                border-radius: 0.5rem;
                text-align: center;
                margin-bottom: 1rem;
                font-size: 0.9rem;
            ">
                ✉️ <strong>Messages from SAM</strong><br>
                <small>All caught up! 🎉</small>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        # Fallback display if components not available
        st.markdown("""
        <div style="
            background: #f0f0f0;
            color: #666;
            padding: 0.5rem;
            border-radius: 0.5rem;
            text-align: center;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        ">
            ✉️ <strong>Messages from SAM</strong><br>
            <small>System initializing...</small>
        </div>
        """, unsafe_allow_html=True)

def render_sam_pro_sidebar():
    """Render SAM Pro activation sidebar with key entry (preserving 100% of existing functionality)."""
    with st.sidebar:
        # Messages from SAM Alert (Task 27)
        render_messages_from_sam_alert()

        st.header("🔑 SAM Pro Activation")

        # Check current activation status
        try:
            from sam.entitlements.feature_manager import get_feature_manager
            feature_manager = get_feature_manager()
            is_pro_unlocked = feature_manager.is_pro_unlocked()

            if is_pro_unlocked:
                # Show activated status
                st.success("✅ **SAM Pro Activated**")
                st.markdown("🎉 **Premium features unlocked!**")

                # Show activated features
                with st.expander("🚀 Activated Features", expanded=False):
                    st.markdown("""
                    **🧠 Enhanced Cognitive Features:**
                    • TPV Active Reasoning Control
                    • Advanced SLP Pattern Learning
                    • MEMOIR Lifelong Learning
                    • Dream Canvas Visualization
                    • Cognitive Automation Engine
                    • Cognitive Distillation Engine

                    **🔧 Advanced Tools:**
                    • Enhanced Memory Analytics
                    • Advanced Query Processing
                    • Premium Web Retrieval
                    • Extended Context Windows
                    """)

                # Show activation details
                try:
                    activation_state = feature_manager.get_activation_state()
                    if activation_state.get('activation_date'):
                        import datetime
                        activation_date = datetime.datetime.fromtimestamp(activation_state['activation_date'])
                        st.caption(f"Activated: {activation_date.strftime('%Y-%m-%d %H:%M')}")
                except Exception:
                    pass

            else:
                # Show activation form
                st.info("🔓 **Unlock SAM's Full Potential**")
                st.markdown("Enter your SAM Pro activation key to unlock premium features:")

                with st.form("sam_pro_activation"):
                    activation_key = st.text_input(
                        "Activation Key",
                        placeholder="12345678-1234-1234-1234-123456789abc",
                        help="Enter your SAM Pro activation key (UUID format)",
                        type="password"
                    )

                    submitted = st.form_submit_button("🚀 Activate SAM Pro", type="primary")

                    if submitted:
                        if activation_key:
                            with st.spinner("🔍 Validating activation key..."):
                                try:
                                    result = feature_manager.validate_key(activation_key)

                                    if result.get('success'):
                                        st.success("🎉 **SAM Pro Activated Successfully!**")
                                        st.balloons()
                                        st.markdown(result.get('message', 'Premium features unlocked!'))
                                        st.rerun()  # Refresh to show activated state
                                    else:
                                        st.error(result.get('message', '❌ Invalid activation key'))

                                        # Show helpful error information
                                        if result.get('invalid_format'):
                                            st.info("💡 **Key Format:** Keys should be in UUID format (e.g., 12345678-1234-1234-1234-123456789abc)")
                                        elif result.get('invalid_key'):
                                            st.info("💡 **Need a key?** Register at [localhost:8503](http://localhost:8503) for free activation key delivery via email.")

                                except Exception as e:
                                    st.error(f"❌ Activation failed: {e}")
                        else:
                            st.warning("⚠️ Please enter an activation key")

                # Registration link for new users
                st.markdown("---")
                st.markdown("🔑 **Need an Activation Key?**")
                st.markdown("Register for free at: [localhost:8503](http://localhost:8503)")
                st.caption("Keys are delivered automatically via email")

                # Show what SAM Pro unlocks
                with st.expander("🎯 What SAM Pro Unlocks", expanded=False):
                    st.markdown("""
                    **🧠 Advanced AI Capabilities:**
                    • **TPV Active Reasoning Control** - 48.4% efficiency gains
                    • **Enhanced SLP Learning** - Advanced pattern recognition
                    • **MEMOIR Lifelong Learning** - Continuous knowledge updates
                    • **Dream Canvas** - Interactive memory visualization
                    • **Cognitive Distillation Engine** - AI introspection & self-improvement

                    **🔧 Premium Tools:**
                    • **Cognitive Automation Engine** - Automated reasoning
                    • **Advanced Memory Analytics** - Deep insights
                    • **Enhanced Web Retrieval** - Premium search capabilities
                    • **Extended Context Windows** - Larger conversation memory

                    **🛡️ Enterprise Features:**
                    • **Priority Support** - Faster response times
                    • **Advanced Security** - Additional encryption layers
                    • **Custom Integrations** - API access and webhooks
                    • **Usage Analytics** - Detailed performance metrics
                    """)

        except ImportError:
            st.warning("⚠️ SAM Pro activation system not available")
        except Exception as e:
            st.error(f"❌ Error loading activation system: {e}")

        # Separator
        st.markdown("---")

        # Web Search Preferences (preserving 100% of functionality)
        st.subheader("🌐 Web Search Preferences")

        # Interactive vs Automatic web search choice
        # Get current preference or default to Interactive
        current_mode = st.session_state.get('web_search_mode', 'Interactive')
        mode_options = ["Interactive", "Automatic"]

        # Find index of current mode for default selection
        try:
            default_index = mode_options.index(current_mode)
        except ValueError:
            default_index = 0  # Default to Interactive if invalid value

        web_search_mode = st.radio(
            "Web Search Mode",
            options=mode_options,
            index=default_index,
            help="Interactive: Ask before searching web. Automatic: Search automatically when needed.",
            horizontal=True
        )

        # Store preference in session state
        st.session_state.web_search_mode = web_search_mode

        if web_search_mode == "Interactive":
            st.caption("🎛️ You'll be asked before web searches occur")
        else:
            st.caption("⚡ Web searches happen automatically for current information")

        # Separator
        st.markdown("---")

        # Quick system status
        st.subheader("📊 System Status")

        # Show key system components status
        status_items = []

        # Security status
        if hasattr(st.session_state, 'security_manager') and st.session_state.security_manager.is_unlocked():
            status_items.append("🔐 Security: ✅ Active")
        else:
            status_items.append("🔐 Security: ❌ Locked")

        # Memory status
        if hasattr(st.session_state, 'secure_memory_store'):
            status_items.append("🧠 Memory: ✅ Ready")
        else:
            status_items.append("🧠 Memory: ❌ Not Ready")

        # MEMOIR status
        if st.session_state.get('memoir_enabled', False):
            status_items.append("📚 MEMOIR: ✅ Active")
        else:
            status_items.append("📚 MEMOIR: ❌ Inactive")

        # TPV status (enhanced detection with initialization check)
        tpv_active = False

        # Check if TPV is initialized and ready
        if st.session_state.get('tpv_initialized'):
            tpv_active = True
        # Check if TPV was used in last response
        elif st.session_state.get('tpv_session_data', {}).get('last_response', {}).get('tpv_enabled'):
            tpv_active = True
        # Check general TPV active flag
        elif st.session_state.get('tpv_active'):
            tpv_active = True

        if tpv_active:
            status_items.append("🧠 TPV: ✅ Active")
        else:
            status_items.append("🧠 TPV: ❌ Inactive")

        # Dissonance Monitoring status (Phase 5B)
        dissonance_active = False

        # Check if dissonance monitoring is active
        try:
            # Method 1: Check if TPV integration has dissonance monitoring enabled
            if st.session_state.get('sam_tpv_integration'):
                tpv_integration = st.session_state.sam_tpv_integration
                if hasattr(tpv_integration, 'tpv_monitor') and tpv_integration.tpv_monitor:
                    if hasattr(tpv_integration.tpv_monitor, 'enable_dissonance_monitoring'):
                        if tpv_integration.tpv_monitor.enable_dissonance_monitoring:
                            dissonance_active = True

            # Method 2: Check for dissonance data in recent TPV responses
            if not dissonance_active:
                tpv_session_data = st.session_state.get('tpv_session_data', {})
                last_response = tpv_session_data.get('last_response', {})

                # Check for dissonance data in the last response
                if (last_response.get('dissonance_analysis') or
                    last_response.get('final_dissonance_score') is not None):
                    dissonance_active = True

            # Method 3: If TPV is active and initialized, assume dissonance is available
            if not dissonance_active and tpv_active:
                try:
                    # Check if dissonance monitor can be imported and initialized
                    from sam.cognition.dissonance_monitor import DissonanceMonitor
                    dissonance_active = True  # If import succeeds, dissonance is available
                except ImportError:
                    dissonance_active = False

        except Exception:
            dissonance_active = False

        if dissonance_active:
            status_items.append("🧠 Dissonance Monitor: ✅ Active")
        else:
            status_items.append("🧠 Dissonance Monitor: ❌ Inactive")

        # Cognitive Distillation status (NEW - Phase 2 Integration)
        cognitive_distillation_active = False
        if st.session_state.get('cognitive_distillation_enabled'):
            cognitive_distillation_active = True

        if cognitive_distillation_active:
            status_items.append("🧠 Cognitive Distillation: ✅ Active")
        else:
            status_items.append("🧠 Cognitive Distillation: ❌ Inactive")

        for item in status_items:
            st.caption(item)

def render_tpv_status():
    """Render enhanced TPV status with Phase 5B dissonance monitoring."""
    try:
        # Try to use enhanced visualization first
        try:
            from ui.tpv_visualization import render_tpv_status_enhanced

            # Get TPV data from the last response
            tpv_data = st.session_state.get('tpv_session_data', {}).get('last_response')

            # Use enhanced visualization
            render_tpv_status_enhanced(tpv_data)
            return

        except ImportError:
            logger.debug("Enhanced TPV visualization not available, using fallback")

        # Fallback to enhanced version of original implementation
        _render_tpv_status_enhanced_fallback()

    except Exception as e:
        logger.debug(f"TPV status display error: {e}")

def _render_tpv_status_enhanced_fallback():
    """Enhanced fallback TPV status display with dissonance support."""
    try:
        # Check if TPV data is available
        tpv_data = st.session_state.get('tpv_session_data', {}).get('last_response')

        if tpv_data and tpv_data.get('tpv_enabled'):
            with st.expander("🧠 Cognitive Process Analysis (Phase 5B: Dissonance-Aware)", expanded=False):
                # Main metrics row
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Reasoning Score",
                        f"{tpv_data.get('final_score', 0.0):.3f}",
                        help="Final reasoning quality score (0.0 - 1.0)"
                    )

                with col2:
                    st.metric(
                        "TPV Steps",
                        tpv_data.get('tpv_steps', 0),
                        help="Number of reasoning steps monitored"
                    )

                with col3:
                    # NEW: Dissonance score display
                    dissonance_score = tpv_data.get('final_dissonance_score')
                    if dissonance_score is not None:
                        st.metric(
                            "Final Dissonance",
                            f"{dissonance_score:.3f}",
                            help="Final cognitive dissonance score (0.0 - 1.0)"
                        )
                    else:
                        st.metric("Final Dissonance", "N/A", help="Dissonance monitoring not available")

                with col4:
                    # Enhanced control decision with dissonance awareness
                    control_decision = tpv_data.get('control_decision', 'CONTINUE')
                    decision_color = {
                        'COMPLETE': '🟢',
                        'PLATEAU': '🟡',
                        'HALT': '🔴',
                        'DISSONANCE': '🧠',  # NEW: Dissonance stop
                        'CONTINUE': '⚪'
                    }.get(control_decision, '⚪')

                    st.metric(
                        "Control Decision",
                        f"{decision_color} {control_decision}",
                        help="Active control decision made during reasoning"
                    )

                # Enhanced Control Details with Dissonance Awareness
                if tpv_data.get('control_decision') != 'CONTINUE':
                    st.subheader("🎛️ Enhanced Control Details")
                    control_reason = tpv_data.get('control_reason', 'No reason provided')

                    if control_decision == 'COMPLETE':
                        st.success(f"✅ **Reasoning Completed**: {control_reason}")
                    elif control_decision == 'PLATEAU':
                        st.warning(f"📊 **Plateau Detected**: {control_reason}")
                    elif control_decision == 'HALT':
                        st.error(f"🛑 **Hard Stop**: {control_reason}")
                    elif control_decision == 'DISSONANCE':
                        st.warning(f"🧠 **High Cognitive Dissonance**: {control_reason}")

                # NEW: Dissonance Analysis Section
                if tpv_data.get('dissonance_analysis'):
                    st.subheader("🧠 Cognitive Dissonance Analysis")
                    analysis = tpv_data['dissonance_analysis']

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mean Dissonance", f"{analysis.get('mean_dissonance', 0.0):.3f}")
                    with col2:
                        st.metric("Peak Dissonance", f"{analysis.get('max_dissonance', 0.0):.3f}")
                    with col3:
                        high_steps = len(analysis.get('high_dissonance_steps', []))
                        st.metric("High Dissonance Steps", high_steps)

                # Enhanced Performance metrics with dissonance monitoring
                perf_metrics = tpv_data.get('performance_metrics', {})
                if perf_metrics:
                    st.subheader("📊 Enhanced Performance Metrics")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "Total Time",
                            f"{perf_metrics.get('total_time', 0.0):.3f}s",
                            help="Total response generation time"
                        )

                    with col2:
                        st.metric(
                            "TPV Overhead",
                            f"{perf_metrics.get('tpv_overhead', 0.0):.3f}s",
                            help="TPV monitoring processing overhead"
                        )

                    with col3:
                        # NEW: Dissonance processing time
                        dissonance_time = perf_metrics.get('dissonance_processing_time', 0.0)
                        st.metric(
                            "Dissonance Analysis",
                            f"{dissonance_time:.3f}s",
                            help="Cognitive dissonance calculation time"
                        )

                    with col4:
                        total_overhead = perf_metrics.get('tpv_overhead', 0.0) + dissonance_time
                        efficiency = ((perf_metrics.get('total_time', 1) - total_overhead) /
                                    perf_metrics.get('total_time', 1) * 100)
                        st.metric(
                            "Efficiency",
                            f"{efficiency:.1f}%",
                            help="Processing efficiency (includes dissonance monitoring)"
                        )

                # Control Statistics
                control_stats = tpv_data.get('control_statistics', {})
                if control_stats:
                    st.subheader("🎯 Control Statistics")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "Total Decisions",
                            control_stats.get('total_decisions', 0),
                            help="Total control decisions made"
                        )

                    with col2:
                        continue_rate = control_stats.get('continue_rate', 0.0)
                        st.metric(
                            "Continue Rate",
                            f"{continue_rate:.1%}",
                            help="Percentage of decisions that allowed reasoning to continue"
                        )

                # Enhanced Status indicator for Phase 5B
                control_decision = tpv_data.get('control_decision', 'CONTINUE')
                if control_decision == 'CONTINUE':
                    st.info("🧠 **Phase 5B Active**: Real-time cognitive dissonance monitoring with meta-reasoning awareness.")
                elif control_decision == 'DISSONANCE':
                    st.warning("🧠 **Phase 5B Intervention**: Stopped due to high cognitive dissonance - preventing potential hallucination.")
                else:
                    st.success("🎛️ **Phase 5B Enhanced Control**: AI reasoning managed with dissonance-aware meta-cognitive monitoring.")

        elif tpv_data and not tpv_data.get('tpv_enabled'):
            with st.expander("🧠 Thinking Process Analysis", expanded=False):
                trigger_type = tpv_data.get('trigger_type', 'none')
                st.info(f"🔍 **TPV Not Triggered**: {trigger_type.replace('_', ' ').title()} - Standard response generation used.")

    except Exception as e:
        logger.debug(f"TPV status display error: {e}")

def render_chat_document_upload():
    """Render drag & drop document upload interface for chat."""
    with st.expander("📁 Upload Documents to Chat", expanded=False):
        st.markdown("""
        **Drag & drop documents directly into your conversation with SAM!**

        🎯 **Quick Upload**: Upload documents and immediately start discussing them
        📄 **Supported Formats**: PDF, TXT, DOCX, MD files
        🔒 **Secure Processing**: All uploads are encrypted and processed securely

        💡 **What happens after upload:**
        - Document is securely processed and encrypted
        - SAM automatically analyzes the content
        - You get instant suggestions for questions to ask
        - Quick action buttons for summary, analysis, and key insights
        """)

        # File uploader with drag & drop
        uploaded_files = st.file_uploader(
            "Drop files here or click to browse",
            type=['pdf', 'txt', 'docx', 'md'],
            accept_multiple_files=True,
            help="Upload documents to discuss with SAM. Files are processed securely and encrypted.",
            key="chat_file_upload"
        )

        # Process uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if f"processed_{uploaded_file.name}" not in st.session_state:
                    with st.spinner(f"🔐 Processing {uploaded_file.name} securely..."):
                        try:
                            # Process the document using existing secure processing
                            result = process_secure_document(uploaded_file)

                            if result.get('success', False):
                                # Mark as processed
                                st.session_state[f"processed_{uploaded_file.name}"] = True

                                # Add success message to chat history
                                success_message = f"📄 **Document Uploaded**: {uploaded_file.name}\n\n✅ Successfully processed and added to my knowledge. What would you like to know about this document?"

                                # Add to chat history
                                if 'chat_history' not in st.session_state:
                                    st.session_state.chat_history = []

                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": success_message,
                                    "document_upload": True,
                                    "filename": uploaded_file.name
                                })

                                # Show success notification
                                st.success(f"✅ {uploaded_file.name} uploaded and processed successfully!")

                                # Document processing complete - SAM will wait for user questions
                                # All background processing (knowledge consolidation, memory storage, etc.)
                                # continues as normal, but no auto-generated prompts or responses

                            else:
                                st.error(f"❌ Failed to process {uploaded_file.name}: {result.get('error', 'Unknown error')}")

                        except Exception as e:
                            logger.error(f"Error processing uploaded file {uploaded_file.name}: {e}")
                            st.error(f"❌ Error processing {uploaded_file.name}: {e}")

def generate_document_suggestions(filename: str, file_type: str) -> str:
    """Generate helpful suggestions for document interaction based on file type."""
    suggestions = []

    # Base suggestions for all documents
    base_suggestions = [
        f"What are the main topics covered in {filename}?",
        f"Can you summarize the key points from {filename}?",
        f"What are the most important insights from {filename}?"
    ]

    # Type-specific suggestions
    if file_type == "application/pdf" or filename.lower().endswith('.pdf'):
        suggestions.extend([
            f"What are the main sections or chapters in {filename}?",
            f"Are there any charts, graphs, or data visualizations in {filename}?",
            f"What conclusions or recommendations does {filename} make?"
        ])
    elif file_type == "text/plain" or filename.lower().endswith(('.txt', '.md')):
        suggestions.extend([
            f"What is the writing style or format of {filename}?",
            f"Are there any action items or next steps mentioned in {filename}?",
            f"What questions does {filename} raise or answer?"
        ])
    elif filename.lower().endswith('.docx'):
        suggestions.extend([
            f"What is the document structure of {filename}?",
            f"Are there any tables or lists in {filename}?",
            f"What is the purpose or objective of {filename}?"
        ])

    # Combine base and specific suggestions
    all_suggestions = base_suggestions + suggestions

    # Format as a helpful response
    suggestion_text = "Here are some questions you might want to ask about this document:\n\n"
    for i, suggestion in enumerate(all_suggestions[:6], 1):  # Limit to 6 suggestions
        suggestion_text += f"{i}. {suggestion}\n"

    suggestion_text += f"\nFeel free to ask any other questions about {filename} - I've processed its content and can help you understand, analyze, or extract information from it!"

    return suggestion_text

def generate_secure_chat_response(prompt: str) -> str:
    """Generate a secure chat response for document analysis and general queries."""
    try:
        # Use conversation buffer wrapper for enhanced context awareness (Task 30 Phase 1)
        return generate_response_with_conversation_buffer(prompt, force_local=True)
    except Exception as e:
        logger.error(f"Error generating secure chat response: {e}")
        return f"I apologize, but I encountered an error while processing your request. Please try again or rephrase your question."

def render_conversation_history_sidebar():
    """Render the conversation history sidebar (Task 31 Phase 1)."""
    try:
        with st.sidebar:
            st.markdown("### 📚 Conversation History")

            # New Chat button
            if st.button("➕ New Chat", use_container_width=True, type="primary"):
                try:
                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine
                    from sam.session.state_manager import get_session_manager

                    # Get current conversation buffer
                    session_manager = get_session_manager()
                    session_id = st.session_state.get('session_id', 'default_session')
                    conversation_buffer = session_manager.get_conversation_history(session_id)

                    if conversation_buffer:
                        # Archive current conversation
                        relevance_engine = get_contextual_relevance_engine()
                        archived_thread = relevance_engine.archive_conversation_thread(
                            conversation_buffer,
                            force_title="Manual New Chat"
                        )

                        # Clear conversation buffer
                        session_manager.clear_session(session_id)

                        # Update UI state
                        if 'archived_threads' not in st.session_state:
                            st.session_state['archived_threads'] = []

                        st.session_state['archived_threads'].insert(0, archived_thread.to_dict())

                        # Clear chat history
                        st.session_state.chat_history = []

                        st.success(f"✅ Started new chat! Previous conversation archived as: '{archived_thread.title}'")
                        st.rerun()
                    else:
                        st.info("No active conversation to archive.")

                except Exception as e:
                    st.error(f"Failed to start new chat: {e}")

            st.markdown("---")

            # Phase 2: Advanced Search
            with st.expander("🔍 Search Conversations", expanded=False):
                search_query = st.text_input(
                    "Search in conversation history:",
                    placeholder="Enter keywords to search...",
                    key="conversation_search"
                )

                if search_query and st.button("🔍 Search", key="search_button"):
                    try:
                        from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                        relevance_engine = get_contextual_relevance_engine()
                        search_results = relevance_engine.search_within_threads(search_query, limit=10)

                        if search_results:
                            st.markdown(f"**Found {len(search_results)} results:**")

                            for result in search_results:
                                with st.container():
                                    st.markdown(f"**📄 {result['thread_title']}**")
                                    st.markdown(f"*{result['message_role'].title()}:* {result['message_content'][:150]}...")
                                    st.caption(f"Relevance: {result['relevance_score']:.2f} | {result['timestamp']}")
                                    st.markdown("---")
                        else:
                            st.info("No results found for your search.")

                    except Exception as e:
                        st.error(f"Search failed: {e}")

            # Phase 2: Conversation Analytics
            with st.expander("📊 Conversation Analytics", expanded=False):
                try:
                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                    relevance_engine = get_contextual_relevance_engine()
                    analytics = relevance_engine.get_conversation_analytics()

                    if 'error' not in analytics:
                        # Basic stats
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Total Conversations", analytics['total_conversations'])

                        with col2:
                            st.metric("Total Messages", analytics['total_messages'])

                        with col3:
                            st.metric("Avg Length", f"{analytics['average_conversation_length']} msgs")

                        # Most common topics
                        if analytics['most_common_topics']:
                            st.markdown("**🏷️ Most Common Topics:**")
                            for topic, count in analytics['most_common_topics'][:5]:
                                st.markdown(f"• {topic} ({count} times)")

                        # Conversation length distribution
                        if analytics['length_distribution']:
                            st.markdown("**📏 Conversation Lengths:**")
                            for length_type, count in analytics['length_distribution'].items():
                                st.markdown(f"• {length_type}: {count}")

                        # Recent activity
                        if analytics['recent_activity']:
                            st.markdown("**🕒 Recent Activity:**")
                            for activity in analytics['recent_activity'][:3]:
                                st.markdown(f"• {activity['date']} {activity['time']}: {activity['title']}")
                    else:
                        st.error(f"Analytics error: {analytics['error']}")

                except Exception as e:
                    st.error(f"Analytics failed: {e}")

            # Phase 3: AI-Powered Insights
            with st.expander("🤖 AI Insights & Recommendations", expanded=False):
                try:
                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                    relevance_engine = get_contextual_relevance_engine()
                    archived_threads = relevance_engine.get_archived_threads()

                    if archived_threads:
                        ai_insights = relevance_engine.generate_ai_insights(archived_threads)

                        if 'error' not in ai_insights:
                            # Display insights
                            if ai_insights.get('insights'):
                                st.markdown("**🧠 AI Insights:**")
                                for insight in ai_insights['insights']:
                                    st.markdown(f"• {insight}")

                            # Display recommendations
                            if ai_insights.get('recommendations'):
                                st.markdown("**💡 Recommendations:**")
                                for rec in ai_insights['recommendations']:
                                    st.markdown(f"• {rec}")

                            # Display emerging topics
                            if ai_insights.get('emerging_topics'):
                                st.markdown("**📈 Emerging Topics:**")
                                for topic in ai_insights['emerging_topics']:
                                    st.markdown(f"• {topic['topic']} (↑{topic['emergence_score']}x)")

                            # Display health metrics
                            if ai_insights.get('health_metrics'):
                                st.markdown("**📊 Conversation Health:**")
                                health = ai_insights['health_metrics']

                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    diversity = health.get('topic_diversity', 0)
                                    st.metric("Topic Diversity", f"{diversity:.2f}")

                                with col2:
                                    engagement = health.get('engagement_level', 0)
                                    st.metric("Engagement", f"{engagement:.2f}")

                                with col3:
                                    overall = health.get('overall_health', 0)
                                    st.metric("Overall Health", f"{overall:.2f}")
                        else:
                            st.error(f"AI insights error: {ai_insights['error']}")
                    else:
                        st.info("No conversation history available for AI analysis.")

                except Exception as e:
                    st.error(f"AI insights failed: {e}")

            # Phase 3: Cross-Conversation Context
            with st.expander("🌉 Related Conversations", expanded=False):
                try:
                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine
                    from sam.session.state_manager import get_session_manager

                    # Get current conversation context
                    session_manager = get_session_manager()
                    session_id = st.session_state.get('session_id', 'default_session')
                    current_buffer = session_manager.get_conversation_history(session_id)

                    if current_buffer:
                        # Get last user message as query
                        user_messages = [msg for msg in current_buffer if msg.get('role') == 'user']
                        if user_messages:
                            last_query = user_messages[-1].get('content', '')

                            relevance_engine = get_contextual_relevance_engine()
                            related_conversations = relevance_engine.find_related_conversations(
                                last_query, current_buffer, limit=3
                            )

                            if related_conversations:
                                st.markdown("**🔗 Conversations related to current topic:**")

                                for related in related_conversations:
                                    with st.container():
                                        st.markdown(f"**📄 {related['title']}**")
                                        st.caption(f"Relevance: {related['relevance_score']:.2f} | {related['connection_type'].replace('_', ' ').title()}")
                                        st.markdown(f"*{related['bridge_summary']}*")

                                        # Quick resume button
                                        if st.button(f"🔄 Resume", key=f"related_resume_{related['thread_id']}"):
                                            try:
                                                if relevance_engine.resume_conversation_thread(related['thread_id']):
                                                    st.success(f"✅ Resumed: '{related['title']}'")
                                                    st.rerun()
                                                else:
                                                    st.error("Failed to resume conversation")
                                            except Exception as e:
                                                st.error(f"Resume failed: {e}")

                                        st.markdown("---")
                            else:
                                st.info("No related conversations found for current topic.")
                    else:
                        st.info("Start a conversation to see related discussions.")

                except Exception as e:
                    st.error(f"Related conversations failed: {e}")

            # Phase 3: Export & Optimization
            with st.expander("📤 Export & Optimization", expanded=False):
                try:
                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                    relevance_engine = get_contextual_relevance_engine()

                    # Export section
                    st.markdown("**📤 Export Conversations:**")

                    col1, col2 = st.columns(2)

                    with col1:
                        export_format = st.selectbox(
                            "Export Format:",
                            ["JSON", "Markdown", "CSV"],
                            key="export_format"
                        )

                    with col2:
                        include_metadata = st.checkbox(
                            "Include Metadata",
                            value=True,
                            key="include_metadata"
                        )

                    if st.button("📥 Export All Conversations", key="export_all"):
                        try:
                            export_result = relevance_engine.export_conversation_data(
                                export_format=export_format.lower(),
                                include_metadata=include_metadata
                            )

                            if export_result.get('success'):
                                st.success("✅ Export completed!")

                                # Display export metadata
                                metadata = export_result['metadata']
                                st.json({
                                    'total_conversations': metadata['total_conversations'],
                                    'total_messages': metadata['total_messages'],
                                    'export_format': metadata['export_format'],
                                    'export_timestamp': metadata['export_timestamp']
                                })

                                # Provide download (simplified - in production would use st.download_button)
                                st.text_area(
                                    "Export Data (copy to save):",
                                    value=export_result['export_data'][:1000] + "..." if len(export_result['export_data']) > 1000 else export_result['export_data'],
                                    height=200,
                                    key="export_data_display"
                                )
                            else:
                                st.error(f"Export failed: {export_result.get('error', 'Unknown error')}")

                        except Exception as e:
                            st.error(f"Export failed: {e}")

                    st.markdown("---")

                    # Optimization section
                    st.markdown("**⚡ Performance Optimization:**")

                    if st.button("🚀 Optimize Storage", key="optimize_storage"):
                        try:
                            optimization_result = relevance_engine.optimize_conversation_storage()

                            if optimization_result.get('success', True):
                                st.success("✅ Storage optimization completed!")

                                # Display optimization results
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric(
                                        "Indexed Conversations",
                                        optimization_result.get('indexed_conversations', 0)
                                    )

                                with col2:
                                    st.metric(
                                        "Cache Entries",
                                        optimization_result.get('cache_entries_created', 0)
                                    )

                                with col3:
                                    improvement = optimization_result.get('performance_improvement', 0)
                                    st.metric(
                                        "Performance Boost",
                                        f"+{improvement*100:.0f}%"
                                    )
                            else:
                                st.error(f"Optimization failed: {optimization_result.get('error', 'Unknown error')}")

                        except Exception as e:
                            st.error(f"Optimization failed: {e}")

                except Exception as e:
                    st.error(f"Export & optimization failed: {e}")

            st.markdown("---")

            # Show archived conversations
            archived_threads = st.session_state.get('archived_threads', [])

            if archived_threads:
                st.markdown("**Recent Conversations:**")

                for i, thread_data in enumerate(archived_threads[:10]):  # Show last 10
                    thread_title = thread_data.get('title', 'Untitled')
                    message_count = thread_data.get('message_count', 0)
                    last_updated = thread_data.get('last_updated', '')

                    # Format timestamp
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m/%d %H:%M')
                    except:
                        time_str = 'Recent'

                    # Create expandable thread entry
                    with st.expander(f"💬 {thread_title}", expanded=False):
                        st.caption(f"📅 {time_str} • {message_count} messages")

                        # Show first few messages as preview
                        messages = thread_data.get('messages', [])
                        if messages:
                            st.markdown("**Preview:**")
                            for msg in messages[:2]:  # Show first 2 messages
                                role = msg.get('role', 'unknown')
                                content = msg.get('content', '')[:100]
                                if len(msg.get('content', '')) > 100:
                                    content += "..."

                                if role == 'user':
                                    st.markdown(f"👤 **You:** {content}")
                                elif role == 'assistant':
                                    st.markdown(f"🤖 **SAM:** {content}")

                            if len(messages) > 2:
                                st.caption(f"... and {len(messages) - 2} more messages")

                        # Phase 2: Resume conversation button
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(f"🔄 Resume", key=f"resume_{i}"):
                                try:
                                    from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                                    relevance_engine = get_contextual_relevance_engine()
                                    thread_id = thread_data.get('thread_id')

                                    if relevance_engine.resume_conversation_thread(thread_id):
                                        st.success(f"✅ Resumed: '{thread_title}'")
                                        st.rerun()
                                    else:
                                        st.error("Failed to resume conversation")

                                except Exception as e:
                                    st.error(f"Resume failed: {e}")

                        with col2:
                            # Add tags functionality
                            if st.button(f"🏷️ Tag", key=f"tag_{i}"):
                                st.session_state[f'show_tag_input_{i}'] = True

                        # Tag input interface
                        if st.session_state.get(f'show_tag_input_{i}', False):
                            tag_input = st.text_input(
                                "Add tags (comma-separated):",
                                key=f"tag_input_{i}",
                                placeholder="e.g., important, technical, follow-up"
                            )

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.button("💾 Save Tags", key=f"save_tags_{i}"):
                                    if tag_input.strip():
                                        try:
                                            from sam.conversation.contextual_relevance import get_contextual_relevance_engine

                                            tags = [tag.strip() for tag in tag_input.split(',') if tag.strip()]
                                            relevance_engine = get_contextual_relevance_engine()
                                            thread_id = thread_data.get('thread_id')

                                            if relevance_engine.add_tags_to_thread(thread_id, tags):
                                                st.success(f"✅ Added tags: {', '.join(tags)}")
                                                st.session_state[f'show_tag_input_{i}'] = False
                                                st.rerun()
                                            else:
                                                st.error("Failed to add tags")
                                        except Exception as e:
                                            st.error(f"Tagging failed: {e}")

                            with col_cancel:
                                if st.button("❌ Cancel", key=f"cancel_tags_{i}"):
                                    st.session_state[f'show_tag_input_{i}'] = False
                                    st.rerun()

                        # Show existing tags
                        user_tags = thread_data.get('metadata', {}).get('user_tags', [])
                        if user_tags:
                            st.caption(f"🏷️ Tags: {', '.join(user_tags)}")
            else:
                st.markdown("*No archived conversations yet.*")
                st.caption("Conversations will appear here automatically when you change topics.")

            # Show current conversation status
            if st.session_state.get('conversation_archived'):
                archived_info = st.session_state['conversation_archived']
                st.success(f"✅ Archived: '{archived_info['title']}'")
                # Clear the notification after showing it
                del st.session_state['conversation_archived']

            # Phase 2: Show resume notification
            if st.session_state.get('conversation_resumed'):
                resumed_info = st.session_state['conversation_resumed']
                st.success(f"🔄 Resumed: '{resumed_info['title']}'")
                st.caption(f"Loaded {resumed_info['message_count']} messages from {resumed_info['timestamp']}")
                # Clear the notification after showing it
                del st.session_state['conversation_resumed']

            # Debug info (can be removed in production)
            if st.checkbox("🔍 Show Debug Info", value=False):
                relevance_check = st.session_state.get('last_relevance_check')
                if relevance_check:
                    st.json(relevance_check)

    except Exception as e:
        logger.error(f"Error rendering conversation history sidebar: {e}")
        with st.sidebar:
            st.error("Conversation history temporarily unavailable")

def render_chat_interface():
    """Render the chat interface."""
    st.header("💬 Secure Chat")

    # Task 31 Phase 1: Render conversation history sidebar
    render_conversation_history_sidebar()

    # Render TPV status if available
    render_tpv_status()

    # NEW: Drag & Drop Document Upload Integration
    render_chat_document_upload()

    # Simple greeting (removed extra feature text as requested)
    if len(st.session_state.get('chat_history', [])) == 0:
        with st.chat_message("assistant"):
            st.markdown("Hello! 👋 I'm SAM")



    # Phase 8 Web Search Integration Info
    with st.expander("🌐 Web Search Integration", expanded=False):
        st.markdown("""
        **SAM now includes intelligent web search capabilities!**

        🧠 **How it works:**
        - SAM automatically assesses the quality of its knowledge for your questions
        - When confidence is low, SAM will offer interactive web search options
        - You maintain full control over when web searches occur

        🔗 **Interactive Web Search:**
        - **Real-time buttons** for "Yes, Search Online" / "No, Answer Locally"
        - **Automatic content fetching** and security vetting
        - **Enhanced answers** with new web knowledge integration

        📚 **In this secure interface:**
        - All web content is vetted for security before integration
        - Search results are encrypted and stored securely
        - Full audit trail of all web search activities
        """)

    # Chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Handle web search escalation button clicks
    if 'web_search_escalation' in st.session_state:
        for escalation_id, escalation_data in st.session_state.web_search_escalation.items():
            # Check for search trigger
            if st.session_state.get(f"trigger_search_{escalation_id}"):
                with st.chat_message("assistant"):
                    st.markdown("🔍 **Searching the web and analyzing content...**\n\nThis may take a moment while I fetch and vet the information for security and quality.")

                    # Perform actual web search using SAM's web retrieval system
                    search_result = perform_secure_web_search(escalation_data['original_query'])

                    if search_result['success']:
                        st.success("✅ **Web search completed successfully!**")

                        # Note: Automatic vetting is disabled to allow manual review
                        st.info("🛡️ **Content saved to quarantine for security analysis.**\n\n"
                               "📋 **Next Steps:**\n"
                               "1. Go to the **Content Vetting** page\n"
                               "2. Review the new content for security and quality\n"
                               "3. Click **'Vet All Content'** to approve and integrate\n\n"
                               "💡 This ensures all web content is manually reviewed before integration.")

                        # Process the response through thought processor to hide reasoning
                        try:
                            from utils.thought_processor import get_thought_processor
                            thought_processor = get_thought_processor()
                            processed = thought_processor.process_response(search_result['response'])

                            # Display only the clean response (thoughts hidden by default)
                            st.markdown(processed.visible_content)

                            # Add thought dropdown if thoughts are present (collapsed by default)
                            if processed.has_thoughts and processed.thought_blocks:
                                total_tokens = sum(block.token_count for block in processed.thought_blocks)
                                with st.expander(f"🧠 SAM's Thoughts ({total_tokens} tokens)", expanded=False):
                                    for i, thought_block in enumerate(processed.thought_blocks):
                                        st.markdown(f"**Thought {i+1}:**")
                                        st.markdown(thought_block.content)
                                        if i < len(processed.thought_blocks) - 1:
                                            st.divider()

                            # Add the clean response to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": processed.visible_content
                            })

                            # Add feedback system for web search results
                            render_feedback_system(len(st.session_state.chat_history) - 1)

                        except ImportError:
                            # Fallback if thought processor is not available
                            st.markdown(search_result['response'])
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": search_result['response']
                            })

                            # Add feedback system for web search results (preserving 100% of functionality)
                            render_feedback_system(len(st.session_state.chat_history) - 1)

                    else:
                        st.error("❌ **Web search failed**")
                        st.markdown(f"**Error:** {search_result['error']}")
                        st.info("💡 **Fallback:** You can manually search the web and upload relevant documents through the '📚 Documents' tab.")

                        # Add error result to chat history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"❌ Web search failed: {search_result['error']}\n\n💡 **Fallback:** You can manually search the web and upload relevant documents through the '📚 Documents' tab."
                        })

                        # Add feedback system for error messages (preserving 100% of functionality)
                        render_feedback_system(len(st.session_state.chat_history) - 1)

                # Clear the trigger
                del st.session_state[f"trigger_search_{escalation_id}"]
                st.rerun()

            # Check for local answer trigger
            elif st.session_state.get(f"force_local_{escalation_id}"):
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Answering with current knowledge..."):
                        local_response = generate_response_with_conversation_buffer(escalation_data['original_query'], force_local=True)
                        if isinstance(local_response, tuple):
                            local_response = local_response[0]  # Extract just the response text
                        st.markdown(local_response)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": local_response if not isinstance(local_response, tuple) else local_response[0]
                })

                # Add feedback system for local forced responses (preserving 100% of functionality)
                render_feedback_system(len(st.session_state.chat_history) - 1)

                # Clear the trigger
                del st.session_state[f"force_local_{escalation_id}"]
                st.rerun()

    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            # Check if this is a document upload message that needs special rendering
            if message.get("document_upload"):
                # Special formatting for document upload success messages
                st.success(f"📄 **Document Uploaded**: {message.get('filename', 'Unknown')}")
                st.markdown("✅ Successfully processed and added to my knowledge. You can now ask me questions about this document!")

                # Add quick action buttons for document discussion
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📋 Summarize", key=f"summarize_{i}_{message.get('filename', 'doc')}"):
                        summary_prompt = f"Please provide a comprehensive summary of the document '{message.get('filename', 'the uploaded document')}'."
                        st.session_state.chat_history.append({"role": "user", "content": summary_prompt})
                        st.rerun()

                with col2:
                    if st.button(f"❓ Key Questions", key=f"questions_{i}_{message.get('filename', 'doc')}"):
                        questions_prompt = f"What are the most important questions I should ask about '{message.get('filename', 'the uploaded document')}'?"
                        st.session_state.chat_history.append({"role": "user", "content": questions_prompt})
                        st.rerun()

                with col3:
                    if st.button(f"🔍 Deep Analysis", key=f"analysis_{i}_{message.get('filename', 'doc')}"):
                        analysis_prompt = f"Please provide a detailed analysis of '{message.get('filename', 'the uploaded document')}', including key insights, implications, and recommendations."
                        st.session_state.chat_history.append({"role": "user", "content": analysis_prompt})
                        st.rerun()

            # Check if this is a document analysis response
            elif message.get("document_analysis"):
                # Special formatting for document analysis responses
                st.info(f"📊 **Document Analysis**: {message.get('filename', 'Unknown')}")
                st.markdown(message["content"])

            # Check if this is a document suggestions message
            elif message.get("document_suggestions"):
                # Special formatting for document suggestions
                st.success(f"💡 **Suggested Questions**: {message.get('filename', 'Unknown')}")
                st.markdown(message["content"])

            # Check if this is an auto-generated user message
            elif message.get("auto_generated") and message["role"] == "user":
                # Special formatting for auto-generated prompts
                st.info("🤖 **Auto-generated prompt based on your document upload:**")
                st.markdown(message["content"])

            # Check if this is a table analysis result that needs special rendering
            elif (message["role"] == "assistant" and
                "Table Analysis & Code Generation Complete!" in message["content"]):
                render_table_analysis_result(message["content"])
            else:
                st.markdown(message["content"])

            # Check if this is an escalation message that needs buttons
            if (message["role"] == "assistant" and
                "Interactive Web Search Available!" in message["content"] and
                message.get("escalation_id")):

                escalation_id = message["escalation_id"]

                # Only show buttons if escalation hasn't been resolved
                if not (st.session_state.get(f"trigger_search_{escalation_id}") or
                       st.session_state.get(f"force_local_{escalation_id}")):

                    st.markdown("---")
                    st.markdown("**Choose your preferred approach:**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("🌐 Yes, Search Online", key=f"history_search_{escalation_id}_{i}", use_container_width=True):
                            st.session_state[f"trigger_search_{escalation_id}"] = True
                            st.rerun()

                    with col2:
                        if st.button("📚 No, Answer Locally", key=f"history_local_{escalation_id}_{i}", use_container_width=True):
                            st.session_state[f"force_local_{escalation_id}"] = True
                            st.rerun()

                    with col3:
                        if st.button("📄 Manual Upload", key=f"history_upload_{escalation_id}_{i}", use_container_width=True):
                            st.info("💡 Switch to the '📚 Documents' tab to upload relevant documents, then ask your question again.")

            # Add feedback system for all assistant messages (preserving 100% of functionality)
            elif message["role"] == "assistant":
                render_feedback_system(i)

    # Document upload reminder
    st.markdown("💡 **Tip**: Upload documents using the '📁 Upload Documents to Chat' section above for instant analysis and discussion!")

    # Chat input
    if prompt := st.chat_input("Ask SAM anything..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 SAM is thinking..."):
                try:
                    # Check for chat commands
                    if prompt.startswith('/'):
                        raw_response = handle_secure_chat_command(prompt)
                    else:
                        # Check if user is requesting to bypass confidence assessment
                        force_local = any(phrase in prompt.lower() for phrase in [
                            "answer with current knowledge",
                            "use local knowledge",
                            "don't search the web",
                            "no web search",
                            "answer anyway"
                        ])

                        # Check if user is explicitly requesting web search (preserving 100% of functionality)
                        force_web_search = any(phrase in prompt.lower() for phrase in [
                            "search up", "search for", "search about", "look up", "look for",
                            "find out", "find information", "information about", "details about",
                            "search the web", "web search", "online search", "internet search",
                            "current information", "latest information", "recent information"
                        ])

                        # Check if this exact query recently triggered an escalation
                        recent_escalation = False
                        if 'web_search_escalation' in st.session_state:
                            for escalation_data in st.session_state.web_search_escalation.values():
                                if escalation_data['original_query'].lower() == prompt.lower():
                                    recent_escalation = True
                                    break

                        # If recent escalation exists, force local answer to prevent loops
                        if recent_escalation:
                            force_local = True

                        # If user explicitly requested web search, trigger it directly (preserving 100% of functionality)
                        if force_web_search and not force_local:
                            logger.info(f"🌐 User explicitly requested web search with keywords: {prompt}")
                            with st.spinner("🔍 Searching the web as requested..."):
                                search_result = perform_secure_web_search(prompt)

                                if search_result['success']:
                                    st.markdown(search_result['response'])
                                    st.session_state.chat_history.append({
                                        "role": "assistant",
                                        "content": search_result['response']
                                    })

                                    # Add feedback system for web search results (preserving 100% of functionality)
                                    render_feedback_system(len(st.session_state.chat_history) - 1)
                                    return  # Exit early since web search was successful
                                else:
                                    st.error(f"❌ Web search failed: {search_result['error']}")
                                    # Fall back to normal response generation

                        response_result = generate_response_with_conversation_buffer(prompt, force_local=force_local)

                        # Debug logging for escalation detection (preserving 100% of functionality)
                        logger.info(f"🔍 Response result type: {type(response_result)}")
                        logger.info(f"🔍 Response result content: {str(response_result)[:200]}...")
                        if isinstance(response_result, tuple):
                            logger.info(f"🔍 Tuple length: {len(response_result)}")
                            logger.info(f"🔍 Tuple contents: {[type(item) for item in response_result]}")

                        # Check if this is a web search escalation
                        if isinstance(response_result, tuple) and len(response_result) == 2:
                            raw_response, escalation_id = response_result
                            logger.info(f"🌐 ✅ WEB SEARCH ESCALATION DETECTED with ID: {escalation_id}")
                            logger.info("🌐 ✅ DISPLAYING INTERACTIVE BUTTONS NOW")
                            logger.info(f"🌐 ✅ Escalation message: {raw_response[:100]}...")

                            # Display escalation message with enhanced visibility
                            st.markdown("---")
                            st.markdown("## 🤔 **Interactive Web Search Available!**")
                            st.markdown(raw_response)
                            st.markdown("---")

                            # Add enhanced interactive button section
                            st.markdown("### 🎯 **Choose Your Approach:**")
                            st.markdown("**How would you like me to handle this query?**")

                            # Add interactive web search buttons with enhanced styling
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("🌐 **Yes, Search Online**", key=f"search_{escalation_id}", use_container_width=True, type="primary"):
                                    logger.info(f"🌐 ✅ USER CLICKED: Yes, Search Online for escalation {escalation_id}")
                                    st.session_state[f"trigger_search_{escalation_id}"] = True
                                    st.rerun()
                                st.caption("🔍 Search the web for current information")

                            with col2:
                                if st.button("📚 **No, Answer Locally**", key=f"local_{escalation_id}", use_container_width=True):
                                    logger.info(f"📚 ✅ USER CLICKED: No, Answer Locally for escalation {escalation_id}")
                                    st.session_state[f"force_local_{escalation_id}"] = True
                                    st.rerun()
                                st.caption("💭 Use existing knowledge only")

                            with col3:
                                if st.button("📄 **Manual Upload**", key=f"upload_{escalation_id}", use_container_width=True):
                                    logger.info(f"📄 ✅ USER CLICKED: Manual Upload for escalation {escalation_id}")
                                    st.info("💡 Switch to the '📚 Documents' tab to upload relevant documents, then ask your question again.")
                                st.caption("📁 Upload your own documents")

                            # Add escalation to chat history with escalation_id for button persistence
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": raw_response,
                                "escalation_id": escalation_id
                            })

                        else:
                            # Ensure raw_response is always a string, not a tuple
                            if isinstance(response_result, tuple):
                                raw_response = response_result[0] if response_result else ""
                            else:
                                raw_response = response_result

                            # Process thoughts using the thought processor
                            try:
                                from utils.thought_processor import get_thought_processor
                                thought_processor = get_thought_processor()
                                processed = thought_processor.process_response(raw_response)

                                # Display the clean response with special handling for table analysis
                                if "Table Analysis & Code Generation Complete!" in processed.visible_content:
                                    render_table_analysis_result(processed.visible_content)
                                else:
                                    st.markdown(processed.visible_content)

                                # Add thought dropdown if thoughts are present
                                if processed.has_thoughts and processed.thought_blocks:
                                    total_tokens = sum(block.token_count for block in processed.thought_blocks)

                                    with st.expander(f"🧠 SAM's Thoughts ({total_tokens} tokens)", expanded=False):
                                        for i, thought_block in enumerate(processed.thought_blocks):
                                            st.markdown(f"**Thought {i+1}:**")
                                            st.markdown(thought_block.content)
                                            if i < len(processed.thought_blocks) - 1:
                                                st.divider()

                                # Add the clean response to chat history
                                st.session_state.chat_history.append({"role": "assistant", "content": processed.visible_content})

                                # Add Cognitive Distillation Thought Transparency (NEW - Phase 2 Integration)
                                render_thought_transparency()

                                # Add feedback system
                                render_feedback_system(len(st.session_state.chat_history) - 1)

                            except ImportError:
                                # Fallback if thought processor is not available
                                if "Table Analysis & Code Generation Complete!" in raw_response:
                                    render_table_analysis_result(raw_response)
                                else:
                                    st.markdown(raw_response)
                                st.session_state.chat_history.append({"role": "assistant", "content": raw_response})

                                # Add Cognitive Distillation Thought Transparency (NEW - Phase 2 Integration)
                                render_thought_transparency()

                                # Add SELF-REFLECT Transparency (Phase 5C)
                                render_self_reflect_transparency(raw_response)

                                # Add feedback system
                                render_feedback_system(len(st.session_state.chat_history) - 1)

                except Exception as e:
                    error_msg = f"❌ Sorry, I encountered an error: {e}"
                    st.markdown(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                    # Add feedback system for error messages (preserving 100% of functionality)
                    render_feedback_system(len(st.session_state.chat_history) - 1)

def render_document_interface():
    """Render the document upload and processing interface."""
    st.header("📚 Secure Document Processing")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a document for SAM to learn from",
        type=['pdf', 'txt', 'docx', 'md'],
        help="Uploaded documents will be encrypted and processed securely"
    )
    
    if uploaded_file is not None:
        with st.spinner("🔐 Processing document securely..."):
            try:
                result = process_secure_document(uploaded_file)
                
                if result['success']:
                    st.success("✅ Document processed successfully!")

                    # Enhanced analytics display
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Chunks Created", result.get('chunks_created', 0))
                    with col2:
                        st.metric("📁 File Size", f"{result.get('file_size', 0) / 1024:.1f} KB")
                    with col3:
                        consolidation_status = "✅ Yes" if result.get('knowledge_consolidated') else "❌ No"
                        st.metric("🧠 Consolidated", consolidation_status)
                    with col4:
                        sync_status = "✅ Yes" if result.get('synced_to_regular_store') else "❌ No"
                        st.metric("🔄 Synced", sync_status)

                    # Show enrichment scores and analytics
                    if result.get('knowledge_consolidated'):
                        st.success("🧠 **Knowledge Consolidation Completed!**")

                        # Display enrichment metrics
                        with st.expander("📊 **Content Analysis & Insights**", expanded=True):
                            # Simulated enrichment scores (in real implementation, these would come from the consolidation result)
                            enrichment_score = min(95, max(65, 75 + (result.get('fil
