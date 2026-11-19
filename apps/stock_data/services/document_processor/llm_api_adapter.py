import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import requests
from openai import OpenAI, OpenAIError

LOG_PREFIX = "[LLM API Adapter]"
logger = logging.getLogger(__name__)


class LLMApiAdapter(ABC):
    @abstractmethod
    def ask(self, config, prompt) -> str | None: ...


class OllamaApiAdapter(LLMApiAdapter):
    def build_url(self, base_url: str) -> str:
        return f"{base_url}/api/chat"

    def build_payload(self, model: str, prompt, config) -> dict[str, Any]:
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "keep_alive": config.keep_alive,
            "options": {
                "temperature": prompt.temperature,
                "top_p": 1,
                "top_k": 1,
                "num_predict": -1,
                "num_ctx": config.num_ctx,
            },
        }
        # Use schema from prompt if available
        schema = getattr(prompt, "schema", None)
        if prompt.with_json_schema:
            payload["format"] = schema
        else:
            payload["format"] = "json"
        return payload

    def parse_response(self, response_text: str) -> str:
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error("%s Failed to parse JSON response: %s", LOG_PREFIX, e)
            raise ValueError(f"Invalid JSON response: {e}") from e

        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]

        raise ValueError(f"Unexpected response format: {data}")

    def ask(self, config, prompt) -> str | None:
        url = self.build_url(config.base_url)
        payload = self.build_payload(config.model, prompt, config)
        try:
            response = requests.post(url, json=payload, timeout=config.timeout_seconds)
            response.raise_for_status()
            return self.parse_response(response.text)
        except requests.RequestException as e:
            logger.error("%s Ollama HTTP request failed: %s", LOG_PREFIX, e)
            return None
        except ValueError as e:
            logger.error("%s Ollama response parsing failed: %s", LOG_PREFIX, e)
            return None


class OpenAIClientAdapter(LLMApiAdapter):
    """Adapter using the official OpenAI library."""

    def ask(self, config, prompt) -> str | None:
        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None,
        )

        schema = getattr(prompt, "schema", None)

        try:
            response_format = {"type": "json_object"}
            if prompt.with_json_schema and schema:
                response_format = {
                    "type": "json_schema",
                    "json_schema": {"name": "financial_extraction", "schema": schema, "strict": True},
                }

            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": prompt.system_prompt},
                    {"role": "user", "content": prompt.user_prompt},
                ],
                response_format=response_format,
                temperature=prompt.temperature,
                timeout=config.timeout_seconds,
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            logger.error("%s OpenAI request failed: %s", LOG_PREFIX, e)
            return None
