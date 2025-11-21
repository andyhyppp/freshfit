# Agents

FreshFit is composed of small, single-purpose agents wired together with ADK’s `ParallelAgent` and `SequentialAgent` helpers. This page summarizes each agent, the model/tools it uses, and notable behaviors or contracts.

| Agent | File | Model | Tools | Highlights |
| --- | --- | --- | --- | --- |
| Router | `agents/router_agent.py` | `Gemini 2.5 Flash` | — | Classifies requests as styling vs. CRUD, asks clarifying questions, and dispatches to OutfitFlow or cloth registrar. |
| Weather | `agents/weather_agent.py` | `Gemini 2.5 Flash` | `google_search`, `date_tool` | Normalizes weather into temp buckets, °C stats, precip chance; always logs when falling back to stale data. |
| Wardrobe Cataloger | `agents/wardrobe_cataloger.py` | `Gemini 2.5 Flash` | `demo_wardrobe_tool` | Pulls from SQLite, enforces rotation (prefers >2 days since last worn), emits summaries + missing categories. |
| Outfit Designer | `agents/outfit_designer.py` | `Gemini 2.5 Flash` | `google_search` | Builds ≥5 outfits, never hallucinates clothing, enforces accessories/outerwear rules, supports travel capsules. |
| Preference Ranking | `agents/preference_ranking.py` | `Gemini 2.5 Flash` | `preference_history_tool` | Reranks outfits, guarantees a “loved combo” plus an “exploration” look, emits decision traces. |
| Explanation | `agents/explanation_agent.py` | `Gemini 2.5 Flash` | — | Generates concise rationales per outfit plus CTA text telling users how to respond. |
| Feedback Learning | `agents/feedback_learning.py` | `Gemini 2.5 Flash` | — | Logs which outfit was picked, captures ratings/tags, and emits metrics events for analytics. |
| Cloth Adder | `agents/cloth_registrar.py` | `Gemini 2.5 Flash` | `add_wardrobe_tool` | Extracts structured metadata from text/image, enforces vocab for category/warmth/formality/body zone. |
| Cloth Deleter | `agents/cloth_registrar.py` | `Gemini 2.5 Flash` | `demo_wardrobe_tool`, `delete_wardrobe_tool` | Resolves item IDs via lookup before deletion, confirms with user when multiple matches exist. |
| Metrics Agent (optional) | `agents/metrics_agent.py` | `Gemini 2.5 Flash` | — | Processes `metrics_events` emitted by feedback learning (selection, ratings, preference updates). |

## Composition Helpers

- **ParallelAgent** bundles weather + wardrobe cataloger so upstream context arrives concurrently.
- **SequentialAgent** strings together designer → ranking → explanation for deterministic ordering.
- **OutfitFlowAgent** is a light wrapper class extending `SequentialAgent` to customize naming.

## Output Keys

| Agent | Output key | Downstream consumer |
| --- | --- | --- |
| `weather_agent` | `weather` | Outfit designer (context) |
| `wardrobe_cataloger` | `wardrobe_items` | Outfit designer |
| `outfit_designer` | `outfits` | Preference ranking |
| `preference_ranking` | `ranked_outfits` | Explanation agent |
| `explanation_agent` | `explanations` | CLI renderer |
| `feedback_learning` | `outfit_feedback`, `metrics_events` | Preference history tool / metrics agent |

Use this grid when wiring new branches or debugging contract mismatches — mismatched keys are the most common source of orchestration errors.

