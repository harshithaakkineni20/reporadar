# RepoRadar Portfolio Pitch

## Problem

Developers, companies, and investors want to discover important open-source projects before they become obvious. GitHub stars alone are a lagging signal, and trending pages mostly show what is already popular.

## In Simpler Terms

RepoRadar tries to answer:

> Which GitHub repos are starting to move right now?

## Solution

RepoRadar turns public GitHub activity into temporal repo features, ranks projects by early momentum, and evaluates whether the top-ranked repos actually gained future attention.

The system starts with a transparent baseline score so every recommendation can be explained. The roadmap upgrades this into a learning-to-rank model and eventually a graph/neural model over users, repositories, topics, and time.

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
2. Time-based train/test split with ranking metrics
3. Gradient-boosted learning-to-rank model
4. README/topic embeddings for semantic repo similarity
5. user-repo interaction graph
6. temporal graph neural network or neural reranker
7. RAG explanations over README files, issues, releases, and docs

## Demo Narrative

The strongest demo is a dashboard called "Trending Soon." It shows repos likely to gain attention next week, the evidence behind each prediction, and how well prior predictions performed.
