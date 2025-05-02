#!/usr/bin/env python3
"""
Pulls GitHub metrics for each framework in data/frameworks.yml
and writes a compact data/metrics.json that the web front-end consumes.
"""

import json, os, subprocess, sys, datetime as dt, yaml, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
YAML_FILE = DATA / "frameworks.yml"
JSON_FILE = DATA / "metrics.json"
HEADERS = {}
if token := os.getenv("GH_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {token}"

# GraphQL query template – single repo
GQL = """
query($owner: String!, $name: String!){
  repository(owner: $owner, name: $name){
    stargazerCount
    forkCount
    defaultBranchRef{ target{ ... on Commit{ history{ totalCount } } } }
    watchers{ totalCount }
    isPrivate
  }
}
"""

def run_query(owner, name):
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": GQL, "variables": {"owner": owner, "name": name}},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"]["repository"]

def main():
    rows = yaml.safe_load(YAML_FILE.read_text())
    out = {
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "frameworks": [],
    }

    for fw in rows:
        owner, name = fw["repo"].split("/", 1)
        try:
            data = run_query(owner, name)
        except Exception as e:
            print(f"⚠️  {fw['repo']} failed: {e}", file=sys.stderr)
            continue

        commits = data["defaultBranchRef"]["target"]["history"]["totalCount"]
        out["frameworks"].append(
            {
                **fw,
                "stars": data["stargazerCount"],
                "forks": data["forkCount"],
                "watchers": data["watchers"]["totalCount"],
                "commits": commits,
            }
        )

    JSON_FILE.write_text(json.dumps(out, indent=2))
    print(f"Wrote {JSON_FILE}")

if __name__ == "__main__":
    main()
