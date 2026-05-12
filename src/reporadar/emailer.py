from __future__ import annotations

import csv
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from reporadar.history import discoveries_for_run, latest_run_date, load_runs


SUBSCRIBER_COLUMNS = ["email", "name", "status", "created_at"]


def build_weekly_digest(
    history_dir: Path,
    *,
    run_date: str | None = None,
    top: int = 10,
) -> tuple[str, str]:
    run_date = run_date or latest_run_date(history_dir)
    if not run_date:
        return "RepoRadar weekly update", "RepoRadar has no stored runs yet."

    runs = {row.get("run_date"): row for row in load_runs(history_dir)}
    run = runs.get(run_date, {})
    rows = discoveries_for_run(history_dir, run_date=run_date, limit=top)

    subject = f"RepoRadar weekly discovery update: {run_date}"
    lines = [
        f"RepoRadar weekly discovery update for {run_date}",
        "",
        "Run summary:",
        f"- Events analyzed: {run.get('events', 'unknown')}",
        f"- Ranked repos: {run.get('ranked_repos', 'unknown')}",
        f"- Enriched repos: {run.get('enriched_repos', 'unknown')}",
        f"- Stored repo observations: {run.get('candidate_repos', 'unknown')}",
        "",
        "Top discoveries:",
    ]

    if not rows:
        lines.append("- No candidates passed the current filters.")
    for index, row in enumerate(rows, start=1):
        trend = format_trend(row)
        url = row.get("html_url") or f"https://github.com/{row.get('repo_name', '')}"
        lines.extend(
            [
                f"{index}. {row.get('repo_name')} ({row.get('category')})",
                f"   discovery={row.get('discovery_score')} quality={row.get('quality_score')} noise={row.get('noise_score')} {trend}",
                f"   {row.get('description') or 'No description available.'}",
                f"   {url}",
            ]
        )

    lines.extend(
        [
            "",
            "How to read this:",
            "- New means the repo was not in prior stored weekly snapshots.",
            "- Delta compares discovery score with the previous stored appearance.",
            "- Repeated appearances can mean sustained momentum instead of a one-time spike.",
        ]
    )
    return subject, "\n".join(lines)


def format_trend(row: dict[str, str]) -> str:
    if row.get("is_new") == "true":
        return "[new]"
    delta = row.get("discovery_delta", "")
    previous_rank = row.get("previous_rank", "")
    if not delta:
        return ""
    return f"[delta={delta}, previous_rank={previous_rank}]"


def read_recipients(subscribers_path: Path | None = None) -> list[str]:
    recipients: list[str] = []
    env_recipients = os.environ.get("REPORADAR_EMAIL_TO", "")
    recipients.extend(email.strip() for email in env_recipients.split(",") if email.strip())

    if subscribers_path and subscribers_path.exists():
        with subscribers_path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                status = row.get("status", "active").strip().lower()
                email = row.get("email", "").strip()
                if email and status in {"", "active"}:
                    recipients.append(email)

    return sorted(set(recipients))


def send_digest(
    *,
    subject: str,
    body: str,
    recipients: list[str],
) -> int:
    if not recipients:
        return 0

    host = require_env("REPORADAR_SMTP_HOST")
    port = int(os.environ.get("REPORADAR_SMTP_PORT", "587"))
    username = os.environ.get("REPORADAR_SMTP_USERNAME", "")
    password = os.environ.get("REPORADAR_SMTP_PASSWORD", "")
    sender = os.environ.get("REPORADAR_EMAIL_FROM", username)
    if not sender:
        raise RuntimeError("Set REPORADAR_EMAIL_FROM or REPORADAR_SMTP_USERNAME.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    if port == 465:
        with smtplib.SMTP_SSL(host, port) as smtp:
            login_if_configured(smtp, username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            login_if_configured(smtp, username, password)
            smtp.send_message(message)
    return len(recipients)


def login_if_configured(smtp: smtplib.SMTP, username: str, password: str) -> None:
    if username and password:
        smtp.login(username, password)


def require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
