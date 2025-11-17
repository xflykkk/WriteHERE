# LiteLLM Integration Guide

WriteHERE now supports [LiteLLM](https://github.com/BerriAI/litellm), allowing you to use 100+ LLMs with a unified API interface, including local models, custom endpoints, and cost tracking.

## What is LiteLLM?

LiteLLM is a unified API interface that allows you to call OpenAI, Azure, Anthropic, Cohere, and 100+ LLMs using the OpenAI format. It also provides:
- Load balancing across multiple deployments
- Cost tracking and budgets
- Unified logging
- Caching
- Fallbacks

## Quick Start

### Option 1: Global LiteLLM Proxy

Use LiteLLM proxy for all models in WriteHERE.

**Step 1: Start LiteLLM Proxy**

```bash
# Install LiteLLM
pip install litellm[proxy]

# Start the proxy server
litellm --port 4000
```

**Step 2: Configure WriteHERE**

Edit `recursive/model_config.yaml`:

```yaml
litellm:
  enabled: true
  base_url: "http://localhost:4000"  # Your LiteLLM proxy URL
  api_key: "sk-1234"                  # Optional: if proxy requires auth
```

**Step 3: Run WriteHERE**

All models will now route through LiteLLM:

```bash
cd recursive
python engine.py --filename input.jsonl --output-filename output.jsonl --mode story
```

### Option 2: Model-Specific Configuration

Configure custom endpoints for individual models.

Edit `recursive/model_config.yaml`:

```yaml
models:
  # Use LiteLLM for a specific model
  deepseek-chat:
    provider: "openai"  # OpenAI-compatible API
    display_name: "DeepSeek Chat"
    base_url: "http://localhost:4000/v1"
    api_key: "${LITELLM_API_KEY}"  # Environment variable reference
    temperature:
      composition: 0.3
      reasoning: 0.3
      planning: 0.1
    max_tokens: 8192

  # Use local LLM via LiteLLM
  local-llama-3:
    provider: "openai"
    display_name: "Local Llama 3"
    base_url: "http://localhost:8000/v1"
    api_key: "not-needed"
    temperature:
      composition: 0.7
      reasoning: 0.5
      planning: 0.3
    max_tokens: 4096
```

Then use the model:

```bash
python engine.py --filename input.jsonl --output-filename output.jsonl --model deepseek-chat --mode story
```

## Common Use Cases

### 1. Use DeepSeek via LiteLLM

```yaml
# Add to model_config.yaml
models:
  deepseek-chat:
    provider: "openai"
    display_name: "DeepSeek Chat"
    base_url: "https://api.deepseek.com/v1"  # DeepSeek API endpoint
    api_key: "${DEEPSEEK_API_KEY}"
    temperature:
      composition: 0.3
      reasoning: 0.3
      planning: 0.1
    max_tokens: 8192

# Set environment variable
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Run
python engine.py --model deepseek-chat --mode story --filename input.jsonl --output-filename output.jsonl
```

### 2. Use Local Ollama Models

```yaml
# Add to model_config.yaml
models:
  ollama-llama3:
    provider: "openai"
    display_name: "Ollama Llama 3"
    base_url: "http://localhost:11434/v1"  # Ollama OpenAI-compatible endpoint
    api_key: "ollama"  # Ollama doesn't require a real key
    temperature:
      composition: 0.7
      reasoning: 0.5
      planning: 0.3
    max_tokens: 4096

# Make sure Ollama is running
ollama serve

# Pull the model
ollama pull llama3

# Run WriteHERE
python engine.py --model ollama-llama3 --mode story --filename input.jsonl --output-filename output.jsonl
```

### 3. Use vLLM or Text Generation Inference

```yaml
# vLLM or TGI models
models:
  vllm-mistral:
    provider: "openai"
    display_name: "vLLM Mistral"
    base_url: "http://localhost:8000/v1"  # vLLM or TGI endpoint
    api_key: "EMPTY"
    temperature:
      composition: 0.7
      reasoning: 0.5
      planning: 0.3
    max_tokens: 4096
```

### 4. Use Azure OpenAI

```yaml
models:
  azure-gpt-4:
    provider: "openai"
    display_name: "Azure GPT-4"
    base_url: "https://your-resource.openai.azure.com/openai/deployments/your-deployment"
    api_key: "${AZURE_OPENAI_KEY}"
    temperature:
      composition: 0.3
      reasoning: 0.3
      planning: 0.1
    max_tokens: 4096
```

### 5. Load Balancing with LiteLLM Proxy

Configure LiteLLM proxy for load balancing:

**litellm_config.yaml:**

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o-deployment-1
      api_base: https://resource-1.openai.azure.com
      api_key: ${AZURE_KEY_1}
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o-deployment-2
      api_base: https://resource-2.openai.azure.com
      api_key: ${AZURE_KEY_2}

router_settings:
  routing_strategy: usage-based-routing  # or simple-shuffle, latency-based
```

Start proxy:

```bash
litellm --config litellm_config.yaml --port 4000
```

Configure WriteHERE:

```yaml
litellm:
  enabled: true
  base_url: "http://localhost:4000"
```

## Environment Variable References

You can reference environment variables in the configuration:

```yaml
models:
  my-model:
    base_url: "${MY_BASE_URL}"  # Will be replaced with env var value
    api_key: "${MY_API_KEY}"
```

Set environment variables:

```bash
export MY_BASE_URL="http://localhost:4000/v1"
export MY_API_KEY="your-api-key"
```

## Configuration Priority

WriteHERE uses the following priority for base_url and api_key:

1. **Model-specific config** in `model_config.yaml` (highest priority)
2. **Global LiteLLM config** if `litellm.enabled: true`
3. **Environment variables** in `api_key.env` (lowest priority)

Example:

```yaml
# Global LiteLLM (priority 2)
litellm:
  enabled: true
  base_url: "http://localhost:4000"
  api_key: "global-key"

models:
  gpt-4o:
    # Model-specific (priority 1 - will override global)
    base_url: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"

  deepseek-chat:
    # No base_url/api_key specified, will use global LiteLLM config
    provider: "openai"
    temperature:
      composition: 0.3
```

## Testing Your Configuration

Test if your LiteLLM setup works:

```bash
cd recursive

# Test the config loader
python -c "
from model_config_loader import get_model_config_loader

loader = get_model_config_loader()

# Check LiteLLM config
print('LiteLLM Config:', loader.get_litellm_config())

# Check model config
print('Model Config:', loader.get_model_config('your-model-name'))
"

# Run a simple test
python engine.py \
  --filename ../test_data/meta_fiction.jsonl \
  --output-filename /tmp/test_output.jsonl \
  --model your-model-name \
  --mode story
```

## Troubleshooting

### Issue: "Connection refused" error

**Solution:** Make sure LiteLLM proxy or your custom endpoint is running:

```bash
# Check if service is running
curl http://localhost:4000/health

# Start LiteLLM proxy
litellm --port 4000
```

### Issue: "API key not found" error

**Solution:** Set the environment variable or configure it in `model_config.yaml`:

```bash
export LITELLM_API_KEY="your-key"
```

Or in config:

```yaml
litellm:
  api_key: "your-key"
```

### Issue: Model not found in LiteLLM

**Solution:** Check your LiteLLM proxy configuration and model names:

```bash
# List available models
curl http://localhost:4000/models
```

### Issue: Different response format

**Solution:** WriteHERE expects OpenAI-compatible response format. Make sure your endpoint returns:

```json
{
  "choices": [{
    "message": {
      "content": "response text"
    }
  }]
}
```

## Advanced: LiteLLM Proxy Features

### Cost Tracking

LiteLLM proxy can track costs across models:

```yaml
# litellm_config.yaml
general_settings:
  max_budget: 100  # USD
  budget_duration: 30d
```

### Caching

Enable caching to reduce API calls:

```yaml
# litellm_config.yaml
general_settings:
  cache: true
  cache_params:
    type: redis
    host: localhost
    port: 6379
```

### Logging

Configure logging to track all requests:

```yaml
# litellm_config.yaml
general_settings:
  success_callback: ["langfuse"]  # or "lunary", "helicone", etc.
```

## Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Proxy Server](https://docs.litellm.ai/docs/proxy/quick_start)
- [Supported LLMs](https://docs.litellm.ai/docs/providers)
- [Cost Tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)

## Example: Complete Setup

Here's a complete example for running WriteHERE with multiple models via LiteLLM:

**1. Create litellm_config.yaml:**

```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: ${OPENAI_API_KEY}

  - model_name: deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: ${DEEPSEEK_API_KEY}

  - model_name: local-llama
    litellm_params:
      model: ollama/llama3
      api_base: http://localhost:11434

general_settings:
  cache: true
  max_budget: 50
```

**2. Start LiteLLM proxy:**

```bash
export OPENAI_API_KEY="your-openai-key"
export DEEPSEEK_API_KEY="your-deepseek-key"

litellm --config litellm_config.yaml --port 4000
```

**3. Configure WriteHERE:**

Edit `recursive/model_config.yaml`:

```yaml
litellm:
  enabled: true
  base_url: "http://localhost:4000"

defaults:
  story_model: "deepseek-chat"
  report_model: "gpt-4o"
  selector_model: "local-llama"
  summarizer_model: "local-llama"
```

**4. Run WriteHERE:**

```bash
cd recursive
python engine.py --filename input.jsonl --output-filename output.jsonl --mode story
```

All models will now route through LiteLLM with cost tracking, caching, and unified logging!
