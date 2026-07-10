import json

from src import message_enhancer as message_enhancer_module
from src.message_enhancer import (
    LLMEnhancementError,
    build_message_enhancement_prompt,
    enhance_message_with_llm,
    parse_message_enhancement_response,
)
from src.models import CuratedArticle


MISSING = object()


class FakeResponseObject:
    def __init__(
        self,
        *,
        choices=MISSING,
        response_id="resp-test",
        model="minimaxai/minimax-m3",
        usage=None,
    ):
        self.id = response_id
        self.model = model
        self.usage = usage
        if choices is not MISSING:
            self.choices = choices

    def model_dump(self):
        data = {
            "id": self.id,
            "object": "chat.completion",
            "created": 1,
            "model": self.model,
            "usage": self.usage,
        }
        if hasattr(self, "choices"):
            data["choices"] = self.choices
        return data


class FakeChoiceObject:
    def __init__(self, *, message=MISSING, finish_reason="stop"):
        self.finish_reason = finish_reason
        if message is not MISSING:
            self.message = message


class FakeMessageObject:
    def __init__(self, *, content=None, reasoning_content=None):
        self.content = content
        if reasoning_content is not MISSING:
            self.reasoning_content = reasoning_content


def make_article(
    title: str = "Samsung and SK Hynix expand HBM investment for AI chips",
    snippet: str = "Samsung and SK Hynix are increasing HBM investment as AI chip demand grows.",
    url: str = "https://example.com/article",
) -> CuratedArticle:
    return CuratedArticle(
        title=title,
        source="Reuters",
        url=url,
        snippet=snippet,
        relevance_score=12,
        why_selected="rule-based reason",
        korean_summary="",
        career_market_insight="",
        recommendation_reasons=["반도체 공급망", "인프라 투자"],
    )


def fake_openai_returning(monkeypatch, response=None, error=None):
    class FakeCompletions:
        def create(self, model, messages):
            if error is not None:
                raise error
            return response

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(message_enhancer_module, "OpenAI", FakeOpenAI)


def assert_strict_error(response, expected_stage: str, expected_type: str, monkeypatch):
    fake_openai_returning(monkeypatch, response=response)

    try:
        enhance_message_with_llm(
            [make_article()],
            api_key="api-key",
            model="nvidia-model",
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == expected_stage
        assert exc.error_type == expected_type
        return exc

    raise AssertionError("Expected LLMEnhancementError")


def test_prompt_contains_grounding_guardrails() -> None:
    prompt = build_message_enhancement_prompt([make_article()])

    assert "Do not assume you read the full article body." in prompt
    assert "Use only title, source, snippet, and rule_based_reasons." in prompt
    assert "If there is not enough evidence, return an empty string for preview." in prompt
    assert "Output strict JSON only." in prompt
    assert "Do not write market forecasts." in prompt
    assert "Do not write investment advice." in prompt
    assert "Do not write developer career advice or career insight." in prompt
    assert "Evidence must contain only words that appear in the original title or snippet." in prompt
    assert "If there is only one final article, daily_trends must be an empty array." in prompt
    assert "Include only trends directly supported by at least two final articles." in prompt
    assert "Return at most two daily_trends items." in prompt
    assert "Semantic deduplication is disabled for this release." in prompt
    assert "Do not remove, merge, hide, or reorder articles." in prompt
    assert "Return every article index exactly once." in prompt
    assert "Leave duplicate handling to the existing URL and rule-based steps." in prompt


def test_prompt_has_no_conflicting_semantic_dedup_instructions() -> None:
    prompt = build_message_enhancement_prompt(
        [
            make_article(url="https://example.com/one"),
            make_article(
                title="Samsung SK Hynix expand HBM investment for AI chips",
                snippet="Samsung and SK Hynix expand HBM investment.",
                url="https://example.com/two",
            ),
        ]
    )

    forbidden_fragments = (
        "best representative index",
        "same event",
        "include only the best representative",
        "omit",
        "omitted",
        "Title similarity candidates",
        "semantic deduplication:",
    )
    for fragment in forbidden_fragments:
        assert fragment not in prompt


def test_parse_message_enhancement_response_applies_grounded_fields() -> None:
    articles = [make_article()]
    response = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "삼성과 SK하이닉스의 HBM 투자 확대를 다룬 기사입니다.",
                    "why_selected": "반도체 공급망과 인프라 투자 신호가 함께 나타난 기사입니다.",
                    "confidence": "high",
                    "evidence": ["Samsung", "HBM", "investment"],
                }
            ],
            "daily_trends": ["AI 반도체 투자 확대"],
        }
    )

    enhanced_articles, daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert len(enhanced_articles) == 1
    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert enhanced_articles[0].preview == "삼성과 SK하이닉스의 HBM 투자 확대를 다룬 기사입니다."
    assert enhanced_articles[0].enhanced_why_selected == "반도체 공급망과 인프라 투자 신호가 함께 나타난 기사입니다."
    assert enhanced_articles[0].confidence == "high"
    assert enhanced_articles[0].evidence == ["Samsung", "HBM", "investment"]
    assert daily_trends == []


def test_low_confidence_removes_preview() -> None:
    articles = [make_article()]
    response = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "삼성과 SK하이닉스의 HBM 투자 확대를 다룬 기사입니다.",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "low",
                    "evidence": ["Samsung", "HBM"],
                }
            ],
            "daily_trends": [],
        }
    )

    enhanced_articles, _daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert enhanced_articles[0].preview == ""
    assert enhanced_articles[0].confidence == "low"


def test_preview_requires_grounded_evidence() -> None:
    articles = [make_article()]
    response = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "삼성과 SK하이닉스의 HBM 투자 확대를 다룬 기사입니다.",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "high",
                    "evidence": ["nonexistent"],
                }
            ],
            "daily_trends": [],
        }
    )

    enhanced_articles, _daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert enhanced_articles[0].preview == ""
    assert enhanced_articles[0].evidence == []


def test_omitted_article_index_does_not_remove_article() -> None:
    articles = [
        make_article(url="https://example.com/one"),
        make_article(
            title="Samsung SK Hynix increase AI chip HBM investment",
            snippet="Samsung and SK Hynix increase HBM spending.",
            url="https://example.com/two",
        ),
    ]
    response = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "",
                    "why_selected": "중복 사건의 대표 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Samsung", "HBM"],
                }
            ],
            "daily_trends": [],
        }
    )

    enhanced_articles, _daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert [article.url for article in enhanced_articles] == [
        "https://example.com/one",
        "https://example.com/two",
    ]
    assert enhanced_articles[0].enhanced_why_selected == "중복 사건의 대표 기사입니다."
    assert enhanced_articles[1].enhanced_why_selected == ""


def test_daily_trends_allow_only_two_items_for_multiple_articles() -> None:
    articles = [
        make_article(url="https://example.com/one"),
        make_article(
            title="Enterprise AI deployment and API pricing changes",
            snippet="Enterprise customer deployment expands as API pricing changes.",
            url="https://example.com/two",
        ),
    ]
    response = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Samsung", "HBM"],
                },
                {
                    "index": 1,
                    "korean_title": "기업 AI 도입과 API 가격 변화",
                    "preview": "",
                    "why_selected": "기업 도입과 가격 변화 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Enterprise", "API pricing"],
                },
            ],
            "daily_trends": [
                "AI 인프라 투자 확대",
                "기업 AI 도입 확대",
                "모델 가격 경쟁 심화",
            ],
        }
    )

    _enhanced_articles, daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert daily_trends == ["AI 인프라 투자 확대", "기업 AI 도입 확대"]


def test_markdown_wrapped_json_is_rejected_without_repair() -> None:
    articles = [make_article()]
    response = """```json
{"articles": [], "daily_trends": []}
```"""

    enhanced_articles, daily_trends = parse_message_enhancement_response(
        response,
        articles,
    )

    assert enhanced_articles == []
    assert daily_trends == []


def test_enhance_message_with_llm_passes_timeout_to_openai_client(monkeypatch) -> None:
    captured_client_kwargs = {}

    class FakeCompletions:
        def create(self, model, messages):
            return FakeResponse(
                json.dumps(
                    {
                        "articles": [
                            {
                                "index": 0,
                                "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                                "preview": "",
                                "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                                "confidence": "medium",
                                "evidence": ["Samsung", "HBM"],
                            }
                        ],
                        "daily_trends": [],
                    }
                )
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured_client_kwargs.update(kwargs)
            self.chat = FakeChat()

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)

    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]

    monkeypatch.setattr(message_enhancer_module, "OpenAI", FakeOpenAI)

    enhanced_articles, _daily_trends = enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="nvidia-model",
        base_url="https://integrate.api.nvidia.com/v1",
        timeout_seconds=60.0,
    )

    assert captured_client_kwargs == {
        "api_key": "api-key",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "timeout": 60.0,
    }
    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"


def test_enhance_message_with_llm_preserves_fallback_on_api_error(monkeypatch) -> None:
    articles = [make_article()]

    class FakeOpenAI:
        def __init__(self, **kwargs):
            pass

        @property
        def chat(self):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr(message_enhancer_module, "OpenAI", FakeOpenAI)

    enhanced_articles, daily_trends = enhance_message_with_llm(
        articles,
        api_key="api-key",
        model="nvidia-model",
    )

    assert enhanced_articles == articles
    assert daily_trends == []


def test_enhance_message_with_llm_strict_api_error_is_sanitized(monkeypatch) -> None:
    class FakeCompletions:
        def create(self, model, messages):
            raise RuntimeError(
                "Authorization: Bearer secret-api-key api_key=secret-api-key failed"
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(message_enhancer_module, "OpenAI", FakeOpenAI)

    try:
        enhance_message_with_llm(
            [make_article()],
            api_key="secret-api-key",
            model="nvidia-model",
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == "api_request_failed"
        assert "secret-api-key" not in exc.message
        assert "Authorization: Bearer [REDACTED]" in exc.message
    else:
        raise AssertionError("Expected LLMEnhancementError")


def test_empty_choices_is_response_structure_invalid(monkeypatch) -> None:
    response = FakeResponseObject(choices=[])

    exc = assert_strict_error(
        response,
        "response_structure_invalid",
        "EmptyChoicesError",
        monkeypatch,
    )

    assert "no choices" in exc.message
    assert exc.response_metadata["response_choices_count"] == 0
    assert exc.response_metadata["response_object_type"] == "FakeResponseObject"
    assert exc.response_metadata["response_model"] == "minimaxai/minimax-m3"
    assert exc.response_metadata["response_usage_present"] is False
    assert "choices" in exc.response_metadata["response_keys"]


def test_none_choices_is_response_structure_invalid(monkeypatch) -> None:
    response = FakeResponseObject(choices=None)

    exc = assert_strict_error(
        response,
        "response_structure_invalid",
        "NullChoicesError",
        monkeypatch,
    )

    assert "choices field was None" in exc.message


def test_missing_choices_attribute_is_response_structure_invalid(monkeypatch) -> None:
    response = FakeResponseObject()

    exc = assert_strict_error(
        response,
        "response_structure_invalid",
        "MissingChoicesError",
        monkeypatch,
    )

    assert "choices field" in exc.message


def test_choice_without_message_is_response_structure_invalid(monkeypatch) -> None:
    response = FakeResponseObject(choices=[FakeChoiceObject()])

    exc = assert_strict_error(
        response,
        "response_structure_invalid",
        "MissingMessageError",
        monkeypatch,
    )

    assert "message field" in exc.message
    assert exc.response_metadata["first_choice_finish_reason"] == "stop"
    assert exc.response_metadata["response_message_present"] is False


def test_message_content_none_is_response_content_missing(monkeypatch) -> None:
    response = FakeResponseObject(
        choices=[FakeChoiceObject(message=FakeMessageObject(content=None))]
    )

    exc = assert_strict_error(
        response,
        "response_content_missing",
        "MissingContentError",
        monkeypatch,
    )

    assert "content was missing" in exc.message
    assert exc.response_metadata["response_message_present"] is True
    assert exc.response_metadata["response_content_type"] == "NoneType"
    assert exc.response_metadata["response_content_length"] == 0


def test_message_content_empty_is_response_content_missing(monkeypatch) -> None:
    response = FakeResponseObject(
        choices=[FakeChoiceObject(message=FakeMessageObject(content=""))]
    )

    exc = assert_strict_error(
        response,
        "response_content_missing",
        "MissingContentError",
        monkeypatch,
    )

    assert "content was empty" in exc.message
    assert exc.response_metadata["response_content_type"] == "str"
    assert exc.response_metadata["response_content_length"] == 0


def test_reasoning_content_only_is_not_used_as_json(monkeypatch) -> None:
    response = FakeResponseObject(
        choices=[
            FakeChoiceObject(
                message=FakeMessageObject(
                    content="",
                    reasoning_content="thinking but no final json",
                )
            )
        ]
    )

    exc = assert_strict_error(
        response,
        "response_content_missing",
        "ReasoningOnlyResponseError",
        monkeypatch,
    )

    assert "reasoning_content is not used as JSON" in exc.message
    assert exc.response_metadata["response_has_reasoning_content"] is True
    assert exc.response_metadata["reasoning_content_length"] == len(
        "thinking but no final json"
    )


def test_finish_reason_length_is_recorded_when_content_missing(monkeypatch) -> None:
    response = FakeResponseObject(
        choices=[
            FakeChoiceObject(
                message=FakeMessageObject(content=""),
                finish_reason="length",
            )
        ]
    )

    exc = assert_strict_error(
        response,
        "response_content_missing",
        "MissingContentError",
        monkeypatch,
    )

    assert "finish_reason was length" in exc.message
    assert exc.response_metadata["first_choice_finish_reason"] == "length"


def test_normal_response_content_is_passed_to_parser(monkeypatch) -> None:
    response_text = json.dumps(
        {
            "articles": [
                {
                    "index": 0,
                    "korean_title": "삼성과 SK하이닉스의 HBM 투자 확대",
                    "preview": "",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Samsung", "HBM"],
                }
            ],
            "daily_trends": [],
        }
    )
    response = FakeResponseObject(
        choices=[
            FakeChoiceObject(
                message=FakeMessageObject(content=response_text),
                finish_reason="stop",
            )
        ],
        usage={"total_tokens": 1},
    )
    fake_openai_returning(monkeypatch, response=response)

    enhanced_articles, daily_trends = enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="nvidia-model",
        raise_on_error=True,
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert daily_trends == []


def test_api_call_exception_is_api_request_failed(monkeypatch) -> None:
    fake_openai_returning(monkeypatch, error=RuntimeError("network unavailable"))

    try:
        enhance_message_with_llm(
            [make_article()],
            api_key="api-key",
            model="nvidia-model",
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == "api_request_failed"
        assert exc.error_type == "RuntimeError"
    else:
        raise AssertionError("Expected LLMEnhancementError")


def test_response_extraction_error_is_not_api_request_failed(monkeypatch) -> None:
    response = FakeResponseObject(choices=[])

    exc = assert_strict_error(
        response,
        "response_structure_invalid",
        "EmptyChoicesError",
        monkeypatch,
    )

    assert exc.stage != "api_request_failed"


def test_non_strict_response_structure_error_preserves_fallback(monkeypatch) -> None:
    articles = [make_article()]
    response = FakeResponseObject(choices=[])
    fake_openai_returning(monkeypatch, response=response)

    enhanced_articles, daily_trends = enhance_message_with_llm(
        articles,
        api_key="api-key",
        model="nvidia-model",
    )

    assert enhanced_articles == articles
    assert daily_trends == []


def test_parse_message_enhancement_response_strict_json_error_has_excerpt() -> None:
    response_text = "```json {not valid json} ```"

    try:
        parse_message_enhancement_response(
            response_text,
            [make_article()],
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == "response_parse_failed"
        assert exc.error_type == "InvalidJSONError"
        assert "not valid JSON" in exc.message
        assert exc.response_excerpt == response_text
    else:
        raise AssertionError("Expected LLMEnhancementError")


def test_parse_message_enhancement_response_strict_empty_articles_fails() -> None:
    response_text = json.dumps({"articles": [], "daily_trends": []})

    try:
        parse_message_enhancement_response(
            response_text,
            [make_article()],
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == "response_parse_failed"
        assert exc.error_type == "NoParseableArticlesError"
        assert "parseable article entries" in exc.message
        assert exc.response_excerpt == response_text
    else:
        raise AssertionError("Expected LLMEnhancementError")
