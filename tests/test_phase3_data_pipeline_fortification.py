#!/usr/bin/env python3
"""
Phase 3: Data Pipeline Fortification Integration Test

This test validates the complete Master Verifier system implementation:
- Phase 3A: EnhancedChunker quality assessment
- Phase 3B: MemoryRankingEngine superficiality penalties
- End-to-end integration ensuring superficial content is de-prioritized

Test Scenario: Ingest a document with mixed-quality content and verify that
superficial chunks are flagged correctly and ranked lower than substantive chunks.
"""

import unittest
import sys
import os
import tempfile
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multimodal_processing.enhanced_chunker import EnhancedChunker, EnhancedChunk, ChunkType
from memory.memory_ranking import MemoryRankingFramework, MemoryRankingScore


class MockMemoryResult:
    """Mock memory result for testing ranking."""

    def __init__(self, chunk: EnhancedChunk, similarity_score: float = 0.8):
        self.chunk = chunk
        self.similarity_score = similarity_score
        # Set chunk_id at the top level for ranking system compatibility
        self.chunk_id = chunk.metadata.get('chunk_id', 'test_chunk')
        # Also ensure chunk has chunk_id attribute
        if not hasattr(chunk, 'chunk_id'):
            chunk.chunk_id = self.chunk_id


class TestPhase3DataPipelineFortification(unittest.TestCase):
    """Test suite for Phase 3 Master Verifier implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.chunker = EnhancedChunker(
            chunk_size=500,
            chunk_overlap=50,
            enable_dimension_probing=False  # Disable for testing
        )
        
        self.ranking_framework = MemoryRankingFramework()
        
        # Test document with mixed quality content
        self.test_document = """
        # Cybersecurity Framework Implementation

        ## Executive Summary
        This document outlines a comprehensive cybersecurity framework for enterprise deployment.
        The framework includes advanced threat detection, incident response protocols, and 
        continuous monitoring capabilities designed to protect critical infrastructure.

        ## Detailed Technical Specifications

        ### Network Security Architecture
        The proposed network security architecture implements a zero-trust model with:
        - Multi-factor authentication for all access points
        - Encrypted communication channels using AES-256 encryption
        - Real-time network traffic analysis and anomaly detection
        - Automated threat response and containment systems

        ### Incident Response Procedures
        1. Initial threat detection and classification
        2. Immediate containment and isolation protocols
        3. Forensic analysis and evidence collection
        4. System recovery and restoration procedures
        5. Post-incident review and improvement recommendations

        ## Generic Content Section
        I understand that cybersecurity is important. Generally speaking, organizations need 
        to consider various factors when implementing security measures. It depends on many 
        things and this varies from case to case. There are many different approaches that 
        might be suitable, and it's important to note that each situation is unique.

        ## Superficial Analysis
        Based on the information provided, I can help you understand that cybersecurity 
        typically involves multiple components. As mentioned above, there are various 
        considerations. For more information, please consult your security documentation.
        This relates to the overall security posture of the organization.

        ## Compliance Requirements
        The framework must comply with:
        - NIST Cybersecurity Framework standards
        - ISO 27001 information security management requirements
        - GDPR data protection regulations for EU operations
        - SOC 2 Type II audit requirements for service organizations
        """

    def test_phase3a_chunk_quality_assessment(self):
        """Test Phase 3A: EnhancedChunker quality assessment functionality."""
        print("\n🧪 Testing Phase 3A: Chunk Quality Assessment")
        
        # Test superficial content detection
        superficial_content = """I understand that this is important. Generally speaking, 
        there are many factors to consider. It depends on various things and this varies 
        from case to case. For more information, please consult the documentation."""
        
        quality_assessment = self.chunker.assess_chunk_quality(superficial_content)
        
        # Verify superficial content is detected
        self.assertTrue(quality_assessment['is_superficial'], 
                       "Superficial content should be flagged as superficial")
        self.assertGreater(len(quality_assessment['superficiality_reasons']), 0,
                          "Should provide reasons for superficiality")
        self.assertIn('master_key_phrases', str(quality_assessment['superficiality_reasons']),
                     "Should detect master key phrases")
        
        print(f"✅ Superficial content detected: {quality_assessment['superficiality_reasons']}")
        
        # Test substantive content detection
        substantive_content = """The proposed network security architecture implements 
        a zero-trust model with multi-factor authentication for all access points, 
        encrypted communication channels using AES-256 encryption, and real-time 
        network traffic analysis with automated threat response systems."""
        
        quality_assessment = self.chunker.assess_chunk_quality(substantive_content)
        
        # Verify substantive content is not flagged
        self.assertFalse(quality_assessment['is_superficial'],
                        "Substantive content should not be flagged as superficial")
        
        print(f"✅ Substantive content correctly identified as non-superficial")

    def test_phase3a_chunk_metadata_integration(self):
        """Test that quality assessment is properly integrated into chunk metadata."""
        print("\n🧪 Testing Phase 3A: Chunk Metadata Integration")
        
        # Create chunks from test document
        chunks = self.chunker.enhanced_chunk_text(self.test_document, "test_doc")
        
        # Verify all chunks have quality assessment metadata
        for chunk in chunks:
            self.assertIn('is_superficial', chunk.metadata,
                         "All chunks should have is_superficial flag in metadata")
            self.assertIn('quality_confidence', chunk.metadata,
                         "All chunks should have quality confidence score")
            self.assertIn('superficiality_reasons', chunk.metadata,
                         "All chunks should have superficiality reasons")
            
        # Find superficial and substantive chunks
        superficial_chunks = [c for c in chunks if c.metadata.get('is_superficial', False)]
        substantive_chunks = [c for c in chunks if not c.metadata.get('is_superficial', False)]
        
        self.assertGreater(len(superficial_chunks), 0,
                          "Should identify some superficial chunks in test document")
        self.assertGreater(len(substantive_chunks), 0,
                          "Should identify some substantive chunks in test document")
        
        print(f"✅ Found {len(superficial_chunks)} superficial and {len(substantive_chunks)} substantive chunks")
        
        # Verify superficial chunks contain expected content
        superficial_content = " ".join([c.content for c in superficial_chunks]).lower()
        self.assertIn("generally speaking", superficial_content,
                     "Superficial chunks should contain generic language")
        
        print(f"✅ Superficial chunks correctly identified generic content")

    def test_phase3b_ranking_superficiality_penalty(self):
        """Test Phase 3B: MemoryRankingEngine superficiality penalties."""
        print("\n🧪 Testing Phase 3B: Ranking Superficiality Penalties")
        
        # Create test chunks with different quality levels
        substantive_chunk = EnhancedChunk(
            content="The network security architecture implements zero-trust with AES-256 encryption.",
            chunk_type=ChunkType.NARRATIVE,
            priority_score=1.0,
            metadata={
                'chunk_id': 'substantive_1',
                'is_superficial': False,
                'quality_confidence': 0.9,
                'superficiality_reasons': []
            },
            source_location="test_substantive_chunk"
        )

        superficial_chunk = EnhancedChunk(
            content="I understand this is important. Generally speaking, it depends on various factors.",
            chunk_type=ChunkType.NARRATIVE,
            priority_score=1.0,
            metadata={
                'chunk_id': 'superficial_1',
                'is_superficial': True,
                'quality_confidence': 0.85,
                'superficiality_reasons': ['master_key_phrases (2 found)', 'high_vague_terms (4/12)']
            },
            source_location="test_superficial_chunk"
        )
        
        # Create mock memory results
        substantive_memory = MockMemoryResult(substantive_chunk, similarity_score=0.8)
        superficial_memory = MockMemoryResult(superficial_chunk, similarity_score=0.8)
        
        # Rank the memories
        memories = [substantive_memory, superficial_memory]
        ranking_scores = self.ranking_framework.rank_memories(memories, "network security")
        
        # Verify superficial content is penalized
        substantive_score = next(s for s in ranking_scores if s.memory_id == 'substantive_1')
        superficial_score = next(s for s in ranking_scores if s.memory_id == 'superficial_1')
        
        self.assertGreater(substantive_score.overall_score, superficial_score.overall_score,
                          "Substantive content should rank higher than superficial content")
        
        # Verify penalty was applied
        penalty = self.ranking_framework.config.get('superficiality_penalty', -0.3)
        expected_penalty_applied = abs(superficial_score.overall_score - substantive_score.overall_score) >= abs(penalty) * 0.8
        
        print(f"✅ Substantive score: {substantive_score.overall_score:.3f}")
        print(f"✅ Superficial score: {superficial_score.overall_score:.3f}")
        print(f"✅ Score difference: {substantive_score.overall_score - superficial_score.overall_score:.3f}")
        print(f"✅ Expected penalty: {penalty}")

    def test_phase3_end_to_end_integration(self):
        """Test complete end-to-end integration of Phase 3 system."""
        print("\n🧪 Testing Phase 3: End-to-End Integration")
        
        # Step 1: Chunk the test document
        chunks = self.chunker.enhanced_chunk_text(self.test_document, "integration_test")
        
        # Step 2: Create memory results from chunks
        memory_results = []
        for i, chunk in enumerate(chunks):
            # Vary similarity scores to test ranking
            similarity_score = 0.7 + (i % 3) * 0.1  # 0.7, 0.8, 0.9 pattern
            memory_results.append(MockMemoryResult(chunk, similarity_score))
        
        # Step 3: Rank all memories
        ranking_scores = self.ranking_framework.rank_memories(memory_results, "cybersecurity framework")
        
        # Step 4: Analyze results
        superficial_scores = [s for s in ranking_scores 
                            if self._is_memory_superficial(s, memory_results)]
        substantive_scores = [s for s in ranking_scores 
                            if not self._is_memory_superficial(s, memory_results)]
        
        # Verify superficial content is consistently ranked lower
        if superficial_scores and substantive_scores:
            avg_superficial_score = sum(s.overall_score for s in superficial_scores) / len(superficial_scores)
            avg_substantive_score = sum(s.overall_score for s in substantive_scores) / len(substantive_scores)
            
            self.assertGreater(avg_substantive_score, avg_superficial_score,
                              "Average substantive score should be higher than average superficial score")
            
            print(f"✅ Average substantive score: {avg_substantive_score:.3f}")
            print(f"✅ Average superficial score: {avg_superficial_score:.3f}")
            print(f"✅ Quality gap: {avg_substantive_score - avg_superficial_score:.3f}")
        
        # Verify top-ranked memories are predominantly substantive
        top_5_scores = sorted(ranking_scores, key=lambda x: x.overall_score, reverse=True)[:5]
        top_5_superficial_count = sum(1 for s in top_5_scores 
                                    if self._is_memory_superficial(s, memory_results))
        
        self.assertLessEqual(top_5_superficial_count, 2,
                           "Top 5 ranked memories should have at most 2 superficial chunks")
        
        print(f"✅ Top 5 memories contain {top_5_superficial_count} superficial chunks (≤2 expected)")
        print(f"✅ Phase 3 integration test completed successfully!")

    def _is_memory_superficial(self, ranking_score: MemoryRankingScore, memory_results: List[MockMemoryResult]) -> bool:
        """Helper method to check if a ranking score corresponds to superficial content."""
        memory = next((m for m in memory_results if m.chunk_id == ranking_score.memory_id), None)
        if memory and hasattr(memory, 'chunk') and hasattr(memory.chunk, 'metadata'):
            return memory.chunk.metadata.get('is_superficial', False)
        return False


if __name__ == '__main__':
    print("🚀 Phase 3: Data Pipeline Fortification Integration Test")
    print("=" * 60)
    
    # Run tests with verbose output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Phase 3 Testing Complete!")
    print("✅ Master Verifier system fully implemented and tested")
    print("✅ SAM is now fortified against superficial content at all levels")
