from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_llm_provider_config
from src.message_builder import build_telegram_message
from src.message_enhancer import LLMEnhancementError, enhance_message_with_llm
from src.models import Article, CuratedArticle
from src.rule_based_selector import select_high_signal_articles
from src.telegram_sender import send_telegram_message


SMOKE_TEST_PREFIX = "[SMOKE TEST]"
EXPECTED_PROVIDER = "nvidia"
EXPECTED_MODEL = "minimaxai/minimax-m3"


class SmokeTestError(RuntimeError):
    pass


def build_fixture_articles() -> list[Article]:
    return [
        Article(
            title=(
                "Synthetic test data: AI semiconductor suppliers expand HBM "
                "and GPU capacity investment"
            ),
            source="Synthetic Smoke Fixture - Not Real News",
            url="https://example.com/smoke/semiconductor-investment",
            snippet=(
                "TEST DATA ONLY: A fabricated alert says chip, HBM, GPU, "
                "foundry, data center capacity, and capex are expanding "
                "together for AI infrastructure."
            ),
        ),
        Article(
            title=(
                "Synthetic test data: enterprise AI platform cuts API pricing "
                "for customer deployments"
            ),
            source="Synthetic Smoke Fixture - Not Real News",
            url="https://example.com/smoke/ai-pricing-enterprise",
            snippet=(
                "TEST DATA ONLY: A fabricated alert describes API pricing "
                "changes, lower inference cost, and enterprise customer "
                "rollout planning."
            ),
        ),
        Article(
            title=(
                "Synthetic test data: AI platform update mentions enterprise "
                "workflow but gives few specifics"
            ),
            source="Synthetic Smoke Fixture - Not Real News",
            url="https://example.com/smoke/ambiguous-platform-update",
            snippet=(
                "TEST DATA ONLY: A fabricated alert mentions an enterprise "
                "workflow platform update, but provides no concrete customer, "
                "release date, price, deployment scope, or outcome."
            ),
        ),
    ]


def run_smoke_test(
    environ: Mapping[str, str] | None = None,
    *,
    emit_logs: bool = True,
) -> dict[str, object]:
    started_at = time.monotonic()
    env = environ if environ is not None else os.environ
    result: dict[str, object] = {
        "provider": env.get("LLM_PROVIDER", "").strip().lower(),
        "model": env.get("NVIDIA_MODEL", "").strip(),
        "rule_based_selected_articles": 0,
        "llm_enhancement_success": False,
        "preview_generated_articles": 0,
        "preview_omitted_articles": 0,
        "daily_trends_count": 0,
        "telegram_send_success": False,
        "llm_error_stage": "",
        "llm_error_type": "",
        "llm_error_message": "",
        "llm_response_excerpt": "",
        "response_object_type": "",
        "response_id_present": False,
        "response_model": "",
        "response_choices_count": 0,
        "response_usage_present": False,
        "first_choice_finish_reason": "",
        "response_message_present": False,
        "response_content_type": "",
        "response_content_length": 0,
        "response_has_reasoning_content": False,
        "reasoning_content_length": 0,
        "response_keys": "",
        "elapsed_seconds": 0.0,
    }

    try:
        _validate_required_env(env)
        llm_config = get_llm_provider_config(env)
        if llm_config is None or llm_config.provider != EXPECTED_PROVIDER:
            raise SmokeTestError("NVIDIA provider configuration could not be loaded.")

        fixtures = build_fixture_articles()
        curated_articles = select_high_signal_articles(fixtures, limit=3)
        result["rule_based_selected_articles"] = len(curated_articles)
        if len(curated_articles) != len(fixtures):
            raise SmokeTestError(
                "Rule-based selector did not select all smoke test fixtures."
            )

        try:
            enhanced_articles, daily_trends = enhance_message_with_llm(
                curated_articles,
                llm_config.api_key,
                model=llm_config.model,
                base_url=llm_config.base_url,
                timeout_seconds=llm_config.timeout_seconds,
                raise_on_error=True,
            )
        except LLMEnhancementError as exc:
            _set_llm_error_result(result, exc)
            raise SmokeTestError(
                f"LLM enhancement failed at {exc.stage}: {exc.message}"
            ) from exc
        if len(enhanced_articles) != len(curated_articles):
            raise SmokeTestError(
                "LLM enhancement changed article count; semantic dedup is disabled."
            )

        llm_success = _has_usable_enhancement(enhanced_articles)
        result["llm_enhancement_success"] = llm_success
        result["daily_trends_count"] = len(daily_trends)
        _set_preview_counts(result, enhanced_articles)
        if not llm_success:
            result["llm_error_stage"] = "no_usable_enhancement"
            result["llm_error_type"] = "NoUsableEnhancementError"
            result["llm_error_message"] = (
                "No user-visible enhancement fields survived validation."
            )
            raise SmokeTestError(
                "LLM enhancement failed or returned no usable enhancement."
            )

        message_body = build_telegram_message(
            enhanced_articles,
            header="NVIDIA Message Smoke Test",
            show_summary=True,
            daily_trends=daily_trends,
        )
        if not message_body:
            raise SmokeTestError("Telegram message builder returned an empty message.")

        message = f"{SMOKE_TEST_PREFIX}\n{message_body}"
        telegram_sent = send_telegram_message(
            env["TELEGRAM_BOT_TOKEN"].strip(),
            env["TELEGRAM_CHAT_ID"].strip(),
            message,
        )
        result["telegram_send_success"] = telegram_sent
        if not telegram_sent:
            raise SmokeTestError("Telegram send failed.")

        return result
    finally:
        result["elapsed_seconds"] = round(time.monotonic() - started_at, 2)
        if emit_logs:
            _print_result(result)


def _validate_required_env(env: Mapping[str, str]) -> None:
    provider = env.get("LLM_PROVIDER", "").strip().lower()
    if provider != EXPECTED_PROVIDER:
        raise SmokeTestError("LLM_PROVIDER must be 'nvidia' for this smoke test.")

    required_names = (
        "NVIDIA_API_KEY",
        "NVIDIA_MODEL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    )
    missing = [name for name in required_names if not env.get(name, "").strip()]
    if missing:
        raise SmokeTestError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    model = env.get("NVIDIA_MODEL", "").strip()
    if model != EXPECTED_MODEL:
        raise SmokeTestError(
            f"NVIDIA_MODEL must be '{EXPECTED_MODEL}' for this smoke test."
        )


def _has_usable_enhancement(articles: list[CuratedArticle]) -> bool:
    return any(
        article.korean_title.strip()
        or article.preview.strip()
        or article.enhanced_why_selected.strip()
        for article in articles
    )


def _set_preview_counts(
    result: dict[str, object],
    articles: list[CuratedArticle],
) -> None:
    generated_count = sum(
        1
        for article in articles
        if article.preview.strip() and article.confidence.lower() != "low"
    )
    result["preview_generated_articles"] = generated_count
    result["preview_omitted_articles"] = len(articles) - generated_count


def _set_llm_error_result(
    result: dict[str, object],
    exc: LLMEnhancementError,
) -> None:
    result["llm_error_stage"] = exc.stage
    result["llm_error_type"] = exc.error_type
    result["llm_error_message"] = exc.message
    result["llm_response_excerpt"] = exc.response_excerpt
    for key, value in exc.response_metadata.items():
        if key in result:
            result[key] = value


def _print_result(result: dict[str, object]) -> None:
    print(f"provider: {result['provider']}")
    print(f"model: {result['model']}")
    print(f"rule_based_selected_articles: {result['rule_based_selected_articles']}")
    print(f"llm_enhancement_success: {str(result['llm_enhancement_success']).lower()}")
    print(f"preview_generated_articles: {result['preview_generated_articles']}")
    print(f"preview_omitted_articles: {result['preview_omitted_articles']}")
    print(f"daily_trends_count: {result['daily_trends_count']}")
    print(f"telegram_send_success: {str(result['telegram_send_success']).lower()}")
    if result.get("llm_error_stage"):
        print(f"llm_error_stage: {result['llm_error_stage']}")
    if result.get("llm_error_type"):
        print(f"llm_error_type: {result['llm_error_type']}")
    if result.get("llm_error_message"):
        print(f"llm_error_message: {result['llm_error_message']}")
    if result.get("llm_response_excerpt"):
        print(f"llm_response_excerpt: {result['llm_response_excerpt']}")
    print(f"response_object_type: {result['response_object_type']}")
    print(f"response_id_present: {str(result['response_id_present']).lower()}")
    print(f"response_model: {result['response_model']}")
    print(f"response_choices_count: {result['response_choices_count']}")
    print(f"response_usage_present: {str(result['response_usage_present']).lower()}")
    print(f"first_choice_finish_reason: {result['first_choice_finish_reason']}")
    print(f"response_message_present: {str(result['response_message_present']).lower()}")
    print(f"response_content_type: {result['response_content_type']}")
    print(f"response_content_length: {result['response_content_length']}")
    print(
        "response_has_reasoning_content: "
        f"{str(result['response_has_reasoning_content']).lower()}"
    )
    print(f"reasoning_content_length: {result['reasoning_content_length']}")
    print(f"response_keys: {result['response_keys']}")
    print(f"elapsed_seconds: {result['elapsed_seconds']}")


def main() -> None:
    try:
        run_smoke_test()
    except SmokeTestError as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
