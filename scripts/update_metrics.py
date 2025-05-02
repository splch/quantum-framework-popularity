#!/usr/bin/env python3
"""
Pulls GitHub metrics for each framework in data/frameworks.yml
and writes a compact data/metrics.json that the web front-end consumes.
"""

from __future__ import annotations

import json
import os
import sys
import datetime as dt
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
YAML_FILE = DATA / "frameworks.yml"
JSON_FILE = DATA / "metrics.json"

# --- GitHub GraphQL helpers -------------------------------------------------

ENDPOINT = "https://api.github.com/graphql"
HEADERS: dict[str, str] = {}
if token := os.getenv("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"

gql_query = """
query($owner: String!, $name: String!){
  repository(owner: $owner, name: $name){
    stargazerCount
    forkCount
    watchers{ totalCount }
    defaultBranchRef{
      target{
        ... on Commit{ history{ totalCount } }
      }
    }
  }
}
"""


def run_query(owner: str, name: str) -> dict[str, Any] | None:
    """Return the GraphQL repo object or *None* if not found/accessible."""
    r = requests.post(
        ENDPOINT,
        json={"query": gql_query, "variables": {"owner": owner, "name": name}},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    # GitHub returns {"data":{"repository":null},"errors":[...]} when missing
    return payload.get("data", {}).get("repository")


# --- Main -------------------------------------------------------------------


def main() -> None:
    rows: list[dict[str, Any]] = yaml.safe_load(YAML_FILE.read_text())

    out: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "frameworks": [],
    }

    for fw in rows:
        repo_str: str = fw["repo"]
        owner, name = repo_str.split("/", 1)

        try:
            repo = run_query(owner, name)
        except Exception as exc:
            print(f"⚠️  GraphQL request failed for {repo_str}: {exc}", file=sys.stderr)
            continue

        if repo is None:
            print(f"⚠️  Repository not found or inaccessible: {repo_str}", file=sys.stderr)
            continue

        # Some archived or empty repos may not have a default branch yet
        commits = 0
        branch_ref = repo.get("defaultBranchRef") or {}
        target = branch_ref.get("target") if isinstance(branch_ref, dict) else None
        if isinstance(target, dict):
            history = target.get("history")
            if isinstance(history, dict):
                commits = history.get("totalCount", 0) or 0

        out["frameworks"].append(
            {
                **fw,
                "stars": repo.get("stargazerCount", 0),
                "forks": repo.get("forkCount", 0),
                "watchers": repo.get("watchers", {}).get("totalCount", 0),
                "commits": commits,
            }
        )

    JSON_FILE.write_text(json.dumps(out, indent=2))
    print(f"✅  Wrote {JSON_FILE.relative_to(ROOT)} with {len(out['frameworks'])} records")


if __name__ == "__main__":
    main()
