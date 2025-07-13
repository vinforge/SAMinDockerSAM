#!/usr/bin/env python3
"""
SAM Pro Registration Script
==========================

Standalone script for registering for SAM Pro activation keys.
This script is completely separate from the installation process and can be run
at any time to register for premium features.

Usage:
    python register_sam_pro.py

Features:
- Starts registration web interface on localhost:8503
- Handles user registration workflow
- Manages email delivery of activation keys
- Provides clear activation instructions
- Self-contained with proper error handling

Author: SAM Development Team
Version: 2.0.0
"""

import os
import sys
import time
import subprocess
import webbrowser
import signal
from pathlib import Path
from typing import Optional

def print_header():
    """Print the registration script header."""
    print("=" * 70)
    print("🧠 SAM Pro Registration System")
    print("=" * 70)
    print("Register for premium SAM features including:")
    print("  • 🎨 Dream Canvas - Interactive memory visualization")
    print("  • 🧠 TPV Active Reasoning Control")
    print("  • 📁 Cognitive Automation (SLP System)")
    print("  • 🔬 Advanced Analytics and Monitoring")
    print("=" * 70)

def check_dependencies() -> bool:
    """Check if required dependencies are available."""
    print("\n🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Check for streamlit
    try:
        import streamlit
        print("✅ Streamlit available")
    except ImportError:
        print("❌ Streamlit not found")
        print("💡 Install with: pip install streamlit")
        return False
    
    # Check for registration interface
    if not Path("sam_pro_registration.py").exists():
        print("❌ Registration interface not found (sam_pro_registration.py)")
        print("💡 Please ensure you have the complete SAM installation")
        return False
    
    # Check for key distribution system
    if not Path("scripts/key_distribution_system.py").exists():
        print("❌ Key distribution system not found")
        print("💡 Please ensure you have the complete SAM installation")
        return False
    
    print("✅ All dependencies available")
    return True

def start_registration_interface() -> Optional[subprocess.Popen]:
    """Start the registration web interface."""
    print("\n🚀 Starting SAM Pro registration interface...")
    
    try:
        # Start the registration interface on localhost:8503
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run",
            "sam_pro_registration.py",
            "--server.port=8503",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false",
            "--server.headless=true"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ Registration interface starting...")
        print("⏳ Waiting for interface to initialize (15 seconds)...")
        time.sleep(15)
        
        # Check if process is still running
        if process.poll() is not None:
            print("❌ Registration interface failed to start")
            return None
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start registration interface: {e}")
        return None

def open_registration_page():
    """Open the registration page in the user's browser."""
    registration_url = "http://localhost:8503"
    print(f"\n🌐 Opening registration page: {registration_url}")
    
    try:
        webbrowser.open(registration_url)
        print("✅ Registration page opened in your browser")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"💡 Please manually open: {registration_url}")

def display_instructions():
    """Display registration instructions."""
    print("\n📋 Registration Instructions:")
    print("=" * 50)
    print("1. 📝 Fill out the registration form with your details")
    print("2. ✅ Accept the terms and conditions")
    print("3. 🚀 Click 'Register for SAM Pro'")
    print("4. 📧 Check your email for the activation key")
    print("5. 🔑 Use the key in SAM's interface to unlock Pro features")
    print("=" * 50)

def wait_for_completion(process: subprocess.Popen):
    """Wait for user to complete registration."""
    print("\n⏳ Registration interface is running...")
    print("💡 Complete your registration in the browser, then return here")
    print("🔄 Press Ctrl+C when you're done to stop the registration interface")
    
    try:
        while True:
            # Check if process is still running
            if process.poll() is not None:
                print("\n⚠️  Registration interface stopped unexpectedly")
                break
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n🔄 Stopping registration interface...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ Registration interface stopped")
        except subprocess.TimeoutExpired:
            print("⚠️  Force stopping registration interface...")
            process.kill()
        except Exception as e:
            print(f"⚠️  Error stopping interface: {e}")

def display_next_steps():
    """Display next steps after registration."""
    print("\n🎯 Next Steps:")
    print("=" * 40)
    print("1. 📧 Check your email for the SAM Pro activation key")
    print("2. 🚀 Start SAM with: python start_sam_secure.py")
    print("3. 🔐 Enter your master password to unlock SAM")
    print("4. 🔑 Look for 'SAM Pro Activation' in the sidebar")
    print("5. ✨ Enter your activation key to unlock Pro features")
    print("=" * 40)
    
    print("\n💡 Helpful Information:")
    print("• Activation keys are sent immediately upon registration")
    print("• Check your spam folder if you don't see the email")
    print("• You can re-run this script anytime: python register_sam_pro.py")
    print("• SAM works without Pro features - they're optional enhancements")
    
    print("\n🔗 Useful Links:")
    print("• SAM Documentation: docs/ folder in your installation")
    print("• GitHub Repository: https://github.com/forge-1825/SAM")
    print("• Support: sam-pro@forge1825.net")

def display_troubleshooting():
    """Display troubleshooting information."""
    print("\n🔧 Troubleshooting:")
    print("=" * 40)
    print("❓ Registration page won't load?")
    print("  • Wait a few more seconds and refresh")
    print("  • Check if port 8503 is available")
    print("  • Try manually: streamlit run sam_pro_registration.py --server.port 8503")
    
    print("\n❓ Didn't receive activation email?")
    print("  • Check your spam/junk folder")
    print("  • Verify email address was entered correctly")
    print("  • Wait a few minutes - delivery can take time")
    print("  • Contact support: sam-pro@forge1825.net")
    
    print("\n❓ Registration form shows errors?")
    print("  • Ensure all required fields are filled")
    print("  • Use a valid email address format")
    print("  • Accept the terms and conditions")
    
    print("\n❓ Need help with SAM installation?")
    print("  • Run: python setup.py")
    print("  • Check: SETUP_OPTIONS.md")
    print("  • Review: docs/installation_guide.md")

def main():
    """Main registration workflow."""
    print_header()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot start registration due to missing dependencies")
        print("💡 Please complete SAM installation first: python setup.py")
        return 1
    
    # Start registration interface
    process = start_registration_interface()
    if not process:
        print("\n❌ Failed to start registration interface")
        display_troubleshooting()
        return 1
    
    # Open registration page
    open_registration_page()
    
    # Display instructions
    display_instructions()
    
    # Wait for completion
    wait_for_completion(process)
    
    # Display next steps
    display_next_steps()
    
    print("\n🎉 Registration process complete!")
    print("Thank you for choosing SAM Pro!")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏭️  Registration cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please try again or contact support: sam-pro@forge1825.net")
        sys.exit(1)
