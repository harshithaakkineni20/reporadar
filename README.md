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

The first version is intentionally small and runnable today. It uses GH Archive-style events, builds repo-level features, ranks repositories, and evaluates whether the ranking matched future growth.

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

Evaluate the ranking against future growth in the sample data:

```bash
PYTHONPATH=src python3 -m reporadar evaluate \
  --input data/sample/gh_events_sample.jsonl \
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

Then rank the downloaded archives:

```bash
PYTHONPATH=src python3 -m reporadar rank \
  --input data/raw/gharchive \
  --output outputs/real_rankings.csv
```

Source: https://www.gharchive.org/

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
- LightGBM or XGBoost learning-to-rank model
- precision@k, recall@k, NDCG@k
- feature importance dashboard

### Version 0.3: Neural/Graph Upgrade

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
