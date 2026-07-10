from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import replace

from src.models import CuratedArticle

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


CONFIDENCE_LEVELS = {"high", "medium", "low"}
DIAGNOSTIC_MESSAGE_LENGTH = 500
RESPONSE_EXCERPT_LENGTH = 500
SAFE_RESPONSE_KEYS = ("id", "object", "created", "model", "choices", "usage")
MINIMAX_M3_MODEL = "minimaxai/minimax-m3"
DEFAULT_NVIDIA_COMPLETION_MAX_TOKENS = 2048
DEFAULT_NVIDIA_COMPLETION_TEMPERATURE = 0.2
FORBIDDEN_PREVIEW_TERMS = (
    "투자 조언",
    "매수",
    "매도",
    "추천 종목",
    "커리어",
    "개발자",
    "해야 합니다",
)


class LLMEnhancementError(RuntimeError):
    def __init__(
        self,
        stage: str,
        message: str,
        *,
        error_type: str = "LLMEnhancementError",
        response_metadata: dict[str, object] | None = None,
        response_excerpt: str = "",
    ):
        super().__init__(message)
        self.stage = stage
        self.error_type = error_type
        self.message = message
        self.response_metadata = response_metadata or _empty_response_metadata()
        self.response_excerpt = response_excerpt


def build_message_enhancement_prompt(articles: list[CuratedArticle]) -> str:
    article_blocks = []
    for index, article in enumerate(articles):
        article_blocks.append(
            "\n".join(
                [
                    f"index: {index}",
                    f"title: {article.title}",
                    f"source: {article.source}",
                    f"snippet: {article.snippet}",
                    "rule_based_reasons: "
                    + ", ".join(article.recommendation_reasons),
                ]
            )
        )

    return f"""You enhance a Telegram decision card for Google Alerts articles.

Core philosophy:
- Rule-based selection already decided which articles are worth showing.
- You do not select new articles.
- You may only make the message easier to understand.

Grounding rules:
- Do not assume you read the full article body.
- Use only title, source, snippet, and rule_based_reasons.
- If there is not enough evidence, return an empty string for preview.
- Do not force a preview.
- Do not infer company intent.
- Do not invent numbers, facts, causes, or outcomes.
- Do not write market forecasts.
- Do not write investment advice.
- Do not write developer career advice or career insight.
- Do not write "Why it Matters".
- Do not write a full summary.
- Evidence must contain only words that appear in the original title or snippet.

Output rules:
- Output strict JSON only.
- Write korean_title, preview, why_selected, and daily_trends in Korean.
- Keep the original article title unchanged by referring to articles by index.
- korean_title must be short, natural, and grounded in the title/snippet.
- korean_title should be 20 to 45 Korean characters when possible.
- preview must be 25 to 70 Korean characters.
- preview must be one sentence.
- preview must not include future outlook, investment advice, or career advice.
- why_selected should explain the rule-based signal in one reader-friendly Korean sentence.
- confidence must be one of: high, medium, low.
- If confidence is low, preview must be an empty string.
- daily_trends should contain only common trends across multiple final articles.
- If there is only one final article, daily_trends must be an empty array.
- Include only trends directly supported by at least two final articles.
- Return at most two daily_trends items.
- If there is no clear common trend, daily_trends must be an empty array.

Semantic deduplication is disabled for this release.
- Do not remove, merge, hide, or reorder articles.
- Return every article index exactly once.
- Leave duplicate handling to the existing URL and rule-based steps.

JSON schema:
{{
  "articles": [
    {{
      "index": 0,
      "korean_title": "",
      "preview": "",
      "why_selected": "",
      "confidence": "high",
      "evidence": []
    }}
  ],
  "daily_trends": []
}}

Articles:
{chr(10).join(article_blocks)}
"""


def enhance_message_with_llm(
    articles: list[CuratedArticle],
    api_key: str,
    model: str,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
    provider: str | None = None,
    *,
    raise_on_error: bool = False,
) -> tuple[list[CuratedArticle], list[str]]:
    if not articles or OpenAI is None:
        if raise_on_error and OpenAI is None:
            raise LLMEnhancementError(
                "client_unavailable",
                "OpenAI-compatible client is not installed.",
            )
        return articles, []

    prompt = build_message_enhancement_prompt(articles)

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if timeout_seconds is not None:
            client_kwargs["timeout"] = timeout_seconds

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **_build_completion_kwargs(model, provider),
        )
    except Exception as exc:
        if raise_on_error:
            raise LLMEnhancementError(
                "api_request_failed",
                _sanitize_diagnostic_text(
                    f"{type(exc).__name__}: {exc}",
                    secrets=(api_key,),
                ),
                error_type=type(exc).__name__,
            ) from exc
        return articles, []

    try:
        response_text, response_metadata = _extract_response_text(response)
    except LLMEnhancementError as exc:
        if raise_on_error:
            raise _sanitize_llm_error(exc, secrets=(api_key,)) from exc
        return articles, []

    try:
        enhanced_articles, daily_trends = parse_message_enhancement_response(
            response_text,
            articles,
            raise_on_error=raise_on_error,
        )
    except LLMEnhancementError as exc:
        if raise_on_error:
            exc.response_metadata = response_metadata
            raise _sanitize_llm_error(exc, secrets=(api_key,)) from exc
        return articles, []

    if not enhanced_articles:
        if raise_on_error:
            raise LLMEnhancementError(
                "response_parse_failed",
                "LLM response did not produce any enhanced articles.",
                error_type="NoEnhancedArticlesError",
                response_metadata=response_metadata,
                response_excerpt=_response_excerpt(response_text),
            )
        return articles, []

    return enhanced_articles, daily_trends


def parse_message_enhancement_response(
    response_text: str,
    articles: list[CuratedArticle],
    *,
    raise_on_error: bool = False,
) -> tuple[list[CuratedArticle], list[str]]:
    if not response_text:
        if raise_on_error:
            raise LLMEnhancementError(
                "response_parse_failed",
                "LLM response was empty.",
                error_type="EmptyResponseContentError",
            )
        return [], []

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as exc:
        if raise_on_error:
            raise LLMEnhancementError(
                "response_parse_failed",
                f"LLM response was not valid JSON: {exc.msg}.",
                error_type="InvalidJSONError",
                response_excerpt=_response_excerpt(response_text),
            ) from exc
        return [], []

    if not isinstance(data, dict):
        if raise_on_error:
            raise LLMEnhancementError(
                "response_parse_failed",
                "LLM response JSON root was not an object.",
                error_type="InvalidJSONRootError",
                response_excerpt=_response_excerpt(response_text),
            )
        return [], []

    raw_articles = data.get("articles")
    if not isinstance(raw_articles, list):
        if raise_on_error:
            raise LLMEnhancementError(
                "response_parse_failed",
                "LLM response did not contain an articles list.",
                error_type="MissingArticlesListError",
                response_excerpt=_response_excerpt(response_text),
            )
        return [], []

    enhanced_by_index: dict[int, CuratedArticle] = {}
    seen_indices: set[int] = set()
    for raw_article in raw_articles:
        if not isinstance(raw_article, dict):
            continue

        index = raw_article.get("index")
        if not isinstance(index, int):
            continue

        if index < 0 or index >= len(articles) or index in seen_indices:
            continue

        seen_indices.add(index)
        original = articles[index]
        enhanced_by_index[index] = (
            replace(
                original,
                korean_title=_clean_korean_title(
                    raw_article.get("korean_title", "")
                ),
                preview=_clean_preview(
                    raw_article.get("preview", ""),
                    raw_article.get("confidence", ""),
                    raw_article.get("evidence", []),
                    original,
                ),
                enhanced_why_selected=_clean_sentence(
                    raw_article.get("why_selected", ""),
                    max_length=120,
                ),
                confidence=_clean_confidence(raw_article.get("confidence", "")),
                evidence=_filter_grounded_evidence(
                    raw_article.get("evidence", []),
                    original,
                ),
            )
        )

    if raise_on_error and not enhanced_by_index:
        raise LLMEnhancementError(
            "response_parse_failed",
            "LLM response did not contain any parseable article entries.",
            error_type="NoParseableArticlesError",
            response_excerpt=_response_excerpt(response_text),
        )

    enhanced_articles = [
        enhanced_by_index.get(index, article)
        for index, article in enumerate(articles)
    ]

    return enhanced_articles, _clean_daily_trends(
        data.get("daily_trends", []),
        article_count=len(enhanced_articles),
    )


def _clean_korean_title(value) -> str:
    title = _clean_sentence(value, max_length=45)
    if len(title) > 45:
        return ""
    return title


def _clean_preview(
    value,
    confidence_value,
    evidence_value,
    article: CuratedArticle,
) -> str:
    confidence = _clean_confidence(confidence_value)
    if confidence == "low":
        return ""

    evidence = _filter_grounded_evidence(evidence_value, article)
    if not evidence:
        return ""

    preview = _clean_sentence(value, max_length=90)
    if not preview:
        return ""

    if any(term in preview for term in FORBIDDEN_PREVIEW_TERMS):
        return ""

    return preview


def _clean_confidence(value) -> str:
    confidence = str(value or "").strip().lower()
    if confidence in CONFIDENCE_LEVELS:
        return confidence
    return "low"


def _filter_grounded_evidence(value, article: CuratedArticle) -> list[str]:
    if not isinstance(value, list):
        return []

    source_text = " ".join([article.title, article.snippet]).lower()
    grounded = []
    for item in value:
        evidence = _clean_sentence(item, max_length=40)
        if not evidence:
            continue

        if evidence.lower() not in source_text:
            continue

        if evidence not in grounded:
            grounded.append(evidence)

        if len(grounded) == 5:
            break

    return grounded


def _clean_daily_trends(value, article_count: int) -> list[str]:
    if article_count < 2 or not isinstance(value, list):
        return []

    trends = []
    for item in value:
        trend = _clean_sentence(item, max_length=60)
        if not trend:
            continue

        if trend not in trends:
            trends.append(trend)

        if len(trends) == 2:
            break

    return trends


def _clean_sentence(value, max_length: int) -> str:
    if not isinstance(value, str):
        return ""

    cleaned = " ".join(value.split())
    if len(cleaned) > max_length:
        return ""

    return cleaned


def _build_completion_kwargs(
    model: str,
    provider: str | None = None,
) -> dict[str, object]:
    normalized_provider = str(provider or "").strip().lower()
    normalized_model = str(model or "").strip()
    if normalized_provider == "openai":
        return {}

    if normalized_provider != "nvidia" and normalized_model != MINIMAX_M3_MODEL:
        return {}

    kwargs: dict[str, object] = {
        "max_tokens": DEFAULT_NVIDIA_COMPLETION_MAX_TOKENS,
        "temperature": DEFAULT_NVIDIA_COMPLETION_TEMPERATURE,
        "stream": False,
    }
    if normalized_model == MINIMAX_M3_MODEL:
        kwargs["extra_body"] = {
            "chat_template_kwargs": {
                "thinking_mode": "disabled",
            },
        }

    return kwargs


def _extract_response_text(response) -> tuple[str, dict[str, object]]:
    metadata = _response_metadata(response)
    if response is None:
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response object was None.",
            error_type="MissingResponseError",
            response_metadata=metadata,
        )

    if not _has_field(response, "choices"):
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response did not expose a choices field.",
            error_type="MissingChoicesError",
            response_metadata=metadata,
        )

    choices = _get_field(response, "choices")
    if choices is None:
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response choices field was None.",
            error_type="NullChoicesError",
            response_metadata=metadata,
        )

    if not _is_sequence(choices):
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response choices field was not a sequence.",
            error_type="InvalidChoicesTypeError",
            response_metadata=metadata,
        )

    if len(choices) == 0:
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response contained no choices.",
            error_type="EmptyChoicesError",
            response_metadata=metadata,
        )

    first_choice = next(iter(choices))
    if first_choice is None:
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response first choice was None.",
            error_type="NullChoiceError",
            response_metadata=metadata,
        )

    if not _has_field(first_choice, "message"):
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response first choice did not expose a message field.",
            error_type="MissingMessageError",
            response_metadata=metadata,
        )

    message = _get_field(first_choice, "message")
    if message is None:
        raise LLMEnhancementError(
            "response_structure_invalid",
            "NVIDIA response first choice message was None.",
            error_type="NullMessageError",
            response_metadata=metadata,
        )

    content = _get_field(message, "content")
    reasoning_content = _get_field(message, "reasoning_content")
    reasoning_length = _string_length(reasoning_content)
    finish_reason = metadata.get("first_choice_finish_reason", "")

    if content is None:
        raise LLMEnhancementError(
            "response_content_missing",
            _missing_content_message(
                finish_reason,
                reasoning_length,
                content_was_empty=False,
            ),
            error_type=_content_missing_error_type(reasoning_length),
            response_metadata=metadata,
        )

    if not isinstance(content, str):
        raise LLMEnhancementError(
            "response_content_missing",
            "NVIDIA response message.content was not a string.",
            error_type="InvalidContentTypeError",
            response_metadata=metadata,
        )

    if not content.strip():
        raise LLMEnhancementError(
            "response_content_missing",
            _missing_content_message(
                finish_reason,
                reasoning_length,
                content_was_empty=True,
            ),
            error_type=_content_missing_error_type(reasoning_length),
            response_metadata=metadata,
        )

    return content, metadata


def _response_metadata(response) -> dict[str, object]:
    metadata = _empty_response_metadata()
    metadata["response_object_type"] = type(response).__name__
    if response is None:
        return metadata

    response_id = _get_field(response, "id")
    metadata["response_id_present"] = bool(response_id)
    response_model = _get_field(response, "model")
    metadata["response_model"] = _safe_string(response_model)
    metadata["response_usage_present"] = _get_field(response, "usage") is not None
    metadata["response_keys"] = _safe_response_keys(response)

    choices = _get_field(response, "choices")
    if _is_sequence(choices):
        metadata["response_choices_count"] = len(choices)
        if choices:
            first_choice = next(iter(choices))
            _add_first_choice_metadata(metadata, first_choice)
    elif choices is None:
        metadata["response_choices_count"] = 0

    return metadata


def _add_first_choice_metadata(
    metadata: dict[str, object],
    first_choice,
) -> None:
    finish_reason = _get_field(first_choice, "finish_reason")
    if finish_reason is None and _has_field(first_choice, "finish_reason"):
        metadata["first_choice_finish_reason"] = "null"
    elif finish_reason is not None:
        metadata["first_choice_finish_reason"] = _safe_string(finish_reason)
    elif first_choice is not None:
        metadata["first_choice_finish_reason"] = "unknown"

    message = _get_field(first_choice, "message")
    metadata["response_message_present"] = message is not None
    if message is None:
        return

    content = _get_field(message, "content")
    if content is None:
        metadata["response_content_type"] = "NoneType"
    else:
        metadata["response_content_type"] = type(content).__name__
        metadata["response_content_length"] = _string_length(content)

    reasoning_content = _get_field(message, "reasoning_content")
    reasoning_length = _string_length(reasoning_content)
    metadata["response_has_reasoning_content"] = reasoning_length > 0
    metadata["reasoning_content_length"] = reasoning_length


def _empty_response_metadata() -> dict[str, object]:
    return {
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
    }


def _has_field(value, field_name: str) -> bool:
    if isinstance(value, dict):
        return field_name in value

    return hasattr(value, field_name)


def _get_field(value, field_name: str):
    if isinstance(value, dict):
        return value.get(field_name)

    return getattr(value, field_name, None)


def _is_sequence(value) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _string_length(value) -> int:
    if isinstance(value, str):
        return len(value)

    return 0


def _safe_string(value) -> str:
    if value is None:
        return ""

    return _sanitize_diagnostic_text(str(value))


def _safe_response_keys(response) -> str:
    data = _response_dict(response)
    if isinstance(data, dict):
        return ",".join(key for key in SAFE_RESPONSE_KEYS if key in data)

    return ",".join(key for key in SAFE_RESPONSE_KEYS if _has_field(response, key))


def _response_dict(response):
    for method_name in ("model_dump", "to_dict", "dict"):
        method = getattr(response, method_name, None)
        if not callable(method):
            continue

        try:
            data = method()
        except Exception:
            continue

        if isinstance(data, dict):
            return data

    return None


def _content_missing_error_type(reasoning_length: int) -> str:
    if reasoning_length > 0:
        return "ReasoningOnlyResponseError"

    return "MissingContentError"


def _missing_content_message(
    finish_reason,
    reasoning_length: int,
    *,
    content_was_empty: bool,
) -> str:
    content_state = "empty" if content_was_empty else "missing"
    if reasoning_length > 0:
        return (
            f"NVIDIA response message.content was {content_state}, "
            "but reasoning_content was present. reasoning_content is not used as JSON."
        )

    if finish_reason == "length":
        return (
            f"NVIDIA response message.content was {content_state} and "
            "finish_reason was length; max_tokens or reasoning token consumption may be involved."
        )

    return f"NVIDIA response message.content was {content_state}."


def _sanitize_llm_error(
    exc: LLMEnhancementError,
    *,
    secrets: tuple[str, ...],
) -> LLMEnhancementError:
    return LLMEnhancementError(
        exc.stage,
        _sanitize_diagnostic_text(exc.message, secrets=secrets),
        error_type=exc.error_type,
        response_metadata=exc.response_metadata,
        response_excerpt=_sanitize_diagnostic_text(
            exc.response_excerpt,
            secrets=secrets,
        ),
    )


def _response_excerpt(response_text: str) -> str:
    return _sanitize_diagnostic_text(response_text)[:RESPONSE_EXCERPT_LENGTH]


def _sanitize_diagnostic_text(
    value: str,
    *,
    secrets: tuple[str, ...] = (),
) -> str:
    text = " ".join(str(value or "").split())
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")

    text = re.sub(
        r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+",
        r"\1[REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)(api[-_]?key\s*[:=]\s*)[^\s,;]+",
        r"\1[REDACTED]",
        text,
    )
    return text[:DIAGNOSTIC_MESSAGE_LENGTH]
