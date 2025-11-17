# Model Configuration Setup

## Quick Start

1. **Copy the example configuration:**
   ```bash
   cp model_config.yaml.example model_config.yaml
   ```

2. **Edit `model_config.yaml` and replace placeholder API keys:**
   - For LiteLLM models: Replace `YOUR_LITELLM_API_KEY_HERE` with your actual LiteLLM API key
   - For OpenAI models: Set `OPENAI` environment variable or add to `api_key.env`
   - For Anthropic models: Set `CLAUDE` environment variable or add to `api_key.env`
   - For Google models: Set `GEMINI` environment variable or add to `api_key.env`

3. **Use the configuration:**
   ```bash
   # Use default models (LiteLLM)
   python engine.py --filename input.jsonl --output-filename output.jsonl

   # Use a specific preset
   python engine.py --preset litellm_fast --filename input.jsonl

   # Use a specific model
   python engine.py --model qwen3-next-80b-a3b-instruct --filename input.jsonl
   ```

## Security Notes

⚠️ **IMPORTANT**:
- `model_config.yaml` is in `.gitignore` to protect your API keys
- Never commit `model_config.yaml` with real API keys to version control
- Only commit changes to `model_config.yaml.example` (with placeholder keys)

## Available LiteLLM Models

The configuration includes tested LiteLLM models:

### Production Models (High Quality)
- **qwen3-next-80b-a3b-instruct** - 80B parameters, excellent for complex tasks
- **grok-4-fast** - Fast production model with strong performance

### Fast Testing Models
- **qwen3-30b-a3b-instruct-2507-ali** - 30B fast model on Alibaba Cloud
- **gemini-2.5-flash-lite** - Ultra-fast Google model

## LiteLLM Presets

Three recommended presets for different use cases:

- **litellm_production** - Best quality using 80B models
- **litellm_fast** - Quick testing with fast models
- **litellm_balanced** - Mix of quality and speed

Example:
```bash
python engine.py --preset litellm_production --filename story.jsonl
```

## Get LiteLLM API Key

LiteLLM endpoint: https://litellm.zeabur.app/v1

Contact your LiteLLM provider for API access.
