import re

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

OFFICIAL_SOURCE_NAMES = {
    "google blog",
    "openai blog",
    "anthropic blog",
    "nvidia blog",
    "microsoft blog",
}

EVENT_TYPE_CATEGORIES = [
    (
        "official_release",
        "공식 발표",
        2,
        (
            "launches",
            "releases",
            "announces",
            "introduces",
            "unveils",
            "rolls out",
            "preview",
            "beta",
            "ga",
            "available",
        ),
    ),
    (
        "pricing_cost",
        "가격 / 비용 변화",
        4,
        (
            "pricing",
            "price cut",
            "raises prices",
            "subscription",
            "paid tier",
            "cost",
            "margin",
            "inference cost",
            "api pricing",
            "cheaper",
            "budget",
            "usage cap",
        ),
    ),
    (
        "infrastructure_investment",
        "인프라 투자",
        4,
        (
            "data center",
            "datacenter",
            "capex",
            "buildout",
            "capacity expansion",
            "power grid",
            "cloud infrastructure",
            "gpu cluster",
            "infrastructure investment",
            "ai infrastructure",
        ),
    ),
    (
        "semiconductor_supply_chain",
        "반도체 공급망",
        4,
        (
            "chip",
            "chips",
            "semiconductor",
            "gpu",
            "hbm",
            "foundry",
            "fab",
            "wafer",
            "yield",
            "packaging",
            "cowos",
            "tsmc",
            "sk hynix",
            "samsung",
            "lithography",
            "node",
        ),
    ),
    (
        "government_regulation",
        "정부 / 규제",
        3,
        (
            "regulation",
            "policy",
            "law",
            "antitrust",
            "executive order",
            "white house",
            "eu ai act",
            "lawmakers",
            "ftc",
            "doj",
            "sovereign ai",
        ),
    ),
    (
        "developer_ecosystem",
        "개발자 생태계",
        4,
        (
            "api",
            "sdk",
            "documentation",
            "github",
            "open source",
            "release notes",
            "framework",
            "developer preview",
            "tooling",
            "app store",
            "marketplace",
        ),
    ),
    (
        "enterprise_adoption",
        "기업 도입",
        3,
        (
            "enterprise",
            "workplace",
            "copilot",
            "productivity",
            "workflow",
            "customer",
            "deployment",
            "rollout",
            "procurement",
        ),
    ),
    (
        "security_incident",
        "보안 사고",
        4,
        (
            "breach",
            "vulnerability",
            "exploit",
            "jailbreak",
            "prompt injection",
            "data exposure",
            "cve",
            "security flaw",
            "incident",
        ),
    ),
    (
        "product_platform_strategy",
        "제품 / 플랫폼 전략",
        3,
        (
            "operating system",
            "default integration",
            "distribution deal",
            "bundle",
            "partnership",
            "ecosystem",
            "app marketplace",
            "product strategy",
            "platform strategy",
        ),
    ),
    (
        "funding_ipo_ma",
        "투자 / IPO / M&A",
        4,
        (
            "funding",
            "valuation",
            "ipo",
            "market debut",
            "acquires",
            "merger",
            "stake",
            "investment round",
            "takeover",
        ),
    ),
]

EVENT_SCORE_ONLY_CATEGORIES = {
    "official_release",
    "pricing_cost",
    "infrastructure_investment",
    "semiconductor_supply_chain",
    "government_regulation",
    "security_incident",
    "product_platform_strategy",
    "funding_ipo_ma",
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
    (("top 10", "best tools", "ultimate guide", "things you need to know"), -3),
    (("fear", "fears", "scary", "terrifying", "anxiety", "emotional reaction"), -3),
    (("culture war", "backlash", "outrage", "panic"), -3),
    (("ai will take your job", "ai replacing jobs", "jobs panic"), -2),
    (("rumored", "reportedly", "may", "could", "might", "leak", "unconfirmed"), -2),
    (("stock to buy", "soars", "surges", "multibagger", "price target", "penny stock"), -4),
    (("coupon", "deal", "review", "vs", "alternative"), -2),
    (("shocking", "you won't believe"), -3),
)


def select_high_signal_articles(
    articles: list[Article],
    limit: int = 3,
) -> list[CuratedArticle]:
    scored_articles = []
    for article in articles:
        (
            score,
            source_name,
            signals,
            primary_signal,
            recommendation_reasons,
        ) = _score_article(article)
        if score >= 4:
            scored_articles.append(
                (
                    score,
                    article,
                    source_name,
                    signals,
                    primary_signal,
                    recommendation_reasons,
                )
            )

    scored_articles.sort(key=lambda item: item[0], reverse=True)

    return [
        CuratedArticle(
            title=article.title,
            source=article.source,
            url=article.url,
            snippet=article.snippet,
            relevance_score=score,
            why_selected=_build_why_selected(article, source_name, signals, primary_signal),
            korean_summary="본문 요약은 생성하지 않았습니다. 원문 제목과 링크를 기준으로 선별했습니다.",
            career_market_insight=_build_career_market_insight(primary_signal),
            recommendation_reasons=recommendation_reasons,
        )
        for (
            score,
            article,
            source_name,
            signals,
            primary_signal,
            recommendation_reasons,
        ) in scored_articles[:limit]
    ]


def _score_article(article: Article) -> tuple[int, str, list[str], str, list[str]]:
    text = " ".join([article.title, article.source, article.snippet]).lower()
    score = 0
    matched_source = ""
    matched_signals = []
    signal_scores: dict[str, int] = {}

    for title_pattern, points, category in TITLE_BOOSTS:
        if title_pattern.lower() in article.title.lower():
            score += points
            _add_signal_match(matched_signals, signal_scores, category, points)

    matched_source = _match_trusted_source(article.source)
    if matched_source:
        score += SOURCE_SCORES[matched_source]

    for category, points, keywords, label, _insight in SIGNAL_CATEGORIES:
        if any(keyword in text for keyword in keywords):
            score += points
            _add_signal_match(matched_signals, signal_scores, category, points)

    matched_event_types = _match_event_types(text, matched_source)
    for code, _label, points in matched_event_types:
        if code in EVENT_SCORE_ONLY_CATEGORIES:
            score += points

    for patterns, penalty in LOW_VALUE_PATTERNS:
        if any(_contains_pattern(text, pattern) for pattern in patterns):
            score += penalty

    if _is_question_headline(article.title):
        score -= 2

    primary_signal = _select_primary_signal(matched_signals, signal_scores)
    recommendation_reasons = _build_recommendation_reasons(
        matched_source,
        matched_event_types,
    )
    return score, matched_source, matched_signals, primary_signal, recommendation_reasons


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _add_signal_match(
    matched_signals: list[str],
    signal_scores: dict[str, int],
    category: str,
    points: int,
) -> None:
    _append_unique(matched_signals, category)
    signal_scores[category] = signal_scores.get(category, 0) + points


def _select_primary_signal(
    matched_signals: list[str],
    signal_scores: dict[str, int],
) -> str:
    if not matched_signals:
        return ""

    return max(matched_signals, key=lambda signal: signal_scores.get(signal, 0))


def _match_trusted_source(source_text: str) -> str:
    normalized_source = source_text.lower()
    for source in SOURCE_SCORES:
        if source in normalized_source:
            return source

    return ""


def _match_event_types(text: str, matched_source: str) -> list[tuple[str, str, int]]:
    matched_event_types = []
    for code, label, points, patterns in EVENT_TYPE_CATEGORIES:
        if any(_contains_pattern(text, pattern) for pattern in patterns):
            matched_event_types.append((code, label, points))

    if matched_source in OFFICIAL_SOURCE_NAMES:
        _append_event_type(matched_event_types, "official_release")

    return matched_event_types


def _append_event_type(
    matched_event_types: list[tuple[str, str, int]],
    code: str,
) -> None:
    if any(matched_code == code for matched_code, _label, _points in matched_event_types):
        return

    for event_code, label, points, _patterns in EVENT_TYPE_CATEGORIES:
        if event_code == code:
            matched_event_types.append((event_code, label, points))
            return


def _build_recommendation_reasons(
    matched_source: str,
    matched_event_types: list[tuple[str, str, int]],
    limit: int = 3,
) -> list[str]:
    reasons = []
    if matched_source:
        reasons.append("신뢰도 높은 출처")

    for _code, label, _points in sorted(
        matched_event_types,
        key=lambda event_type: event_type[2],
        reverse=True,
    ):
        _append_unique(reasons, label)
        if len(reasons) == limit:
            return reasons

    return reasons[:limit]


def _is_question_headline(title: str) -> bool:
    normalized_title = " ".join(title.split()).strip()
    headline_before_source = normalized_title.split(" | ", 1)[0].strip()
    return normalized_title.endswith("?") or headline_before_source.endswith("?")


def _contains_pattern(text: str, pattern: str) -> bool:
    if pattern == "may":
        return re.search(r"\bmay\b(?!\s+\d)", text) is not None

    escaped_pattern = re.escape(pattern.lower())
    escaped_pattern = escaped_pattern.replace(r"\ ", r"\s+")
    prefix = r"\b" if pattern[0].isalnum() else ""
    suffix = r"\b" if pattern[-1].isalnum() else ""
    return re.search(prefix + escaped_pattern + suffix, text) is not None


def _build_why_selected(
    article: Article,
    source_name: str,
    signals: list[str],
    primary_signal: str,
) -> str:
    reasons = []
    if source_name:
        reasons.append(f"신뢰도 높은 출처({article.source or source_name})")

    labels_by_category = {category: label for category, _points, _keywords, label, _insight in SIGNAL_CATEGORIES}
    if primary_signal:
        reasons.append(f"주요 신호: {labels_by_category[primary_signal]}")
        secondary_signals = [signal for signal in signals if signal != primary_signal]
        if secondary_signals:
            reasons.append(
                "보조 신호: "
                + " / ".join(labels_by_category[signal] for signal in secondary_signals)
            )

    evidence_source = "알림 요약" if article.snippet else "제목"
    evidence_text = _shorten_evidence(article.snippet or article.title)
    evidence = f"{evidence_source} 근거: {evidence_text}"

    interpretation = _build_primary_signal_interpretation(primary_signal)
    if not reasons:
        reasons.append("출처와 제목 기준의 전략적 검토 후보")

    return (
        " / ".join(reasons)
        + f". {evidence}. {interpretation}"
    )


def _build_career_market_insight(primary_signal: str) -> str:
    insights_by_category = {
        category: insight
        for category, _points, _keywords, _label, insight in SIGNAL_CATEGORIES
    }

    if primary_signal in insights_by_category:
        return insights_by_category[primary_signal]

    return "출처 신뢰도와 전략적 시장/기술 변화 가능성을 기준으로 선별했습니다."


def _build_primary_signal_interpretation(primary_signal: str) -> str:
    interpretations = {
        "platform_shift": "이는 AI 경쟁의 중심이 개별 기능보다 플랫폼 장악력과 개발자 생태계로 이동하는 신호일 수 있습니다.",
        "infrastructure": "이는 AI 수요가 모델 경쟁을 넘어 데이터센터, GPU, 전력, 클라우드 투자로 확장되는 신호일 수 있습니다.",
        "ecosystem_competition": "이는 소비자 AI와 기업 AI의 주도권이 모델 성능뿐 아니라 제품 생태계와 유통 채널 경쟁으로 이동하는 신호일 수 있습니다.",
        "enterprise": "이는 AI가 실험 단계를 넘어 업무 흐름과 기업 소프트웨어 구매 기준에 들어가는 신호일 수 있습니다.",
        "regulation": "이는 정부와 규제가 AI 시장의 속도, 책임 범위, 경쟁 구도에 직접 영향을 주기 시작했다는 신호일 수 있습니다.",
        "semiconductor": "이는 AI 경쟁의 병목이 알고리즘뿐 아니라 칩, 메모리, 공급망 역량으로 옮겨가는 신호일 수 있습니다.",
        "interface_shift": "이는 검색, 브라우저, 어시스턴트가 사용자의 정보 접근 방식과 AI 서비스 유통 경로를 바꾸는 신호일 수 있습니다.",
    }
    return interpretations.get(
        primary_signal,
        "이는 출처 신뢰도와 제목의 전략적 맥락을 기준으로 읽어볼 만한 후보입니다.",
    )


def _shorten_evidence(text: str, max_length: int = 160) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized

    return normalized[: max_length - 3].rstrip() + "..."


def score_to_stars(score: int) -> str:
    if score >= 12:
        return "⭐⭐⭐⭐⭐"

    if score >= 8:
        return "⭐⭐⭐⭐☆"

    return "⭐⭐⭐☆☆"
