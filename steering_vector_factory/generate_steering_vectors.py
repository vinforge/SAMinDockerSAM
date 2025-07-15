#!/usr/bin/env python3
"""
Main Script for Steering Vector Generation Pipeline
==================================================

This script orchestrates the complete pipeline for generating steering vectors:
1. Creates contrastive datasets using a teacher model
2. Extracts steering vectors using direct PyTorch model access
3. Saves vectors to SAM's assets directory

Usage:
    python generate_steering_vectors.py --api-key YOUR_OPENAI_KEY
    python generate_steering_vectors.py --config config.yaml

Author: SAM Development Team
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List

# Add the steering_vector_factory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataset_builder import ContrastivePairBuilder, create_sample_questions
from extract_vectors import VectorExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steering_vector_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SteeringVectorPipeline:
    """Complete pipeline for generating steering vectors."""
    
    def __init__(self, config: Dict):
        """Initialize the pipeline with configuration."""
        self.config = config
        self.dataset_dir = Path("datasets")
        self.vectors_dir = Path("steering_vectors")
        self.sam_assets_dir = Path("../sam/assets/steering_vectors")
        
        # Create directories
        self.dataset_dir.mkdir(exist_ok=True)
        self.vectors_dir.mkdir(exist_ok=True)
        self.sam_assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.dataset_builder = ContrastivePairBuilder(
            api_key=config.get("openai_api_key"),
            model_name=config.get("teacher_model", "gpt-4")
        )
        
        self.vector_extractor = VectorExtractor(
            model_name=config.get("target_model", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"),
            device=config.get("device", "auto"),
            load_in_8bit=config.get("load_in_8bit", True)
        )
    
    def run_complete_pipeline(self, styles: List[str] = None) -> Dict[str, bool]:
        """
        Run the complete steering vector generation pipeline.
        
        Args:
            styles: List of reasoning styles to generate. If None, generates all available styles.
            
        Returns:
            Dictionary mapping style names to success status
        """
        if styles is None:
            styles = list(self.dataset_builder.reasoning_styles.keys())
        
        logger.info(f"Starting steering vector pipeline for styles: {styles}")
        
        # Get questions for dataset generation
        questions = self._get_questions()
        
        results = {}
        
        for style in styles:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing style: {style}")
            logger.info(f"{'='*50}")
            
            try:
                # Step 1: Generate contrastive dataset
                dataset_file = self.dataset_dir / f"{style}_pairs.jsonl"
                if not dataset_file.exists() or self.config.get("regenerate_datasets", False):
                    logger.info(f"Generating contrastive dataset for {style}")
                    stats = self.dataset_builder.generate_pairs(
                        questions=questions,
                        style_name=style,
                        output_file=str(dataset_file),
                        delay_seconds=self.config.get("api_delay", 1.0)
                    )
                    logger.info(f"Dataset generation stats: {stats}")
                else:
                    logger.info(f"Using existing dataset: {dataset_file}")
                
                # Step 2: Extract steering vectors
                vector_file = self.vectors_dir / f"{style}.pt"
                logger.info(f"Extracting steering vectors for {style}")
                steering_vector = self.vector_extractor.extract_steering_vectors(
                    dataset_file=str(dataset_file),
                    output_file=str(vector_file)
                )
                
                # Step 3: Copy to SAM assets directory
                sam_vector_file = self.sam_assets_dir / f"{style}.pt"
                self._copy_vector_to_sam(vector_file, sam_vector_file)
                
                # Step 4: Generate prompt templates for Phase 2
                self._generate_prompt_templates(style, steering_vector)
                
                results[style] = True
                logger.info(f"✓ Successfully generated steering vector for {style}")
                
            except Exception as e:
                logger.error(f"✗ Failed to generate steering vector for {style}: {e}")
                results[style] = False
                continue
        
        # Generate summary
        self._generate_summary(results)
        
        return results
    
    def _get_questions(self) -> List[str]:
        """Get questions for dataset generation."""
        if "custom_questions_file" in self.config:
            questions_file = Path(self.config["custom_questions_file"])
            if questions_file.exists():
                with open(questions_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
        
        # Use default sample questions
        questions = create_sample_questions()
        
        # Extend with additional questions if specified
        if "additional_questions" in self.config:
            questions.extend(self.config["additional_questions"])
        
        return questions
    
    def _copy_vector_to_sam(self, source_file: Path, target_file: Path):
        """Copy steering vector to SAM's assets directory."""
        import shutil
        shutil.copy2(source_file, target_file)
        logger.info(f"Copied steering vector to SAM assets: {target_file}")
    
    def _generate_prompt_templates(self, style: str, steering_vector):
        """Generate prompt templates for Phase 2 implementation."""
        # Create prompt template based on the reasoning style
        style_config = self.dataset_builder.reasoning_styles.get(style)
        if not style_config:
            return
        
        template_data = {
            "style_name": style,
            "description": style_config.description,
            "system_instruction": self._extract_system_instruction(style_config),
            "reasoning_pattern": self._extract_reasoning_pattern(style_config),
            "strength_modulation": {
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5
            }
        }
        
        # Save template for Phase 2
        template_file = self.sam_assets_dir / f"{style}_template.json"
        with open(template_file, 'w') as f:
            import json
            json.dump(template_data, f, indent=2)
        
        logger.info(f"Generated prompt template: {template_file}")
    
    def _extract_system_instruction(self, style_config) -> str:
        """Extract system instruction from style configuration."""
        positive_template = style_config.positive_prompt_template
        
        # Extract the instructional part (before "Question:")
        if "Question:" in positive_template:
            instruction = positive_template.split("Question:")[0].strip()
            return instruction
        
        return positive_template
    
    def _extract_reasoning_pattern(self, style_config) -> str:
        """Extract reasoning pattern description."""
        return style_config.description
    
    def _generate_summary(self, results: Dict[str, bool]):
        """Generate a summary of the pipeline execution."""
        successful = [style for style, success in results.items() if success]
        failed = [style for style, success in results.items() if not success]
        
        logger.info(f"\n{'='*60}")
        logger.info("STEERING VECTOR GENERATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total styles processed: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        
        if successful:
            logger.info(f"\n✓ Successfully generated vectors for:")
            for style in successful:
                logger.info(f"  - {style}")
        
        if failed:
            logger.info(f"\n✗ Failed to generate vectors for:")
            for style in failed:
                logger.info(f"  - {style}")
        
        logger.info(f"\nSteering vectors saved to: {self.sam_assets_dir}")
        logger.info("Ready for Phase 2 implementation!")

def load_config(config_file: str) -> Dict:
    """Load configuration from YAML file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    return {}

def create_default_config() -> Dict:
    """Create default configuration."""
    return {
        "teacher_model": "gpt-4",
        "target_model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "device": "auto",
        "load_in_8bit": True,
        "api_delay": 1.0,
        "regenerate_datasets": False,
        "additional_questions": []
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate steering vectors for SAM")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--config", default="config.yaml", help="Configuration file")
    parser.add_argument("--styles", nargs="+", help="Specific styles to generate")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        config = create_default_config()
        logger.info("Using default configuration")
    
    # Override with command line arguments
    if args.api_key:
        config["openai_api_key"] = args.api_key
    
    # Check for API key
    if "openai_api_key" not in config and "OPENAI_API_KEY" not in os.environ:
        logger.error("OpenAI API key required. Set via --api-key or OPENAI_API_KEY environment variable")
        sys.exit(1)
    
    # Initialize and run pipeline
    pipeline = SteeringVectorPipeline(config)
    results = pipeline.run_complete_pipeline(styles=args.styles)
    
    # Exit with appropriate code
    if all(results.values()):
        logger.info("All steering vectors generated successfully!")
        sys.exit(0)
    else:
        logger.error("Some steering vectors failed to generate")
        sys.exit(1)

if __name__ == "__main__":
    main()
