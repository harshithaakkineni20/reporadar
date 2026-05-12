from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GITHUB_API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"


def split_repo_name(repo_name: str) -> tuple[str, str]:
    parts = repo_name.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Expected repo name in owner/name format: {repo_name}")
    return parts[0], parts[1]


def find_github_token() -> str | None:
    """Find a GitHub token without requiring users to copy secrets into the repo."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token

    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None

    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip()
    return None


@dataclass
class GitHubClient:
    token: str | None = None
    timeout: int = 30

    @classmethod
    def from_environment(cls) -> "GitHubClient":
        return cls(token=find_github_token())

    def get_json(self, path: str) -> dict[str, Any]:
        url = f"{GITHUB_API_URL}{path}"
        request = self._request(url, accept="application/vnd.github+json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {"metadata_error": "not_found"}
            if exc.code == 403:
                return {"metadata_error": "rate_limited_or_forbidden"}
            return {"metadata_error": f"http_{exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"metadata_error": exc.__class__.__name__}

    def get_text(self, path: str, max_chars: int = 4000) -> str:
        url = f"{GITHUB_API_URL}{path}"
        request = self._request(url, accept="application/vnd.github.raw+json")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read(max_chars * 4).decode("utf-8", errors="replace")[:max_chars]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            return ""

    def _request(self, url: str, accept: str) -> urllib.request.Request:
        headers = {
            "Accept": accept,
            "User-Agent": "RepoRadar/0.1",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return urllib.request.Request(url, headers=headers)


def enrich_repo(
    repo_name: str,
    client: GitHubClient,
    include_readme: bool = True,
    readme_chars: int = 4000,
) -> dict[str, Any]:
    owner, repo = split_repo_name(repo_name)
    repository = client.get_json(f"/repos/{owner}/{repo}")
    if repository.get("metadata_error"):
        return {
            "repo_name": repo_name,
            "metadata_error": repository["metadata_error"],
        }

    languages = client.get_json(f"/repos/{owner}/{repo}/languages")
    if languages.get("metadata_error"):
        languages = {}

    readme_excerpt = ""
    if include_readme:
        readme_excerpt = client.get_text(f"/repos/{owner}/{repo}/readme", max_chars=readme_chars)

    license_info = repository.get("license") or {}
    owner_info = repository.get("owner") or {}

    return {
        "repo_name": repo_name,
        "html_url": repository.get("html_url", ""),
        "description": repository.get("description") or "",
        "homepage": repository.get("homepage") or "",
        "primary_language": repository.get("language") or "",
        "languages_json": json.dumps(languages, sort_keys=True),
        "topics": ";".join(repository.get("topics") or []),
        "license_key": license_info.get("key", ""),
        "license_name": license_info.get("name", ""),
        "stargazers_count": repository.get("stargazers_count", 0),
        "forks_count": repository.get("forks_count", 0),
        "watchers_count": repository.get("watchers_count", 0),
        "open_issues_count": repository.get("open_issues_count", 0),
        "size": repository.get("size", 0),
        "default_branch": repository.get("default_branch", ""),
        "created_at": repository.get("created_at", ""),
        "updated_at": repository.get("updated_at", ""),
        "pushed_at": repository.get("pushed_at", ""),
        "is_fork": repository.get("fork", False),
        "is_archived": repository.get("archived", False),
        "is_template": repository.get("is_template", False),
        "has_issues": repository.get("has_issues", False),
        "has_projects": repository.get("has_projects", False),
        "has_wiki": repository.get("has_wiki", False),
        "has_pages": repository.get("has_pages", False),
        "has_discussions": repository.get("has_discussions", False),
        "visibility": repository.get("visibility", ""),
        "owner_type": owner_info.get("type", ""),
        "readme_excerpt": clean_multiline(readme_excerpt),
        "metadata_error": "",
    }


def clean_multiline(value: str) -> str:
    return " ".join(value.replace("\x00", " ").split())


def write_json_cache(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
