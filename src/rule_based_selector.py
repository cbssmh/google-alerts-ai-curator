from src.models import Article, CuratedArticle


SOURCE_SCORES = {
    "reuters": 4,
    "bloomberg": 4,
    "financial times": 4,
    "wall street journal": 4,
    "the information": 4,
    "new york times": 4,
    "the economist": 4,
    "time": 3,
    "the washington post": 3,
    "google blog": 3,
    "openai blog": 3,
    "anthropic blog": 3,
    "nvidia blog": 3,
    "microsoft blog": 3,
    "techcrunch": 2,
    "the verge": 2,
    "wired": 2,
    "mit technology review": 2,
}

TITLE_BOOSTS = (
    ("AI search", 5, "interface_shift"),
    ("AI order", 5, "regulation"),
    ("executive order", 5, "regulation"),
    ("White House", 5, "regulation"),
    ("dethroning OpenAI", 5, "ecosystem_competition"),
    ("Google I/O", 4, "platform_shift"),
    ("ecosystem", 4, "ecosystem_competition"),
    ("operating system", 4, "platform_shift"),
    ("infrastructure", 4, "infrastructure"),
    ("chips", 4, "semiconductor"),
)

SIGNAL_CATEGORIES = [
    (
        "platform_shift",
        4,
        (
            "platform",
            "operating system",
            "marketplace",
            "app store",
            "developer ecosystem",
            "api",
            "sdk",
            "foundation model",
        ),
        "Platform Shift",
        "플랫폼 지형 변화는 생태계 주도권, 유통 경로, 개발자와 기업의 기술 선택 기준을 바꿀 수 있습니다.",
    ),
    (
        "infrastructure",
        4,
        (
            "data center",
            "datacenter",
            "gpu",
            "nvidia",
            "inference",
            "cloud infrastructure",
            "capacity",
            "power grid",
        ),
        "AI Infrastructure",
        "AI 인프라 확장은 데이터센터, GPU, 전력, 클라우드 공급망 전반의 투자 우선순위를 바꾸고 있습니다.",
    ),
    (
        "ecosystem_competition",
        4,
        (
            "competition",
            "compete",
            "rival",
            "partnership",
            "ecosystem",
            "alliance",
            "distribution",
        ),
        "Ecosystem Competition",
        "생태계 경쟁은 모델, 클라우드, 반도체, 애플리케이션 기업 간 협력과 수익 배분 구조를 흔들 수 있습니다.",
    ),
    (
        "enterprise",
        3,
        ("enterprise", "workplace", "productivity", "agent", "copilot", "gemini", "workflow"),
        "Enterprise Adoption",
        "기업용 AI 도입은 업무 프로세스, 소프트웨어 구매 기준, 자동화 시장의 경쟁 축을 바꾸고 있습니다.",
    ),
    (
        "regulation",
        3,
        (
            "regulation",
            "policy",
            "antitrust",
            "government",
            "lawmakers",
            "eu ai act",
            "state-backed",
            "sovereign",
        ),
        "Government / Regulation",
        "정부와 규제의 개입은 AI 시장의 진입 장벽, 제품 출시 속도, 글로벌 확장 전략을 좌우할 수 있습니다.",
    ),
    (
        "semiconductor",
        4,
        ("semiconductor", "chip", "chips", "foundry", "tsmc", "samsung", "sk hynix", "memory"),
        "Semiconductor Race",
        "반도체 경쟁은 AI 성능, 비용 구조, 공급망 협상력의 핵심 변수가 되고 있습니다.",
    ),
    (
        "interface_shift",
        3,
        (
            "search",
            "browser",
            "interface",
            "assistant",
            "chatbot",
            "answer engine",
            "ai overview",
        ),
        "AI Interface Shift",
        "검색, 브라우저, 어시스턴트 인터페이스 변화는 사용자가 정보와 소프트웨어를 소비하는 경로를 바꿀 수 있습니다.",
    ),
]

LOW_VALUE_PATTERNS = (
    (("celebrity", "viral", "meme", "funny", "rumor"), -3),
    (("top 10", "things you need to know"), -2),
    (("fear", "scary", "terrifying", "anxiety", "emotional reaction"), -3),
    (("culture war", "backlash", "outrage", "panic"), -3),
    (("ai will take your job", "ai replacing jobs", "jobs panic"), -2),
)


def select_high_signal_articles(
    articles: list[Article],
    limit: int = 3,
) -> list[CuratedArticle]:
    scored_articles = []
    for article in articles:
        score, source_name, signals = _score_article(article)
        if score >= 4:
            scored_articles.append((score, article, source_name, signals))

    scored_articles.sort(key=lambda item: item[0], reverse=True)

    return [
        CuratedArticle(
            title=article.title,
            source=article.source,
            url=article.url,
            snippet=article.snippet,
            relevance_score=score,
            why_selected=_build_why_selected(source_name, signals),
            korean_summary="본문 요약은 생성하지 않았습니다. 원문 제목과 링크를 기준으로 선별했습니다.",
            career_market_insight=_build_career_market_insight(signals),
        )
        for score, article, source_name, signals in scored_articles[:limit]
    ]


def _score_article(article: Article) -> tuple[int, str, list[str]]:
    text = " ".join([article.title, article.source, article.snippet]).lower()
    score = 0
    matched_source = ""
    matched_signals = []

    for title_pattern, points, category in TITLE_BOOSTS:
        if title_pattern.lower() in article.title.lower():
            score += points
            if category not in matched_signals:
                matched_signals.append(category)

    for source, source_score in SOURCE_SCORES.items():
        if source in article.source.lower() or source in text:
            score += source_score
            matched_source = source
            break

    for category, points, keywords, label, _insight in SIGNAL_CATEGORIES:
        if any(keyword in text for keyword in keywords):
            score += points
            matched_signals.append(category)

    for patterns, penalty in LOW_VALUE_PATTERNS:
        if any(pattern in text for pattern in patterns):
            score += penalty

    return score, matched_source, matched_signals


def _build_why_selected(source_name: str, signals: list[str]) -> str:
    reasons = []
    if source_name:
        reasons.append(f"신뢰도 높은 출처({source_name})")

    labels_by_category = {category: label for category, _points, _keywords, label, _insight in SIGNAL_CATEGORIES}
    reasons.extend(labels_by_category[signal] for signal in signals)

    return (
        " / ".join(reasons)
        + " 신호가 있습니다. 이 흐름은 AI 시장의 경쟁 구도와 기술 채택 방향을 바꿀 수 있어 중요합니다."
    )


def _build_career_market_insight(signals: list[str]) -> str:
    insights_by_category = {
        category: insight
        for category, _points, _keywords, _label, insight in SIGNAL_CATEGORIES
    }

    for category, _points, _keywords, _label, _insight in SIGNAL_CATEGORIES:
        if category in signals:
            return insights_by_category[category]

    return "출처 신뢰도와 전략적 시장/기술 변화 가능성을 기준으로 선별했습니다."
