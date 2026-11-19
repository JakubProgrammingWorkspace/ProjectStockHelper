import logging
import os
from dataclasses import dataclass
from enum import StrEnum

import requests

from apps.stock_data.services.document_processor.llm_api_adapter import LLMApiAdapter

LOG_PREFIX = "[LLM Handler]"
logger = logging.getLogger(__name__)


class ModelEnum(StrEnum):
    """Available LLM models."""

    LLAMA_33 = "llama3.3"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"


class ProviderEnum(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class LLMConfig:
    """Configuration for LLM handler."""

    model: str = ModelEnum.LLAMA_33.value
    base_url: str = ""
    api_key: str | None = None
    timeout_seconds: int = 1200  # 20 minutes for large models
    num_ctx: int = 128000  # Increased for large documents
    keep_alive: int = 300  # Keep model in memory for 5 minutes


class LLMHandler:
    """HTTP handler for LLM inference. Format-specific logic is delegated to the adapter."""

    def __init__(self, config: LLMConfig, adapter: LLMApiAdapter):
        self.config = config
        self.adapter = adapter
        logger.info("%s Initialized LLMHandler: model=%s", LOG_PREFIX, self.config.model)

    @classmethod
    def from_env(cls, provider: str = ProviderEnum.OPENAI) -> "LLMHandler":
        """
        Factory that reads LLM environment variables and selects the correct adapter.

        Raises:
            ValueError: If LLM_API_MODEL is not set.
        """
        from apps.stock_data.services.document_processor.llm_api_adapter import (
            OllamaApiAdapter,
            OpenAIClientAdapter,
        )

        model = os.environ.get("LLM_API_MODEL")
        if not model:
            raise ValueError("LLM_API_MODEL environment variable is not set")

        api_key = os.environ.get("LLM_API_KEY")
        base_url = os.environ.get("LLM_API_BASE_URL", "")

        adapter = OllamaApiAdapter() if provider == ProviderEnum.OLLAMA else OpenAIClientAdapter()

        config = LLMConfig(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

        return cls(config=config, adapter=adapter)

    def ask(self, prompt) -> str | None:
        """Send a prompt to the LLM and retrieve the response via the adapter."""
        return self.adapter.ask(self.config, prompt)

    def unload_model(self):
        """Unload the model from memory to free resources (Ollama specific)."""
        try:
            unload_payload = {"model": self.config.model, "keep_alive": 0}
            requests.post(f"{self.config.base_url}/api/generate", json=unload_payload, timeout=30)
            logger.info("%s Model %s unloaded", LOG_PREFIX, self.config.model)
        except Exception as e:
            logger.warning("%s Error unloading model: %s", LOG_PREFIX, e)
