"""
Multi-Provider LLM Support for Kosmos.

This module provides a unified interface for working with different LLM providers
(Anthropic, OpenAI, and other OpenAI-compatible APIs).

Basic usage:
    ```python
    from kosmos.core.providers import get_provider
    from kosmos.config import get_config

    config = get_config()
    provider = get_provider(config)

    response = provider.generate("What is machine learning?")
    print(response.content)
    ```
"""

from kosmos.core.providers.base import (
    LLMProvider,
    Message,
    UsageStats,
    LLMResponse,
    ProviderAPIError
)
from kosmos.core.providers.factory import (
    get_provider,
    get_provider_from_config,
    list_providers,
    register_provider
)

__all__ = [
    "LLMProvider",
    "Message",
    "UsageStats",
    "LLMResponse",
    "ProviderAPIError",
    "get_provider",
    "get_provider_from_config",
    "list_providers",
    "register_provider",
]
