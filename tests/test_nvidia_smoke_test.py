from __future__ import annotations

from dataclasses import replace

import pytest

from scripts import smoke_test_nvidia_enhancer as smoke_module
from src.dedup_store import DedupStore
from src.rule_based_selector import select_high_signal_articles


def make_env() -> dict[str, str]:
    return {
        "LLM_PROVIDER": "nvidia",
        "NVIDIA_API_KEY": "secret-nvidia-key",
        "NVIDIA_MODEL": "minimaxai/minimax-m3",
        "NVIDIA_TIMEOUT_SECONDS": "60",
        "TELEGRAM_BOT_TOKEN": "secret-telegram-token",
        "TELEGRAM_CHAT_ID": "secret-chat-id",
    }


def enhanced_articles_from(articles):
    return [
        replace(
            articles[0],
            korean_title="AI 반도체 투자 확대 테스트",
            preview="HBM과 GPU capacity investment 신호를 다룬 테스트입니다.",
            enhanced_why_selected="반도체 공급망과 인프라 투자 신호가 함께 나타난 테스트 기사입니다.",
            confidence="high",
            evidence=["HBM", "GPU"],
        ),
        replace(
            articles[1],
            korean_title="기업 AI 가격 변화 테스트",
            preview="API pricing과 enterprise deployment 신호를 다룬 테스트입니다.",
            enhanced_why_selected="가격 변화와 기업 도입 신호가 함께 나타난 테스트 기사입니다.",
            confidence="medium",
            evidence=["API pricing", "enterprise"],
        ),
        replace(
            articles[2],
            korean_title="모호한 플랫폼 업데이트 테스트",
            preview="",
            enhanced_why_selected="기업 워크플로 언급은 있지만 세부 근거가 제한적인 테스트 기사입니다.",
            confidence="low",
            evidence=[],
        ),
    ]


def test_missing_nvidia_api_key_fails() -> None:
    env = make_env()
    env["NVIDIA_API_KEY"] = ""

    with pytest.raises(smoke_module.SmokeTestError, match="NVIDIA_API_KEY"):
        smoke_module.run_smoke_test(env, emit_logs=False)


def test_missing_nvidia_model_fails() -> None:
    env = make_env()
    env["NVIDIA_MODEL"] = ""

    with pytest.raises(smoke_module.SmokeTestError, match="NVIDIA_MODEL"):
        smoke_module.run_smoke_test(env, emit_logs=False)


def test_unexpected_nvidia_model_fails() -> None:
    env = make_env()
    env["NVIDIA_MODEL"] = "other/model"

    with pytest.raises(smoke_module.SmokeTestError, match="minimaxai/minimax-m3"):
        smoke_module.run_smoke_test(env, emit_logs=False)


def test_fixture_articles_pass_rule_based_selector() -> None:
    fixtures = smoke_module.build_fixture_articles()

    selected = select_high_signal_articles(fixtures, limit=3)

    assert len(fixtures) == 3
    assert len(selected) == 3
    assert all(article.url.startswith("https://example.com/") for article in fixtures)
    assert all("Synthetic" in article.source for article in fixtures)


def test_smoke_test_reuses_enhancer_builder_and_sender_without_dedup(
    monkeypatch,
    capsys,
) -> None:
    env = make_env()
    calls = {
        "enhancer": False,
        "builder": False,
        "telegram": False,
        "dedup_save": False,
    }

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
    ):
        calls["enhancer"] = True
        assert api_key == env["NVIDIA_API_KEY"]
        assert model == env["NVIDIA_MODEL"]
        assert base_url == "https://integrate.api.nvidia.com/v1"
        assert timeout_seconds == 60.0
        return enhanced_articles_from(articles), ["AI 인프라와 기업 AI 도입"]

    def fake_build_telegram_message(
        articles,
        header="Daily High-Signal Tech Alerts",
        show_summary=True,
        daily_trends=None,
    ):
        calls["builder"] = True
        assert len(articles) == 3
        assert show_summary is True
        assert daily_trends == ["AI 인프라와 기업 AI 도입"]
        return "telegram body"

    def fake_send_telegram_message(bot_token, chat_id, message):
        calls["telegram"] = True
        assert bot_token == env["TELEGRAM_BOT_TOKEN"]
        assert chat_id == env["TELEGRAM_CHAT_ID"]
        assert message.startswith("[SMOKE TEST]\n")
        assert "telegram body" in message
        return True

    def fake_dedup_save(self):
        calls["dedup_save"] = True

    monkeypatch.setattr(
        smoke_module,
        "enhance_message_with_llm",
        fake_enhance_message_with_llm,
    )
    monkeypatch.setattr(
        smoke_module,
        "build_telegram_message",
        fake_build_telegram_message,
    )
    monkeypatch.setattr(
        smoke_module,
        "send_telegram_message",
        fake_send_telegram_message,
    )
    monkeypatch.setattr(DedupStore, "save", fake_dedup_save)

    result = smoke_module.run_smoke_test(env)
    captured = capsys.readouterr()
    logged_text = captured.out + captured.err

    assert calls == {
        "enhancer": True,
        "builder": True,
        "telegram": True,
        "dedup_save": False,
    }
    assert result["rule_based_selected_articles"] == 3
    assert result["llm_enhancement_success"] is True
    assert result["preview_generated_articles"] == 2
    assert result["preview_omitted_articles"] == 1
    assert result["daily_trends_count"] == 1
    assert result["telegram_send_success"] is True
    assert "provider: nvidia" in logged_text
    assert "model: minimaxai/minimax-m3" in logged_text

    secret_values = (
        env["NVIDIA_API_KEY"],
        env["TELEGRAM_BOT_TOKEN"],
        env["TELEGRAM_CHAT_ID"],
    )
    for secret_value in secret_values:
        assert secret_value not in logged_text

    generated_file_text = (
        (smoke_module.PROJECT_ROOT / "scripts/smoke_test_nvidia_enhancer.py").read_text(
            encoding="utf-8"
        )
        + (
            smoke_module.PROJECT_ROOT / ".github/workflows/nvidia-smoke-test.yml"
        ).read_text(encoding="utf-8")
    )
    for secret_value in secret_values:
        assert secret_value not in generated_file_text


def test_llm_failure_fails_workflow_before_telegram(monkeypatch, capsys) -> None:
    env = make_env()
    telegram_called = False

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
    ):
        return articles, []

    def fake_send_telegram_message(*args):
        nonlocal telegram_called
        telegram_called = True
        return True

    monkeypatch.setattr(
        smoke_module,
        "enhance_message_with_llm",
        fake_enhance_message_with_llm,
    )
    monkeypatch.setattr(
        smoke_module,
        "send_telegram_message",
        fake_send_telegram_message,
    )

    with pytest.raises(smoke_module.SmokeTestError, match="LLM enhancement failed"):
        smoke_module.run_smoke_test(env)

    logged_text = capsys.readouterr().out
    assert "llm_enhancement_success: false" in logged_text
    assert telegram_called is False


def test_telegram_failure_fails_workflow(monkeypatch, capsys) -> None:
    env = make_env()

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
    ):
        return enhanced_articles_from(articles), []

    monkeypatch.setattr(
        smoke_module,
        "enhance_message_with_llm",
        fake_enhance_message_with_llm,
    )
    monkeypatch.setattr(
        smoke_module,
        "send_telegram_message",
        lambda *args: False,
    )

    with pytest.raises(smoke_module.SmokeTestError, match="Telegram send failed"):
        smoke_module.run_smoke_test(env)

    logged_text = capsys.readouterr().out
    assert "telegram_send_success: false" in logged_text


def test_confidence_and_evidence_only_do_not_count_as_llm_success(
    monkeypatch,
    capsys,
) -> None:
    env = make_env()

    def fake_enhance_message_with_llm(
        articles,
        api_key,
        model,
        base_url=None,
        timeout_seconds=None,
    ):
        return [
            replace(article, confidence="low", evidence=["HBM"])
            for article in articles
        ], []

    monkeypatch.setattr(
        smoke_module,
        "enhance_message_with_llm",
        fake_enhance_message_with_llm,
    )

    with pytest.raises(smoke_module.SmokeTestError, match="LLM enhancement failed"):
        smoke_module.run_smoke_test(env)

    logged_text = capsys.readouterr().out
    assert "llm_enhancement_success: false" in logged_text


def test_display_field_counts_as_llm_success() -> None:
    selected_articles = select_high_signal_articles(
        smoke_module.build_fixture_articles(),
        limit=3,
    )
    articles = [
        replace(
            enhanced_articles_from(selected_articles)[0],
            preview="",
            enhanced_why_selected="",
            confidence="low",
            evidence=[],
        )
    ]

    assert smoke_module._has_usable_enhancement(articles) is True
