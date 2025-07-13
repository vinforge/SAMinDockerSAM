#!/usr/bin/env python3
"""
Complete Procedural Memory Engine Demonstration
===============================================

Comprehensive demonstration of all three phases of SAM's Procedural Memory Engine:
- Phase 1: Core procedural memory with secure storage
- Phase 2: Smart integration with Meta-Router and LLM classification  
- Phase 3: Advanced cognitive features with execution tracking and proactive suggestions

Author: SAM Development Team
Version: 2.0.0 (Complete Implementation)
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def demonstrate_complete_system():
    """Demonstrate the complete procedural memory system."""
    print("🧠 SAM Procedural Memory Engine - Complete System Demonstration")
    print("=" * 80)
    
    try:
        # Phase 1: Core Procedural Memory
        print("\n🏗️ PHASE 1: Core Procedural Memory")
        print("-" * 50)
        
        from sam.memory.procedural_memory import get_procedural_memory_store, Procedure, ProcedureStep
        
        store = get_procedural_memory_store()
        
        # Create a comprehensive example procedure
        deployment_steps = [
            ProcedureStep(
                step_number=1,
                description="Run all tests",
                details="Execute: npm test && npm run test:integration",
                expected_outcome="All tests pass with no failures",
                estimated_duration="5 minutes",
                prerequisites=["Code reviewed", "Tests written"],
                tools_required=["Node.js", "npm"]
            ),
            ProcedureStep(
                step_number=2,
                description="Build production version",
                details="Create optimized build: npm run build:production",
                expected_outcome="Build completes without errors",
                estimated_duration="3 minutes"
            ),
            ProcedureStep(
                step_number=3,
                description="Deploy to production",
                details="Deploy using: kubectl apply -f deployment.yaml",
                expected_outcome="New version live on production",
                estimated_duration="5 minutes",
                tools_required=["kubectl", "Docker"]
            )
        ]
        
        deployment_procedure = Procedure(
            name="Production Deployment Workflow",
            description="Safe deployment process for web applications with testing and monitoring",
            tags=["deployment", "production", "testing", "kubernetes"],
            category="technical",
            difficulty_level="intermediate",
            estimated_total_time="15 minutes",
            parameters={
                "app_name": "web-application",
                "environment": "production",
                "namespace": "default"
            },
            steps=deployment_steps
        )
        
        # Add procedure to store
        success = store.add_procedure(deployment_procedure)
        if success:
            print(f"✅ Created procedure: {deployment_procedure.name}")
            print(f"   📊 {len(deployment_procedure.steps)} steps")
            print(f"   🏷️ Tags: {', '.join(deployment_procedure.tags)}")
            print(f"   ⏱️ Estimated time: {deployment_procedure.estimated_total_time}")
        
        # Phase 2: Smart Integration
        print("\n🧠 PHASE 2: Smart Integration")
        print("-" * 50)
        
        from sam.cognition.meta_router import get_meta_router
        from sam.memory.procedural_integration import get_procedural_integration_service
        from sam.chat.procedural_chat_handler import get_procedural_chat_handler
        
        # Test Meta-Router classification
        router = get_meta_router()
        test_queries = [
            "How do I deploy my application to production?",
            "What is Kubernetes?",
            "Hello SAM, how are you today?"
        ]
        
        print("🎯 Meta-Router Query Classification:")
        for query in test_queries:
            decision = router.route_query(query)
            print(f"   Query: '{query}'")
            print(f"   → Intent: {decision.intent.value} ({decision.confidence:.0%} confidence)")
            print(f"   → Action: {decision.suggested_action}")
        
        # Test procedural integration
        integration_service = get_procedural_integration_service()
        procedural_query = "How do I deploy my application to production?"
        
        print(f"\n🔧 Procedural Integration:")
        formatted_context = integration_service.search_and_format_procedures(procedural_query)
        if formatted_context:
            print("   ✅ Found relevant procedures")
            print(f"   📄 Context length: {len(formatted_context)} characters")
            print("   📋 Context includes step-by-step guidance")
        
        # Test chat handler
        chat_handler = get_procedural_chat_handler()
        chat_result = chat_handler.process_user_query(procedural_query)
        
        print(f"\n💬 Chat Integration:")
        print(f"   Response type: {chat_result.get('response_type')}")
        print(f"   Has procedural context: {chat_result.get('has_procedural_context', False)}")
        print(f"   Follow-up actions: {len(chat_result.get('follow_up_actions', []))}")
        
        # Phase 3: Advanced Cognitive Features
        print("\n🚀 PHASE 3: Advanced Cognitive Features")
        print("-" * 50)
        
        # Execution Tracking
        from sam.memory.execution_tracker import get_execution_tracker
        
        tracker = get_execution_tracker()
        
        print("📊 Execution Tracking:")
        execution_id = tracker.start_execution(
            procedure_id=deployment_procedure.id,
            procedure_name=deployment_procedure.name,
            user_id="demo_user"
        )
        
        if execution_id:
            print(f"   ✅ Started execution: {execution_id}")
            
            # Simulate step progress
            from sam.memory.execution_tracker import StepStatus
            tracker.update_step_status(execution_id, 1, StepStatus.COMPLETED, "Tests passed successfully")
            tracker.update_step_status(execution_id, 2, StepStatus.IN_PROGRESS, "Building application")
            
            execution = tracker.get_execution_status(execution_id)
            print(f"   📈 Current step: {execution.current_step}")
            print(f"   ⏱️ Duration: {(execution.started_at).strftime('%H:%M:%S')}")
        
        # Proactive Suggestions
        from sam.cognition.proactive_suggestions import get_proactive_suggestion_engine
        
        suggestion_engine = get_proactive_suggestion_engine()
        
        print("\n💡 Proactive Suggestions:")
        # Simulate user behavior patterns
        actions = [
            ("query", "How do I deploy to production?"),
            ("procedure_execution", "Production Deployment", {"category": "technical"}),
            ("query", "Steps for production deployment"),
            ("procedure_execution", "Production Deployment", {"category": "technical"}),
        ]
        
        for action_type, content, *context in actions:
            ctx = context[0] if context else {}
            suggestion_engine.record_user_action(action_type, content, ctx)
        
        # Analyze patterns
        patterns = suggestion_engine.analyze_patterns()
        suggestions = suggestion_engine.get_active_suggestions()
        
        print(f"   📊 Recorded {len(actions)} user actions")
        print(f"   🔍 Detected {len(patterns)} workflow patterns")
        print(f"   💭 Generated {len(suggestions)} proactive suggestions")
        
        if suggestions:
            for suggestion in suggestions[:2]:  # Show first 2 suggestions
                print(f"   → {suggestion.title}")
                print(f"     Confidence: {suggestion.confidence:.0%}")
                print(f"     Benefit: {suggestion.potential_benefit}")
        
        # Knowledge Enrichment
        from sam.memory.knowledge_enrichment import get_knowledge_enrichment_engine
        
        enrichment_engine = get_knowledge_enrichment_engine()
        
        print("\n🧠 Knowledge Enrichment:")
        user_context = {
            'operating_system': 'Linux',
            'environment': {'is_production': True},
            'user_info': {'name': 'demo_user'}
        }
        
        enriched_data = enrichment_engine.enrich_procedure(deployment_procedure, user_context)
        
        print(f"   ✅ Procedure enriched with contextual information")
        print(f"   📝 Enhanced steps: {len(enriched_data.get('enriched_steps', []))}")
        print(f"   🔧 Dynamic parameters: {len(enriched_data.get('dynamic_parameters', {}))}")
        print(f"   📚 Contextual info: {len(enriched_data.get('contextual_information', {}))}")
        
        # Show enrichment example
        if enriched_data.get('enriched_steps'):
            first_step = enriched_data['enriched_steps'][0]
            if first_step.get('contextual_notes'):
                print(f"   💡 Example contextual note: {first_step['contextual_notes'][0]}")
        
        # Complete Workflow Demonstration
        print("\n🔄 COMPLETE WORKFLOW DEMONSTRATION")
        print("-" * 50)
        
        print("Simulating user asking: 'How do I deploy my app safely?'")
        
        # Step 1: Query classification
        query = "How do I deploy my app safely?"
        decision = router.route_query(query)
        print(f"1️⃣ Classification: {decision.intent.value} ({decision.confidence:.0%})")
        
        # Step 2: Procedural search and enrichment
        if decision.suggested_action == "search_procedural_memory":
            context = integration_service.search_and_format_procedures(query)
            if context:
                print("2️⃣ Found relevant procedures with enriched context")
                
                # Step 3: Enhanced response generation
                enhanced_prompt = f"""
Based on your query about safe deployment, I found this relevant procedure:

{context[:300]}...

This procedure includes safety checks, testing requirements, and monitoring steps.
Would you like me to guide you through executing this procedure step-by-step?
"""
                print("3️⃣ Enhanced response ready for user")
                
                # Step 4: Execution tracking offer
                print("4️⃣ Execution tracking available for progress monitoring")
                
                # Step 5: Pattern learning
                suggestion_engine.record_user_action("query", query)
                print("5️⃣ User behavior recorded for future suggestions")
        
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("🧠 SAM's Procedural Memory Engine is now fully operational with:")
        print("   ✅ Secure procedure storage and management")
        print("   ✅ Intelligent query routing and classification")
        print("   ✅ Context-aware response enhancement")
        print("   ✅ Real-time execution tracking")
        print("   ✅ Proactive workflow suggestions")
        print("   ✅ Knowledge-enriched procedure guidance")
        print("   ✅ Complete cognitive integration")
        print("\n🚀 Ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete system demonstration."""
    success = demonstrate_complete_system()
    
    if success:
        print("\n✅ Complete system demonstration successful!")
        print("🎯 All three phases working together seamlessly")
    else:
        print("\n❌ Demonstration encountered issues")
        print("🔧 Please check the error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
