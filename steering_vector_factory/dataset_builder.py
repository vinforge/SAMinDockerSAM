"""
Contrastive Dataset Builder for Steering Vector Generation
=========================================================

This module creates contrastive pairs of responses using a teacher model
to generate training data for steering vector extraction.

Author: SAM Development Team
Version: 1.0.0
"""

import json
import logging
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import openai
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)

@dataclass
class ReasoningStyle:
    """Configuration for a specific reasoning style."""
    name: str
    positive_prompt_template: str
    negative_prompt_template: str
    description: str

class ContrastivePairBuilder:
    """Builds contrastive datasets for steering vector generation."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4"):
        """
        Initialize the contrastive pair builder.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model_name: Teacher model to use for generation
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        
        # Predefined reasoning styles
        self.reasoning_styles = {
            "researcher_style": ReasoningStyle(
                name="researcher_style",
                positive_prompt_template="""Please answer the following question with detailed, step-by-step reasoning, in the style of a meticulous researcher. 

Break down your thinking process, cite relevant principles, consider multiple perspectives, and show your analytical methodology clearly.

Question: {question}""",
                negative_prompt_template="""Please answer the following question directly and concisely.

Question: {question}""",
                description="Detailed analytical reasoning with research methodology"
            ),
            
            "step_by_step_reasoning": ReasoningStyle(
                name="step_by_step_reasoning", 
                positive_prompt_template="""Please answer the following question using clear, numbered steps. Break down your reasoning process systematically.

Show each logical step in your thinking process, explaining how you move from one step to the next.

Question: {question}""",
                negative_prompt_template="""Please answer the following question directly without showing your reasoning steps.

Question: {question}""",
                description="Systematic step-by-step logical progression"
            ),
            
            "creative_explorer": ReasoningStyle(
                name="creative_explorer",
                positive_prompt_template="""Please answer the following question by exploring creative possibilities and alternative perspectives. 

Think outside the box, consider unconventional approaches, and explore multiple creative angles before settling on your answer.

Question: {question}""",
                negative_prompt_template="""Please answer the following question using only conventional, straightforward reasoning.

Question: {question}""",
                description="Creative and exploratory thinking patterns"
            )
        }
    
    def generate_pairs(self, questions: List[str], style_name: str, 
                      output_file: str, delay_seconds: float = 1.0) -> Dict[str, int]:
        """
        Generate contrastive pairs for a specific reasoning style.
        
        Args:
            questions: List of questions to generate pairs for
            style_name: Name of the reasoning style to use
            output_file: Path to save the JSONL output
            delay_seconds: Delay between API calls to respect rate limits
            
        Returns:
            Dictionary with generation statistics
        """
        if style_name not in self.reasoning_styles:
            raise ValueError(f"Unknown reasoning style: {style_name}")
        
        style = self.reasoning_styles[style_name]
        pairs = []
        stats = {"total_questions": len(questions), "successful_pairs": 0, "failed_pairs": 0}
        
        logger.info(f"Generating {len(questions)} contrastive pairs for style: {style_name}")
        
        for i, question in enumerate(tqdm(questions, desc=f"Generating {style_name} pairs")):
            try:
                # Generate positive response
                positive_prompt = style.positive_prompt_template.format(question=question)
                positive_response = self._call_teacher_model(positive_prompt)
                
                # Small delay between calls
                time.sleep(delay_seconds)
                
                # Generate negative response  
                negative_prompt = style.negative_prompt_template.format(question=question)
                negative_response = self._call_teacher_model(negative_prompt)
                
                if positive_response and negative_response:
                    pair = {
                        "question": question,
                        "positive_prompt": positive_prompt,
                        "positive_response": positive_response,
                        "negative_prompt": negative_prompt,
                        "negative_response": negative_response,
                        "style": style_name,
                        "pair_id": i
                    }
                    pairs.append(pair)
                    stats["successful_pairs"] += 1
                else:
                    logger.warning(f"Failed to generate pair for question {i}: empty response")
                    stats["failed_pairs"] += 1
                
                # Delay between question pairs
                time.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Error generating pair for question {i}: {e}")
                stats["failed_pairs"] += 1
                continue
        
        # Save to JSONL file
        self._save_pairs(pairs, output_file, style)
        
        logger.info(f"Generated {stats['successful_pairs']} pairs, {stats['failed_pairs']} failures")
        return stats
    
    def _call_teacher_model(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call the teacher model with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800
                )
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"Teacher model call failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        return None
    
    def _save_pairs(self, pairs: List[Dict], output_file: str, style: ReasoningStyle):
        """Save pairs to JSONL file with metadata."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            # Write metadata header
            metadata = {
                "type": "metadata",
                "style_name": style.name,
                "description": style.description,
                "total_pairs": len(pairs),
                "model_used": self.model_name
            }
            f.write(json.dumps(metadata) + '\n')
            
            # Write pairs
            for pair in pairs:
                f.write(json.dumps(pair) + '\n')
        
        logger.info(f"Saved {len(pairs)} pairs to {output_file}")

def create_sample_questions() -> List[str]:
    """Create a diverse set of sample questions for testing."""
    return [
        "How does photosynthesis work?",
        "What are the key factors that led to the fall of the Roman Empire?",
        "Explain the concept of machine learning to a 10-year-old.",
        "How would you solve climate change?",
        "What is the relationship between quantum mechanics and general relativity?",
        "How do neural networks learn?",
        "What makes a good leader?",
        "Explain the economic impact of automation.",
        "How does the human immune system work?",
        "What are the ethical implications of artificial intelligence?"
    ]

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    builder = ContrastivePairBuilder()
    questions = create_sample_questions()
    
    # Generate datasets for each style
    for style_name in builder.reasoning_styles.keys():
        output_file = f"datasets/{style_name}_pairs.jsonl"
        stats = builder.generate_pairs(questions, style_name, output_file)
        print(f"Style {style_name}: {stats}")
