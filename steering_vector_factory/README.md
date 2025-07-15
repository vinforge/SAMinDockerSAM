# Steering Vector Factory

This directory contains the offline pipeline for generating steering vectors that enable SAM to adopt different reasoning styles during inference.

## Overview

The Steering Vector Factory implements a contrastive learning approach to extract "steering vectors" from a powerful teacher model (GPT-4) that can later be used to guide SAM's reasoning patterns. This is Phase 1 of the KV Cache Steering implementation.

## Architecture

```
steering_vector_factory/
├── dataset_builder.py      # Generates contrastive response pairs
├── extract_vectors.py      # Extracts steering vectors from pairs  
├── generate_steering_vectors.py  # Main orchestration script
├── config.yaml            # Configuration file
├── requirements.txt       # Dependencies
└── README.md              # This file

Generated outputs:
├── datasets/              # Contrastive datasets (JSONL)
├── steering_vectors/      # Raw steering vectors (.pt files)
└── ../sam/assets/steering_vectors/  # Vectors for SAM integration
```

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment (recommended)
python -m venv steering_env
source steering_env/bin/activate  # On Windows: steering_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Access

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or pass it directly:
```bash
python generate_steering_vectors.py --api-key your-api-key-here
```

### 3. Generate Steering Vectors

Generate all available reasoning styles:
```bash
python generate_steering_vectors.py
```

Generate specific styles:
```bash
python generate_steering_vectors.py --styles researcher_style step_by_step_reasoning
```

Use custom configuration:
```bash
python generate_steering_vectors.py --config custom_config.yaml
```

## Available Reasoning Styles

### 1. **researcher_style**
- **Description**: Detailed analytical reasoning with research methodology
- **Characteristics**: Systematic analysis, multiple perspectives, evidence-based conclusions
- **Use Cases**: Academic research, complex problem analysis, thorough investigations

### 2. **step_by_step_reasoning**  
- **Description**: Systematic step-by-step logical progression
- **Characteristics**: Numbered steps, clear logical flow, explicit reasoning chain
- **Use Cases**: Problem-solving, tutorials, mathematical reasoning

### 3. **creative_explorer**
- **Description**: Creative and exploratory thinking patterns
- **Characteristics**: Alternative perspectives, unconventional approaches, creative solutions
- **Use Cases**: Brainstorming, innovation, artistic endeavors

## Configuration Options

Edit `config.yaml` to customize:

```yaml
# Teacher model for dataset generation
teacher_model: "gpt-4"

# Target model for vector extraction  
target_model: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

# Hardware settings
device: "auto"
load_in_8bit: true

# API settings
api_delay: 1.0
regenerate_datasets: false

# Custom questions
additional_questions:
  - "Your custom question here"
```

## Output Files

### Datasets (`datasets/`)
- `{style}_pairs.jsonl`: Contrastive response pairs for each style
- Format: One JSON object per line with positive/negative response pairs

### Steering Vectors (`steering_vectors/`)
- `{style}.pt`: PyTorch tensor files containing extracted steering vectors
- Contains key vectors, value vectors, and metadata

### SAM Assets (`../sam/assets/steering_vectors/`)
- `{style}.pt`: Steering vectors copied for SAM integration
- `{style}_template.json`: Prompt templates for Phase 2 implementation

## Technical Details

### Contrastive Dataset Generation
1. Uses a teacher model (GPT-4) to generate response pairs
2. Positive prompts encourage the target reasoning style
3. Negative prompts use neutral/direct reasoning
4. Pairs are saved in JSONL format for processing

### Vector Extraction Process
1. Loads DeepSeek-R1 model directly in PyTorch
2. Processes positive and negative responses through the model
3. Extracts KV cache states from target layers (8-15)
4. Computes difference vectors: `positive_kv - negative_kv`
5. Averages across all pairs to create final steering vector

### Memory Optimization
- Uses 8-bit quantization by default
- Processes in small batches
- Targets middle-to-late transformer layers
- Automatic device selection (CUDA/MPS/CPU)

## Troubleshooting

### Common Issues

**CUDA Out of Memory**
```bash
# Reduce model precision or use CPU
python generate_steering_vectors.py --config config_cpu.yaml
```

**API Rate Limits**
```yaml
# Increase delay in config.yaml
api_delay: 2.0
```

**Model Download Issues**
```bash
# Pre-download the model
python -c "from transformers import AutoModel; AutoModel.from_pretrained('deepseek-ai/DeepSeek-R1-Distill-Qwen-7B')"
```

### Logs and Debugging

Check the log file for detailed information:
```bash
tail -f steering_vector_generation.log
```

## Integration with SAM

Once steering vectors are generated, they will be automatically copied to `sam/assets/steering_vectors/` and are ready for Phase 2 integration with SAM's inference pipeline.

The generated prompt templates in `{style}_template.json` provide the foundation for implementing prompt-based steering approximation in Phase 2.

## Performance Notes

- **Generation Time**: ~10-30 minutes per style (depending on hardware and API speed)
- **Memory Usage**: 8-16GB RAM recommended for 7B model
- **Storage**: ~100MB per steering vector set
- **API Costs**: ~$2-5 per style with GPT-4 (10 questions × 2 responses)

## Next Steps

After successful generation:
1. Verify steering vectors in `sam/assets/steering_vectors/`
2. Proceed to Phase 2: Prompt-Based Steering Approximation
3. Test integration with SAM's inference pipeline
4. Evaluate reasoning quality improvements

## Support

For issues or questions:
1. Check the log file: `steering_vector_generation.log`
2. Review configuration in `config.yaml`
3. Ensure API keys and model access are properly configured
