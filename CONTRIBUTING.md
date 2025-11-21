# Contributing to FreshFit

Thanks for helping make FreshFit better! This guide covers the basics for setting up your environment, writing code, and submitting contributions.

## Environment Setup

1. **Clone + create a virtualenv**
   ```bash
   git clone https://github.com/yourusername/freshfit.git
   cd freshfit
   python -m venv .venv && source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # optional, if you add dev extras
   ```
3. **Configure secrets**
   - Copy `.env.example` to `.env`.
   - Add `GOOGLE_API_KEY` and any tool-specific credentials.

## Tooling & Quality Gates

- **Formatter**: `black .`
- **Linting**: `ruff check .`
- **Imports**: `isort .` (if you prefer combined `ruff --fix`, that works too)
- **Type checking**: `mypy main.py agents`
- **Tests**: `pytest --maxfail=1 --disable-warnings`
- **Docs**: `mkdocs serve` for live preview.

> Tip: install `pre-commit` and run `pre-commit install` to automatically enforce these checks before each commit.

## Branch & PR Workflow

1. Branch from `main` (`git checkout -b feat/my-feature`).
2. Make focused commits with Conventional Commit prefixes (`feat:`, `fix:`, `docs:`…).
3. Keep PRs scoped — if you touch docs + code, explain both in the description.
4. Ensure the checklist below passes before opening the PR:
   - [ ] Lint / format / types succeed locally
   - [ ] `pytest` passes
   - [ ] README or docs updated if behavior or UX changed
   - [ ] Screenshots or CLI transcripts included for UX changes

## Filing Issues

- **Bug reports**: include reproduction steps, expected vs actual behavior, and CLI logs.
- **Feature requests**: describe the user story, acceptance criteria, and any dependencies.
- **Docs fixes**: link to the page + section that needs love.

## Getting Help

Open a GitHub Discussion or tag a maintainer on the issue/PR if you’re blocked. We try to respond within a couple of business days.

Welcome aboard, and thank you for contributing to FreshFit! 🎉

