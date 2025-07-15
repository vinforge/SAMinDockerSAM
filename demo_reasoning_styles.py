#!/usr/bin/env python3
"""
SAM Reasoning Style Steering Demonstration
==========================================

This script demonstrates the prompt-based reasoning style steering
functionality implemented in Phase 2 of the KV Cache Steering project.

Usage:
    python demo_reasoning_styles.py

Author: SAM Development Team
Version: 1.0.0
"""

import logging
from sam.reasoning.prompt_steerer import PromptSteerer, apply_reasoning_style

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_prompt_steering():
    """Demonstrate the prompt steering functionality."""
    print("🧠 SAM Reasoning Style Steering Demonstration")
    print("=" * 60)
    
    # Initialize the prompt steerer
    steerer = PromptSteerer()
    
    # Test prompt
    base_prompt = "How does machine learning work?"
    
    print(f"\n📝 Base Prompt: {base_prompt}")
    print("-" * 60)
    
    # Demonstrate different reasoning styles
    styles_to_test = [
        ("researcher_style", 1.2),
        ("step_by_step_reasoning", 1.0),
        ("creative_explorer", 1.1)
    ]
    
    for style_name, strength in styles_to_test:
        print(f"\n🎯 Style: {style_name} (strength: {strength})")
        print("-" * 40)
        
        # Get style information
        style_info = steerer.get_style_info(style_name)
        if style_info:
            print(f"Description: {style_info['description']}")
            print(f"Pattern: {style_info['reasoning_pattern']}")
        
        # Apply the style
        enhanced_prompt = steerer.apply_style(base_prompt, style_name, strength)
        
        print(f"\n📋 Enhanced Prompt:")
        print(enhanced_prompt)
        print("\n" + "=" * 60)

def demonstrate_strength_variations():
    """Demonstrate how different strengths affect prompt enhancement."""
    print("\n🔧 Strength Variation Demonstration")
    print("=" * 60)
    
    steerer = PromptSteerer()
    base_prompt = "What are the benefits of renewable energy?"
    style = "researcher_style"
    
    strengths = [0.5, 1.0, 2.0]
    
    for strength in strengths:
        print(f"\n💪 Strength: {strength}")
        print("-" * 30)
        
        enhanced_prompt = steerer.apply_style(base_prompt, style, strength)
        print(f"Length: {len(enhanced_prompt)} characters")
        print(f"Preview: {enhanced_prompt[:200]}...")
        
        if strength < 2.0:
            print()

def demonstrate_utility_functions():
    """Demonstrate utility functions."""
    print("\n🛠️ Utility Functions Demonstration")
    print("=" * 60)
    
    # Using the convenience function
    prompt = "Explain quantum computing"
    enhanced = apply_reasoning_style(prompt, "step_by_step_reasoning", 1.0)
    
    print(f"Original: {prompt}")
    print(f"Enhanced: {enhanced[:100]}...")
    
    # Get available styles
    steerer = PromptSteerer()
    styles = steerer.get_available_styles()
    print(f"\nAvailable styles: {', '.join(styles)}")

def demonstrate_error_handling():
    """Demonstrate error handling and fallback behavior."""
    print("\n🛡️ Error Handling Demonstration")
    print("=" * 60)
    
    steerer = PromptSteerer()
    base_prompt = "Test prompt"
    
    # Test with unknown style
    result = steerer.apply_style(base_prompt, "unknown_style", 1.0)
    print(f"Unknown style result: {result == base_prompt}")
    
    # Test with default style
    result = steerer.apply_style(base_prompt, "default", 1.0)
    print(f"Default style result: {result == base_prompt}")

def interactive_demo():
    """Interactive demonstration where user can try different styles."""
    print("\n🎮 Interactive Demonstration")
    print("=" * 60)
    
    steerer = PromptSteerer()
    styles = steerer.get_available_styles()
    
    print("Available reasoning styles:")
    for i, style in enumerate(styles, 1):
        info = steerer.get_style_info(style)
        print(f"{i}. {style}: {info['description'] if info else 'No description'}")
    
    try:
        while True:
            print("\n" + "-" * 40)
            prompt = input("Enter your prompt (or 'quit' to exit): ").strip()
            
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            
            if not prompt:
                continue
            
            print("\nSelect a reasoning style:")
            for i, style in enumerate(styles, 1):
                print(f"{i}. {style}")
            
            try:
                choice = int(input("Enter choice (1-{}): ".format(len(styles))))
                if 1 <= choice <= len(styles):
                    selected_style = styles[choice - 1]
                    
                    strength = float(input("Enter strength (0.1-3.0, default 1.0): ") or "1.0")
                    strength = max(0.1, min(3.0, strength))
                    
                    enhanced = steerer.apply_style(prompt, selected_style, strength)
                    
                    print(f"\n🎯 Style: {selected_style} (strength: {strength})")
                    print(f"📋 Enhanced Prompt:")
                    print(enhanced)
                else:
                    print("Invalid choice!")
                    
            except ValueError:
                print("Invalid input!")
                
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")

def main():
    """Main demonstration function."""
    print("🚀 Starting SAM Reasoning Style Steering Demo")
    
    try:
        # Basic demonstrations
        demonstrate_prompt_steering()
        demonstrate_strength_variations()
        demonstrate_utility_functions()
        demonstrate_error_handling()
        
        # Interactive demo
        print("\n" + "=" * 60)
        response = input("Would you like to try the interactive demo? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_demo()
        
        print("\n✅ Demo completed successfully!")
        print("\nNext steps:")
        print("1. Run the steering vector factory to generate actual vectors")
        print("2. Integrate with SAM's profile system")
        print("3. Test with real model inference")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main()
