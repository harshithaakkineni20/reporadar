# RepoRadar Discovery Review

Generated: 2026-05-12 10:49 UTC
Source: `outputs/discovery.csv`

## How To Read This

This report is a review queue, not a final truth list. RepoRadar first ranks repositories by activity momentum, then enriches the highest-ranked repos with GitHub metadata, labels their likely use case, and filters obvious noise.

Your job as the reviewer is to ask: Is this repo a real useful project, is the category right, and should RepoRadar promote, hide, or relabel similar repos next time?

## What Happened

- Repositories analyzed: 50
- Discovery candidates after filters: 4
- Human-reviewed candidates: 4
- Repos labeled as noise: 20
- Repos left uncategorized: 14
- Minimum quality: 5.0
- Maximum noise: 3.5

## Category Mix

| Category | Count |
|---|---:|
| `personal_content_noise` | 20 |
| `uncategorized` | 14 |
| `ai_ml_data` | 4 |
| `apps_products` | 3 |
| `datasets_research` | 2 |
| `developer_tools` | 2 |
| `infra_devops` | 2 |
| `automation_bots_scrapers` | 1 |
| `creative_games_media` | 1 |
| `security_privacy` | 1 |

## Candidate Cards

### 1. [hyperspaceai/agi](https://github.com/hyperspaceai/agi)

- Category: `ai_ml_data`
- Why it surfaced: matched: ai, llm, agent, transformer, model
- Human review: `keep` on 2026-05-12 - Active and interesting AI/agent repo; keep as a good discovery candidate.
- Scores: discovery `39.239`, quality `13.800`, noise `1.500`
- Description: The first distributed AGI system. Thousands of autonomous AI agents collaboratively train models, share experiments via P2P gossip, and push breakthroughs here. Fully peer-to-peer. Join from your browser or CLI.
- Metadata: language `unknown`, license `mit`, stars `1650`, forks `180`, open issues `19`
- Topics: `agi`, `ai-agents`, `ai-research`, `artificial-general-intelligence`, `autonomous-agents`, `autonomous-agents-`, `autoresearch`, `collaborative-ai`
- Next review action: keep / reject / relabel?

### 2. [antirez/ds4](https://github.com/antirez/ds4)

- Category: `ai_ml_data`
- Why it surfaced: matched: agent, vector, model
- Human review: `keep` on 2026-05-12 - Active and technically interesting local inference repo; keep.
- Scores: discovery `29.497`, quality `11.400`, noise `3.250`
- Description: DeepSeek 4 Flash local inference engine for Metal and CUDA
- Metadata: language `C`, license `mit`, stars `7708`, forks `589`, open issues `41`
- Topics: none
- Next review action: keep / reject / relabel?

### 3. [SoliSpirit/proxy-list](https://github.com/SoliSpirit/proxy-list)

- Category: `developer_tools`
- Why it surfaced: matched: tool
- Human review: `keep` on 2026-05-12 - Active utility repo with clear developer use case; keep.
- Scores: discovery `29.464`, quality `8.772`, noise `2.250`
- Description: An automated proxy list that updates every 3 hours with HTTP, HTTPS, SOCKS4, and SOCKS5 proxies from multiple countries.
- Metadata: language `unknown`, license `unknown`, stars `69`, forks `9`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?

### 4. [openclaw/clawsweeper-state](https://github.com/openclaw/clawsweeper-state)

- Category: `developer_tools`
- Why it surfaced: matched: tool
- Human review: `keep` on 2026-05-12 - Active repo and useful enough to keep for review despite sparse metadata.
- Scores: discovery `23.807`, quality `5.485`, noise `3.250`
- Description: No description available.
- Metadata: language `JavaScript`, license `mit`, stars `8`, forks `4`, open issues `0`
- Topics: none
- Next review action: keep / reject / relabel?


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
- This report is generated from a small top-N enrichment pass, so results improve as more ranked repos are enriched.
