from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="RepoRadar", layout="wide")
st.title("RepoRadar")
st.caption("Early signals for open-source repositories")

default_path = Path("outputs/sample_rankings.csv")
ranking_file = st.sidebar.text_input("Rankings CSV", str(default_path))
path = Path(ranking_file)

if not path.exists():
    st.info(
        "Run `PYTHONPATH=src python3 -m reporadar rank "
        "--input data/sample/gh_events_sample.jsonl --output outputs/sample_rankings.csv` first."
    )
    st.stop()

df = pd.read_csv(path)
metric_cols = st.columns(4)
metric_cols[0].metric("Repos", len(df))
metric_cols[1].metric("Top Score", round(float(df["score"].max()), 2))
metric_cols[2].metric("Repos With Future Growth", int((df["future_growth"] > 0).sum()))
metric_cols[3].metric("Median Actors", round(float(df["unique_actors"].median()), 1))

st.subheader("Trending Soon")
st.dataframe(
    df[
        [
            "rank",
            "repo_name",
            "score",
            "why",
            "stars",
            "forks",
            "unique_actors",
            "activity_velocity",
            "future_growth",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

selected = st.selectbox("Inspect repo", df["repo_name"].tolist())
row = df[df["repo_name"] == selected].iloc[0]

st.subheader(selected)
st.write(row["why"])
st.bar_chart(
    row[
        [
            "stars",
            "forks",
            "unique_actors",
            "issues_opened",
            "pull_requests_opened",
            "commits",
            "releases",
        ]
    ]
)
