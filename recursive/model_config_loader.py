"""
Model Configuration Loader for WriteHERE
Loads and manages model configurations from model_config.yaml
"""

import os
import yaml
from typing import Dict, Any, Optional


class ModelConfigLoader:
    """Loads and provides access to model configurations"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model configuration loader

        Args:
            config_path: Path to the model_config.yaml file.
                        If None, uses default location in same directory.
        """
        if config_path is None:
            # Default to model_config.yaml in the same directory as this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "model_config.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load the YAML configuration file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Warning: Model config file not found at {self.config_path}")
            print("Using default configuration")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            print("Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file is not available"""
        return {
            'defaults': {
                'story_model': 'gpt-4o',
                'report_model': 'gpt-4o',
                'selector_model': 'gpt-4o-mini',
                'summarizer_model': 'gpt-4o-mini'
            },
            'models': {
                'gpt-4o': {
                    'provider': 'openai',
                    'temperature': {
                        'composition': 0.3,
                        'reasoning': 0.3,
                        'planning': 0.1
                    }
                },
                'gpt-4o-mini': {
                    'provider': 'openai',
                    'temperature': {
                        'composition': 0.3,
                        'reasoning': 0.3,
                        'planning': 0.1
                    }
                }
            },
            'advanced': {
                'enable_fallback': False,
                'max_retries': 3,
                'timeout': 120
            }
        }

    def get_default_model(self, mode: str = "story") -> str:
        """
        Get the default model for a given mode

        Args:
            mode: Either "story" or "report"

        Returns:
            Model name string
        """
        defaults = self.config.get('defaults', {})
        if mode == "story":
            return defaults.get('story_model', 'gpt-4o')
        elif mode == "report":
            return defaults.get('report_model', 'gpt-4o')
        else:
            return defaults.get('story_model', 'gpt-4o')

    def get_selector_model(self) -> str:
        """Get the selector model for report generation"""
        defaults = self.config.get('defaults', {})
        return defaults.get('selector_model', 'gpt-4o-mini')

    def get_summarizer_model(self) -> str:
        """Get the summarizer model for report generation"""
        defaults = self.config.get('defaults', {})
        return defaults.get('summarizer_model', 'gpt-4o-mini')

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific model

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model configuration
        """
        models = self.config.get('models', {})
        model_config = models.get(model_name, {}).copy()

        # Resolve environment variable references in api_key and base_url
        if 'api_key' in model_config and isinstance(model_config['api_key'], str):
            model_config['api_key'] = self._resolve_env_var(model_config['api_key'])
        if 'base_url' in model_config and isinstance(model_config['base_url'], str):
            model_config['base_url'] = self._resolve_env_var(model_config['base_url'])

        return model_config

    def _resolve_env_var(self, value: str) -> str:
        """
        Resolve environment variable references in format ${VAR_NAME}

        Args:
            value: String that may contain env var references

        Returns:
            String with env vars resolved
        """
        import re
        import os

        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)

    def get_temperature(self, model_name: str, task_type: str = "composition") -> float:
        """
        Get temperature setting for a model and task type

        Args:
            model_name: Name of the model
            task_type: One of "composition", "reasoning", "planning"

        Returns:
            Temperature value (float)
        """
        model_config = self.get_model_config(model_name)
        temps = model_config.get('temperature', {})

        # Default temperatures if not specified
        default_temps = {
            'composition': 0.3,
            'reasoning': 0.3,
            'planning': 0.1
        }

        return temps.get(task_type, default_temps.get(task_type, 0.3))

    def get_preset(self, preset_name: str) -> Optional[Dict[str, str]]:
        """
        Get a predefined model preset

        Args:
            preset_name: Name of the preset (e.g., "premium", "balanced", "economy")

        Returns:
            Dictionary with model assignments or None if preset not found
        """
        presets = self.config.get('presets', {})
        return presets.get(preset_name)

    def apply_preset(self, preset_name: str) -> bool:
        """
        Apply a preset to the defaults

        Args:
            preset_name: Name of the preset to apply

        Returns:
            True if preset was applied, False if preset not found
        """
        preset = self.get_preset(preset_name)
        if preset is None:
            return False

        # Update defaults with preset values
        self.config['defaults'].update(preset)
        return True

    def list_available_models(self) -> list:
        """Get list of all available model names"""
        return list(self.config.get('models', {}).keys())

    def list_available_presets(self) -> list:
        """Get list of all available preset names"""
        return list(self.config.get('presets', {}).keys())

    def get_advanced_setting(self, setting_name: str, default=None):
        """Get an advanced configuration setting"""
        advanced = self.config.get('advanced', {})
        return advanced.get(setting_name, default)

    def get_litellm_config(self) -> Dict[str, Any]:
        """
        Get LiteLLM configuration

        Returns:
            Dictionary with LiteLLM settings (enabled, base_url, api_key)
        """
        litellm_config = self.config.get('litellm', {}).copy()

        # Resolve environment variable references
        if 'api_key' in litellm_config and isinstance(litellm_config['api_key'], str):
            litellm_config['api_key'] = self._resolve_env_var(litellm_config['api_key'])
        if 'base_url' in litellm_config and isinstance(litellm_config['base_url'], str):
            litellm_config['base_url'] = self._resolve_env_var(litellm_config['base_url'])

        return litellm_config

    def is_litellm_enabled(self) -> bool:
        """Check if LiteLLM is globally enabled"""
        litellm_config = self.config.get('litellm', {})
        return litellm_config.get('enabled', False)

    def get_model_base_url(self, model_name: str) -> Optional[str]:
        """
        Get base_url for a specific model

        Args:
            model_name: Name of the model

        Returns:
            base_url string or None
        """
        model_config = self.get_model_config(model_name)
        return model_config.get('base_url')

    def get_model_api_key(self, model_name: str) -> Optional[str]:
        """
        Get api_key for a specific model

        Args:
            model_name: Name of the model

        Returns:
            api_key string or None
        """
        model_config = self.get_model_config(model_name)
        return model_config.get('api_key')


# Singleton instance for global access
_config_loader_instance = None


def get_model_config_loader(config_path: Optional[str] = None) -> ModelConfigLoader:
    """
    Get the singleton instance of ModelConfigLoader

    Args:
        config_path: Optional path to config file (only used on first call)

    Returns:
        ModelConfigLoader instance
    """
    global _config_loader_instance
    if _config_loader_instance is None:
        _config_loader_instance = ModelConfigLoader(config_path)
    return _config_loader_instance


def reload_config(config_path: Optional[str] = None):
    """Force reload of configuration"""
    global _config_loader_instance
    _config_loader_instance = ModelConfigLoader(config_path)
    return _config_loader_instance


if __name__ == "__main__":
    # Test the configuration loader
    loader = get_model_config_loader()

    print("=== Model Configuration Loader Test ===\n")

    print("Default Models:")
    print(f"  Story: {loader.get_default_model('story')}")
    print(f"  Report: {loader.get_default_model('report')}")
    print(f"  Selector: {loader.get_selector_model()}")
    print(f"  Summarizer: {loader.get_summarizer_model()}")

    print("\nAvailable Models:")
    for model in loader.list_available_models():
        print(f"  - {model}")

    print("\nAvailable Presets:")
    for preset in loader.list_available_presets():
        print(f"  - {preset}")

    print("\nGPT-4o Configuration:")
    config = loader.get_model_config('gpt-4o')
    print(f"  Provider: {config.get('provider')}")
    print(f"  Composition temp: {loader.get_temperature('gpt-4o', 'composition')}")
    print(f"  Planning temp: {loader.get_temperature('gpt-4o', 'planning')}")

    print("\nAdvanced Settings:")
    print(f"  Enable fallback: {loader.get_advanced_setting('enable_fallback')}")
    print(f"  Max retries: {loader.get_advanced_setting('max_retries')}")
    print(f"  Timeout: {loader.get_advanced_setting('timeout')}")
