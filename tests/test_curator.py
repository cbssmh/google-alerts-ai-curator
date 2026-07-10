import json
from types import SimpleNamespace

from src import curator
from src.curator import build_curator_prompt, curate_articles, parse_curator_response
from src.models import Article, CuratedArticle


def make_article(title: str = "AI infra news") -> Article:
    return Article(
        title=title,
        source="Example",
        url="https://example.com/article",
        snippet="A short article snippet.",
    )


def make_response(score: int = 9, count: int = 1) -> str:
    return json.dumps(
        {
            "articles": [
                {
                    "title": f"Article {index}",
                    "source": "Example",
                    "url": f"https://example.com/article-{index}",
                    "relevance_score": score,
                    "why_selected": "중요한 이유",
                    "korean_summary": "한국어 요약",
                    "career_market_insight": "커리어 및 시장 인사이트",
                }
                for index in range(count)
            ]
        }
    )


def test_prompt_contains_target_interests() -> None:
    prompt = build_curator_prompt([make_article()])

    assert "AI infrastructure" in prompt
    assert "Enterprise AI" in prompt
    assert "semiconductor trends" in prompt
    assert "quant / systematic investing" in prompt
    assert "cybersecurity" in prompt
    assert "global tech career trends" in prompt
    assert "Germany-related IT career opportunities if relevant" in prompt


def test_prompt_says_max_3() -> None:
    prompt = build_curator_prompt([make_article()])

    assert "maximum 3" in prompt


def test_prompt_says_score_at_least_8() -> None:
    prompt = build_curator_prompt([make_article()])

    assert "relevance_score >= 8" in prompt


def test_valid_json_parses_into_curated_article() -> None:
    articles = parse_curator_response(make_response())

    assert len(articles) == 1
    assert isinstance(articles[0], CuratedArticle)
    assert articles[0].title == "Article 0"
    assert articles[0].relevance_score == 9


def test_low_score_article_is_filtered_out() -> None:
    articles = parse_curator_response(make_response(score=7))

    assert articles == []


def test_invalid_json_returns_empty_list() -> None:
    assert parse_curator_response("not json") == []


def test_more_than_3_valid_articles_are_capped_at_3() -> None:
    articles = parse_curator_response(make_response(count=4))

    assert len(articles) == 3


def test_curate_articles_empty_articles_returns_empty_list() -> None:
    assert curate_articles([], api_key="secret") == []


def test_curate_articles_valid_mocked_response_returns_curated_articles(
    monkeypatch,
) -> None:
    class FakeCompletions:
        def create(self, model, messages):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=make_response())
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    monkeypatch.setattr(curator, "OpenAI", FakeOpenAI)

    articles = curate_articles([make_article()], api_key="secret")

    assert len(articles) == 1
    assert articles[0].title == "Article 0"


def test_curate_articles_uses_openai_compatible_base_url(monkeypatch) -> None:
    captured = {}

    class FakeCompletions:
        def create(self, model, messages):
            captured["model"] = model
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=make_response())
                    )
                ]
            )

    class FakeOpenAI:
        def __init__(self, api_key, base_url=None):
            captured["api_key"] = api_key
            captured["base_url"] = base_url
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    monkeypatch.setattr(curator, "OpenAI", FakeOpenAI)

    articles = curate_articles(
        [make_article()],
        api_key="nvapi-key",
        model="nvidia-model",
        base_url="https://integrate.api.nvidia.com/v1",
    )

    assert len(articles) == 1
    assert captured == {
        "api_key": "nvapi-key",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia-model",
    }


def test_curate_articles_api_exception_returns_empty_list(monkeypatch) -> None:
    class FakeCompletions:
        def create(self, model, messages):
            raise RuntimeError("API failed")

    class FakeOpenAI:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(
                completions=FakeCompletions(),
            )

    monkeypatch.setattr(curator, "OpenAI", FakeOpenAI)

    assert curate_articles([make_article()], api_key="secret") == []
