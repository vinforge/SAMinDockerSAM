#!/usr/bin/env python3
"""
SAM Pro Key Registration - Quick Start
=====================================

Simple command-line interface for new users to register and receive SAM Pro activation keys.
This script provides an easy way to get started with SAM Pro without needing to run the full web interface.

Usage:
    python get_sam_pro_key.py

Author: SAM Development Team
Version: 1.0.0
"""

import sys
import os
import json
import re
from pathlib import Path

# Add SAM to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def main():
    """Main registration interface."""
    print("🚀 SAM Pro Registration - Quick Start")
    print("=" * 50)
    print()
    
    # Check if key distribution system is available
    try:
        from scripts.key_distribution_system import KeyDistributionManager
        print("✅ Key distribution system available")
        use_advanced_system = True
    except ImportError:
        print("⚠️  Advanced key distribution system not available")
        print("💡 Using simple key generation instead")
        print()
        use_advanced_system = False
    
    print()
    print("🎯 Get your free SAM Pro activation key!")
    print("📧 We'll send your key via email and display it here as backup")
    print()
    
    # Collect user information
    try:
        name = input("👤 Enter your full name: ").strip()
        if not name:
            print("❌ Name is required")
            return 1
        
        email = input("📧 Enter your email address: ").strip().lower()
        if not email:
            print("❌ Email is required")
            return 1
        
        if not validate_email(email):
            print("❌ Please enter a valid email address")
            return 1
        
        organization = input("🏢 Organization (optional): ").strip()
        use_case = input("🎯 Primary use case (optional): ").strip()
        
        print()
        print("🔄 Processing your registration...")

        if use_advanced_system:
            # Use advanced key distribution manager
            manager = KeyDistributionManager()

            # Register user
            success, message, registration_id = manager.register_user(
                email=email,
                name=name,
                organization=organization or "Personal",
                use_case=use_case or "General AI assistance"
            )

            if not success:
                print(f"❌ Registration failed: {message}")
                return 1

            print(f"✅ Registration successful! ID: {registration_id}")

            # Assign and send key
            key_success, key_message, activation_key = manager.assign_and_send_key(registration_id)

            if key_success and activation_key:
                email_sent = True
            else:
                print(f"⚠️ Advanced key generation failed: {key_message}")
                print("🔄 Falling back to simple key generation...")
                use_advanced_system = False

        if not use_advanced_system:
            # Use simple key generation
            import uuid
            import json
            import hashlib
            from datetime import datetime
            from pathlib import Path

            # Generate key
            activation_key = str(uuid.uuid4())
            email_sent = False

            # Add to keystore
            try:
                security_dir = Path("security")
                security_dir.mkdir(exist_ok=True)
                keystore_file = security_dir / "keystore.json"

                keystore = {}
                if keystore_file.exists():
                    try:
                        with open(keystore_file, 'r') as f:
                            keystore = json.load(f)
                    except:
                        keystore = {}

                keystore[activation_key] = {
                    'email': email,
                    'created_date': datetime.now().isoformat(),
                    'key_type': 'sam_pro_free',
                    'status': 'active'
                }

                with open(keystore_file, 'w') as f:
                    json.dump(keystore, f, indent=2)

                print("✅ Key generated and added to keystore")

            except Exception as e:
                print(f"⚠️ Could not update keystore: {e}")

        if activation_key:
            print("🎉 SAM Pro activation key generated and sent!")
            print()
            print("🔑 Your SAM Pro Activation Key:")
            print("=" * 50)
            print(f"   {activation_key}")
            print("=" * 50)
            print()
            if email_sent:
                print("📧 Key also sent to:", email)
            else:
                print("📧 Email delivery not available - key displayed above as backup")
            print()
            print("🚀 Next Steps:")
            print("1. Start SAM: python secure_streamlit_app.py")
            print("2. Navigate to: localhost:8502")
            print("3. Enter your activation key when prompted")
            print("4. Enjoy SAM Pro features!")
            print()
            print("🌟 SAM Pro Features You've Unlocked:")
            print("• TPV Active Reasoning Control - 48.4% efficiency gains")
            print("• Enhanced SLP Pattern Learning - Advanced pattern recognition")
            print("• MEMOIR Lifelong Learning - Continuous knowledge updates")
            print("• Dream Canvas - Interactive memory visualization")
            print("• Cognitive Distillation Engine - AI introspection & self-improvement")
            print("• Cognitive Automation Engine - Automated reasoning")
            print("• Advanced Memory Analytics - Deep insights")
            print("• Enhanced Web Retrieval - Premium search capabilities")
            
        else:
            print(f"⚠️ Key generation failed")
            print("💡 You can try the simple key generator:")
            print("   python simple_sam_pro_key.py")
            return 1
        
        print()
        print("🎯 Registration Complete!")
        print("💡 Save your activation key - you'll need it to activate SAM Pro")
        print()
        print("❓ Questions? Contact: vin@forge1825.net")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Registration cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please try the web interface: streamlit run sam_pro_registration.py")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
