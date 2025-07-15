"""
Steering Vector Extraction from Contrastive Datasets
====================================================

This module extracts steering vectors from contrastive response pairs
using direct PyTorch model access to the DeepSeek-R1 model.

Author: SAM Development Team  
Version: 1.0.0
"""

import json
import logging
import os
import torch
from typing import List, Dict, Tuple, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SteeringVector:
    """Container for steering vector data."""
    style_name: str
    key_vector: torch.Tensor
    value_vector: torch.Tensor
    layer_indices: List[int]
    metadata: Dict

class VectorExtractor:
    """Extracts steering vectors from contrastive datasets."""
    
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", 
                 device: str = "auto", load_in_8bit: bool = True):
        """
        Initialize the vector extractor.
        
        Args:
            model_name: HuggingFace model identifier for DeepSeek-R1
            device: Device to load model on ("auto", "cuda", "cpu")
            load_in_8bit: Whether to use 8-bit quantization for memory efficiency
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.load_in_8bit = load_in_8bit
        
        logger.info(f"Initializing VectorExtractor with model: {model_name}")
        logger.info(f"Device: {self.device}, 8-bit loading: {load_in_8bit}")
        
        # Load model and tokenizer
        self.tokenizer = self._load_tokenizer()
        self.model = self._load_model()
        
        # Configuration for extraction
        self.target_layers = list(range(8, 16))  # Focus on middle-to-late layers
        self.max_sequence_length = 2048
        
    def _setup_device(self, device: str) -> torch.device:
        """Setup the appropriate device for model loading."""
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return torch.device("mps")
            else:
                return torch.device("cpu")
        return torch.device(device)
    
    def _load_tokenizer(self) -> AutoTokenizer:
        """Load the tokenizer for the model."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            return tokenizer
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise
    
    def _load_model(self) -> AutoModelForCausalLM:
        """Load the model with appropriate configuration."""
        try:
            model_kwargs = {
                "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32,
                "device_map": "auto" if self.device.type == "cuda" else None,
                "trust_remote_code": True
            }
            
            if self.load_in_8bit and self.device.type == "cuda":
                model_kwargs["load_in_8bit"] = True
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            model.eval()
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def extract_steering_vectors(self, dataset_file: str, output_file: str, 
                                batch_size: int = 1) -> SteeringVector:
        """
        Extract steering vectors from a contrastive dataset.
        
        Args:
            dataset_file: Path to JSONL file with contrastive pairs
            output_file: Path to save the steering vector
            batch_size: Batch size for processing (keep small for memory)
            
        Returns:
            SteeringVector object containing the extracted vectors
        """
        logger.info(f"Extracting steering vectors from {dataset_file}")
        
        # Load dataset
        pairs = self._load_dataset(dataset_file)
        if not pairs:
            raise ValueError(f"No valid pairs found in {dataset_file}")
        
        # Extract vectors for each pair
        key_diffs = []
        value_diffs = []
        
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            batch_key_diffs, batch_value_diffs = self._process_batch(batch)
            key_diffs.extend(batch_key_diffs)
            value_diffs.extend(batch_value_diffs)
        
        # Average across all pairs
        avg_key_vector = torch.stack(key_diffs).mean(dim=0)
        avg_value_vector = torch.stack(value_diffs).mean(dim=0)
        
        # Create steering vector object
        metadata = self._extract_metadata(dataset_file)
        steering_vector = SteeringVector(
            style_name=metadata.get("style_name", "unknown"),
            key_vector=avg_key_vector,
            value_vector=avg_value_vector,
            layer_indices=self.target_layers,
            metadata=metadata
        )
        
        # Save to file
        self._save_steering_vector(steering_vector, output_file)
        
        logger.info(f"Successfully extracted steering vector for {steering_vector.style_name}")
        return steering_vector
    
    def _load_dataset(self, dataset_file: str) -> List[Dict]:
        """Load contrastive pairs from JSONL file."""
        pairs = []
        
        with open(dataset_file, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                if data.get("type") != "metadata":  # Skip metadata lines
                    pairs.append(data)
        
        logger.info(f"Loaded {len(pairs)} contrastive pairs")
        return pairs
    
    def _process_batch(self, batch: List[Dict]) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        """Process a batch of contrastive pairs to extract vector differences."""
        key_diffs = []
        value_diffs = []
        
        for pair in tqdm(batch, desc="Processing pairs", leave=False):
            try:
                # Get KV cache states for positive and negative responses
                pos_kv_cache = self._get_kv_cache(pair["positive_response"])
                neg_kv_cache = self._get_kv_cache(pair["negative_response"])
                
                if pos_kv_cache is not None and neg_kv_cache is not None:
                    # Calculate differences for target layers
                    pair_key_diffs = []
                    pair_value_diffs = []
                    
                    for layer_idx in self.target_layers:
                        if layer_idx < len(pos_kv_cache) and layer_idx < len(neg_kv_cache):
                            # Extract key and value tensors from the last token
                            pos_key, pos_value = pos_kv_cache[layer_idx]
                            neg_key, neg_value = neg_kv_cache[layer_idx]
                            
                            # Get last token representations
                            pos_key_last = pos_key[:, :, -1, :].mean(dim=(0, 1))  # Average over batch and heads
                            pos_value_last = pos_value[:, :, -1, :].mean(dim=(0, 1))
                            neg_key_last = neg_key[:, :, -1, :].mean(dim=(0, 1))
                            neg_value_last = neg_value[:, :, -1, :].mean(dim=(0, 1))
                            
                            # Calculate differences
                            key_diff = pos_key_last - neg_key_last
                            value_diff = pos_value_last - neg_value_last
                            
                            pair_key_diffs.append(key_diff)
                            pair_value_diffs.append(value_diff)
                    
                    if pair_key_diffs and pair_value_diffs:
                        # Average across layers for this pair
                        avg_key_diff = torch.stack(pair_key_diffs).mean(dim=0)
                        avg_value_diff = torch.stack(pair_value_diffs).mean(dim=0)
                        
                        key_diffs.append(avg_key_diff)
                        value_diffs.append(avg_value_diff)
                
            except Exception as e:
                logger.warning(f"Failed to process pair: {e}")
                continue
        
        return key_diffs, value_diffs
    
    def _get_kv_cache(self, text: str) -> Optional[List[Tuple[torch.Tensor, torch.Tensor]]]:
        """Get KV cache states for a given text."""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                max_length=self.max_sequence_length,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Forward pass with cache
            with torch.no_grad():
                outputs = self.model(**inputs, use_cache=True, output_hidden_states=True)
                return outputs.past_key_values
                
        except Exception as e:
            logger.warning(f"Failed to get KV cache: {e}")
            return None
    
    def _extract_metadata(self, dataset_file: str) -> Dict:
        """Extract metadata from dataset file."""
        with open(dataset_file, 'r') as f:
            first_line = f.readline().strip()
            metadata = json.loads(first_line)
            if metadata.get("type") == "metadata":
                return metadata
        return {}
    
    def _save_steering_vector(self, steering_vector: SteeringVector, output_file: str):
        """Save steering vector to file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        save_data = {
            "style_name": steering_vector.style_name,
            "key_vector": steering_vector.key_vector.cpu(),
            "value_vector": steering_vector.value_vector.cpu(),
            "layer_indices": steering_vector.layer_indices,
            "metadata": steering_vector.metadata,
            "model_name": self.model_name,
            "extraction_config": {
                "target_layers": self.target_layers,
                "max_sequence_length": self.max_sequence_length
            }
        }
        
        torch.save(save_data, output_file)
        logger.info(f"Saved steering vector to {output_file}")

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    extractor = VectorExtractor()
    
    # Process all dataset files
    dataset_dir = "datasets"
    output_dir = "steering_vectors"
    
    for filename in os.listdir(dataset_dir):
        if filename.endswith("_pairs.jsonl"):
            style_name = filename.replace("_pairs.jsonl", "")
            dataset_file = os.path.join(dataset_dir, filename)
            output_file = os.path.join(output_dir, f"{style_name}.pt")
            
            try:
                steering_vector = extractor.extract_steering_vectors(dataset_file, output_file)
                print(f"✓ Generated steering vector for {style_name}")
            except Exception as e:
                print(f"✗ Failed to generate steering vector for {style_name}: {e}")
