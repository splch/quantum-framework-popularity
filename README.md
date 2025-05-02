# Quantum Framework Popularity Dashboard

Live site: **<https://splch.github.io/quantum-framework-popularity>**

## Update cadence

A GitHub Actions workflow runs daily (`0 8 * * *` UTC) and:

1. Queries the GitHub GraphQL API for each repo in `data/frameworks.yml`.
2. Regenerates `data/metrics.json`.
3. Commits the new snapshot, which triggers a Pages redeploy.

## Local development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export GH_TOKEN=ghp_yourPAT  # needed only for local runs
python scripts/update_metrics.py
python -m http.server 8000
open http://localhost:8000/docs/
```
