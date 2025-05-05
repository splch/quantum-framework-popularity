#!/usr/bin/env python3
"""
Pull GitHub metrics for each framework in data/frameworks.yml
and APPEND a daily snapshot to data/metrics.json, so we keep
a full history.
"""
from __future__ import annotations
import datetime as dt
import json, os, sys
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
YAML_FILE = DATA_DIR / "frameworks.yml"
JSON_FILE = DATA_DIR / "metrics.json"

GQL = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    forkCount
    watchers { totalCount }
    defaultBranchRef {
      target {
        ... on Commit { history { totalCount } }
      }
    }
  }
}
"""


def run_query(owner: str, name: str, headers: dict[str, str]) -> dict[str, Any] | None:
    """Return GitHub repo object or None if missing/inaccessible."""
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": GQL, "variables": {"owner": owner, "name": name}},
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("repository")


def build_snapshot(
    frameworks: list[dict[str, Any]], headers: dict[str, str]
) -> dict[str, Any]:
    snap: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "frameworks": [],
    }

    for fw in frameworks:
        owner, name = fw["repo"].split("/", 1)
        try:
            repo = run_query(owner, name, headers) or {}
        except Exception as exc:
            print(f"⚠️  {fw['repo']} query failed: {exc}", file=sys.stderr)
            repo = {}

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
    frameworks: list[dict[str, Any]] = yaml.safe_load(YAML_FILE.read_text())

    headers: dict[str, str] = {}
    if token := os.getenv("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    new_snap = build_snapshot(frameworks, headers)

    # Load previous history (support the legacy single‑snapshot file too)
    if JSON_FILE.exists():
        previous = json.loads(JSON_FILE.read_text())
        if "history" in previous and isinstance(previous["history"], list):
            history = previous["history"]
        else:  # old one‑shot format
            history = [previous]
    else:
        history = []

    history.append(new_snap)

    JSON_FILE.write_text(json.dumps({"history": history}, indent=2))
    print(f"✅  metrics.json updated - {len(history)} snapshots total")


if __name__ == "__main__":
    main()
