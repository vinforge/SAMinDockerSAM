#!/usr/bin/env python3
"""
SAM Master Password Reset Tool

This tool allows you to reset the master password for SAM when needed.
Use this if you've forgotten your master password or need to start fresh.

Author: SAM Development Team
Version: 1.0.0
"""

import os
import sys
import json
import getpass
import shutil
from pathlib import Path
from datetime import datetime

def print_header():
    """Print the tool header."""
    print("=" * 60)
    print("🔐 SAM Master Password Reset Tool")
    print("=" * 60)
    print()

def print_warning():
    """Print important warnings."""
    print("⚠️  WARNING: This will reset your SAM master password!")
    print()
    print("📋 What this tool does:")
    print("   • Backs up existing security configuration")
    print("   • Resets the master password")
    print("   • Preserves SAM Pro activation keys")
    print("   • Forces SAM to show setup wizard on next start")
    print()
    print("💡 Use this tool if:")
    print("   • You forgot your master password")
    print("   • SAM is stuck in security setup")
    print("   • You need to start fresh with security")
    print()

def backup_existing_security():
    """Backup existing security configuration."""
    try:
        security_dir = Path("security")
        if security_dir.exists():
            backup_dir = Path(f"security_backup_{int(datetime.now().timestamp())}")
            shutil.copytree(security_dir, backup_dir)
            print(f"✅ Security backup created: {backup_dir}")
            return backup_dir
        else:
            print("ℹ️  No existing security directory found")
            return None
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def preserve_sam_pro_keys():
    """Preserve SAM Pro activation keys."""
    try:
        # Check for keystore
        keystore_file = Path("security/keystore.json")
        sam_config_entitlements = Path("sam/config/entitlements.json")
        
        preserved_keys = {}
        
        if keystore_file.exists():
            with open(keystore_file, 'r') as f:
                keystore = json.load(f)
                preserved_keys['keystore'] = keystore
                print(f"✅ Preserved {len(keystore)} SAM Pro keys from keystore")
        
        if sam_config_entitlements.exists():
            with open(sam_config_entitlements, 'r') as f:
                entitlements = json.load(f)
                preserved_keys['entitlements'] = entitlements
                print(f"✅ Preserved entitlements configuration")
        
        return preserved_keys
        
    except Exception as e:
        print(f"⚠️  Could not preserve SAM Pro keys: {e}")
        return {}

def reset_security_configuration():
    """Reset the security configuration."""
    try:
        # Remove security directory
        security_dir = Path("security")
        if security_dir.exists():
            shutil.rmtree(security_dir)
            print("✅ Security configuration reset")
        
        # Remove SAM state files
        sam_state_dir = Path.home() / ".sam"
        if sam_state_dir.exists():
            shutil.rmtree(sam_state_dir)
            print("✅ SAM state files reset")
        
        return True
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

def restore_sam_pro_keys(preserved_keys):
    """Restore SAM Pro activation keys."""
    try:
        if not preserved_keys:
            print("ℹ️  No SAM Pro keys to restore")
            return True
        
        # Recreate security directory
        security_dir = Path("security")
        security_dir.mkdir(exist_ok=True)
        
        # Restore keystore
        if 'keystore' in preserved_keys:
            keystore_file = security_dir / "keystore.json"
            with open(keystore_file, 'w') as f:
                json.dump(preserved_keys['keystore'], f, indent=2)
            print("✅ SAM Pro keystore restored")
        
        # Restore entitlements
        if 'entitlements' in preserved_keys:
            config_dir = Path("sam/config")
            config_dir.mkdir(parents=True, exist_ok=True)
            entitlements_file = config_dir / "entitlements.json"
            with open(entitlements_file, 'w') as f:
                json.dump(preserved_keys['entitlements'], f, indent=2)
            print("✅ SAM Pro entitlements restored")
        
        return True
        
    except Exception as e:
        print(f"❌ Key restoration failed: {e}")
        return False

def create_fresh_setup_status():
    """Create fresh setup status to trigger setup wizard."""
    try:
        security_dir = Path("security")
        security_dir.mkdir(exist_ok=True)
        
        setup_status = {
            "setup_completed": False,
            "docker_mode": True,
            "setup_timestamp": None,
            "master_password_set": False,
            "encryption_enabled": False,
            "reset_timestamp": datetime.now().isoformat(),
            "reset_tool_version": "1.0.0"
        }
        
        setup_file = security_dir / "setup_status.json"
        with open(setup_file, 'w') as f:
            json.dump(setup_status, f, indent=2)
        
        print("✅ Fresh setup status created")
        return True
        
    except Exception as e:
        print(f"❌ Setup status creation failed: {e}")
        return False

def main():
    """Main reset workflow."""
    print_header()
    print_warning()
    
    # Confirmation
    response = input("❓ Do you want to proceed with master password reset? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Reset cancelled by user")
        return 1
    
    print("\n🔄 Starting master password reset...")
    
    # Step 1: Backup existing security
    print("\n📦 Step 1: Backing up existing security configuration...")
    backup_dir = backup_existing_security()
    
    # Step 2: Preserve SAM Pro keys
    print("\n🔑 Step 2: Preserving SAM Pro activation keys...")
    preserved_keys = preserve_sam_pro_keys()
    
    # Step 3: Reset security configuration
    print("\n🧹 Step 3: Resetting security configuration...")
    if not reset_security_configuration():
        print("❌ Reset failed!")
        return 1
    
    # Step 4: Restore SAM Pro keys
    print("\n🔄 Step 4: Restoring SAM Pro keys...")
    if not restore_sam_pro_keys(preserved_keys):
        print("⚠️  Key restoration failed, but reset completed")
    
    # Step 5: Create fresh setup status
    print("\n🆕 Step 5: Creating fresh setup configuration...")
    if not create_fresh_setup_status():
        print("⚠️  Setup status creation failed")
    
    # Success
    print("\n" + "=" * 60)
    print("✅ MASTER PASSWORD RESET COMPLETED!")
    print("=" * 60)
    print()
    print("🎯 Next Steps:")
    print("   1. Restart SAM (docker compose restart)")
    print("   2. Go to http://localhost:8502")
    print("   3. You'll see the master password setup wizard")
    print("   4. Create your new master password")
    print("   5. Your SAM Pro keys should still work")
    print()
    
    if backup_dir:
        print(f"💾 Backup saved to: {backup_dir}")
        print("   (You can delete this backup once everything works)")
    
    print("\n🎉 SAM is ready for a fresh start!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Reset cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
