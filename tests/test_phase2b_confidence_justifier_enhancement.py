#!/usr/bin/env python3
"""
Test Suite for Phase 2B: AdvancedConfidenceJustifier Enhancement
===============================================================

Tests the enhancement of AdvancedConfidenceJustifier with Master Verifier
integration for superficiality-aware confidence scoring.

Author: SAM Development Team
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock

# Import the components to test
from reasoning.confidence_justifier import (
    AdvancedConfidenceJustifier, 
    EvidenceType, 
    ConfidenceLevel,
    ConfidenceEvidence
)


class TestPhase2BConfidenceJustifierEnhancement:
    """Test cases for enhanced confidence justifier with superficiality detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.justifier = AdvancedConfidenceJustifier(profile="general")
    
    def test_new_evidence_type_added(self):
        """Test that RESPONSE_SUBSTANTIVENESS evidence type is available."""
        assert hasattr(EvidenceType, 'RESPONSE_SUBSTANTIVENESS')
        assert EvidenceType.RESPONSE_SUBSTANTIVENESS.value == "response_substantiveness"
    
    def test_evidence_weights_include_substantiveness(self):
        """Test that evidence weights include substantiveness for all profiles."""
        for profile in ["general", "researcher", "business", "legal"]:
            justifier = AdvancedConfidenceJustifier(profile=profile)
            weight = justifier._get_evidence_weight(EvidenceType.RESPONSE_SUBSTANTIVENESS)
            assert weight > 0, f"Substantiveness weight should be positive for {profile} profile"
            assert weight <= 1.0, f"Substantiveness weight should be <= 1.0 for {profile} profile"
    
    def test_assess_response_substantiveness_no_verification(self):
        """Test substantiveness assessment when no verification is performed."""
        response_analysis = {
            "verification_method": "none"
        }
        
        evidence = self.justifier._assess_response_substantiveness(response_analysis)
        
        assert evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS
        assert evidence.score == 0.7  # Neutral score
        assert "No superficiality verification performed" in evidence.description
        assert "Master Verifier not available" in evidence.supporting_details[0]
    
    def test_assess_response_substantiveness_superficial_detected(self):
        """Test substantiveness assessment when superficial response is detected."""
        response_analysis = {
            "is_substantive": False,
            "verification_confidence": 0.9,
            "verification_method": "pattern_matching",
            "superficiality_check": {
                "verification_explanation": "Contains master key patterns: ['let's solve this']"
            }
        }
        
        evidence = self.justifier._assess_response_substantiveness(response_analysis)
        
        assert evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS
        assert evidence.score < 0.5  # Should be penalized
        assert "Superficial response detected" in evidence.description
        assert "master key patterns" in evidence.description
        assert "pattern_matching" in evidence.supporting_details[0]
        assert "0.90" in evidence.supporting_details[1]  # Verification confidence
    
    def test_assess_response_substantiveness_substantive_verified(self):
        """Test substantiveness assessment when substantive response is verified."""
        response_analysis = {
            "is_substantive": True,
            "verification_confidence": 0.85,
            "verification_method": "model_based",
            "superficiality_check": {
                "verification_explanation": "No master key patterns detected, detailed analysis provided"
            }
        }
        
        evidence = self.justifier._assess_response_substantiveness(response_analysis)
        
        assert evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS
        assert evidence.score > 0.8  # Should be rewarded
        assert "Substantive response verified" in evidence.description
        assert "No master key patterns detected" in evidence.description
        assert "model_based" in evidence.supporting_details[0]
    
    def test_confidence_justification_with_superficial_response(self):
        """Test complete confidence justification for superficial response."""
        response_analysis = {
            "is_substantive": False,
            "verification_confidence": 0.8,
            "verification_method": "pattern_matching",
            "superficiality_check": {
                "verification_explanation": "Contains master key patterns"
            },
            "evidence_sources": [],
            "dimension_scores": {"credibility": 0.6, "utility": 0.7},
            "assumptions": ["test assumption"],
            "uncertainty_indicators": [],
            "confidence_indicators": []
        }
        
        justification = self.justifier.justify_confidence(response_analysis)
        
        # Should have low confidence due to superficiality
        assert justification.confidence_score < 0.6
        assert justification.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW, ConfidenceLevel.MODERATE]
        
        # Should include substantiveness evidence
        substantiveness_evidence = None
        for evidence in justification.evidence_items:
            if evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS:
                substantiveness_evidence = evidence
                break
        
        assert substantiveness_evidence is not None
        assert substantiveness_evidence.score < 0.5
    
    def test_confidence_justification_with_substantive_response(self):
        """Test complete confidence justification for substantive response."""
        response_analysis = {
            "is_substantive": True,
            "verification_confidence": 0.9,
            "verification_method": "model_based",
            "superficiality_check": {
                "verification_explanation": "Detailed substantive analysis provided"
            },
            "evidence_sources": [{"metadata": {"source_type": "academic"}}],
            "dimension_scores": {"credibility": 0.8, "utility": 0.8},
            "assumptions": [],
            "uncertainty_indicators": [],
            "confidence_indicators": ["clearly", "definitely"]
        }
        
        justification = self.justifier.justify_confidence(response_analysis)
        
        # Should have higher confidence due to substantiveness
        assert justification.confidence_score > 0.6
        
        # Should include substantiveness evidence with high score
        substantiveness_evidence = None
        for evidence in justification.evidence_items:
            if evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS:
                substantiveness_evidence = evidence
                break
        
        assert substantiveness_evidence is not None
        assert substantiveness_evidence.score > 0.8
    
    def test_limiting_factors_include_superficiality_warnings(self):
        """Test that limiting factors include special superficiality warnings."""
        # Create evidence with critical superficiality issue
        evidence_items = [
            ConfidenceEvidence(
                evidence_type=EvidenceType.RESPONSE_SUBSTANTIVENESS,
                score=0.2,  # Critical level
                weight=0.15,
                description="Contains multiple master key patterns",
                supporting_details=[]
            ),
            ConfidenceEvidence(
                evidence_type=EvidenceType.SOURCE_CREDIBILITY,
                score=0.3,  # Also low
                weight=0.20,
                description="No credible sources",
                supporting_details=[]
            )
        ]
        
        limiting_factors = self.justifier._identify_limiting_factors(evidence_items)
        
        # Should include special superficiality warning
        superficiality_warning = None
        for factor in limiting_factors:
            if "🚨 Critical superficiality issue" in factor:
                superficiality_warning = factor
                break
        
        assert superficiality_warning is not None
        assert "master key patterns" in superficiality_warning
    
    def test_reliability_assessment_includes_superficiality_notes(self):
        """Test that reliability assessment includes superficiality-specific notes."""
        # Test critical superficiality
        evidence_items = [
            ConfidenceEvidence(
                evidence_type=EvidenceType.RESPONSE_SUBSTANTIVENESS,
                score=0.2,
                weight=0.15,
                description="Critical superficiality",
                supporting_details=[]
            )
        ]
        
        assessment = self.justifier._generate_reliability_assessment(0.3, evidence_items)
        assert "⚠️ CRITICAL: Response shows significant superficiality issues" in assessment
        
        # Test minor superficiality
        evidence_items[0].score = 0.4
        assessment = self.justifier._generate_reliability_assessment(0.5, evidence_items)
        assert "⚠️ Note: Response may contain superficial elements" in assessment
        
        # Test verified substantive
        evidence_items[0].score = 0.9
        assessment = self.justifier._generate_reliability_assessment(0.8, evidence_items)
        assert "✅ Response verified as substantive and detailed" in assessment
    
    def test_context_evidence_includes_substantiveness(self):
        """Test that context evidence assessment includes substantiveness information."""
        context = {
            "is_substantive": False,
            "verification_confidence": 0.8,
            "critiques": []
        }
        
        context_evidence = self.justifier._assess_context_evidence(context)
        
        # Should include substantiveness evidence from context
        substantiveness_evidence = None
        for evidence in context_evidence:
            if evidence.evidence_type == EvidenceType.RESPONSE_SUBSTANTIVENESS:
                substantiveness_evidence = evidence
                break
        
        assert substantiveness_evidence is not None
        assert substantiveness_evidence.score < 0.5  # Should be penalized
        assert "Context indicates superficial response" in substantiveness_evidence.description
    
    def test_different_profiles_have_different_substantiveness_weights(self):
        """Test that different profiles assign different weights to substantiveness."""
        profiles = ["general", "researcher", "business", "legal"]
        weights = {}
        
        for profile in profiles:
            justifier = AdvancedConfidenceJustifier(profile=profile)
            weight = justifier._get_evidence_weight(EvidenceType.RESPONSE_SUBSTANTIVENESS)
            weights[profile] = weight
        
        # Business should have high weight for substantiveness
        assert weights["business"] >= weights["researcher"]
        assert weights["general"] > 0.1  # Should have meaningful weight
        
        # All profiles should have positive weights
        for profile, weight in weights.items():
            assert weight > 0, f"{profile} should have positive substantiveness weight"
    
    def test_confidence_breakdown_includes_substantiveness_component(self):
        """Test that confidence breakdown includes substantiveness as a component."""
        response_analysis = {
            "is_substantive": True,
            "verification_confidence": 0.8,
            "verification_method": "pattern_matching",
            "evidence_sources": [],
            "dimension_scores": {},
            "assumptions": [],
            "uncertainty_indicators": [],
            "confidence_indicators": []
        }
        
        justification = self.justifier.justify_confidence(response_analysis)
        
        # Check that substantiveness is in the breakdown
        assert "response_substantiveness" in justification.confidence_breakdown.component_scores
        assert "response_substantiveness" in justification.confidence_breakdown.component_weights
        assert "response_substantiveness" in justification.confidence_breakdown.weighted_scores
        
        # Verify the component has reasonable values
        substantiveness_score = justification.confidence_breakdown.component_scores["response_substantiveness"]
        assert 0.0 <= substantiveness_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])
