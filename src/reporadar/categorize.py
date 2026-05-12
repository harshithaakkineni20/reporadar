from __future__ import annotations

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


NOISE_TERMS = [
    "test",
    "tmp",
    "temp",
    "backup",
    "log",
    "logs",
    "cdn",
    "img",
    "image-bed",
    "imagebed",
    "picgo",
    "github.io",
    "pages",
    "blog",
    "portfolio",
    "old",
    "dump",
]


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
        category_score = 0.0
        matched: list[str] = []
        for keyword in keywords:
            if keyword in text:
                category_score += 1.0 if " " not in keyword else 1.5
                matched.append(keyword)
        scores[category] = category_score
        reasons[category] = matched

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_score = sum(scores.values())

    if noise_score >= 4.5 and quality_score < 6:
        best_category = "personal_content_noise"
        confidence = min(1.0, noise_score / 8)
        reason = "noise indicators: " + ", ".join(find_noise_terms(text)[:4])
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
    fields = [
        "repo_name",
        "description",
        "homepage",
        "primary_language",
        "topics",
        "license_key",
        "readme_excerpt",
    ]
    return " ".join(str(row.get(field, "")).lower().replace("_", " ") for field in fields)


def compute_noise_score(row: dict[str, Any], text: str) -> float:
    score = 0.0
    matched_terms = find_noise_terms(text)
    score += min(5.0, len(matched_terms) * 1.25)

    repo_name = str(row.get("repo_name", "")).lower()
    description = str(row.get("description", "")).strip()
    topics = str(row.get("topics", "")).strip()

    if repo_name.endswith(".github.io") or "github.io" in repo_name:
        score += 3.0
    if any(term in repo_name for term in ("img", "image-bed", "imagebed", "cdn", "log", "test")):
        score += 1.0
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
    return [term for term in NOISE_TERMS if term in text]


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
