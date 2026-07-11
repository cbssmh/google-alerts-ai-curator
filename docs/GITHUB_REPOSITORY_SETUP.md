# GitHub Repository Setup

This document describes the recommended public GitHub metadata for the 2.0
product identity. These settings are not changed by code commits or pushes; they
must be applied in the GitHub UI by a repository administrator.

## Recommended Repository Name

Recommended:

```text
google-alerts-ai-landscape
```

Alternatives:

- `ai-daily-landscape`
- `google-alerts-daily-landscape`
- `ai-news-landscape`

Why `google-alerts-ai-landscape` is the best fit:

- Keeps Google Alerts visible as the discovery source.
- Reflects the 2.0 product identity around Daily Landscape.
- Communicates the project direction more clearly than the old curator name.
- Avoids being too generic.

## Recommended About Description

```text
Rule-based AI news curation that turns daily Google Alerts into a grounded AI Landscape and reading-decision brief.
```

This description is short enough for GitHub About and avoids implying full
article understanding, market forecasting, or investment analysis.

## Recommended Topics

Use 8 to 12 topics. Recommended set:

- `python`
- `google-alerts`
- `telegram-bot`
- `llm`
- `nvidia-nim`
- `openai`
- `ai-news`
- `news-curation`
- `github-actions`
- `rule-based`
- `daily-briefing`
- `ai-landscape`

## Rename Steps

In GitHub:

1. Open the repository.
2. Go to **Settings**.
3. Go to **General**.
4. Find **Repository name**.
5. Enter:

   ```text
   google-alerts-ai-landscape
   ```

6. Click **Rename**.

## Local Remote Update

After the GitHub repository is renamed, update the local remote:

```bash
git remote set-url origin https://github.com/cbssmh/google-alerts-ai-landscape.git
git remote -v
```

## Post-Rename Checklist

- Confirm GitHub Actions still run.
- Confirm README links render correctly.
- Confirm internal documentation links work.
- Confirm the clone URL changed.
- Update external references to the old repository URL.
- Confirm GitHub Pages is not configured or does not need changes.
- Confirm there are no package or container registry references to update.
- Update the local `origin` remote.

## What a Push Does Not Change

`git push` can publish README and documentation changes. It does not change:

- Repository name.
- GitHub About description.
- Repository topics.
- Social preview image.

Those settings must be changed in GitHub.
