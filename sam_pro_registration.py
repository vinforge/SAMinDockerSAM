#!/usr/bin/env python3
"""
SAM Pro Registration Web Interface

Simple web interface for users to register for SAM Pro activation keys.
Provides a user-friendly form with instant key generation.

Author: SAM Development Team
Version: 2.0.0 - Docker Compatible
"""

import streamlit as st
import sys
import os
import uuid
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

# Add SAM to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_sam_pro_key():
    """Generate a new SAM Pro activation key."""
    return str(uuid.uuid4())

def create_key_hash(key):
    """Create SHA-256 hash of the key for validation."""
    return hashlib.sha256(key.encode()).hexdigest()

def ensure_security_directory():
    """Ensure security directory exists."""
    security_dir = Path("security")
    security_dir.mkdir(exist_ok=True)
    return security_dir

def add_key_to_keystore(activation_key, email, name="SAM User"):
    """Add key to keystore."""
    try:
        security_dir = ensure_security_directory()
        keystore_file = security_dir / "keystore.json"

        # Load existing keystore or create new one
        keystore = {}
        if keystore_file.exists():
            try:
                with open(keystore_file, 'r') as f:
                    keystore = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                keystore = {}

        # Add new key
        keystore[activation_key] = {
            'email': email,
            'name': name,
            'created_date': datetime.now().isoformat(),
            'key_type': 'sam_pro_free',
            'status': 'active',
            'features': [
                'procedural_memory',
                'tpv_active_reasoning',
                'enhanced_slp_learning',
                'memoir_lifelong_learning',
                'dream_canvas',
                'cognitive_distillation',
                'cognitive_automation',
                'advanced_memory_analytics',
                'enhanced_web_retrieval'
            ]
        }

        # Save keystore
        with open(keystore_file, 'w') as f:
            json.dump(keystore, f, indent=2)

        return True

    except Exception as e:
        st.error(f"Could not update keystore: {e}")
        return False

def add_key_to_entitlements(activation_key):
    """Add key hash to entitlements for validation."""
    try:
        security_dir = ensure_security_directory()
        entitlements_file = security_dir / "entitlements.json"

        # Load existing entitlements or create new one
        entitlements = {}
        if entitlements_file.exists():
            try:
                with open(entitlements_file, 'r') as f:
                    entitlements = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                entitlements = {}

        # Ensure sam_pro_keys section exists
        if 'sam_pro_keys' not in entitlements:
            entitlements['sam_pro_keys'] = {}

        # Add key hash
        key_hash = create_key_hash(activation_key)
        entitlements['sam_pro_keys'][key_hash] = {
            'created_date': datetime.now().isoformat(),
            'key_type': 'free_tier',
            'status': 'active'
        }

        # Save entitlements
        with open(entitlements_file, 'w') as f:
            json.dump(entitlements, f, indent=2)

        return True

    except Exception as e:
        st.error(f"Could not update entitlements: {e}")
        return False

def main():
    """Main registration interface."""
    st.set_page_config(
        page_title="SAM Pro Registration",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 SAM Pro Registration</h1>
        <p>Get your activation key for the world's most advanced AI memory system</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
    ## 🎯 **What is SAM Pro?**
    
    SAM Pro unlocks premium features in SAM (Secure AI Memory), including:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h4>🧠 Procedural Memory Engine</h4>
            <p>Revolutionary step-by-step intelligence with 95% query classification accuracy</p>
        </div>

        <div class="feature-box">
            <h4>⚡ Real-time Execution Tracking</h4>
            <p>Monitor AI workflows and cognitive processes in real-time</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-box">
            <h4>🎨 Dream Canvas</h4>
            <p>Interactive memory visualization with cognitive synthesis</p>
        </div>

        <div class="feature-box">
            <h4>🤖 Proactive Suggestions</h4>
            <p>AI that anticipates your needs and suggests next steps</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Registration form
    st.markdown("## 📝 **Register for SAM Pro**")
    
    with st.form("registration_form"):
        st.markdown("### Your Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Full Name *",
                placeholder="John Doe",
                help="Your full name for the activation key"
            )
            
            email = st.text_input(
                "Email Address *",
                placeholder="john@example.com",
                help="We'll send your activation key to this email"
            )
        
        with col2:
            organization = st.text_input(
                "Organization",
                placeholder="Acme Corporation",
                help="Your company or organization (optional)"
            )
            
            use_case = st.selectbox(
                "Primary Use Case",
                [
                    "",
                    "Research & Development",
                    "Business Intelligence",
                    "Educational/Academic",
                    "Personal Knowledge Management",
                    "Content Creation",
                    "Data Analysis",
                    "Software Development",
                    "Other"
                ],
                help="How do you plan to use SAM Pro?"
            )
        
        # Additional use case details
        if use_case == "Other":
            use_case_details = st.text_area(
                "Please describe your use case",
                placeholder="Describe how you plan to use SAM Pro...",
                height=100
            )
        else:
            use_case_details = ""
        
        # Terms and conditions
        st.markdown("### Terms & Conditions")
        
        terms_accepted = st.checkbox(
            "I agree to the SAM Pro terms of use and privacy policy",
            help="By checking this box, you agree to use SAM Pro in accordance with our terms"
        )
        
        # Submit button
        submitted = st.form_submit_button(
            "🚀 Register for SAM Pro",
            use_container_width=True
        )
        
        if submitted:
            # Validation
            errors = []
            
            if not name.strip():
                errors.append("Name is required")
            
            if not email.strip() or '@' not in email:
                errors.append("Valid email address is required")
            
            if not terms_accepted:
                errors.append("You must accept the terms and conditions")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Process registration
                with st.spinner("🔄 Processing your registration..."):
                    try:
                        # Generate key using our simple system
                        activation_key = generate_sam_pro_key()

                        # Add to keystore and entitlements
                        keystore_success = add_key_to_keystore(activation_key, email.strip(), name.strip())
                        entitlements_success = add_key_to_entitlements(activation_key)

                        if keystore_success and entitlements_success:
                            st.balloons()
                            st.markdown("""
                            <div class="success-box">
                                <h3>🎉 Registration Successful!</h3>
                                <p><strong>Your SAM Pro activation key is ready!</strong></p>
                            </div>
                            """, unsafe_allow_html=True)

                            # Display the key
                            st.markdown("### 🔑 **Your SAM Pro Activation Key:**")
                            st.code(activation_key, language=None)

                            st.markdown(f"""
                            ### 🎯 **Next Steps:**

                            1. **Copy your activation key** (shown above)
                            2. **Go to SAM's main interface** at [http://localhost:8502](http://localhost:8502)
                            3. **Look for "SAM Pro Activation"** in the sidebar
                            4. **Paste your key** and click activate
                            5. **Enjoy the world's first Procedural Intelligence System!**

                            ### 🌟 **What You Just Unlocked:**
                            - 🧠 **Procedural Memory Engine** - Revolutionary step-by-step intelligence
                            - 🎯 **95% Query Classification Accuracy** - Intelligent intent recognition
                            - ⚡ **Real-time Execution Tracking** - Monitor your AI workflows
                            - 🤖 **Proactive Suggestions** - AI that anticipates your needs
                            - 🎨 **Dream Canvas** - Interactive memory visualization
                            - 📊 **Advanced Analytics** - Deep insights into your data
                            - 🌐 **Enhanced Web Retrieval** - Premium search capabilities

                            **Registration Details:**
                            - **Name:** {name.strip()}
                            - **Email:** {email.strip()}
                            - **Organization:** {organization.strip() or "Personal"}

                            ### ❓ **Questions?**
                            Contact us at: **vin@forge1825.net**
                            """)

                            # Success metrics
                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🔑 Keys Generated", "1", "New!")
                            with col2:
                                st.metric("🧠 Features Unlocked", "8", "+8")
                            with col3:
                                st.metric("🚀 Ready to Use", "100%", "✅")

                        else:
                            st.error("❌ Registration failed. Please try again or contact support.")

                    except Exception as e:
                        st.error(f"❌ System error: {str(e)}")
                        st.info("💡 You can also try the command-line registration: `python simple_sam_pro_key.py`")
    
    # Footer information
    st.markdown("---")
    
    st.markdown("""
    ## 🔗 **Useful Links**
    
    - **📥 Download SAM:** [github.com/forge-1825/SAM](https://github.com/forge-1825/SAM)
    - **📖 Installation Guide:** Check the README.md in the repository
    - **🔐 Encryption Setup:** ENCRYPTION_SETUP_GUIDE.md
    - **🐛 Support:** [GitHub Issues](https://github.com/forge-1825/SAM/issues)
    
    ## ❓ **Frequently Asked Questions**
    
    **Q: How long does it take to receive my activation key?**  
    A: Activation keys are sent immediately upon registration. Check your spam folder if you don't see it.
    
    **Q: Can I use SAM without a Pro key?**  
    A: Yes! SAM's core features are free. Pro features add advanced capabilities like Dream Canvas and cognitive automation.
    
    **Q: Is my data secure?**  
    A: Absolutely! SAM uses enterprise-grade AES-256 encryption and operates completely locally on your machine.
    
    **Q: Can I use SAM Pro commercially?**  
    A: Yes, SAM Pro can be used for commercial purposes. See our terms of use for details.
    """)
    
    # Contact information
    st.markdown("""
    ---
    
    **Need help?** Contact us at: **sam-pro@forge1825.net**
    
    *SAM Pro - Secure AI Memory | The Future of AI Consciousness*
    """)

if __name__ == "__main__":
    main()
