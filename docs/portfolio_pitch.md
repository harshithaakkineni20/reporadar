# RepoRadar Portfolio Pitch

## Problem

Developers, companies, and investors want to discover important open-source projects before they become obvious. GitHub stars alone are a lagging signal, and trending pages mostly show what is already popular.

## In Simpler Terms

RepoRadar tries to answer:

> Which GitHub repos are starting to move right now?

## Solution

RepoRadar turns public GitHub activity into temporal repo features, ranks projects by early momentum, and evaluates whether the top-ranked repos actually gained future attention.

The system starts with a transparent baseline score so every recommendation can be explained. It now also includes rolling feature windows and a pairwise learning-to-rank model that learns which signals separate future winners from low-growth repos.

The discovery layer enriches top-ranked repos with GitHub metadata, categorizes their use case, and separates useful discovery candidates from noisy repos such as test apps, image beds, personal sites, logs, and generated content.

## Why Big Tech Would Care

This maps to several real product areas:

- GitHub repository discovery
- developer ecosystem intelligence
- feed ranking
- search ranking
- recommendation systems
- anomaly detection
- early trend detection

## ML Depth Roadmap

1. Baseline ranking from handcrafted features
2. Rolling feature-label windows from GH Archive events
3. Pairwise learning-to-rank model with saved weights
4. Time-based train/test split with ranking metrics
5. Category-aware discovery using descriptions, topics, languages, and README excerpts
6. Quality/noise scoring for practical repo discovery
7. Gradient-boosted learning-to-rank model
8. README/topic embeddings for semantic repo similarity
9. user-repo interaction graph
10. temporal graph neural network or neural reranker
11. RAG explanations over README files, issues, releases, and docs

## Demo Narrative

The strongest demo is a dashboard called "Trending Soon." It shows repos likely to gain attention next week, the evidence behind each prediction, and how well prior predictions performed.
