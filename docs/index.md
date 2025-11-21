# FreshFit Handbook

Welcome to the internal handbook for FreshFit — a Gemini-powered wardrobe and outfit copilot. This site explains the system architecture, agent roster, prompt patterns, and configuration needed to run or extend the project.

## Highlights

- Multi-agent graph built with Google’s Agent Developer Kit (ADK)
- Gemini router that chooses between styling (OutfitFlow) and wardrobe CRUD (Cloth Registrar)
- Live weather enrichment, wardrobe rotation, explainable recommendations, and a feedback loop
- CLI-first UX that doubles as an integration harness for future surfaces

## Quickstart

```bash
git clone https://github.com/yourusername/freshfit.git
cd freshfit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add GOOGLE_API_KEY and other secrets
python main.py
```

Need sample data? Run `scripts/create_demo_wardrobe_db.py` to (re)seed `data/demo_wardrobe.db`.

## Document Map

- [Architecture](architecture.md) – execution graph, routing rules, data flow
- [Agents](agents.md) – per-agent responsibilities, tools, schemas
- [Prompts](prompts.md) – instruction templates, guardrails, retry guidance
- [Configuration](configuration.md) – environment variables, tooling, local data
- [Product Spec](PRD.md) – product requirements doc
- [Claude Notes](CLAUDE.md) – ideation notes

Use the left-hand nav or the list above to jump to any section. For questions or updates, open a PR and link to the relevant page.

