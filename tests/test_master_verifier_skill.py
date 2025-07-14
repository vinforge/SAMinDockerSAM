#!/usr/bin/env python3
"""
Test Suite for Master Verifier Skill
====================================

Tests for the Master-RM based verification system that detects
superficial "master key" responses in SAM's reasoning pipelines.

Author: SAM Development Team
Version: 1.0.0
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the skill and dependencies
from sam.orchestration.skills.master_verifier_skill import MasterVerifierSkill
from sam.orchestration.skills.base import SkillExecutionError, SkillDependencyError
from sam.orchestration.uif import SAM_UIF, UIFStatus


class TestMasterVerifierSkill:
    """Test cases for Master Verifier Skill."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary config file for testing
        self.temp_config = {
            'model': {
                'name': 'sarosavo/Master-RM',
                'cache_dir': './test_model_cache',
                'device': 'cpu',
                'max_length': 512
            },
            'verification': {
                'confidence_threshold': 0.8,
                'master_key_patterns': [
                    'thought process:', 'let\'s solve this', 'solution:'
                ],
                'min_response_length': 10,
                'enable_caching': True
            },
            'integration': {
                'enable_fallback': True,
                'fallback_method': 'pattern_matching'
            }
        }
        
        # Create temporary config file
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        )
        yaml.dump(self.temp_config, self.temp_config_file)
        self.temp_config_file.close()
        
        # Initialize skill with test config
        self.skill = MasterVerifierSkill(config_path=self.temp_config_file.name)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.temp_config_file.name).unlink(missing_ok=True)
    
    def test_skill_initialization(self):
        """Test that the skill initializes correctly."""
        assert self.skill.skill_name == "master_verifier_skill"
        assert self.skill.skill_version == "1.0.0"
        assert self.skill.skill_category == "reasoning"
        assert "verification_question" in self.skill.required_inputs
        assert "verification_response" in self.skill.required_inputs
        assert "is_substantive" in self.skill.output_keys
    
    def test_config_loading(self):
        """Test configuration loading."""
        assert self.skill.config['model']['name'] == 'sarosavo/Master-RM'
        assert self.skill.config['verification']['confidence_threshold'] == 0.8
        assert 'thought process:' in self.skill.config['verification']['master_key_patterns']
    
    def test_default_config_fallback(self):
        """Test fallback to default config when file doesn't exist."""
        skill = MasterVerifierSkill(config_path="nonexistent_config.yaml")
        assert skill.config['model']['name'] == 'sarosavo/Master-RM'
        assert skill.config['verification']['confidence_threshold'] == 0.8
    
    def test_pattern_matching_verification_superficial(self):
        """Test pattern matching detection of superficial responses."""
        superficial_response = "Let's solve this step by step. First, I need to think about the solution."
        
        result = self.skill._pattern_matching_verification(superficial_response)
        
        assert result['is_substantive'] is False
        assert result['verification_method'] == 'pattern_matching'
        assert 'master key patterns' in result['verification_explanation']
        assert result['verification_confidence'] > 0.6
    
    def test_pattern_matching_verification_substantive(self):
        """Test pattern matching detection of substantive responses."""
        substantive_response = "The quantum mechanical model describes electron behavior through wave functions and probability distributions."
        
        result = self.skill._pattern_matching_verification(substantive_response)
        
        assert result['is_substantive'] is True
        assert result['verification_method'] == 'pattern_matching'
        assert 'No master key patterns detected' in result['verification_explanation']
        assert result['verification_confidence'] == 0.7
    
    def test_pattern_matching_verification_too_short(self):
        """Test pattern matching rejection of very short responses."""
        short_response = "Yes."
        
        result = self.skill._pattern_matching_verification(short_response)
        
        assert result['is_substantive'] is False
        assert result['verification_method'] == 'pattern_matching'
        assert 'too short' in result['verification_explanation']
        assert result['verification_confidence'] == 0.9
    
    def test_length_heuristic_verification(self):
        """Test length-based heuristic verification."""
        # Very short response
        short_result = self.skill._length_heuristic_verification("No.")
        assert short_result['is_substantive'] is False
        assert 'Very short' in short_result['verification_explanation']
        
        # Medium length response
        medium_response = "This is a medium length response that provides some detail but not extensive analysis."
        medium_result = self.skill._length_heuristic_verification(medium_response)
        assert medium_result['is_substantive'] is True
        assert 'Medium length' in medium_result['verification_explanation']
        
        # Long response
        long_response = "This is a comprehensive response that provides extensive detail and analysis. " * 5
        long_result = self.skill._length_heuristic_verification(long_response)
        assert long_result['is_substantive'] is True
        assert 'Long response' in long_result['verification_explanation']
    
    def test_cache_key_generation(self):
        """Test cache key generation for verification requests."""
        question = "What is 2+2?"
        response = "The answer is 4."
        reference = "4"
        
        key1 = self.skill._generate_cache_key(question, response, reference)
        key2 = self.skill._generate_cache_key(question, response, reference)
        key3 = self.skill._generate_cache_key(question, "Different response", reference)
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
        assert len(key1) == 32  # MD5 hash length
    
    def test_fallback_verification_methods(self):
        """Test different fallback verification methods."""
        response = "Let's solve this problem step by step."
        context = {}
        
        # Test pattern matching fallback
        self.skill.config['integration']['fallback_method'] = 'pattern_matching'
        result1 = self.skill._fallback_verification(response, context)
        assert result1['verification_method'] == 'pattern_matching'
        assert result1['is_substantive'] is False  # Contains master key pattern
        
        # Test length heuristic fallback
        self.skill.config['integration']['fallback_method'] = 'length_heuristic'
        result2 = self.skill._fallback_verification(response, context)
        assert result2['verification_method'] == 'length_heuristic'
        
        # Test always pass fallback
        self.skill.config['integration']['fallback_method'] = 'always_pass'
        result3 = self.skill._fallback_verification(response, context)
        assert result3['verification_method'] == 'always_pass'
        assert result3['is_substantive'] is True
    
    def test_execute_with_valid_inputs(self):
        """Test skill execution with valid inputs."""
        uif = SAM_UIF(
            input_query="Test verification",
            intermediate_data={
                'verification_question': 'What is 2+2?',
                'verification_response': 'The answer is 4 because 2+2=4.',
                'verification_reference': '4'
            }
        )
        
        # Mock the model-based verification to avoid loading actual model
        with patch.object(self.skill, '_verify_response') as mock_verify:
            mock_verify.return_value = {
                'is_substantive': True,
                'verification_confidence': 0.9,
                'verification_explanation': 'Test result',
                'verification_method': 'pattern_matching'
            }
            
            result_uif = self.skill.execute(uif)
            
            assert result_uif.intermediate_data['is_substantive'] is True
            assert result_uif.intermediate_data['verification_confidence'] == 0.9
            assert 'verification_explanation' in result_uif.intermediate_data
            mock_verify.assert_called_once()
    
    def test_execute_with_missing_inputs(self):
        """Test skill execution with missing required inputs."""
        uif = SAM_UIF(
            input_query="Test verification",
            intermediate_data={
                'verification_question': 'What is 2+2?'
                # Missing verification_response
            }
        )
        
        with pytest.raises(SkillDependencyError):
            self.skill.execute(uif)
    
    def test_execute_with_caching(self):
        """Test that caching works correctly."""
        uif = SAM_UIF(
            input_query="Test verification",
            intermediate_data={
                'verification_question': 'What is 2+2?',
                'verification_response': 'The answer is 4.',
                'verification_reference': '4'
            }
        )
        
        # Mock the verification method
        with patch.object(self.skill, '_verify_response') as mock_verify:
            mock_verify.return_value = {
                'is_substantive': True,
                'verification_confidence': 0.9,
                'verification_explanation': 'Test result',
                'verification_method': 'pattern_matching'
            }
            
            # First execution should call verification
            result1 = self.skill.execute(uif)
            assert mock_verify.call_count == 1
            
            # Second execution should use cache
            result2 = self.skill.execute(uif)
            assert mock_verify.call_count == 1  # Should not increase
            
            # Results should be identical
            assert result1.intermediate_data['is_substantive'] == result2.intermediate_data['is_substantive']
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        initial_stats = self.skill.get_statistics()
        assert initial_stats['total_verifications'] == 0
        
        # Simulate some verifications
        self.skill._verification_count = 10
        self.skill._substantive_count = 7
        self.skill._superficial_count = 3
        self.skill._cache_hits = 5
        self.skill._cache_misses = 5
        
        stats = self.skill.get_statistics()
        assert stats['total_verifications'] == 10
        assert stats['substantive_responses'] == 7
        assert stats['superficial_responses'] == 3
        assert stats['cache_hit_rate'] == 0.5
    
    def test_can_handle_query(self):
        """Test query handling capability detection."""
        # Should handle verification-related queries
        assert self.skill.can_handle_query("Please verify this response")
        assert self.skill.can_handle_query("Check if this is substantive")
        assert self.skill.can_handle_query("Validate the quality of this answer")
        
        # Should not handle unrelated queries
        assert not self.skill.can_handle_query("What is the weather today?")
        assert not self.skill.can_handle_query("Calculate 2+2")
    
    @patch('sam.orchestration.skills.master_verifier_skill.AutoTokenizer')
    @patch('sam.orchestration.skills.master_verifier_skill.AutoModelForSequenceClassification')
    def test_model_loading_success(self, mock_model_class, mock_tokenizer_class):
        """Test successful model loading."""
        # Mock the model and tokenizer
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_model_class.from_pretrained.return_value = mock_model
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        
        # Mock torch
        with patch('sam.orchestration.skills.master_verifier_skill.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            
            model, tokenizer = self.skill._load_model()
            
            assert model == mock_model
            assert tokenizer == mock_tokenizer
            mock_model_class.from_pretrained.assert_called_once()
            mock_tokenizer_class.from_pretrained.assert_called_once()
    
    def test_model_loading_failure(self):
        """Test model loading failure handling."""
        # Test ImportError (transformers not available)
        with patch('sam.orchestration.skills.master_verifier_skill.AutoTokenizer', side_effect=ImportError):
            with pytest.raises(SkillExecutionError, match="transformers library"):
                self.skill._load_model()


if __name__ == "__main__":
    pytest.main([__file__])
