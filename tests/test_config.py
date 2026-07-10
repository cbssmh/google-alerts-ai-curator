from src.config import (
    DEFAULT_NVIDIA_BASE_URL,
    DEFAULT_NVIDIA_MODEL,
    DEFAULT_NVIDIA_TIMEOUT_SECONDS,
    DEFAULT_OPENAI_MODEL,
    get_llm_provider_config,
)


def test_missing_provider_and_missing_openai_key_disables_llm() -> None:
    assert get_llm_provider_config({}) is None


def test_openai_key_without_provider_preserves_legacy_openai_path() -> None:
    config = get_llm_provider_config({"OPENAI_API_KEY": "openai-key"})

    assert config is not None
    assert config.provider == "openai"
    assert config.api_key == "openai-key"
    assert config.model == DEFAULT_OPENAI_MODEL
    assert config.base_url is None
    assert config.timeout_seconds is None


def test_openai_provider_uses_openai_model() -> None:
    config = get_llm_provider_config(
        {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_MODEL": "gpt-test",
        }
    )

    assert config is not None
    assert config.provider == "openai"
    assert config.model == "gpt-test"


def test_nvidia_provider_uses_nim_settings() -> None:
    config = get_llm_provider_config(
        {
            "LLM_PROVIDER": "nvidia",
            "NVIDIA_API_KEY": "nvapi-key",
            "NVIDIA_MODEL": "nvidia-model",
            "NVIDIA_BASE_URL": "https://example.nvidia.test/v1",
            "NVIDIA_TIMEOUT_SECONDS": "45.5",
            "OPENAI_API_KEY": "openai-key",
        }
    )

    assert config is not None
    assert config.provider == "nvidia"
    assert config.api_key == "nvapi-key"
    assert config.model == "nvidia-model"
    assert config.base_url == "https://example.nvidia.test/v1"
    assert config.timeout_seconds == 45.5


def test_nvidia_provider_has_nim_defaults() -> None:
    config = get_llm_provider_config(
        {
            "LLM_PROVIDER": "nvidia",
            "NVIDIA_API_KEY": "nvapi-key",
        }
    )

    assert config is not None
    assert config.model == DEFAULT_NVIDIA_MODEL
    assert config.base_url == DEFAULT_NVIDIA_BASE_URL
    assert config.timeout_seconds == DEFAULT_NVIDIA_TIMEOUT_SECONDS


def test_invalid_nvidia_timeout_uses_default() -> None:
    config = get_llm_provider_config(
        {
            "LLM_PROVIDER": "nvidia",
            "NVIDIA_API_KEY": "nvapi-key",
            "NVIDIA_TIMEOUT_SECONDS": "not-a-number",
        }
    )

    assert config is not None
    assert config.timeout_seconds == DEFAULT_NVIDIA_TIMEOUT_SECONDS


def test_missing_provider_key_falls_back_to_rule_based_path() -> None:
    assert get_llm_provider_config({"LLM_PROVIDER": "openai"}) is None
    assert get_llm_provider_config({"LLM_PROVIDER": "nvidia"}) is None
    assert get_llm_provider_config({"LLM_PROVIDER": "unknown"}) is None
