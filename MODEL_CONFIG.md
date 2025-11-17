# Model Configuration Guide

WriteHERE now supports flexible model configuration through a YAML configuration file, making it easy to manage multiple models and switch between different setups.

## Quick Start

### 1. Configure Your Models

The model configuration file is located at `recursive/model_config.yaml`. You can customize:

- **Default models** for story and report generation
- **Selector and summarizer models** for report generation
- **Model-specific settings** like temperature and token limits
- **Predefined presets** for different use cases

### 2. Usage Options

#### Option A: Use Default Models from Config

Simply omit the `--model` parameter, and the system will use defaults from `model_config.yaml`:

```bash
# Story generation with default model
python engine.py --filename input.jsonl --output-filename output.jsonl --mode story

# Report generation with default models
python engine.py --filename input.jsonl --output-filename output.jsonl --mode report --engine-backend serpapi
```

#### Option B: Specify Model via Command Line

Override the default by providing a specific model:

```bash
# Use Claude for story generation
python engine.py --filename input.jsonl --output-filename output.jsonl --model claude-3-7-sonnet-20250219 --mode story

# Use Gemini for report generation
python engine.py --filename input.jsonl --output-filename output.jsonl --model gemini-2.5-pro-preview-03-25 --mode report
```

#### Option C: Use Predefined Presets

Apply a complete preset configuration:

```bash
# Use the "premium" preset (Claude 3.7 Sonnet + GPT-4o)
python engine.py --filename input.jsonl --output-filename output.jsonl --preset premium --mode story

# Use the "economy" preset (all GPT-4o-mini)
python engine.py --filename input.jsonl --output-filename output.jsonl --preset economy --mode report

# Use the "gemini" preset
python engine.py --filename input.jsonl --output-filename output.jsonl --preset gemini --mode report
```

#### Option D: Fine-tune Report Generation Models

For report mode, you can specify selector and summarizer models:

```bash
python engine.py \
  --filename input.jsonl \
  --output-filename output.jsonl \
  --model gpt-4o \
  --selector-model gemini-2.0-flash \
  --summarizer-model gemini-2.0-flash \
  --mode report \
  --engine-backend serpapi
```

## Configuration File Structure

### Default Models

```yaml
defaults:
  story_model: "gpt-4o"              # Default for story generation
  report_model: "gpt-4o"             # Default for report generation
  selector_model: "gpt-4o-mini"      # For selecting relevant search results
  summarizer_model: "gpt-4o-mini"    # For summarizing search results
```

### Model Definitions

Each model can have specific settings:

```yaml
models:
  gpt-4o:
    provider: "openai"
    display_name: "GPT-4o"
    temperature:
      composition: 0.3    # For writing tasks
      reasoning: 0.3      # For thinking tasks
      planning: 0.1       # For planning tasks
    max_tokens: 4096
    supports_vision: true
```

### Predefined Presets

Quick configurations for different scenarios:

```yaml
presets:
  # High quality, slower, more expensive
  premium:
    story_model: "claude-3-7-sonnet-20250219"
    report_model: "gpt-4o"
    selector_model: "gpt-4o-mini"
    summarizer_model: "gpt-4o-mini"

  # Balanced quality and cost
  balanced:
    story_model: "gpt-4o"
    report_model: "gpt-4o"
    selector_model: "gpt-4o-mini"
    summarizer_model: "gpt-4o-mini"

  # Fast and economical
  economy:
    story_model: "gpt-4o-mini"
    report_model: "gpt-4o-mini"
    selector_model: "gpt-4o-mini"
    summarizer_model: "gpt-4o-mini"
```

## Supported Models

### OpenAI
- `gpt-4o` - Latest GPT-4o model
- `gpt-4o-mini` - Faster, more economical version
- `o1` - OpenAI's reasoning model

### Anthropic (Claude)
- `claude-3-7-sonnet-20250219` - Latest Claude 3.7 Sonnet
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet

### Google (Gemini)
- `gemini-2.5-pro-preview-03-25` - Gemini 2.5 Pro
- `gemini-2.0-flash` - Fast Gemini model

### OpenRouter
- `google/gemini-2.5-pro-preview-03-25` - Gemini via OpenRouter
- Any other OpenRouter-supported model

## Command-Line Reference

### Required Arguments
- `--filename`: Input JSONL file path
- `--output-filename`: Output JSONL file path
- `--mode`: Generation mode (`story` or `report`)

### Model Configuration Arguments
- `--model`: Main model to use (optional, uses config default if not specified)
- `--preset`: Use a predefined preset (premium, balanced, economy, gemini, claude)
- `--selector-model`: Model for selecting search results (report mode only)
- `--summarizer-model`: Model for summarizing search results (report mode only)

### Other Arguments
- `--engine-backend`: Search engine backend (serpapi or searxng) for report mode
- `--nodes-json-file`: Path to save execution graph for visualization
- `--today-date`: Date to use in prompts (default: current date)

## Examples

### Story Generation

```bash
# Use default model from config
python engine.py --filename input.jsonl --output-filename output.jsonl --mode story

# Use specific model
python engine.py --filename input.jsonl --output-filename output.jsonl --model claude-3-7-sonnet-20250219 --mode story

# Use premium preset
python engine.py --filename input.jsonl --output-filename output.jsonl --preset premium --mode story
```

### Report Generation

```bash
# Use defaults with SerpAPI search
python engine.py --filename input.jsonl --output-filename output.jsonl --mode report --engine-backend serpapi

# Use Gemini preset with SearXNG
python engine.py --filename input.jsonl --output-filename output.jsonl --preset gemini --mode report --engine-backend searxng

# Custom configuration
python engine.py \
  --filename input.jsonl \
  --output-filename output.jsonl \
  --model gpt-4o \
  --selector-model gemini-2.0-flash \
  --summarizer-model gemini-2.0-flash \
  --mode report \
  --engine-backend serpapi
```

## API Key Configuration

Model configuration is separate from API key configuration. API keys are still managed in `recursive/api_key.env`:

```env
OPENAI=your-openai-api-key
CLAUDE=your-anthropic-api-key
GEMINI=your-google-api-key
OPENROUTER=your-openrouter-api-key
SERPAPI=your-serpapi-key
```

## Backward Compatibility

The new configuration system is fully backward compatible:
- Old scripts that specify `--model` will continue to work
- The `--model` parameter now overrides the config file default
- If neither `--model` nor a preset is specified, the system uses defaults from `model_config.yaml`

## Customizing Configuration

To add your own models or presets:

1. Edit `recursive/model_config.yaml`
2. Add new models under the `models` section
3. Add new presets under the `presets` section
4. Use your custom models via `--model` or presets via `--preset`

Example:

```yaml
models:
  my-custom-model:
    provider: "openai"
    temperature:
      composition: 0.5
      reasoning: 0.3
      planning: 0.1

presets:
  my-preset:
    story_model: "my-custom-model"
    report_model: "gpt-4o"
    selector_model: "gpt-4o-mini"
    summarizer_model: "gpt-4o-mini"
```

Then use it:

```bash
python engine.py --filename input.jsonl --output-filename output.jsonl --preset my-preset --mode story
```
