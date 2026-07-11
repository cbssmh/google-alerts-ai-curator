# Google Alerts AI Curator 2.0 Message Specification

## Purpose

The Telegram message exists to help the user understand today's selected AI news
batch and choose what to read within 10 seconds.

The message is not a news summary. It is a reading-decision surface. It should
show the observable repeated patterns in today's selected Google Alerts batch,
then make the best article links easy to scan and open.

The desired user action is:

1. Open the Telegram message.
2. Understand the visible shape of today's selected batch.
3. Identify one or more articles worth reading.
4. Open the source link when the article appears useful.

The message should never imply that the system read full article bodies or that
the selected batch represents the entire AI market.

## Reading Flow

The preferred reading flow is:

~~~text
Today's AI Landscape
        ↓
Repeated Themes
        ↓
Keywords
        ↓
Companies
        ↓
Selected Articles
        ↓
Open Link
~~~

This order moves from orientation to decision.

Today's AI Landscape tells the user what kind of batch they are looking at.
Repeated Themes show which topics appeared more than once. Keywords and
Companies provide recognition anchors. Selected Articles provide the actual
reading choices. The link is the final action, not the first cognitive burden.

The message should not start by listing several article titles when there is a
valid batch-level pattern. Starting with individual articles makes the user infer
the pattern manually, which is exactly the work the product should reduce.

## Information Hierarchy

| Layer | Name | Purpose | Display rule |
| --- | --- | --- | --- |
| Layer 1 | Today's AI Landscape | Give one-breath orientation for the selected batch. | Show only when grounded and non-empty. |
| Layer 2 | Themes | Show repeated topic groups across selected articles. | Show only specific multi-article themes. |
| Layer 3 | Keywords | Provide compact recognition anchors. | Show only grounded, non-generic terms. |
| Layer 4 | Companies | Identify visible companies, institutions, models, or products. | Show only source-grounded names. |
| Layer 5 | Articles | Help the user choose what to open. | Always show selected articles when a message is sent. |

Each layer must earn its place. If a layer has no valid content, the section is
hidden instead of being filled with generic text.

## Adaptive Behaviour

Adaptive behaviour defines how much message intelligence the system should use
for the current batch.

Rule-based selection always runs before message generation. LLM enhancement is
optional and should be used only when it can add grounded reader value. The
message should remain useful when no LLM provider is configured or when LLM
output fails validation.

| Case | LLM use | Landscape behaviour | Telegram message |
| --- | --- | --- | --- |
| 0 selected articles | Do not call LLM. | Not applicable. | Do not send an article briefing. Operational output may say "No high-signal articles selected." |
| 1 selected article | Optional for article enhancement if provider exists. | Do not show Landscape. | Show the single article card. |
| 2 selected articles | Optional for article enhancement if provider exists. | Do not show Landscape by default. | Show article cards unless a future product decision explicitly allows a two-article landscape. |
| 3 or more selected articles, no LLM provider | Do not call LLM. | Not available. | Show rule-based article cards. |
| 3 or more selected articles, LLM provider configured | Use one LLM call for landscape and article enhancement. | Attempt Landscape generation, then validate. | Show Landscape plus article cards if valid; otherwise article cards only. |
| LLM API failure | LLM call failed. | Hide Landscape. | Fall back to rule-based article cards. |
| LLM JSON parse failure | Treat enhancement as unavailable. | Hide Landscape. | Fall back according to existing parser and production policy. |
| Landscape invalid or empty | Keep valid article enhancement if available. | Hide invalid sections. | Show article cards only. |
| Theme missing | Keep other valid Landscape fields. | Hide Themes section. | Show headline, keywords, companies, and articles when valid. |
| Keyword missing | Keep other valid Landscape fields. | Hide Keywords section. | Show remaining valid sections. |
| Company missing | Keep other valid Landscape fields. | Hide Companies section. | Show remaining valid sections. |
| Preview missing | Keep the article. | Not affected. | Show title, optional Korean title, why selected, and link. |

This specification intentionally separates "LLM use" from "Landscape display."
The system may call the LLM for article-level enhancement, but the message should
display Landscape only when the current batch supports it.

### Adaptive Examples

~~~text
Input: 1 selected article
Output: Article card only
Reason: A single article cannot establish a repeated pattern.
~~~

~~~text
Input: 3 selected articles about HBM, GPU clusters, and data centers
Output: Landscape + Themes + Keywords + Companies + Article cards
Reason: The batch contains repeated infrastructure evidence.
~~~

~~~text
Input: 3 selected articles about unrelated topics
Output: Article cards only
Reason: A forced Landscape would be less honest than no Landscape.
~~~

## Today's AI Landscape

Today's AI Landscape is the optional top-level orientation layer.

Definition:

> The observable repeated patterns in today's selected Google Alerts articles.

It is not market analysis. It is not a statement about the entire AI industry.
It does not claim representativeness beyond the selected batch. It should read
like a careful observation, not like a forecast.

Allowed:

- A short headline grounded in multiple selected articles.
- Specific repeated themes.
- Source-grounded keywords.
- Source-grounded companies, institutions, products, or model names.

Not allowed:

- Market predictions.
- Investment implications.
- Career advice.
- Claims that require full article bodies.
- Claims about all AI news or the whole AI market.
- New facts not present in title, source, snippet, or rule-based reasons.

Recommended display:

~~~text
Today's AI Landscape

AI infrastructure and enterprise AI pricing appeared together in today's alerts.

Repeated Themes
- AI Infrastructure
- Enterprise Pricing

Keywords
HBM · GPU · API pricing

Companies
NVIDIA · Microsoft
~~~

## Themes

A Theme is a specific repeated topic group across selected articles.

Good Themes:

- AI Infrastructure
- Enterprise AI
- Regulation
- Funding
- Pricing
- Semiconductor Supply
- Model Release
- Developer Tooling

Bad Themes:

- AI
- Technology
- Industry
- Business
- News
- Updates

A valid Theme must be specific enough to help the user understand the batch. It
should be supported by multiple selected articles. The theme label should be
short, stable, and scannable.

### Theme Summary Visibility

| Option | Pros | Cons |
| --- | --- | --- |
| Show theme labels only | Fast scan, short message, low repetition. | Less context for ambiguous labels. |
| Show labels plus one-line summaries | More context, easier for first-time users. | Longer message and higher risk of repeating article previews. |
| Hide themes unless summaries are available | Avoids thin labels. | Misses useful orientation when labels are enough. |

Recommendation:

Show theme labels only in Telegram for 2.0. Keep theme summaries as internal
structured data for validation, testing, prompt tuning, and future UI surfaces.
This keeps the Telegram message short and avoids repeating article content.

## Keywords

Keywords provide quick recognition anchors for the batch.

They should help the user identify the specific technical or business terms that
appear in the selected articles. Keywords are not tags for broad taxonomy.

Allowed Keywords:

- Terms present in a selected article title or snippet.
- Technical terms such as `HBM`, `GPU`, `inference`, `API pricing`.
- Product or model terms when they appear in the source metadata.
- Repeated terms, or strong event terms from top selected articles.

Disallowed Keywords:

- Generic terms such as `AI`, `technology`, `company`, `industry`, `news`.
- Terms invented by the LLM.
- Terms that require full article body evidence.
- Duplicates caused by case, pluralization, or spacing differences.

Display rule:

- Maximum 6 keywords.
- Use compact separator text: `HBM · GPU · API pricing`.
- Do not add explanatory prose around keywords.

## Companies

Companies includes visible organizations, institutions, products, or model names
that help the user understand who appears in the selected batch.

Allowed:

- Companies: `NVIDIA`, `OpenAI`, `Microsoft`, `Samsung`.
- Institutions: `White House`, `FTC`, `EU`.
- Products or models: `ChatGPT`, `Gemini`, `Claude`, `Mistral`.
- Cloud, chip, or platform brands when present in the source metadata.

Disallowed:

- Generic roles such as `startup`, `chipmaker`, `cloud provider`.
- Organizations not present in title or snippet.
- Inferred parent companies unless the source metadata names them.
- Long lists of every entity in every article.

Display rule:

- Maximum 5 names.
- Prefer repeated entities.
- Allow a single-article entity only when it is central to a top selected
  article.

## Article Card

The Article Card is the reading-decision unit. Its structure should remain:

~~~text
Tier
Original Title

Korean Title

Preview

Why Selected
Reason

Link
~~~

### Original Title

Purpose:

- Preserve the source's actual framing.
- Let the user recognize the article.
- Avoid replacing source evidence with generated copy.

Rule:

- Always display.
- Preserve content.
- Escape for Telegram HTML.

### Korean Title

Purpose:

- Reduce scanning cost for Korean users.
- Clarify the source title without changing its meaning.

Rule:

- Optional.
- Short and grounded.
- Hide when empty or invalid.

### Preview

Purpose:

- Provide a short, grounded reason to consider opening the link.
- Help the user distinguish similar articles.

Rule:

- Optional.
- One sentence.
- Must be supported by title or snippet evidence.
- Hide when confidence is low or evidence validation fails.

### Why Selected

Purpose:

- Explain the deterministic signal in reader-facing language.
- Make rule-based selection transparent.

Rule:

- Prefer LLM-enhanced wording when validated.
- Fall back to rule-based reasons.
- Avoid internal category labels when possible.

### Link

Purpose:

- Preserve the article as the final action.
- Keep the product honest by sending the user to the source.

Rule:

- Always display when the article card is shown.
- Escape URL attributes for Telegram HTML.

## UI Wireframes

### Candidate A: Landscape First

~~~text
Today's AI Landscape

AI infrastructure and enterprise pricing appeared together in today's alerts.

Repeated Themes
- AI Infrastructure
- Enterprise Pricing

Keywords
HBM · GPU · API pricing

Companies
NVIDIA · Microsoft

━━━━━━━━━━━━━━

ESSENTIAL
Original article title

Korean title

Grounded preview sentence.

Why Selected
Reader-facing reason.

Read →
~~~

Pros:

- Best match for 2.0 philosophy.
- Gives the user the batch shape before individual links.
- Scales well when 3 to 5 articles are selected.

Cons:

- Slightly longer top section.
- Not useful when no valid repeated pattern exists.

### Candidate B: Article First

~~~text
ESSENTIAL
Original article title

Korean title

Grounded preview sentence.

Why Selected
Reader-facing reason.

Read →

━━━━━━━━━━━━━━

Today's AI Landscape
Repeated patterns...
~~~

Pros:

- Fast path to the first article.
- Familiar for a traditional news alert.

Cons:

- Makes the user infer the batch-level pattern late.
- Weakens "Patterns Before Articles".
- Landscape becomes a footnote instead of orientation.

### Candidate C: Compact

~~~text
Landscape: AI infrastructure + pricing
Themes: Infrastructure, Enterprise Pricing
Keywords: HBM · GPU · API pricing
Companies: NVIDIA · Microsoft

1. Original article title
   Korean title
   Read →

2. Original article title
   Korean title
   Read →
~~~

Pros:

- Very short.
- Useful for extremely frequent alerts.

Cons:

- Removes too much explanation from article cards.
- Makes "Why selected" harder to see.
- Less transparent about rule-based selection.

### Candidate D: Mobile First

~~~text
Today's AI Landscape
AI infrastructure and enterprise pricing appeared together.

Themes
- AI Infrastructure
- Enterprise Pricing

Keywords
HBM · GPU · API pricing

Articles

ESSENTIAL
Original article title
Korean title
Read →

RECOMMENDED
Original article title
Korean title
Read →
~~~

Pros:

- Strong for quick vertical scanning.
- Shorter than Candidate A.
- Reduces repeated blank space.

Cons:

- Preview and Why Selected may be hidden or compressed.
- Less helpful for deciding between similar articles.

### Recommended UI

Recommendation: Candidate A, with adaptive hiding.

Candidate A best expresses the product's 2.0 direction: understand the batch
first, then decide what to read. It should not appear as a rigid template. If
Landscape is empty, the message should collapse to article cards. If Keywords or
Companies are missing, those sections should disappear. If Preview is invalid,
the article card should still render without it.

This recommendation preserves both scanability and decision quality.

## Copywriting Rules

The copy should sound like a careful analyst describing visible evidence, not a
marketing page or a market forecast.

Preview should avoid repeated endings such as "기사입니다" because repeated
sentence shapes make multiple cards feel machine-generated and reduce
scanability. Different endings also help the user distinguish articles quickly.

Allowed style:

- "HBM and GPU capacity are both mentioned in the alert metadata."
- "Enterprise rollout and API pricing appear in the title and snippet."
- "The alert points to a concrete product release rather than broad commentary."

Disallowed style:

- "This article is important."
- "This is a must-read article."
- "The market will be reshaped."
- "Investors should watch this."
- "Developers need to learn this."
- "After reading the article, we can see..."

Rules:

- Do not exaggerate.
- Do not predict.
- Do not infer hidden intent.
- Do not imply full article access.
- Do not produce investment or career advice.
- Do not use the same sentence ending across every card when avoidable.
- Prefer empty output over unsupported fluency.

## LLM Responsibilities

The LLM may generate:

- Daily Landscape headline.
- Theme labels and internal summaries.
- Grounded keywords.
- Grounded companies, institutions, products, or model names.
- Korean titles.
- Previews.
- Reader-facing why-selected text.
- Confidence and evidence fields for validation.

The LLM must not generate:

- Article selection decisions.
- Article removal, merging, hiding, or reordering.
- Full article summaries.
- Market forecasts.
- Investment advice.
- Career advice.
- "Why it Matters" commentary.
- Entities or keywords absent from title or snippet.
- Claims based on external search or assumed article body content.

The LLM is a synthesis and wording layer. It is not the selector, crawler, or
source of truth.

## Message Length Budget

The message should fit a quick Telegram scan.

Recommended budget:

| Section | Budget |
| --- | --- |
| Landscape headline | 0 or 1 line, around 60 characters when possible. |
| Themes | 0 to 4 labels. |
| Keywords | 0 to 6 terms on one line. |
| Companies | 0 to 5 names on one line. |
| Articles | Usually 3 selected articles; up to 5 only with a separate product decision. |
| Article preview | 0 or 1 sentence per article. |
| Why Selected | 0 or 1 short reason per article. |

Soft maximum:

- Keep the full message under roughly 1200 to 1800 characters for routine runs.
- Avoid approaching Telegram's hard message limit.
- If message length grows, remove optional sections before weakening source
  links or article identity.

Priority under length pressure:

1. Preserve article title and link.
2. Preserve why-selected reason.
3. Preserve valid Landscape headline and theme labels.
4. Remove previews that add little distinction.
5. Remove keywords or companies if they are redundant.

## Failure Behaviour

The message should degrade by hiding invalid sections, not by filling them with
generic content.

| Failure | Behaviour |
| --- | --- |
| Landscape generation fails | Hide Landscape and show article cards. |
| LLM API fails | Use rule-based article cards. |
| LLM JSON is malformed | Follow existing parser policy; production should fall back. |
| Themes are empty | Hide Themes section. |
| Keywords are empty | Hide Keywords section. |
| Companies are empty | Hide Companies section. |
| Preview is empty or low confidence | Hide Preview for that article. |
| Korean title is empty | Show original title only. |
| Why Selected enhancement is empty | Fall back to rule-based reasons. |
| Article count changes | Treat enhancement as invalid; preserve original selected articles. |

Graceful degradation means the user still receives the best deterministic
reading-decision message the system can produce.

## Success Criteria

A good message succeeds when:

- The user understands the visible shape of today's selected AI news within 10
  seconds.
- The user can choose at least one article to open.
- The message does not require reading full article bodies to understand the
  topic area.
- The message does not overclaim beyond Google Alerts metadata.
- Optional sections disappear cleanly when unsupported.
- Article inclusion remains explainable through rule-based selection.
- The message feels compact enough to read in Telegram.

A message fails when:

- It reads like a generic AI market summary.
- It forces a pattern where none exists.
- It repeats the same preview structure on every article.
- It hides the source link behind generated commentary.
- It suggests investment, career, or future market conclusions.

## Future Evolution

### 2.1

Improve the message without changing the evidence boundary.

Possible work:

- Better section length tuning.
- More stable theme label vocabulary.
- Better copy variation rules for previews.
- More explicit smoke-test checks for hidden optional sections.

### 2.2

Improve adaptive presentation.

Possible work:

- Different display modes for 1 article, 2 articles, and 3 or more articles.
- More precise mobile-first spacing.
- Configurable article card verbosity.
- Better handling of multiple valid entities without long lists.

### 3.0

Expand only if the product intentionally expands its evidence boundary.

Possible work:

- Historical run comparison.
- Optional article-body reading with explicit source constraints.
- User feedback loops for read-worthiness.
- Separate surfaces beyond Telegram.

Any future version must preserve the core promise: the message may only claim
what the system's evidence can support.

## Specification Checklist

Before changing prompt, JSON schema, message builder, smoke tests, or README
examples, check the change against this specification:

1. Does it help the user decide what to read within 10 seconds?
2. Does it preserve the Landscape to Articles reading flow?
3. Does it hide unsupported sections instead of inventing content?
4. Does it keep rule-based selection as the article inclusion authority?
5. Does it avoid market prediction, investment advice, and career advice?
6. Does it stay grounded in title, source, snippet, and rule-based reasons?
7. Does it remain readable as a Telegram message on a phone?
