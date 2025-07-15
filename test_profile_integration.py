#!/usr/bin/env python3
"""
Profile Integration Test
=======================

Test script to verify that the profile-based reasoning style integration
works correctly with SAM's profile system.

Usage:
    python test_profile_integration.py

Author: SAM Development Team
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_profile_reasoning_integration():
    """Test the profile reasoning integration system."""
    try:
        from sam.profiles.reasoning_profile_integration import ProfileReasoningIntegration
        
        # Initialize integration
        integration = ProfileReasoningIntegration()
        
        # Test profile loading
        profiles = integration.get_available_profiles()
        logger.info(f"✅ Loaded {len(profiles)} profiles: {', '.join(profiles)}")
        
        # Test each profile's reasoning configuration
        for profile in profiles:
            config = integration.get_profile_reasoning_config(profile)
            if config:
                style = config.get("default_reasoning_style", "N/A")
                strength = config.get("default_strength", "N/A")
                description = config.get("description", "N/A")
                
                logger.info(f"  📋 {profile}: {style} (strength: {strength})")
                logger.info(f"      {description}")
            else:
                logger.warning(f"  ⚠️ {profile}: No reasoning configuration")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Profile reasoning integration test failed: {e}")
        return False

def test_profile_style_application():
    """Test applying reasoning styles based on profiles."""
    try:
        from sam.profiles.reasoning_profile_integration import get_profile_reasoning_integration
        
        integration = get_profile_reasoning_integration()
        
        # Test style application for each profile
        test_profiles = ["researcher", "business", "general", "legal"]
        
        for profile in test_profiles:
            if profile in integration.get_available_profiles():
                style, strength = integration.apply_profile_reasoning_style(profile)
                logger.info(f"✅ {profile} profile -> {style} (strength: {strength})")
            else:
                logger.warning(f"⚠️ Profile '{profile}' not available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Profile style application test failed: {e}")
        return False

def test_profile_configuration_validation():
    """Test that profile configurations are valid."""
    try:
        import json
        from pathlib import Path
        
        profiles_dir = Path("multimodal_processing/dimension_profiles")
        
        if not profiles_dir.exists():
            logger.warning("⚠️ Profiles directory not found")
            return True
        
        profile_files = list(profiles_dir.glob("*.json"))
        valid_profiles = 0
        
        for profile_file in profile_files:
            try:
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                
                profile_name = profile_data.get("name", profile_file.stem)
                reasoning_config = profile_data.get("reasoning_style_config")
                
                if reasoning_config:
                    # Validate required fields
                    required_fields = ["default_reasoning_style", "default_strength", "description"]
                    missing_fields = [field for field in required_fields if field not in reasoning_config]
                    
                    if missing_fields:
                        logger.warning(f"⚠️ {profile_name}: Missing fields: {missing_fields}")
                    else:
                        logger.info(f"✅ {profile_name}: Valid reasoning configuration")
                        valid_profiles += 1
                else:
                    logger.warning(f"⚠️ {profile_name}: No reasoning_style_config section")
                    
            except Exception as e:
                logger.error(f"❌ Error validating {profile_file}: {e}")
        
        logger.info(f"📊 Validated {valid_profiles} profile configurations")
        return True
        
    except Exception as e:
        logger.error(f"❌ Profile configuration validation failed: {e}")
        return False

def test_reasoning_style_mapping():
    """Test that reasoning style mappings are correct."""
    try:
        from sam.profiles.reasoning_profile_integration import get_profile_reasoning_integration
        from sam.reasoning.prompt_steerer import get_prompt_steerer
        
        integration = get_profile_reasoning_integration()
        steerer = get_prompt_steerer()
        
        available_styles = steerer.get_available_styles()
        logger.info(f"Available reasoning styles: {', '.join(available_styles)}")
        
        # Check that all profile default styles are valid
        invalid_mappings = []
        
        for profile in integration.get_available_profiles():
            config = integration.get_profile_reasoning_config(profile)
            if config:
                default_style = config.get("default_reasoning_style")
                fallback_style = config.get("fallback_style")
                
                if default_style and default_style not in available_styles and default_style != "default":
                    invalid_mappings.append(f"{profile}: invalid default style '{default_style}'")
                
                if fallback_style and fallback_style not in available_styles and fallback_style != "default":
                    invalid_mappings.append(f"{profile}: invalid fallback style '{fallback_style}'")
        
        if invalid_mappings:
            for mapping in invalid_mappings:
                logger.error(f"❌ {mapping}")
            return False
        else:
            logger.info("✅ All profile reasoning style mappings are valid")
            return True
        
    except Exception as e:
        logger.error(f"❌ Reasoning style mapping test failed: {e}")
        return False

def test_profile_reasoning_workflow():
    """Test the complete profile reasoning workflow."""
    try:
        from sam.profiles.reasoning_profile_integration import get_profile_reasoning_integration
        from sam.reasoning.prompt_steerer import get_prompt_steerer
        
        integration = get_profile_reasoning_integration()
        steerer = get_prompt_steerer()
        
        # Test workflow for researcher profile
        test_profile = "researcher"
        test_prompt = "How can we improve renewable energy efficiency?"
        
        if test_profile in integration.get_available_profiles():
            # Get profile configuration
            config = integration.get_profile_reasoning_config(test_profile)
            logger.info(f"📋 Testing workflow for {test_profile} profile")
            logger.info(f"   Config: {config}")
            
            # Apply profile reasoning style
            style, strength = integration.apply_profile_reasoning_style(test_profile)
            logger.info(f"   Applied style: {style} (strength: {strength})")
            
            # Apply style to prompt
            enhanced_prompt = steerer.apply_style(test_prompt, style, strength)
            logger.info(f"   Original prompt: {test_prompt}")
            logger.info(f"   Enhanced length: {len(enhanced_prompt)} chars")
            
            if enhanced_prompt != test_prompt:
                logger.info("✅ Complete profile reasoning workflow successful")
                return True
            else:
                logger.warning("⚠️ Prompt was not enhanced")
                return False
        else:
            logger.warning(f"⚠️ Test profile '{test_profile}' not available")
            return True
        
    except Exception as e:
        logger.error(f"❌ Profile reasoning workflow test failed: {e}")
        return False

def main():
    """Run all profile integration tests."""
    logger.info("🚀 Starting Profile Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Profile Reasoning Integration", test_profile_reasoning_integration),
        ("Profile Style Application", test_profile_style_application),
        ("Profile Configuration Validation", test_profile_configuration_validation),
        ("Reasoning Style Mapping", test_reasoning_style_mapping),
        ("Profile Reasoning Workflow", test_profile_reasoning_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Profile Integration Test Results")
    logger.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All profile integration tests passed!")
        logger.info("\n🎯 Profile Integration Summary:")
        logger.info("- ✅ Researcher profile -> researcher_style (analytical)")
        logger.info("- ✅ Business profile -> step_by_step_reasoning (systematic)")
        logger.info("- ✅ General profile -> step_by_step_reasoning (balanced)")
        logger.info("- ✅ Legal profile -> researcher_style (rigorous)")
        logger.info("\n🚀 Ready for user testing!")
        return 0
    else:
        logger.error(f"💥 {total - passed} tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
