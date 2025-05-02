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
export GH_TOKEN=ghp_yourPAT        # needed only for local runs
python scripts/update_metrics.py
python -m http.server 8000
open http://localhost:8000/docs/
```

---

## 8. Enable it

1. Create a new public repository and commit/push the tree above.
2. In **Settings → Secrets → Actions** add (optional) `GH_TOKEN`
   – a lightweight PAT with `public_repo` scope to lift API limits.  
   If omitted, the default `github_token` still works but only ~60 hits/hour.
3. Turn on **GitHub Pages** for the `main` branch, `/docs` folder.
4. Visit your shiny new dashboard!

---

### Why this stack?

| Design choice                  | Reason                                                            |
| ------------------------------ | ----------------------------------------------------------------- |
| **Static site** in `/docs`     | Zero servers, ultra-cheap, GitHub Pages built-in                  |
| **Vanilla JS + Tailwind**      | No build step ⇒ anyone can edit; Tailwind CDN keeps it pretty     |
| **GraphQL API**                | One request per repo, trivial commit-count retrieval              |
| **Dedicated `frameworks.yml`** | Human-friendly list; you can tweak metadata without touching code |
| **Single Action**              | Only 75 LOC, CI-friendly, instantly replaceable                   |
| **No frameworks / bundlers**   | Low cognitive load for future maintainers                         |
