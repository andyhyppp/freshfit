# Configuration & Operations

Everything you need to run FreshFit locally, configure credentials, and manage supporting assets.

## Environment Variables

| Variable | Description |
| --- | --- |
| `GOOGLE_API_KEY` | Required. Enables Gemini + Google Search access via the ADK. |
| `FRESHFIT_ENV` | Optional. Set to `dev`, `staging`, or `prod` for logging tweaks. |
| `WARDROBE_DB_PATH` | Optional override for the SQLite wardrobe DB (defaults to `data/demo_wardrobe.db`). |
| `OPENWEATHER_API_KEY` | Optional future integration; currently weather is fetched via Google Search but this key unlocks API fallbacks. |

Copy `.env.example` to `.env` and populate the values before running `main.py`.

## Dependencies

- Python 3.10+
- `requirements.txt` for runtime dependencies
- Install dev tooling (black, ruff, mypy, pytest, mkdocs) via `pip install -r requirements-dev.txt` (add this file if it doesn’t exist yet).

## Local Data

- `data/demo_wardrobe.db` ships with seed items. Recreate via:
  ```bash
  python scripts/create_demo_wardrobe_db.py
  ```
- Wardrobe CRUD agents operate directly on this file through `tools/demo_wardrobe_tool.py`. Back it up before large experiments.

## Running the CLI

```bash
python main.py
```

Flags/inputs are prompted interactively. The ASCII splash screen confirms you’re in the right place.

## MkDocs Handbook

Serve the documentation locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

This reads `mkdocs.yml` and watches the `docs/` directory for changes. Deploying to GitHub Pages is as simple as `mkdocs gh-deploy` once CI is wired up.

## Testing & Quality

```bash
ruff check .
black --check .
mypy main.py agents
pytest
```

Add these commands to pre-commit hooks or your preferred task runner to catch regressions early.

## Secrets Management

- For local runs, `.env` is fine. Never commit it.
- For CI/CD, store `GOOGLE_API_KEY` (and other secrets) in GitHub Actions secrets and inject them in workflows.

## Logging & Metrics

- CLI prints agent traces when `FRESHFIT_ENV=dev`.
- The `metrics_agent` ingests structured events from `feedback_learning`; wire it up to your analytics sink (BigQuery, Firestore, etc.) as a follow-up task.

