import json

from src import message_enhancer as message_enhancer_module
from src.message_enhancer import (
    LLMEnhancementError,
    build_message_enhancement_prompt,
    enhance_message_with_llm,
    parse_message_enhancement_response,
)
from src.models import CuratedArticle, DailyLandscape, TrendTheme


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


def make_infrastructure_articles() -> list[CuratedArticle]:
    return [
        make_article(
            title="NVIDIA GPU demand lifts cloud infrastructure spending",
            snippet=(
                "NVIDIA GPU demand is increasing cloud infrastructure "
                "spending for enterprise AI deployments."
            ),
            url="https://example.com/one",
        ),
        make_article(
            title="Samsung HBM supply expands for enterprise AI data centers",
            snippet=(
                "Samsung HBM and GPU supply are tied to enterprise AI "
                "data center investment."
            ),
            url="https://example.com/two",
        ),
        make_article(
            title="OpenAI API pricing update targets enterprise customers",
            snippet=(
                "OpenAI API pricing changes mention enterprise customers "
                "and inference cost."
            ),
            url="https://example.com/three",
        ),
    ]


def valid_enhancement_response_text() -> str:
    return json.dumps(
        {
            "landscape": {
                "headline": "AI 인프라 투자와 기업 AI 관련 소식이 함께 나타났습니다.",
                "themes": [
                    {
                        "label": "AI 인프라 투자",
                        "article_indices": [0, 1],
                        "summary": "GPU와 HBM, 데이터센터 투자 관련 소식이 함께 나타났습니다.",
                    }
                ],
                "keywords": ["GPU", "enterprise AI"],
                "entities": ["NVIDIA", "Samsung"],
            },
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
        }
    )


def response_with_landscape(landscape) -> str:
    return json.dumps(
        {
            "landscape": landscape,
            "articles": [
                {
                    "index": 0,
                    "korean_title": "엔비디아 GPU 수요와 인프라 투자",
                    "preview": "",
                    "why_selected": "인프라 투자 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["NVIDIA", "GPU"],
                },
                {
                    "index": 1,
                    "korean_title": "삼성 HBM 공급과 데이터센터 투자",
                    "preview": "",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Samsung", "HBM"],
                },
                {
                    "index": 2,
                    "korean_title": "오픈AI API 가격 변화",
                    "preview": "",
                    "why_selected": "가격 변화와 기업 도입 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["OpenAI", "API pricing"],
                },
            ],
        }
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


def successful_response() -> FakeResponseObject:
    return FakeResponseObject(
        choices=[
            FakeChoiceObject(
                message=FakeMessageObject(
                    content=valid_enhancement_response_text()
                )
            )
        ]
    )


def fake_openai_capturing_create_kwargs(monkeypatch, captured_create_kwargs):
    class FakeCompletions:
        def create(self, **kwargs):
            captured_create_kwargs.update(kwargs)
            return successful_response()

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

    assert "You only see Google Alerts metadata, not full article bodies." in prompt
    assert "Use only title, source, snippet, and rule_based_reasons." in prompt
    assert "Do not claim to have read the article." in prompt
    assert "If there is not enough evidence, return an empty string for preview." in prompt
    assert "Output strict JSON only." in prompt
    assert "Do not wrap JSON in Markdown fences." in prompt
    assert "Do not write market forecasts." in prompt
    assert "Do not write investment advice." in prompt
    assert "Do not write developer career advice or career insight." in prompt
    assert "Do not invent facts, numbers, causes, outcomes, companies, keywords, or entities." in prompt
    assert (
        "Evidence must contain only words that appear in the original title or snippet."
        in prompt
    )
    assert "A daily theme must be supported by multiple articles." in prompt
    assert "Every theme article index must exist in the input." in prompt
    assert "Keywords and entities must appear in the source title or snippet." in prompt
    assert "Semantic deduplication is disabled for this release." in prompt
    assert "Do not remove, merge, hide, or reorder articles." in prompt
    assert "Return every article index exactly once." in prompt
    assert "Leave duplicate handling to the existing URL and rule-based steps." in prompt


def test_prompt_guides_operational_message_ux_tuning() -> None:
    prompt = build_message_enhancement_prompt([make_article()])

    assert (
        "why_selected must explain what this article shows within today's selected batch"
        in prompt
    )
    assert "not just why a keyword matched" in prompt
    assert (
        "connect why_selected to the most relevant observable theme"
        in prompt
    )
    assert (
        "If landscape is empty, explain the rule-based reason in reader-friendly Korean."
        in prompt
    )
    assert "키워드로 선택됐습니다" in prompt
    assert "preview must not simply repeat the title." in prompt
    assert "preview should avoid generic endings" in prompt
    assert "소개됐습니다" in prompt
    assert "preview must not add causality, market impact, or future implications" in prompt
    assert "korean_title must not use sensational wording" in prompt
    assert "Prefer a natural Korean noun phrase over literal translation." in prompt
    assert "핫 코너" in prompt
    assert "Preserve companies, numbers, and event type when source-grounded." in prompt


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
            "landscape": {},
        }
    )

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert len(enhanced_articles) == 1
    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert enhanced_articles[0].preview == "삼성과 SK하이닉스의 HBM 투자 확대를 다룬 기사입니다."
    assert enhanced_articles[0].enhanced_why_selected == "반도체 공급망과 인프라 투자 신호가 함께 나타난 기사입니다."
    assert enhanced_articles[0].confidence == "high"
    assert enhanced_articles[0].evidence == ["Samsung", "HBM", "investment"]
    assert landscape.is_empty()


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
            "landscape": {},
        }
    )

    enhanced_articles, _landscape = parse_message_enhancement_response(
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
            "landscape": {},
        }
    )

    enhanced_articles, _landscape = parse_message_enhancement_response(
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
            "landscape": {},
        }
    )

    enhanced_articles, _landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert [article.url for article in enhanced_articles] == [
        "https://example.com/one",
        "https://example.com/two",
    ]
    assert enhanced_articles[0].enhanced_why_selected == "중복 사건의 대표 기사입니다."
    assert enhanced_articles[1].enhanced_why_selected == ""


def test_landscape_is_parsed_from_multiple_articles() -> None:
    articles = make_infrastructure_articles()
    response = json.dumps(
        {
            "landscape": {
                "headline": "AI 인프라 투자와 기업 AI 관련 소식이 함께 나타났습니다.",
                "themes": [
                    {
                        "label": "AI 인프라 투자",
                        "article_indices": [0, 1],
                        "summary": "GPU와 HBM, 데이터센터 투자 관련 소식이 함께 나타났습니다.",
                    },
                    {
                        "label": "기업 AI 도입",
                        "article_indices": [0, 2],
                        "summary": "enterprise AI와 고객 도입 관련 표현이 함께 나타났습니다.",
                    },
                ],
                "keywords": ["GPU", "Enterprise AI", "inference"],
                "entities": ["NVIDIA", "Samsung", "OpenAI"],
            },
            "articles": [
                {
                    "index": 0,
                    "korean_title": "엔비디아 GPU 수요와 인프라 투자",
                    "preview": "",
                    "why_selected": "반도체 공급망 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["NVIDIA", "GPU"],
                },
                {
                    "index": 1,
                    "korean_title": "삼성 HBM 공급과 데이터센터 투자",
                    "preview": "",
                    "why_selected": "기업 도입과 가격 변화 신호가 나타난 기사입니다.",
                    "confidence": "medium",
                    "evidence": ["Samsung", "HBM"],
                },
            ],
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert landscape.headline == "AI 인프라 투자와 기업 AI 관련 소식이 함께 나타났습니다."
    assert landscape.themes == [
        TrendTheme(
            label="AI 인프라 투자",
            article_indices=[0, 1],
            summary="GPU와 HBM, 데이터센터 투자 관련 소식이 함께 나타났습니다.",
        ),
        TrendTheme(
            label="기업 AI 도입",
            article_indices=[0, 2],
            summary="enterprise AI와 고객 도입 관련 표현이 함께 나타났습니다.",
        ),
    ]
    assert landscape.keywords == ["GPU", "Enterprise AI", "inference"]
    assert landscape.entities == ["NVIDIA", "Samsung", "OpenAI"]


def test_missing_landscape_keeps_article_enhancement() -> None:
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
                }
            ]
        }
    )

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        [make_article()],
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert landscape.is_empty()


def test_invalid_landscape_shapes_are_removed() -> None:
    articles = make_infrastructure_articles()
    response = response_with_landscape(
        {
            "headline": ["not a string"],
            "themes": "not a list",
            "keywords": "GPU",
            "entities": "NVIDIA",
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert landscape.is_empty()


def test_landscape_theme_validation_removes_invalid_indices_and_singletons() -> None:
    articles = make_infrastructure_articles()
    response = response_with_landscape(
        {
            "headline": "AI 인프라 관련 소식이 함께 나타났습니다.",
            "themes": [
                {
                    "label": "AI 인프라 투자",
                    "article_indices": [0, 1, 99, 1, -1, True],
                    "summary": "GPU와 HBM 관련 보도가 함께 나타났습니다.",
                },
                {
                    "label": "기업 AI 도입",
                    "article_indices": [2],
                    "summary": "단일 기사만 포함된 주제입니다.",
                },
                {
                    "label": "AI",
                    "article_indices": [0, 1],
                    "summary": "너무 넓은 주제입니다.",
                },
            ],
            "keywords": [],
            "entities": [],
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert landscape.themes == [
        TrendTheme(
            label="AI 인프라 투자",
            article_indices=[0, 1],
            summary="GPU와 HBM 관련 보도가 함께 나타났습니다.",
        )
    ]


def test_landscape_limits_themes_keywords_and_entities() -> None:
    articles = make_infrastructure_articles()
    response = response_with_landscape(
        {
            "headline": "AI 인프라와 기업 도입 관련 소식이 함께 나타났습니다.",
            "themes": [
                {"label": "AI 인프라 투자", "article_indices": [0, 1], "summary": ""},
                {"label": "기업 AI 도입", "article_indices": [0, 2], "summary": ""},
                {"label": "모델 가격과 비용", "article_indices": [0, 2], "summary": ""},
                {"label": "반도체 공급망", "article_indices": [0, 1], "summary": ""},
                {"label": "정부 규제", "article_indices": [1, 2], "summary": ""},
            ],
            "keywords": [
                "GPU",
                "HBM",
                "enterprise AI",
                "data center",
                "API pricing",
                "inference",
                "cloud infrastructure",
            ],
            "entities": ["NVIDIA", "Samsung", "OpenAI", "GPU", "HBM", "API"],
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert [theme.label for theme in landscape.themes] == [
        "AI 인프라 투자",
        "기업 AI 도입",
        "모델 가격과 비용",
        "반도체 공급망",
    ]
    assert landscape.keywords == [
        "GPU",
        "HBM",
        "enterprise AI",
        "data center",
        "API pricing",
        "inference",
    ]
    assert landscape.entities == ["NVIDIA", "Samsung", "OpenAI", "GPU", "HBM"]


def test_landscape_removes_ungrounded_and_duplicate_terms() -> None:
    articles = make_infrastructure_articles()
    response = response_with_landscape(
        {
            "headline": "AI 인프라 관련 소식이 함께 나타났습니다.",
            "themes": [],
            "keywords": ["GPU", "gpu", "GPUs", "future moat", "AI"],
            "entities": ["NVIDIA", "nvidia", "Anthropic", "company"],
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert landscape.keywords == ["GPU"]
    assert landscape.entities == ["NVIDIA"]


def test_landscape_headline_requires_multiple_articles() -> None:
    response = json.dumps(
        {
            "landscape": {
                "headline": "AI 인프라 관련 소식이 함께 나타났습니다.",
                "themes": [],
                "keywords": ["HBM"],
                "entities": ["Samsung"],
            },
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
        }
    )

    _enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        [make_article()],
    )

    assert landscape.headline == ""
    assert landscape.themes == []
    assert landscape.keywords == ["HBM"]
    assert landscape.entities == ["Samsung"]


def test_json_code_fenced_response_is_parsed() -> None:
    articles = [make_article()]
    response = f"""```json
{valid_enhancement_response_text()}
```"""

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert isinstance(landscape, DailyLandscape)


def test_plain_code_fenced_response_is_parsed() -> None:
    articles = [make_article()]
    response = f"""```
{valid_enhancement_response_text()}
```"""

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        articles,
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert isinstance(landscape, DailyLandscape)


def test_pure_json_response_is_still_parsed() -> None:
    articles = [make_article()]

    enhanced_articles, landscape = parse_message_enhancement_response(
        valid_enhancement_response_text(),
        articles,
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert isinstance(landscape, DailyLandscape)


def test_prefaced_json_is_rejected_without_repair() -> None:
    response = f"""Here is JSON

{valid_enhancement_response_text()}"""

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        [make_article()],
    )

    assert enhanced_articles == []
    assert landscape.is_empty()


def test_result_prefaced_json_is_rejected_without_repair() -> None:
    response = f"""Result:

{valid_enhancement_response_text()}"""

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        [make_article()],
    )

    assert enhanced_articles == []
    assert landscape.is_empty()


def test_code_fenced_malformed_json_fails_without_repair() -> None:
    response = """```json
{"articles": [{"index": 0,}], "landscape": {}}
```"""

    enhanced_articles, landscape = parse_message_enhancement_response(
        response,
        [make_article()],
    )

    assert enhanced_articles == []
    assert landscape.is_empty()


def test_strict_code_fenced_malformed_json_keeps_parse_error() -> None:
    response = """```json
{"articles": [{"index": 0,}], "landscape": {}}
```"""

    try:
        parse_message_enhancement_response(
            response,
            [make_article()],
            raise_on_error=True,
        )
    except LLMEnhancementError as exc:
        assert exc.stage == "response_parse_failed"
        assert exc.error_type == "InvalidJSONError"
        assert "not valid JSON" in exc.message
        assert (
            exc.response_excerpt
            == '```json {"articles": [{"index": 0,}], "landscape": {}} ```'
        )
    else:
        raise AssertionError("Expected LLMEnhancementError")


def test_non_strict_code_fenced_malformed_json_preserves_fallback(
    monkeypatch,
) -> None:
    articles = [make_article()]
    response = FakeResponseObject(
        choices=[
            FakeChoiceObject(
                message=FakeMessageObject(
                    content="""```json
{"articles": [{"index": 0,}], "landscape": {}}
```"""
                )
            )
        ]
    )
    fake_openai_returning(monkeypatch, response=response)

    enhanced_articles, landscape = enhance_message_with_llm(
        articles,
        api_key="api-key",
        model="nvidia-model",
    )

    assert enhanced_articles == articles
    assert landscape.is_empty()


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
                        "landscape": {},
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

    enhanced_articles, _landscape = enhance_message_with_llm(
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


def test_minimax_m3_request_uses_nvidia_build_defaults(monkeypatch) -> None:
    captured_create_kwargs = {}
    fake_openai_capturing_create_kwargs(monkeypatch, captured_create_kwargs)

    enhanced_articles, _landscape = enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="minimaxai/minimax-m3",
        provider="nvidia",
        raise_on_error=True,
    )

    assert captured_create_kwargs["model"] == "minimaxai/minimax-m3"
    assert captured_create_kwargs["max_tokens"] == 2048
    assert captured_create_kwargs["temperature"] == 0.2
    assert captured_create_kwargs["stream"] is False
    assert captured_create_kwargs["extra_body"] == {
        "chat_template_kwargs": {
            "thinking_mode": "disabled",
        }
    }
    assert "top_p" not in captured_create_kwargs
    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"


def test_openai_provider_does_not_receive_minimax_extra_body(monkeypatch) -> None:
    captured_create_kwargs = {}
    fake_openai_capturing_create_kwargs(monkeypatch, captured_create_kwargs)

    enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="gpt-test",
        provider="openai",
        raise_on_error=True,
    )

    assert captured_create_kwargs["model"] == "gpt-test"
    assert "extra_body" not in captured_create_kwargs
    assert "max_tokens" not in captured_create_kwargs
    assert "temperature" not in captured_create_kwargs
    assert "stream" not in captured_create_kwargs


def test_other_nvidia_model_uses_base_kwargs_without_minimax_extra_body(
    monkeypatch,
) -> None:
    captured_create_kwargs = {}
    fake_openai_capturing_create_kwargs(monkeypatch, captured_create_kwargs)

    enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="meta/llama-test",
        provider="nvidia",
        raise_on_error=True,
    )

    assert captured_create_kwargs["model"] == "meta/llama-test"
    assert captured_create_kwargs["max_tokens"] == 2048
    assert captured_create_kwargs["temperature"] == 0.2
    assert captured_create_kwargs["stream"] is False
    assert "extra_body" not in captured_create_kwargs
    assert "top_p" not in captured_create_kwargs


def test_enhance_message_with_llm_preserves_fallback_on_api_error(monkeypatch) -> None:
    articles = [make_article()]

    class FakeOpenAI:
        def __init__(self, **kwargs):
            pass

        @property
        def chat(self):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr(message_enhancer_module, "OpenAI", FakeOpenAI)

    enhanced_articles, landscape = enhance_message_with_llm(
        articles,
        api_key="api-key",
        model="nvidia-model",
    )

    assert enhanced_articles == articles
    assert landscape.is_empty()


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
            "landscape": {},
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

    enhanced_articles, landscape = enhance_message_with_llm(
        [make_article()],
        api_key="api-key",
        model="nvidia-model",
        raise_on_error=True,
    )

    assert enhanced_articles[0].korean_title == "삼성과 SK하이닉스의 HBM 투자 확대"
    assert landscape.is_empty()


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

    enhanced_articles, landscape = enhance_message_with_llm(
        articles,
        api_key="api-key",
        model="nvidia-model",
    )

    assert enhanced_articles == articles
    assert landscape.is_empty()


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
    response_text = json.dumps({"articles": [], "landscape": {}})

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
