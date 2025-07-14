#!/usr/bin/env python3
"""
Test Suite for Phase 2C: Meta-reasoning Pipeline Hardening
==========================================================

Tests the hardened meta-reasoning pipeline with comprehensive superficiality
integration, error handling, and performance monitoring.

Author: SAM Development Team
Version: 1.0.0
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the components to test
from reasoning.phase5_integration import Phase5ResponseEnhancer, Phase5EnhancedResponse


class TestPhase2CPipelineHardening:
    """Test cases for hardened meta-reasoning pipeline with superficiality integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock components
        self.mock_reflective_engine = Mock()
        self.mock_conflict_detector = Mock()
        self.mock_confidence_justifier = Mock()
        
        # Initialize enhancer with mocks
        self.enhancer = Phase5ResponseEnhancer(
            reflective_engine=self.mock_reflective_engine,
            conflict_detector=self.mock_conflict_detector,
            confidence_justifier=self.mock_confidence_justifier
        )
    
    def test_superficiality_context_propagation(self):
        """Test that superficiality information is properly propagated through the pipeline."""
        
        # Mock reflective result with superficiality information
        mock_reflective_result = Mock()
        mock_reflective_result.response_analysis = {
            "is_substantive": False,
            "verification_confidence": 0.8,
            "verification_method": "pattern_matching",
            "superficiality_check": {
                "verification_explanation": "Contains master key patterns"
            }
        }
        mock_reflective_result.alternative_perspectives = []
        mock_reflective_result.adversarial_critiques = []
        mock_reflective_result.dimension_conflicts = []
        mock_reflective_result.confidence_justification = None
        mock_reflective_result.trade_off_analysis = {}
        mock_reflective_result.final_response = "Test response"
        mock_reflective_result.reasoning_chain = []
        mock_reflective_result.critique_summary = "Test"
        mock_reflective_result.meta_confidence = 0.5
        mock_reflective_result.reflection_duration_ms = 100
        mock_reflective_result.timestamp = datetime.now().isoformat()
        
        self.mock_reflective_engine.reflective_reasoning_cycle.return_value = mock_reflective_result
        self.mock_conflict_detector.detect_conflicts.return_value = []
        
        # Mock confidence justification
        mock_confidence_justification = Mock()
        mock_confidence_justification.confidence_score = 0.4
        mock_confidence_justification.confidence_level = Mock()
        mock_confidence_justification.confidence_level.value = "low"
        mock_confidence_justification.reliability_assessment = "Low reliability due to superficiality"
        mock_confidence_justification.primary_factors = []
        mock_confidence_justification.limiting_factors = ["🚨 Critical superficiality issue"]
        self.mock_confidence_justifier.justify_confidence.return_value = mock_confidence_justification
        
        # Test enhancement
        result = self.enhancer.enhance_response("Test query", "Test response")
        
        # Verify superficiality context was passed to confidence justifier
        confidence_call_args = self.mock_confidence_justifier.justify_confidence.call_args
        confidence_context = confidence_call_args[0][1]  # Second argument is context
        
        assert confidence_context["is_substantive"] is False
        assert confidence_context["verification_confidence"] == 0.8
        assert confidence_context["verification_method"] == "pattern_matching"
        assert "superficiality_check" in confidence_context
    
    def test_superficiality_warnings_in_enhanced_response(self):
        """Test that superficiality warnings appear in the enhanced response."""
        
        # Mock superficial response
        mock_reflective_result = Mock()
        mock_reflective_result.response_analysis = {
            "is_substantive": False,
            "verification_confidence": 0.9,
            "verification_method": "model_based",
            "superficiality_check": {
                "verification_explanation": "Response contains multiple master key patterns"
            }
        }
        mock_reflective_result.alternative_perspectives = []
        mock_reflective_result.adversarial_critiques = []
        
        self.mock_reflective_engine.reflective_reasoning_cycle.return_value = mock_reflective_result
        self.mock_conflict_detector.detect_conflicts.return_value = []
        self.mock_confidence_justifier.justify_confidence.return_value = Mock()
        
        result = self.enhancer.enhance_response("Test query", "Test response")
        
        # Verify superficiality warning is in enhanced response
        assert "🚨 **Quality Alert: Superficial Response Detected**" in result.enhanced_response
        assert "master key patterns" in result.enhanced_response
        assert "model_based" in result.enhanced_response
    
    def test_meta_reasoning_summary_includes_superficiality(self):
        """Test that meta-reasoning summary includes superficiality information."""
        
        # Mock superficial response
        mock_reflective_result = Mock()
        mock_reflective_result.response_analysis = {
            "is_substantive": False,
            "verification_confidence": 0.8,
            "verification_method": "pattern_matching"
        }
        mock_reflective_result.alternative_perspectives = []
        mock_reflective_result.adversarial_critiques = []
        mock_reflective_result.meta_confidence = 0.4
        mock_reflective_result.reflection_duration_ms = 150
        
        self.mock_reflective_engine.reflective_reasoning_cycle.return_value = mock_reflective_result
        self.mock_conflict_detector.detect_conflicts.return_value = []
        self.mock_confidence_justifier.justify_confidence.return_value = Mock()
        
        result = self.enhancer.enhance_response("Test query", "Test response")
        
        # Verify superficiality is mentioned in summary
        assert "⚠️ Superficial" in result.meta_reasoning_summary
        assert "pattern_matching" in result.meta_reasoning_summary
    
    def test_performance_monitoring_and_logging(self):
        """Test that performance monitoring logs stage timings."""
        
        # Mock components with realistic delays
        def mock_reflective_cycle(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay
            mock_result = Mock()
            mock_result.response_analysis = {"is_substantive": True, "verification_method": "none"}
            mock_result.alternative_perspectives = []
            mock_result.adversarial_critiques = []
            return mock_result
        
        self.mock_reflective_engine.reflective_reasoning_cycle.side_effect = mock_reflective_cycle
        self.mock_conflict_detector.detect_conflicts.return_value = []
        self.mock_confidence_justifier.justify_confidence.return_value = Mock()
        
        with patch('reasoning.phase5_integration.logger') as mock_logger:
            result = self.enhancer.enhance_response("Test query", "Test response")
            
            # Verify performance logging
            debug_calls = [call for call in mock_logger.debug.call_args_list]
            info_calls = [call for call in mock_logger.info.call_args_list]
            
            # Should have stage timing logs
            stage_logs = [call for call in debug_calls if "Stage" in str(call)]
            assert len(stage_logs) >= 4  # At least 4 stages logged
            
            # Should have pipeline summary log
            pipeline_logs = [call for call in info_calls if "pipeline completed" in str(call)]
            assert len(pipeline_logs) >= 1
    
    def test_fallback_response_with_superficiality_preservation(self):
        """Test that fallback responses preserve superficiality information when possible."""
        
        # Mock reflective engine to raise an exception
        self.mock_reflective_engine.reflective_reasoning_cycle.side_effect = Exception("Test error")
        
        # Mock master verifier in reflective engine for fallback superficiality check
        mock_master_verifier = Mock()
        mock_superficiality_result = {
            "is_substantive": False,
            "verification_confidence": 0.7,
            "verification_explanation": "Contains master key patterns in fallback mode",
            "verification_method": "fallback"
        }
        
        self.mock_reflective_engine.master_verifier = mock_master_verifier
        self.mock_reflective_engine._check_response_superficiality.return_value = mock_superficiality_result
        
        context = {"original_query": "Test query"}
        result = self.enhancer.enhance_response("Test query", "Let's solve this step by step", context)
        
        # Verify fallback response includes superficiality information
        assert not result.phase5_enabled
        assert "⚠️ **Quality Note:**" in result.enhanced_response
        assert "master key patterns" in result.enhanced_response
        assert "⚠️ Superficiality detected in fallback mode" in result.meta_reasoning_summary
    
    def test_pipeline_validation_detects_inconsistencies(self):
        """Test that pipeline validation detects inconsistencies."""
        
        # Create a result with inconsistent superficiality and confidence
        mock_reflective_result = Mock()
        mock_reflective_result.response_analysis = {
            "is_substantive": False,  # Superficial
            "verification_confidence": 0.9,
            "verification_method": "pattern_matching"
        }
        
        # Mock high confidence despite superficiality (inconsistent)
        mock_confidence_justification = Mock()
        mock_confidence_justification.confidence_score = 0.9  # High confidence
        mock_confidence_justification.evidence_items = []  # No substantiveness evidence
        
        # Create test result
        test_result = Phase5EnhancedResponse(
            original_response="Test response",
            reflective_result=mock_reflective_result,
            dimension_conflicts=[],
            confidence_justification=mock_confidence_justification,
            enhanced_response="Test enhanced response",  # No superficiality warning
            meta_reasoning_summary="Test summary",  # No superficiality mention
            processing_time_ms=100,
            phase5_enabled=True,
            timestamp=datetime.now().isoformat()
        )
        
        # Test validation
        validation_result = self.enhancer._validate_pipeline_result(test_result)
        
        # Should detect inconsistencies
        assert not validation_result["valid"]
        issues = validation_result["issues"]
        
        # Should detect high confidence despite superficiality
        high_confidence_issue = any("High confidence despite superficial" in issue for issue in issues)
        assert high_confidence_issue
        
        # Should detect missing substantiveness evidence
        missing_evidence_issue = any("Missing substantiveness evidence" in issue for issue in issues)
        assert missing_evidence_issue
        
        # Should detect missing superficiality warning
        missing_warning_issue = any("Missing superficiality warning" in issue for issue in issues)
        assert missing_warning_issue
    
    def test_pipeline_validation_passes_for_consistent_results(self):
        """Test that pipeline validation passes for consistent results."""
        
        # Create a consistent result
        mock_reflective_result = Mock()
        mock_reflective_result.response_analysis = {
            "is_substantive": True,  # Substantive
            "verification_confidence": 0.9,
            "verification_method": "model_based"
        }
        
        # Mock appropriate confidence
        mock_evidence = Mock()
        mock_evidence.evidence_type.value = "response_substantiveness"
        
        mock_confidence_justification = Mock()
        mock_confidence_justification.confidence_score = 0.8  # Appropriate confidence
        mock_confidence_justification.evidence_items = [mock_evidence]
        
        # Create consistent test result
        test_result = Phase5EnhancedResponse(
            original_response="Test response",
            reflective_result=mock_reflective_result,
            dimension_conflicts=[],
            confidence_justification=mock_confidence_justification,
            enhanced_response="Test enhanced response with good quality",
            meta_reasoning_summary="Quality: Substantive (verified by model_based)",
            processing_time_ms=100,
            phase5_enabled=True,
            timestamp=datetime.now().isoformat()
        )
        
        # Test validation
        validation_result = self.enhancer._validate_pipeline_result(test_result)
        
        # Should pass validation
        assert validation_result["valid"]
        assert len(validation_result["issues"]) == 0
    
    def test_error_handling_preserves_context(self):
        """Test that error handling preserves important context information."""
        
        # Mock reflective engine to raise an exception
        self.mock_reflective_engine.reflective_reasoning_cycle.side_effect = Exception("Critical error")
        
        # Mock that master verifier is not available
        self.mock_reflective_engine.master_verifier = None
        
        context = {
            "original_query": "Test query",
            "is_substantive": False,
            "verification_confidence": 0.8
        }
        
        result = self.enhancer.enhance_response("Test query", "Test response", context)
        
        # Verify fallback response is created
        assert not result.phase5_enabled
        assert "⚠️ **Note:** Advanced meta-reasoning temporarily unavailable" in result.enhanced_response
        assert "Fallback mode: Critical error" in result.meta_reasoning_summary
        
        # Verify error is logged in response analysis
        assert "error" in result.reflective_result.response_analysis


if __name__ == "__main__":
    pytest.main([__file__])
