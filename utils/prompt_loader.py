"""Prompt template loader for LLM agents.

Loads prompt templates from config/prompts.yaml.
Keeps prompts separate from runtime configuration.
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any


# Cache for loaded prompts
_prompts_cache: Optional[Dict[str, str]] = None


def _load_prompts_yaml() -> Dict[str, str]:
    """Load prompts from config/prompts.yaml.
    
    Returns:
        dict: Dictionary of prompt_name -> prompt_template.
    """
    global _prompts_cache
    
    if _prompts_cache is not None:
        return _prompts_cache
    
    prompts_file = Path(__file__).parent.parent / 'config' / 'prompts.yaml'
    
    try:
        if prompts_file.exists():
            with open(prompts_file, 'r', encoding='utf-8') as f:
                _prompts_cache = yaml.safe_load(f) or {}
        else:
            _prompts_cache = {}
    except Exception as e:
        print(f"Warning: Failed to load prompts.yaml: {e}")
        _prompts_cache = {}
    
    return _prompts_cache


def load_prompt(prompt_name: str, default: str = "") -> str:
    """Load a prompt template from config/prompts.yaml.
    
    Args:
        prompt_name (str): Name of the prompt (key in prompts.yaml).
        default (str): Default prompt text if not found.
        
    Returns:
        str: Prompt template text.
        
    Example:
        prompt = load_prompt('alert_summary_prompt')
        # Loads from config/prompts.yaml
    """
    prompts = _load_prompts_yaml()
    return prompts.get(prompt_name, default)


def load_prompt_with_vars(prompt_name: str, **variables) -> str:
    """Load a prompt template and substitute variables.
    
    Uses Python string formatting with named placeholders.
    
    Args:
        prompt_name (str): Name of the prompt.
        **variables: Variables to substitute in the template.
        
    Returns:
        str: Prompt with variables substituted.
        
    Example:
        prompt = load_prompt_with_vars(
            'alert_summary_prompt',
            alerts='[{"severity": "high", "message": "CPU usage"}]'
        )
    """
    template = load_prompt(prompt_name)
    
    if not template:
        return ""
    
    try:
        return template.format(**variables)
    except KeyError as e:
        print(f"Warning: Missing variable {e} in prompt '{prompt_name}'")
        return template
    except Exception as e:
        print(f"Warning: Failed to format prompt '{prompt_name}': {e}")
        return template


def reload_prompts() -> None:
    """Reload prompts from disk (useful for testing or hot-reloading)."""
    global _prompts_cache
    _prompts_cache = None
