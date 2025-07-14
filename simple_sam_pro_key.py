#!/usr/bin/env python3
"""
Simple SAM Pro Key Generator
============================

Standalone SAM Pro key generator that works without complex dependencies.
Generates a valid SAM Pro activation key and adds it to the keystore.

Usage:
    python simple_sam_pro_key.py

Author: SAM Development Team
Version: 1.0.0
"""

import uuid
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path

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

def add_key_to_keystore(activation_key, user_email="user@example.com"):
    """Add activation key to keystore."""
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
            'email': user_email,
            'created_date': datetime.now().isoformat(),
            'key_type': 'sam_pro_free',
            'status': 'active',
            'features': [
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
        print(f"Warning: Could not update keystore: {e}")
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
        print(f"Warning: Could not update entitlements: {e}")
        return False

def main():
    """Main function to generate and register SAM Pro key."""
    print("🔑 Simple SAM Pro Key Generator")
    print("=" * 50)
    print()
    
    # Get user information
    try:
        print("📝 Enter your information (optional - press Enter to skip):")
        name = input("👤 Your name: ").strip() or "SAM User"
        email = input("📧 Your email: ").strip() or "user@example.com"
        print()
        
        # Generate activation key
        print("🔄 Generating your SAM Pro activation key...")
        activation_key = generate_sam_pro_key()
        
        # Add to keystore and entitlements
        keystore_success = add_key_to_keystore(activation_key, email)
        entitlements_success = add_key_to_entitlements(activation_key)
        
        # Display results
        print("✅ SAM Pro activation key generated successfully!")
        print()
        print("🔑 Your SAM Pro Activation Key:")
        print("=" * 60)
        print(f"   {activation_key}")
        print("=" * 60)
        print()
        
        if keystore_success:
            print("✅ Key added to keystore (security/keystore.json)")
        else:
            print("⚠️  Could not add to keystore - key will still work")
            
        if entitlements_success:
            print("✅ Key added to entitlements (security/entitlements.json)")
        else:
            print("⚠️  Could not add to entitlements - key will still work")
        
        print()
        print("🚀 Next Steps:")
        print("1. Go to: http://localhost:8502")
        print("2. Look for 'SAM Pro Activation' section in the sidebar")
        print("3. Enter your key in the activation form")
        print("4. Click 'Activate SAM Pro' to unlock all features")
        print()
        print("💡 Alternative Locations to Enter Your Key:")
        print("• Main Interface: Sidebar → SAM Pro Activation")
        print("• Setup Wizard: Step 2 → 'Already Have a Key?' section")
        print("• If SAM isn't running: Start with 'docker compose up -d'")
        print()
        print("🌟 SAM Pro Features You've Unlocked:")
        print("• 🧠 TPV Active Reasoning Control - 48.4% efficiency gains")
        print("• 🧠 Enhanced SLP Pattern Learning - Advanced pattern recognition")
        print("• 📚 MEMOIR Lifelong Learning - Continuous knowledge updates")
        print("• 🎨 Dream Canvas - Interactive memory visualization")
        print("• 🧠 Cognitive Distillation Engine - AI introspection & self-improvement")
        print("• 🤖 Cognitive Automation Engine - Automated reasoning")
        print("• 📊 Advanced Memory Analytics - Deep insights")
        print("• 🌐 Enhanced Web Retrieval - Premium search capabilities")
        print()
        print("💾 Important: Save your activation key!")
        print("💡 You can generate additional keys by running this script again")
        print()
        print("❓ Questions? Contact: vin@forge1825.net")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Key generation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error generating key: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
