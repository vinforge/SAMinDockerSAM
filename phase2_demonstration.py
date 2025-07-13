#!/usr/bin/env python3
"""
Phase 2 Procedural Memory Demonstration
=======================================

Demonstrates the smart integration features of SAM's Procedural Memory Engine
including Meta-Router classification, context injection, and intelligent chat handling.

Author: SAM Development Team
Version: 2.0.0
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def demonstrate_meta_router():
    """Demonstrate the Meta-Router's LLM-powered query classification."""
    print("🧠 Meta-Router Demonstration")
    print("=" * 50)
    
    try:
        from sam.cognition.meta_router import get_meta_router
        
        router = get_meta_router()
        
        # Test queries that demonstrate intelligent classification
        test_queries = [
            # Procedural queries
            ("How do I deploy code to production?", "Should route to procedural memory"),
            ("Steps to backup the database", "Should route to procedural memory"),
            ("Walk me through creating a sales report", "Should route to procedural memory"),
            
            # Factual queries
            ("What is Docker?", "Should route to knowledge base"),
            ("Who invented Python?", "Should route to knowledge base"),
            ("Define machine learning", "Should route to knowledge base"),
            
            # General chat
            ("Hello SAM!", "Should route to general chat"),
            ("Thanks for your help", "Should route to general chat"),
            ("How are you today?", "Should route to general chat")
        ]
        
        for query, expected in test_queries:
            decision = router.route_query(query)
            
            print(f"\n📝 Query: \"{query}\"")
            print(f"🎯 Intent: {decision.intent.value}")
            print(f"📊 Confidence: {decision.confidence:.2f}")
            print(f"🚀 Action: {decision.suggested_action}")
            print(f"🔧 Method: {decision.metadata.get('classification_method', 'unknown')}")
            print(f"💭 Expected: {expected}")
            
            # Verify classification is reasonable
            if decision.confidence > 0.8:
                print("✅ High confidence classification")
            else:
                print("⚠️ Lower confidence - may need review")
        
        print("\n🎉 Meta-Router demonstration complete!")
        return True
        
    except Exception as e:
        print(f"❌ Meta-Router demonstration failed: {e}")
        return False

def demonstrate_procedural_integration():
    """Demonstrate procedural memory integration and context formatting."""
    print("\n🔧 Procedural Integration Demonstration")
    print("=" * 50)
    
    try:
        from sam.memory.procedural_memory import get_procedural_memory_store
        from sam.memory.procedural_integration import get_procedural_integration_service
        
        # Get the store and add a sample procedure if needed
        store = get_procedural_memory_store()
        integration_service = get_procedural_integration_service()
        
        # Test queries
        test_queries = [
            "How do I create a weekly sales report?",
            "Steps to backup the system",
            "Deploy code to production",
            "Set up a team meeting"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: \"{query}\"")
            
            # Search for procedures
            formatted_context = integration_service.search_and_format_procedures(query)
            
            if formatted_context:
                print("✅ Found relevant procedures!")
                print(f"📄 Context length: {len(formatted_context)} characters")
                
                # Show a preview of the formatted context
                lines = formatted_context.split('\n')
                preview_lines = lines[:10]  # First 10 lines
                print("📋 Context Preview:")
                for line in preview_lines:
                    print(f"   {line}")
                if len(lines) > 10:
                    print(f"   ... ({len(lines) - 10} more lines)")
                
            else:
                print("❌ No relevant procedures found")
                print("💡 This would trigger procedure creation suggestion")
        
        print("\n🎉 Procedural Integration demonstration complete!")
        return True
        
    except Exception as e:
        print(f"❌ Procedural Integration demonstration failed: {e}")
        return False

def demonstrate_chat_integration():
    """Demonstrate the complete chat integration flow."""
    print("\n💬 Chat Integration Demonstration")
    print("=" * 50)
    
    try:
        from sam.chat.procedural_chat_handler import get_procedural_chat_handler
        
        handler = get_procedural_chat_handler()
        
        # Simulate different types of user interactions
        interactions = [
            {
                "query": "How do I backup the database?",
                "type": "Procedural Request",
                "expected": "Should find procedures or offer to create one"
            },
            {
                "query": "What is the difference between SQL and NoSQL?",
                "type": "Factual Question",
                "expected": "Should route to knowledge base"
            },
            {
                "query": "Hello SAM, can you help me today?",
                "type": "General Chat",
                "expected": "Should engage conversationally"
            }
        ]
        
        for interaction in interactions:
            query = interaction["query"]
            interaction_type = interaction["type"]
            expected = interaction["expected"]
            
            print(f"\n📝 {interaction_type}: \"{query}\"")
            print(f"💭 Expected: {expected}")
            
            # Process the query
            result = handler.process_user_query(query)
            
            print(f"🎯 Response Type: {result.get('response_type')}")
            print(f"🧠 Has Procedural Context: {result.get('has_procedural_context', False)}")
            print(f"🚀 Follow-up Actions: {result.get('follow_up_actions', [])}")
            
            # Show routing decision details
            routing_decision = result.get('routing_decision')
            if routing_decision:
                print(f"📊 Classification Confidence: {routing_decision.confidence:.2f}")
                print(f"🔧 Classification Method: {routing_decision.metadata.get('classification_method', 'unknown')}")
            
            # Simulate what would happen in the chat interface
            if result.get('response_type') == 'procedural_guidance':
                print("💡 Chat Interface Action: Show procedural context in expander")
                print("🤖 SAM Response: Enhanced with step-by-step guidance")
            elif result.get('response_type') == 'procedural_not_found':
                print("💡 Chat Interface Action: Show procedure creation suggestion")
                print("🤖 SAM Response: Offer to create new procedure")
            elif result.get('response_type') == 'factual_search':
                print("💡 Chat Interface Action: Route to knowledge base search")
                print("🤖 SAM Response: Provide factual information")
            else:
                print("💡 Chat Interface Action: Engage in normal conversation")
                print("🤖 SAM Response: Conversational response")
        
        print("\n🎉 Chat Integration demonstration complete!")
        return True
        
    except Exception as e:
        print(f"❌ Chat Integration demonstration failed: {e}")
        return False

def demonstrate_end_to_end_flow():
    """Demonstrate the complete end-to-end flow."""
    print("\n🔄 End-to-End Flow Demonstration")
    print("=" * 50)
    
    try:
        print("Simulating user asking: 'How do I create a weekly sales report?'")
        print()
        
        # Step 1: Meta-Router Classification
        print("1️⃣ Meta-Router Classification:")
        from sam.cognition.meta_router import get_meta_router
        router = get_meta_router()
        decision = router.route_query("How do I create a weekly sales report?")
        print(f"   Intent: {decision.intent.value}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Action: {decision.suggested_action}")
        
        # Step 2: Procedural Memory Search
        print("\n2️⃣ Procedural Memory Search:")
        from sam.memory.procedural_integration import get_procedural_integration_service
        integration_service = get_procedural_integration_service()
        context = integration_service.search_and_format_procedures("How do I create a weekly sales report?")
        
        if context:
            print("   ✅ Found relevant procedures")
            print(f"   📄 Context ready for LLM injection ({len(context)} chars)")
        else:
            print("   ❌ No procedures found")
            print("   💡 Would suggest creating new procedure")
        
        # Step 3: Chat Handler Processing
        print("\n3️⃣ Chat Handler Processing:")
        from sam.chat.procedural_chat_handler import get_procedural_chat_handler
        handler = get_procedural_chat_handler()
        result = handler.process_user_query("How do I create a weekly sales report?")
        print(f"   Response Type: {result.get('response_type')}")
        print(f"   Has Context: {result.get('has_procedural_context', False)}")
        
        # Step 4: LLM Response Generation (simulated)
        print("\n4️⃣ LLM Response Generation:")
        if result.get('has_procedural_context'):
            print("   🤖 SAM would respond with step-by-step guidance")
            print("   📋 Using procedural context for accurate instructions")
            print("   🎯 Offering to track user's progress")
        else:
            print("   🤖 SAM would offer to help create the procedure")
            print("   💡 Asking user for details about their process")
            print("   📝 Ready to capture and store new procedure")
        
        # Step 5: User Experience
        print("\n5️⃣ User Experience:")
        print("   👤 User sees relevant, actionable guidance")
        print("   🧠 SAM's procedural memory grows with each interaction")
        print("   🔄 Future queries become more accurate and helpful")
        
        print("\n🎉 End-to-End Flow demonstration complete!")
        return True
        
    except Exception as e:
        print(f"❌ End-to-End Flow demonstration failed: {e}")
        return False

def main():
    """Run the complete Phase 2 demonstration."""
    print("🚀 SAM Procedural Memory Phase 2 Demonstration")
    print("🧠 Smart Integration with Meta-Router & LLM Classification")
    print("=" * 70)
    
    demonstrations = [
        ("Meta-Router", demonstrate_meta_router),
        ("Procedural Integration", demonstrate_procedural_integration),
        ("Chat Integration", demonstrate_chat_integration),
        ("End-to-End Flow", demonstrate_end_to_end_flow)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demonstrations:
        try:
            success = demo_func()
            if success:
                success_count += 1
                print(f"\n✅ {demo_name} demonstration: SUCCESS")
            else:
                print(f"\n❌ {demo_name} demonstration: FAILED")
        except Exception as e:
            print(f"\n❌ {demo_name} demonstration: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 PHASE 2 DEMONSTRATION SUMMARY")
    print("=" * 70)
    print(f"✅ Successful demonstrations: {success_count}/{len(demonstrations)}")
    print(f"📊 Success rate: {(success_count/len(demonstrations))*100:.1f}%")
    
    if success_count == len(demonstrations):
        print("\n🎉 ALL DEMONSTRATIONS SUCCESSFUL!")
        print("🚀 Phase 2 Smart Integration is working perfectly!")
        print("\n🌟 Key Features Demonstrated:")
        print("   • LLM-powered query classification")
        print("   • Intelligent procedural memory search")
        print("   • Context injection for enhanced responses")
        print("   • Seamless chat integration")
        print("   • End-to-end intelligent workflow")
        print("\n💡 SAM now has true procedural intelligence!")
    else:
        print(f"\n⚠️ {len(demonstrations) - success_count} demonstration(s) had issues")
        print("🔧 Please review the output above for details")
    
    return success_count == len(demonstrations)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
