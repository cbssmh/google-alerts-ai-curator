from src.models import Article, CuratedArticle


SOURCE_SCORES = {
    "reuters": 4,
    "bloomberg": 4,
    "financial times": 4,
    "wall street journal": 4,
    "the information": 4,
    "new york times": 4,
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

SIGNAL_CATEGORIES = [
    (
        "career",
        4,
        ("layoffs", "hiring", "jobs", "workforce", "restructuring"),
        "채용/인력 구조 변화",
        "AI 확산이 채용 구조와 개발자 역할 변화에 영향을 줄 가능성이 있습니다.",
    ),
    (
        "infrastructure",
        4,
        ("data center", "datacenter", "gpu", "nvidia", "inference", "cloud infrastructure"),
        "AI 인프라",
        "AI 인프라 수요가 데이터센터, GPU, 클라우드 운영 역량의 가치를 높이고 있습니다.",
    ),
    (
        "enterprise",
        3,
        ("enterprise", "workplace", "productivity", "agent", "copilot", "gemini"),
        "기업용 AI/생산성",
        "기업용 AI 도입은 백엔드, 자동화, 워크플로우 통합 역량 수요와 연결됩니다.",
    ),
    (
        "semiconductor",
        4,
        ("semiconductor", "chip", "foundry", "tsmc", "samsung", "sk hynix", "memory"),
        "반도체 공급망",
        "AI 경쟁이 반도체 공급망과 메모리/GPU 생태계의 중요성을 키우고 있습니다.",
    ),
    (
        "cybersecurity",
        3,
        ("cybersecurity", "breach", "ransomware", "vulnerability"),
        "사이버보안",
        "AI 시대에는 보안 자동화, 취약점 대응, 인프라 방어 역량의 중요성이 커집니다.",
    ),
    (
        "germany",
        4,
        ("germany", "berlin", "munich", "eu blue card", "visa"),
        "독일/EU 커리어 이동성",
        "독일·EU 관련 변화는 글로벌 IT 커리어 이동성과 연결될 수 있습니다.",
    ),
    (
        "regulation",
        3,
        ("regulation", "policy", "antitrust", "government"),
        "정책/규제",
        "정책과 규제 변화는 AI 제품 전략, 시장 진입, 컴플라이언스 역량 수요에 영향을 줄 수 있습니다.",
    ),
]

LOW_VALUE_PATTERNS = (
    (("celebrity", "viral", "meme", "funny", "rumor"), -3),
    (("top 10", "things you need to know"), -2),
)


def select_high_signal_articles(
    articles: list[Article],
    limit: int = 3,
) -> list[CuratedArticle]:
    scored_articles = []
    for article in articles:
        score, source_name, signals = _score_article(article)
        if score >= 5:
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

    return " / ".join(reasons) + " 신호가 있어 우선 검토 대상으로 선정했습니다."


def _build_career_market_insight(signals: list[str]) -> str:
    insights_by_category = {
        category: insight
        for category, _points, _keywords, _label, insight in SIGNAL_CATEGORIES
    }

    for category, _points, _keywords, _label, _insight in SIGNAL_CATEGORIES:
        if category in signals:
            return insights_by_category[category]

    return "출처 신뢰도와 구조적 중요도를 기준으로 선별했습니다."
