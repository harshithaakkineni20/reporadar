# RepoRadar

RepoRadar is an early-signal engine for GitHub projects. It asks a simple question:

> Which open-source repos look like they are about to gain momentum?

This is a portfolio project for ranking, time-series features, developer ecosystem analytics, and eventually graph/neural recommendation models.

## Why This Project Exists

GitHub has millions of repositories. By the time a project appears on every trending page, the signal is already obvious. RepoRadar tries to detect earlier movement from public activity:

- stars and forks
- issue and pull request velocity
- unique contributors
- commit bursts
- release events
- acceleration compared with recent activity

The first version is intentionally small and runnable today. It uses GH Archive-style events, builds repo-level features, trains a pairwise ranking model, and evaluates whether the ranking matched future growth.

## What You Can Demo

```text
Input: public GitHub activity events
Output: repos ranked by early momentum

Example:
1. byteforge/langgraph-agent
   Why: star growth, PR activity, many unique actors, fast event velocity

2. vectorflux/mini-rag
   Why: star growth, fork growth, release activity, commit burst
```

That gives you a clear interview story:

> I built an early-detection ranking system for open-source projects using GitHub event streams. I engineered temporal activity features, created future-growth labels, evaluated ranking quality, and designed the roadmap toward graph-based and neural ranking models.

## Quick Start

Run the sample pipeline without installing anything:

```bash
PYTHONPATH=src python3 -m reporadar rank \
  --input data/sample/gh_events_sample.jsonl \
  --output outputs/sample_rankings.csv
```

Create rolling ML training rows:

```bash
PYTHONPATH=src python3 -m reporadar dataset \
  --input data/sample/gh_events_sample.jsonl \
  --output outputs/sample_training_rows.csv \
  --observation-hours 8 \
  --target-hours 6 \
  --stride-hours 3
```

Train the pairwise ranking model:

```bash
PYTHONPATH=src python3 -m reporadar train \
  --dataset outputs/sample_training_rows.csv \
  --model outputs/sample_ranker.json
```

Rank with the trained model:

```bash
PYTHONPATH=src python3 -m reporadar rank \
  --input data/sample/gh_events_sample.jsonl \
  --model outputs/sample_ranker.json \
  --observation-hours 8 \
  --target-hours 6 \
  --output outputs/sample_ml_rankings.csv
```

Evaluate the ranking against future growth in the sample data:

```bash
PYTHONPATH=src python3 -m reporadar evaluate \
  --input data/sample/gh_events_sample.jsonl \
  --model outputs/sample_ranker.json \
  --observation-hours 8 \
  --target-hours 6 \
  --top-k 3
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Optional Install

```bash
python3 -m pip install -e .
reporadar rank --input data/sample/gh_events_sample.jsonl
```

## Using Real GH Archive Data

GH Archive publishes public GitHub event archives by hour.

```bash
PYTHONPATH=src python3 -m reporadar fetch \
  --date 2026-05-01 \
  --hours 0 1 2 \
  --output data/raw/gharchive
```

Or pull a date range:

```bash
PYTHONPATH=src python3 -m reporadar fetch-range \
  --start-date 2026-05-01 \
  --end-date 2026-05-02 \
  --hours 0 1 2 \
  --output data/raw/gharchive
```

Then rank the downloaded archives:

```bash
PYTHONPATH=src python3 -m reporadar rank \
  --input data/raw/gharchive \
  --output outputs/real_rankings.csv
```

For model training, create rolling windows from the downloaded archives:

```bash
PYTHONPATH=src python3 -m reporadar dataset \
  --input data/raw/gharchive \
  --output data/processed/gharchive_training_rows.csv \
  --observation-hours 24 \
  --target-hours 24 \
  --stride-hours 6
```

Then train and evaluate:

```bash
PYTHONPATH=src python3 -m reporadar train \
  --dataset data/processed/gharchive_training_rows.csv \
  --model outputs/gharchive_ranker.json

PYTHONPATH=src python3 -m reporadar evaluate \
  --input data/raw/gharchive \
  --model outputs/gharchive_ranker.json \
  --observation-hours 24 \
  --target-hours 24 \
  --top-k 20
```

Start small with a few hours first. GH Archive files can be large.

Source: https://www.gharchive.org/

## Continuous Discovery

RepoRadar can run continuously as a scheduled GitHub Actions workflow. In this project, "continuous" means scheduled monitoring: GitHub runs the pipeline automatically, fetches a fresh GH Archive time slice, ranks repositories, enriches the top candidates, categorizes them, and uploads a discovery report.

The workflow lives at:

```text
.github/workflows/reporadar-continuous.yml
```

It runs every Monday at `03:30 UTC`, and it can also be started manually from the GitHub Actions tab.

Manual run from GitHub:

```text
Actions -> RepoRadar Continuous Discovery -> Run workflow
```

Manual run from your terminal:

```bash
PYTHONPATH=src python3 -m reporadar continuous \
  --run-date 2026-05-11 \
  --hours 0 1 2 3 4 5
```

Each continuous run writes a dated folder:

```text
runs/reporadar/YYYY-MM-DD/
```

That folder contains:

- raw GH Archive files
- training rows
- trained ranker
- ranked repositories
- enriched metadata
- categorized discovery CSV
- Markdown discovery report

If the workflow runs on a new date, the results should change because GitHub activity changed. If you run the same date and same hours again, the output should be mostly the same.

## Category-Aware Discovery

Raw activity ranking can surface noisy repositories: image beds, test apps, personal sites, logs, mirrors, and generated content. RepoRadar adds a discovery layer that enriches top-ranked repositories with GitHub metadata, categorizes their use case, and separates noisy repos from useful discovery candidates.

Enrich the top ranked repos with GitHub metadata:

```bash
PYTHONPATH=src python3 -m reporadar enrich \
  --rankings outputs/gharchive_rankings.csv \
  --output data/processed/enriched_repos.csv \
  --top 50
```

Categorize use cases and compute discovery scores:

```bash
PYTHONPATH=src python3 -m reporadar categorize \
  --input data/processed/enriched_repos.csv \
  --output outputs/discovery.csv
```

Show clean category leaderboards:

```bash
PYTHONPATH=src python3 -m reporadar discover \
  --input outputs/discovery.csv \
  --top 10 \
  --hide-noise \
  --hide-uncategorized \
  --min-quality 5 \
  --max-noise 3.5
```

Show one category:

```bash
PYTHONPATH=src python3 -m reporadar discover \
  --input outputs/discovery.csv \
  --category ai_ml_data \
  --top 10 \
  --hide-noise \
  --min-quality 5 \
  --max-noise 3.5
```

Generate a Markdown experiment report:

```bash
PYTHONPATH=src python3 -m reporadar report \
  --input outputs/discovery.csv \
  --output reports/discovery_report.md \
  --labels data/labels/review_labels.csv \
  --top 10 \
  --min-quality 5 \
  --max-noise 3.5
```

The report is designed as a human review document. It explains what happened, shows candidate cards with descriptions and metadata, and gives manual review questions so you can decide whether the model is surfacing genuinely useful repositories.

Human feedback lives in:

```text
data/labels/review_labels.csv
```

Use labels like `keep`, `reject`, or `relabel`. These labels let future reports remember reviewer judgment and create the foundation for a stronger supervised ranking model later.

For weekly use, fetch into a dated folder so each report analyzes one fresh time slice:

```bash
PYTHONPATH=src python3 -m reporadar fetch-range \
  --start-date 2026-05-10 \
  --end-date 2026-05-10 \
  --hours 0 1 2 \
  --output data/raw/gharchive/2026-05-10

PYTHONPATH=src python3 -m reporadar rank \
  --input data/raw/gharchive/2026-05-10 \
  --model outputs/gharchive_ranker.json \
  --observation-hours 2 \
  --target-hours 1 \
  --output outputs/gharchive_rankings.csv
```

If you run the same downloaded files again, results should be mostly the same. If you fetch newer GH Archive files seven days later, the ranked repos should change because GitHub activity changed.

Current categories:

- `ai_ml_data`
- `developer_tools`
- `infra_devops`
- `security_privacy`
- `apps_products`
- `libraries_frameworks`
- `datasets_research`
- `education_tutorials`
- `automation_bots_scrapers`
- `creative_games_media`
- `personal_content_noise`
- `uncategorized`

Metadata used for discovery includes descriptions, topics, primary language, language bytes, license, stars, forks, open issues, repository flags, owner type, timestamps, and README excerpts when available.

## Project Roadmap

### Version 0.1: Today

- GH Archive-style event parser
- repo-level feature aggregation
- baseline ranking score
- future-growth labels
- ranking evaluation
- sample dataset
- unit tests

### Version 0.2: Serious ML

- rolling daily feature windows
- train/test split by time
- pure-Python pairwise learning-to-rank model
- model persistence to JSON
- precision@k, recall@k, NDCG@k
- learned feature weights

### Version 0.3: Neural/Graph Upgrade

- GitHub metadata enrichment
- category-aware repo discovery
- quality and noise scoring
- repo-user interaction graph
- contributor quality embeddings
- language/topic embeddings from README text
- graph neural network or temporal graph model
- neural reranker for candidate repos

### Version 0.4: Recruiter-Friendly App

- Streamlit dashboard
- trending-soon leaderboard
- repo explanation cards
- similar historical growth curves
- "Why this repo?" RAG explanations over README, issues, and release notes

## Responsible Data Use

RepoRadar uses public GitHub event metadata. The project should avoid storing private data, tokens, or unnecessary personally identifying information. For large-scale use, cache responsibly and follow GitHub and GH Archive terms.
