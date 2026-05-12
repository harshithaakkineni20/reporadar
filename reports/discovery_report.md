# RepoRadar Discovery Review

Generated: 2026-05-12 13:12 UTC
Source: `outputs/discovery.csv`

## How To Read This

This report is a review queue, not a final truth list. RepoRadar first ranks repositories by activity momentum, then enriches the highest-ranked repos with GitHub metadata, labels their likely use case, and filters obvious noise.

Your job as the reviewer is to ask: Is this repo a real useful project, is the category right, and should RepoRadar promote, hide, or relabel similar repos next time?

## What Happened

- Repositories analyzed: 50
- Discovery candidates after filters: 8
- Human-reviewed candidates: 4
- Repos labeled as noise: 13
- Repos left uncategorized: 14
- Minimum quality: 5.0
- Maximum noise: 4.0

## Category Mix

| Category | Count |
|---|---:|
| `uncategorized` | 14 |
| `personal_content_noise` | 13 |
| `apps_products` | 6 |
| `ai_ml_data` | 4 |
| `automation_bots_scrapers` | 3 |
| `datasets_research` | 3 |
| `developer_tools` | 2 |
| `infra_devops` | 2 |
| `creative_games_media` | 1 |
| `libraries_frameworks` | 1 |
| `security_privacy` | 1 |

## Candidate Cards

### 1. [hyperspaceai/agi](https://github.com/hyperspaceai/agi)

- Category: `ai_ml_data`
- Why it surfaced: matched: ai, agent, model, llm, transformer
- Human review: `keep` on 2026-05-12 - Active and interesting AI/agent repo; keep as a good discovery candidate.
- Scores: discovery `39.239`, quality `13.800`, noise `1.500`, confidence `0.638`
- Description: The first distributed AGI system. Thousands of autonomous AI agents collaboratively train models, share experiments via P2P gossip, and push breakthroughs here. Fully peer-to-peer. Join from your browser or CLI.
- Metadata: language `unknown`, license `mit`, stars `1650`, forks `180`, open issues `19`
- Topics: `agi`, `ai-agents`, `ai-research`, `artificial-general-intelligence`, `autonomous-agents`, `autonomous-agents-`, `autoresearch`, `collaborative-ai`
- Next review action: keep / reject / relabel?

### 2. [antirez/ds4](https://github.com/antirez/ds4)

- Category: `ai_ml_data`
- Why it surfaced: matched: deepseek, inference, agent, vector, model
- Human review: `keep` on 2026-05-12 - Active and technically interesting local inference repo; keep.
- Scores: discovery `37.747`, quality `13.400`, noise `0.750`, confidence `0.864`
- Description: DeepSeek 4 Flash local inference engine for Metal and CUDA
- Metadata: language `C`, license `mit`, stars `7708`, forks `589`, open issues `41`
- Topics: none
- Next review action: keep / reject / relabel?

### 3. [SoliSpirit/proxy-list](https://github.com/SoliSpirit/proxy-list)

- Category: `developer_tools`
- Why it surfaced: matched: tool
- Human review: `keep` on 2026-05-12 - Active utility repo with clear developer use case; keep.
- Scores: discovery `29.464`, quality `8.772`, noise `2.250`, confidence `1.000`
- Description: An automated proxy list that updates every 3 hours with HTTP, HTTPS, SOCKS4, and SOCKS5 proxies from multiple countries.
- Metadata: language `unknown`, license `unknown`, stars `69`, forks `9`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?

### 4. [edrisranjbar/g2ray](https://github.com/edrisranjbar/g2ray)

- Category: `apps_products`
- Why it surfaced: matched: app, android
- Human review: not reviewed yet
- Scores: discovery `29.279`, quality `7.300`, noise `2.750`, confidence `0.351`
- Description: No description available.
- Metadata: language `Dockerfile`, license `unknown`, stars `2319`, forks `7636`, open issues `6`
- Topics: none
- Next review action: keep / reject / relabel?

### 5. [chenxi750328ai/agent-jianghu](https://github.com/chenxi750328ai/agent-jianghu)

- Category: `ai_ml_data`
- Why it surfaced: matched: agent, ai, rag
- Human review: not reviewed yet
- Scores: discovery `27.643`, quality `6.032`, noise `3.500`, confidence `0.941`
- Description: agent江湖 - 多Agent协作平台
- Metadata: language `Python`, license `mit`, stars `1`, forks `0`, open issues `5`
- Topics: `multi-agent`
- Next review action: keep / reject / relabel?

### 6. [houseofmates/gen](https://github.com/houseofmates/gen)

- Category: `automation_bots_scrapers`
- Why it surfaced: matched: automation, workflow
- Human review: not reviewed yet
- Scores: discovery `25.834`, quality `5.032`, noise `2.250`, confidence `0.432`
- Description: A self-hosted proxy service for freegen.app and geminigen.ai image generation using Playwright automation
- Metadata: language `JavaScript`, license `other`, stars `1`, forks `0`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?

### 7. [jessicacohen554-cyber/hourly-cfe-optimizer](https://github.com/jessicacohen554-cyber/hourly-cfe-optimizer)

- Category: `apps_products`
- Why it surfaced: matched: dashboard
- Human review: not reviewed yet
- Scores: discovery `25.050`, quality `5.200`, noise `2.250`, confidence `0.571`
- Description: Interactive dashboard & optimization engine for analyzing hourly clean energy procurement strategies across 5 US ISO regions
- Metadata: language `JavaScript`, license `gpl-3.0`, stars `0`, forks `0`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?

### 8. [openclaw/clawsweeper-state](https://github.com/openclaw/clawsweeper-state)

- Category: `developer_tools`
- Why it surfaced: matched: tool
- Human review: `keep` on 2026-05-12 - Active repo and useful enough to keep for review despite sparse metadata.
- Scores: discovery `23.807`, quality `5.485`, noise `3.250`, confidence `0.500`
- Description: No description available.
- Metadata: language `JavaScript`, license `mit`, stars `8`, forks `4`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?


## Near Misses To Debug

These repos had enough signal to be worth inspecting, but they did not pass the report filters. This section is for improving the model, not for final recommendations.

| Repo | Category | Discovery | Quality | Noise | Why filtered |
|---|---|---:|---:|---:|---|
| [arcamone1/ntf-rules](https://github.com/arcamone1/ntf-rules) | `uncategorized` | 31.054 | 1.700 | 2.250 | uncategorized; quality 1.700 below min 5.000 |
| [SoliSpirit/v2ray-configs](https://github.com/SoliSpirit/v2ray-configs) | `uncategorized` | 30.164 | 9.700 | 2.250 | uncategorized |
| [living-ip/teleo-codex](https://github.com/living-ip/teleo-codex) | `ai_ml_data` | 30.001 | 3.689 | 2.250 | quality 3.689 below min 5.000 |
| [Raph33AI/alphavault-quant](https://github.com/Raph33AI/alphavault-quant) | `security_privacy` | 28.680 | 2.232 | 3.250 | quality 2.232 below min 5.000 |
| [AndersNBE/kereby-scraper](https://github.com/AndersNBE/kereby-scraper) | `automation_bots_scrapers` | 27.411 | 2.032 | 2.250 | quality 2.032 below min 5.000 |

## What To Check Manually

For each candidate, answer:

1. Is this a real reusable tool, dataset, app, or library?
2. Is the assigned category correct?
3. Would a developer actually want to discover this?
4. Did the model overvalue raw activity, vague keywords, or noisy metadata?
5. Should similar repos be promoted, hidden, or relabeled?

## If You Run This Again Next Week

If you use the same downloaded GH Archive files, the output should be mostly the same because the input data is the same.

If you fetch newer GH Archive data seven days later, RepoRadar will rank a new slice of GitHub activity. Some repos may repeat if they keep gaining momentum, but many should change because the event stream changed.

Use a new dated raw-data folder for each run. If you keep adding files to the same directory, RepoRadar will analyze the combined old and new data.

The practical user value is a weekly discovery brief: instead of browsing GitHub Trending manually, a user can ask RepoRadar for fresh candidates by category, hide noisy repos, and inspect a short list of emerging projects.

Typical weekly flow:

```bash
PYTHONPATH=src python3 -m reporadar fetch-range --start-date YYYY-MM-DD --end-date YYYY-MM-DD --hours 0 1 2 --output data/raw/gharchive/YYYY-MM-DD
PYTHONPATH=src python3 -m reporadar rank --input data/raw/gharchive/YYYY-MM-DD --model outputs/gharchive_ranker.json --observation-hours 2 --target-hours 1 --output outputs/gharchive_rankings.csv
PYTHONPATH=src python3 -m reporadar enrich --rankings outputs/gharchive_rankings.csv --output data/processed/enriched_repos.csv --top 50
PYTHONPATH=src python3 -m reporadar categorize --input data/processed/enriched_repos.csv --output outputs/discovery.csv
PYTHONPATH=src python3 -m reporadar report --input outputs/discovery.csv --output reports/discovery_report.md
```

## Model Notes

- `discovery_score` combines model momentum, metadata quality, and noise penalties.
- `quality_score` rewards useful metadata such as description, topics, README, license, language, stars, forks, PRs, and issues.
- `noise_score` penalizes signals common in test repos, image beds, personal pages, logs, backups, and generated content.
- `personal_content_noise` catches test repos, image beds, logs, blogs, and similar low-discovery-value repos.
- `Near Misses To Debug` shows repos that the filters removed even though they had momentum or useful metadata.
- This report is generated from a small top-N enrichment pass, so results improve as more ranked repos are enriched.
