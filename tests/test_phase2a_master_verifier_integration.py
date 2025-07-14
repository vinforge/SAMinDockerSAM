#!/usr/bin/env python3
"""
Test Suite for Phase 2A: Master Verifier Integration with ReflectiveMetaReasoningEngine
====================================================================================

Tests the integration of Master Verifier Skill with SAM's meta-reasoning pipeline
to detect and handle superficial responses.

Author: SAM Development Team
Version: 1.0.0
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the components to test
from reasoning.reflective_meta_reasoning import ReflectiveMetaReasoningEngine, CritiqueLevel


class TestPhase2AMasterVerifierIntegration:
    """Test cases for Master Verifier integration with meta-reasoning."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock Master Verifier config
        self.temp_config = {
            'verification': {
                'master_key_patterns': [
                    'thought process:', 'let\'s solve this', 'solution:'
                ],
                'min_response_length': 10
            },
            'integration': {
                'fallback_method': 'pattern_matching'
            }
        }
        
        # Create temporary config file
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        )
        yaml.dump(self.temp_config, self.temp_config_file)
        self.temp_config_file.close()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.temp_config_file.name).unlink(missing_ok=True)
    
    @patch('reasoning.reflective_meta_reasoning.MASTER_VERIFIER_AVAILABLE', True)
    @patch('reasoning.reflective_meta_reasoning.MasterVerifierSkill')
    @patch('reasoning.reflective_meta_reasoning.SAM_UIF')
    def test_meta_reasoning_with_superficial_response(self, mock_uif_class, mock_verifier_class):
        """Test meta-reasoning engine detects superficial responses."""
        
        # Mock Master Verifier to detect superficial response
        mock_verifier = Mock()
        mock_verifier_class.return_value = mock_verifier
        
        # Mock UIF for verification
        mock_uif = Mock()
        mock_uif.intermediate_data = {
            'is_substantive': False,
            'verification_confidence': 0.8,
            'verification_explanation': 'Contains master key patterns: [\'let\'s solve this\']',
            'verification_method': 'pattern_matching'
        }
        mock_uif.warnings = []
        mock_verifier.execute.return_value = mock_uif
        mock_uif_class.return_value = mock_uif
        
        # Initialize meta-reasoning engine
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        # Test superficial response
        superficial_response = "Let's solve this step by step. First, I need to think about the solution."
        query = "What is the solution to this problem?"
        
        # Mock other components to focus on superficiality check
        with patch.object(engine, '_generate_alternative_perspectives', return_value=[]), \
             patch.object(engine, '_generate_adversarial_critiques', return_value=[]), \
             patch.object(engine, '_detect_dimension_conflicts', return_value=[]), \
             patch.object(engine, '_justify_confidence', return_value=Mock()), \
             patch.object(engine, '_analyze_trade_offs', return_value={}):
            
            result = engine.reflective_reasoning_cycle(query, superficial_response)
            
            # Verify superficiality was detected
            assert not result.response_analysis['is_substantive']
            assert result.response_analysis['verification_method'] == 'pattern_matching'
            assert 'master key patterns' in result.response_analysis['verification_explanation']
            
            # Verify superficiality warning in final response
            assert '🚨 **Superficiality Alert:**' in result.final_response
            assert 'master key patterns' in result.final_response
            assert 'Low' in result.final_response  # Confidence should be lowered
    
    @patch('reasoning.reflective_meta_reasoning.MASTER_VERIFIER_AVAILABLE', True)
    @patch('reasoning.reflective_meta_reasoning.MasterVerifierSkill')
    @patch('reasoning.reflective_meta_reasoning.SAM_UIF')
    def test_meta_reasoning_with_substantive_response(self, mock_uif_class, mock_verifier_class):
        """Test meta-reasoning engine accepts substantive responses."""
        
        # Mock Master Verifier to accept substantive response
        mock_verifier = Mock()
        mock_verifier_class.return_value = mock_verifier
        
        # Mock UIF for verification
        mock_uif = Mock()
        mock_uif.intermediate_data = {
            'is_substantive': True,
            'verification_confidence': 0.9,
            'verification_explanation': 'No master key patterns detected',
            'verification_method': 'pattern_matching'
        }
        mock_uif.warnings = []
        mock_verifier.execute.return_value = mock_uif
        mock_uif_class.return_value = mock_uif
        
        # Initialize meta-reasoning engine
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        # Test substantive response
        substantive_response = "The quantum mechanical model describes electron behavior through wave functions and probability distributions in atomic orbitals."
        query = "Explain quantum mechanics"
        
        # Mock other components
        with patch.object(engine, '_generate_alternative_perspectives', return_value=[]), \
             patch.object(engine, '_generate_adversarial_critiques', return_value=[]), \
             patch.object(engine, '_detect_dimension_conflicts', return_value=[]), \
             patch.object(engine, '_justify_confidence', return_value=Mock()), \
             patch.object(engine, '_analyze_trade_offs', return_value={}):
            
            result = engine.reflective_reasoning_cycle(query, substantive_response)
            
            # Verify response was accepted as substantive
            assert result.response_analysis['is_substantive']
            assert result.response_analysis['verification_method'] == 'pattern_matching'
            assert 'No master key patterns detected' in result.response_analysis['verification_explanation']
            
            # Verify no superficiality warning in final response
            assert '🚨 **Superficiality Alert:**' not in result.final_response
            assert 'Moderate' in result.final_response  # Confidence should remain moderate
    
    @patch('reasoning.reflective_meta_reasoning.MASTER_VERIFIER_AVAILABLE', False)
    def test_meta_reasoning_without_master_verifier(self):
        """Test meta-reasoning engine works when Master Verifier is not available."""
        
        # Initialize meta-reasoning engine without Master Verifier
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        # Verify Master Verifier is not initialized
        assert engine.master_verifier is None
        
        # Test response analysis without Master Verifier
        response = "Let's solve this step by step."
        context = {"original_query": "Test query"}
        
        analysis = engine._analyze_initial_response(response, context)
        
        # Verify default values are used when Master Verifier is not available
        assert analysis['is_substantive'] is True  # Default to substantive
        assert analysis['verification_confidence'] == 1.0  # Default high confidence
        assert analysis['verification_method'] == 'none'
        assert analysis['superficiality_check'] == {}
    
    @patch('reasoning.reflective_meta_reasoning.MASTER_VERIFIER_AVAILABLE', True)
    @patch('reasoning.reflective_meta_reasoning.MasterVerifierSkill')
    @patch('reasoning.reflective_meta_reasoning.SAM_UIF')
    def test_superficiality_check_error_handling(self, mock_uif_class, mock_verifier_class):
        """Test error handling in superficiality check."""
        
        # Mock Master Verifier to raise an exception
        mock_verifier = Mock()
        mock_verifier_class.return_value = mock_verifier
        mock_verifier.execute.side_effect = Exception("Model loading failed")
        
        # Initialize meta-reasoning engine
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        # Test response analysis with error
        response = "Test response"
        context = {"original_query": "Test query"}
        
        analysis = engine._analyze_initial_response(response, context)
        
        # Verify error handling
        assert analysis['is_substantive'] is True  # Default to substantive on error
        assert analysis['verification_confidence'] == 0.5  # Low confidence due to error
        assert 'error_fallback' in analysis['verification_method']
        assert 'error' in analysis['superficiality_check']
    
    def test_reasoning_chain_includes_superficiality_analysis(self):
        """Test that reasoning chain includes superficiality analysis details."""
        
        # Create mock response analysis with superficiality check
        response_analysis = {
            'assumptions': ['test assumption'],
            'uncertainty_indicators': ['might be'],
            'confidence_indicators': ['definitely'],
            'superficiality_check': {
                'master_verifier_executed': True,
                'verification_explanation': 'Contains master key patterns'
            },
            'is_substantive': False,
            'verification_method': 'pattern_matching',
            'verification_confidence': 0.7
        }
        
        # Initialize engine and build reasoning chain
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        reasoning_chain = engine._build_reasoning_chain(
            response_analysis, [], [], [], Mock(), {}
        )
        
        # Verify superficiality analysis is included in reasoning chain
        initial_analysis = reasoning_chain[0]
        assert initial_analysis['type'] == 'initial_analysis'
        assert 'superficiality_verified' in initial_analysis['details']
        assert initial_analysis['details']['superficiality_verified'] is True
        assert initial_analysis['details']['is_substantive'] is False
        assert initial_analysis['details']['verification_method'] == 'pattern_matching'
        assert initial_analysis['details']['verification_confidence'] == 0.7
    
    def test_confidence_level_adjustment_for_superficial_responses(self):
        """Test that confidence level is adjusted for superficial responses."""
        
        # Create mock response analysis for superficial response
        response_analysis = {
            'is_substantive': False,
            'verification_confidence': 0.6,
            'superficiality_check': {
                'verification_explanation': 'Contains master key patterns'
            }
        }
        
        # Initialize engine
        engine = ReflectiveMetaReasoningEngine(CritiqueLevel.MODERATE)
        
        # Test final response synthesis
        final_response = engine._synthesize_final_response(
            "test query", "test response", [], [], [], {}, response_analysis
        )
        
        # Verify confidence level is lowered
        assert 'Low' in final_response
        assert 'superficial response detected' in final_response
        assert 'verification confidence: 0.60' in final_response


if __name__ == "__main__":
    pytest.main([__file__])
