#!/usr/bin/env python3
"""
Appends a new daily snapshot to data/metrics.json and keeps a full history.

JSON layout (top level):
{
  "history": [
     { "generated_at": "...", "frameworks": [ { … } ] },
     …
  ]
}
"""
from __future__ import annotations
import json, os, sys, datetime as dt
from pathlib import Path
from typing import Any
import requests, yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
YAML_FILE = DATA / "frameworks.yml"
JSON_FILE = DATA / "metrics.json"

HEADERS: dict[str, str] = {}
if token := os.getenv("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"

GQL = """
query($owner: String!, $name: String!){
  repository(owner: $owner, name: $name){
    stargazerCount
    forkCount
    watchers{ totalCount }
    defaultBranchRef{ target{ ... on Commit{ history{ totalCount } } } }
  }
}
"""


def run_query(owner: str, name: str) -> dict[str, Any] | None:
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": GQL, "variables": {"owner": owner, "name": name}},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("repository")


def snapshot() -> dict[str, Any]:
    rows = yaml.safe_load(YAML_FILE.read_text())
    snap = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "frameworks": [],
    }
    for fw in rows:
        owner, name = fw["repo"].split("/", 1)
        repo = run_query(owner, name) or {}
        commits = (
            repo.get("defaultBranchRef", {})
            .get("target", {})
            .get("history", {})
            .get("totalCount", 0)
        )
        snap["frameworks"].append(
            {
                **fw,
                "stars": repo.get("stargazerCount", 0),
                "forks": repo.get("forkCount", 0),
                "watchers": repo.get("watchers", {}).get("totalCount", 0),
                "commits": commits,
            }
        )
    return snap


def main() -> None:
    hist: dict[str, Any] = {"history": []}
    if JSON_FILE.exists():
        hist = json.loads(JSON_FILE.read_text())

    hist.setdefault("history", []).append(snapshot())

    JSON_FILE.write_text(json.dumps(hist, indent=2))
    print(
        f"✅ wrote {JSON_FILE.relative_to(ROOT)} - "
        f"{len(hist['history'])} total snapshots"
    )


if __name__ == "__main__":
    main()
