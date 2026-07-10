from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "minimaxai/minimax-m3"
DEFAULT_NVIDIA_TIMEOUT_SECONDS = 60.0
DISABLED_LLM_PROVIDERS = {"", "none", "off", "rule_based", "rule-based"}


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    api_key: str
    model: str
    base_url: str | None = None
    timeout_seconds: float | None = None


def get_llm_provider_config(
    environ: Mapping[str, str] | None = None,
) -> LLMProviderConfig | None:
    env = environ if environ is not None else os.environ
    provider = env.get("LLM_PROVIDER", "").strip().lower()

    if not provider:
        provider = "openai" if env.get("OPENAI_API_KEY", "").strip() else ""

    if provider in DISABLED_LLM_PROVIDERS:
        return None

    if provider == "openai":
        api_key = env.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None

        return LLMProviderConfig(
            provider="openai",
            api_key=api_key,
            model=env.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
            or DEFAULT_OPENAI_MODEL,
        )

    if provider == "nvidia":
        api_key = env.get("NVIDIA_API_KEY", "").strip()
        if not api_key:
            return None

        return LLMProviderConfig(
            provider="nvidia",
            api_key=api_key,
            model=env.get("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL).strip()
            or DEFAULT_NVIDIA_MODEL,
            base_url=env.get("NVIDIA_BASE_URL", DEFAULT_NVIDIA_BASE_URL).strip()
            or DEFAULT_NVIDIA_BASE_URL,
            timeout_seconds=_parse_timeout_seconds(
                env.get("NVIDIA_TIMEOUT_SECONDS", ""),
                default=DEFAULT_NVIDIA_TIMEOUT_SECONDS,
            ),
        )

    return None


def _parse_timeout_seconds(value: str, default: float) -> float:
    raw_value = value.strip()
    if not raw_value:
        return default

    try:
        timeout_seconds = float(raw_value)
    except ValueError:
        return default

    if timeout_seconds <= 0:
        return default

    return timeout_seconds
