from __future__ import annotations

import re
from dataclasses import dataclass
from math import log1p
from typing import Any


CATEGORY_KEYWORDS = {
    "ai_ml_data": [
        "ai",
        "ml",
        "machine learning",
        "deep learning",
        "llm",
        "rag",
        "agent",
        "langchain",
        "vector",
        "embedding",
        "transformer",
        "neural",
        "model",
        "pytorch",
        "tensorflow",
        "deepseek",
        "openai",
        "anthropic",
        "claude",
        "ollama",
        "assistant",
        "chatbot",
        "inference",
        "generative",
        "coding agent",
        "dataset",
        "benchmark",
    ],
    "developer_tools": [
        "cli",
        "sdk",
        "tool",
        "devtool",
        "plugin",
        "extension",
        "linter",
        "formatter",
        "build",
        "package manager",
        "compiler",
        "debugger",
        "terminal",
        "tui",
        "ide",
        "editor",
        "coding",
        "codegen",
    ],
    "infra_devops": [
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "helm",
        "ci",
        "cd",
        "deploy",
        "cloud",
        "aws",
        "gcp",
        "azure",
        "monitoring",
        "observability",
    ],
    "security_privacy": [
        "security",
        "privacy",
        "auth",
        "oauth",
        "jwt",
        "encryption",
        "vault",
        "scanner",
        "vulnerability",
        "cve",
        "pentest",
    ],
    "apps_products": [
        "app",
        "dashboard",
        "web",
        "frontend",
        "backend",
        "mobile",
        "ios",
        "android",
        "saas",
        "react",
        "nextjs",
        "django",
        "fastapi",
        "flask",
    ],
    "libraries_frameworks": [
        "library",
        "framework",
        "package",
        "sdk",
        "api",
        "crate",
        "gem",
        "npm",
        "pip",
        "module",
    ],
    "datasets_research": [
        "dataset",
        "data",
        "corpus",
        "benchmark",
        "paper",
        "research",
        "experiment",
        "arxiv",
        "evaluation",
    ],
    "education_tutorials": [
        "tutorial",
        "course",
        "learn",
        "example",
        "examples",
        "bootcamp",
        "workshop",
        "notes",
        "homework",
    ],
    "automation_bots_scrapers": [
        "bot",
        "scraper",
        "crawler",
        "automation",
        "workflow",
        "rss",
        "github action",
        "github-action",
        "cron",
    ],
    "creative_games_media": [
        "game",
        "graphics",
        "unity",
        "unreal",
        "music",
        "audio",
        "video",
        "art",
        "creative",
        "roblox",
    ],
}


FIELD_WEIGHTS = {
    "repo_name": 1.2,
    "description": 2.8,
    "topics": 3.0,
    "primary_language": 0.7,
    "homepage": 0.4,
    "license_key": 0.2,
    "readme_excerpt": 0.6,
}


CATEGORY_PRIORITY = [
    "ai_ml_data",
    "developer_tools",
    "security_privacy",
    "datasets_research",
    "infra_devops",
    "apps_products",
    "libraries_frameworks",
    "automation_bots_scrapers",
    "creative_games_media",
    "education_tutorials",
]


NOISE_TERM_WEIGHTS = {
    "smoke test": 3.0,
    "delete after": 3.0,
    "delete-after": 3.0,
    "throwaway": 2.5,
    "placeholder": 2.0,
    "scratch": 2.0,
    "img-bed": 2.5,
    "image-bed": 2.5,
    "imagebed": 2.5,
    "picgo": 2.0,
    "github.io": 2.0,
    "tmp": 1.5,
    "temp": 1.5,
    "backup": 1.5,
    "dump": 1.5,
    "cdn": 1.25,
    "img": 1.25,
    "test": 1.25,
    "log": 1.0,
    "logs": 1.0,
    "pages": 1.0,
    "blog": 1.0,
    "portfolio": 1.0,
    "old": 0.75,
}

NOISE_TERMS = list(NOISE_TERM_WEIGHTS)


@dataclass
class CategoryResult:
    category: str
    category_confidence: float
    quality_score: float
    noise_score: float
    discovery_score: float
    category_reason: str


def categorize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [categorize_row(row) for row in rows]


def categorize_row(row: dict[str, Any]) -> dict[str, Any]:
    result = classify_repo(row)
    enriched = dict(row)
    enriched.update(
        {
            "category": result.category,
            "category_confidence": f"{result.category_confidence:.3f}",
            "quality_score": f"{result.quality_score:.3f}",
            "noise_score": f"{result.noise_score:.3f}",
            "discovery_score": f"{result.discovery_score:.3f}",
            "category_reason": result.category_reason,
        }
    )
    return enriched


def classify_repo(row: dict[str, Any]) -> CategoryResult:
    text = searchable_text(row)
    noise_score = compute_noise_score(row, text)
    quality_score = compute_quality_score(row, noise_score)

    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        category_score, matched = score_category(row, keywords)
        scores[category] = category_score
        reasons[category] = matched

    best_category = max(
        scores,
        key=lambda category: (scores[category], category_priority(category)),
    )
    best_score = scores[best_category]
    total_score = sum(scores.values())

    if noise_score >= 6.0 or (noise_score >= 4.5 and quality_score < 8):
        best_category = "personal_content_noise"
        confidence = min(1.0, noise_score / 8)
        reason = "noise indicators: " + ", ".join(noise_reasons(row, text)[:4])
    elif best_score <= 0:
        best_category = "uncategorized"
        confidence = 0.0
        reason = "no strong category keywords"
    else:
        confidence = best_score / max(total_score, best_score)
        reason = "matched: " + ", ".join(reasons[best_category][:5])

    momentum_score = min(40.0, log1p(abs(as_float(row, "score"))) * 6)
    discovery_score = max(0.0, momentum_score + quality_score - (noise_score * 2.5))

    return CategoryResult(
        category=best_category,
        category_confidence=confidence,
        quality_score=quality_score,
        noise_score=noise_score,
        discovery_score=discovery_score,
        category_reason=reason,
    )


def searchable_text(row: dict[str, Any]) -> str:
    return " ".join(field_text(row, field) for field in FIELD_WEIGHTS)


def field_text(row: dict[str, Any], field: str) -> str:
    return str(row.get(field, "")).lower().replace("_", " ")


def score_category(row: dict[str, Any], keywords: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    matched: list[str] = []
    for field, field_weight in FIELD_WEIGHTS.items():
        text = field_text(row, field)
        tokens = tokenize(text)
        for keyword in keywords:
            if keyword_matches(keyword, text, tokens):
                score += keyword_weight(keyword) * field_weight
                if keyword not in matched:
                    matched.append(keyword)
    return score, matched


def category_priority(category: str) -> int:
    try:
        return len(CATEGORY_PRIORITY) - CATEGORY_PRIORITY.index(category)
    except ValueError:
        return 0


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9][a-z0-9.+#-]*", text.lower()))


def keyword_matches(keyword: str, text: str, tokens: set[str]) -> bool:
    keyword = keyword.lower()
    if " " in keyword:
        return keyword in text
    if len(keyword) <= 3:
        return keyword in tokens
    return keyword in tokens or keyword in text


def keyword_weight(keyword: str) -> float:
    if " " in keyword:
        return 1.5
    if len(keyword) <= 3:
        return 1.25
    return 1.0


def compute_noise_score(row: dict[str, Any], text: str) -> float:
    score = 0.0
    matched_terms = find_noise_terms(text)
    score += min(7.0, sum(NOISE_TERM_WEIGHTS[term] for term in matched_terms))

    repo_name = str(row.get("repo_name", "")).lower()
    description = str(row.get("description", "")).strip()
    topics = str(row.get("topics", "")).strip()

    if repo_name.endswith(".github.io") or "github.io" in repo_name:
        score += 3.0
    if any(term in repo_name for term in ("img", "image-bed", "imagebed", "cdn", "log", "test", "smoke")):
        score += 1.0
    if str(row.get("metadata_error", "")).strip():
        score += 3.0
    if not description:
        score += 1.0
    if not topics:
        score += 0.75
    if as_bool(row.get("is_fork")):
        score += 1.0
    if as_bool(row.get("is_archived")):
        score += 3.0
    if as_float(row, "pushes") > 0 and as_float(row, "stars") == 0 and as_float(row, "forks") == 0:
        score += 1.5
    return score


def find_noise_terms(text: str) -> list[str]:
    tokens = tokenize(text)
    return [term for term in NOISE_TERMS if noise_term_matches(term, text, tokens)]


def noise_reasons(row: dict[str, Any], text: str) -> list[str]:
    reasons = find_noise_terms(text)
    metadata_error = str(row.get("metadata_error", "")).strip()
    if metadata_error:
        reasons.append(f"metadata_error:{metadata_error}")
    if not reasons:
        reasons.append("low metadata quality")
    return reasons


def noise_term_matches(term: str, text: str, tokens: set[str]) -> bool:
    if " " in term or "." in term or "-" in term:
        return term in text
    return term in tokens


def compute_quality_score(row: dict[str, Any], noise_score: float) -> float:
    score = 0.0
    if str(row.get("description", "")).strip():
        score += 2.0
    if str(row.get("topics", "")).strip():
        score += 2.0
    if str(row.get("license_key", "")).strip():
        score += 1.5
    if str(row.get("readme_excerpt", "")).strip():
        score += 1.5
    if str(row.get("primary_language", "")).strip():
        score += 1.0
    if as_float(row, "releases") > 0:
        score += 1.0
    if as_float(row, "pull_requests_opened") > 0:
        score += 1.0
    if as_float(row, "issues_opened") > 0:
        score += 0.75

    stars = max(as_float(row, "stargazers_count"), as_float(row, "stars"))
    forks = max(as_float(row, "forks_count"), as_float(row, "forks"))
    score += min(5.0, log1p(stars) * 1.2)
    score += min(3.0, log1p(forks) * 0.9)

    if as_bool(row.get("is_fork")):
        score -= 1.0
    if as_bool(row.get("is_archived")):
        score -= 4.0
    score -= min(5.0, noise_score * 0.8)
    return max(0.0, score)


def as_float(row: dict[str, Any], key: str) -> float:
    value = row.get(key, 0)
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}
