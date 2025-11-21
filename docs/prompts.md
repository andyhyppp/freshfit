# Prompt Contracts

FreshFit’s reliability comes from keeping prompt contracts tight and repeatable. This page captures the most important guardrails, structured fields, and retry guidelines per agent.

## Global Guidelines

- **Strict schemas**: Each agent pairs instructions with `input_schema` / `output_schema` models. Do not add free-form prose unless explicitly allowed.
- **Tool-first mindset**: When data may be stale (weather, wardrobe, preference history), call the relevant tool instead of guessing.
- **Retries**: All Gemini calls use `HttpRetryOptions(attempts=5, exp_base=7, initial_delay=1)` to gracefully handle 429/5xx responses.
- **No hallucinated wardrobe**: Any clothing surfaced to the user must exist in the SQLite DB or be newly added through the registrar.

## Agent-Specific Contracts

### Weather Agent
- Resolve ambiguous dates via `date_tool` (Pacific Time) before searching.
- Map temperatures into buckets: `cold <10°C`, `cool 10-18°C`, `mild 18-24°C`, `warm 24-30°C`, `hot >30°C`.
- Precipitation chance returned as decimal between 0 and 1.
- Mention any fallback (“Used yesterday’s data because forecast missing”) inside `dress_code` notes.

### Wardrobe Cataloger
- Always call `demo_wardrobe_tool` when `items` input is empty.
- Enforce rotation: avoid items worn in past 2 days unless categories would be missing.
- Provide `wardrobe_summary` and `notes` describing tradeoffs or fallbacks.
- `missing_categories` must list unsatisfied required categories.

### Outfit Designer
- Never invent items outside `wardrobe_items`.
- Compose each outfit with base pieces + shoes + accessory; add outerwear when <18 °C or raining.
- Emit ≥5 outfits for daily mode. Travel mode may produce fewer but must cover itinerary days.
- Provide both `outfit_items` (IDs) and `outfit_item_details` (ID + short name) with consistent ordering.
- `outfit_id` format: `{user_id|anon}-{rank:02d}`.

### Preference Ranking
- Use `preference_history_tool` when candidate slate lacks explicit loved/banned signals.
- Guarantee at least one “loved combo” (if available) and one “exploration” outfit.
- Return ordered IDs in `ranked_outfits` plus a plain-English `decision_trace`.

### Explanation Agent
- 1–2 sentences per outfit; cite weather, occasion, color harmony, and rotation context.
- Never expose raw JSON or internal scores.
- Close with a `selection_prompt` instructing the user to reply with the `outfit_id`.

### Feedback Learning
- Always capture `selected_outfit_id` before requesting ratings.
- For each outfit, persist decision + stars + `future_intent`.
- Emit `metrics_events` for every selection or rating so the metrics agent can log KPIs.
- If a user skips ratings, re-prompt using `rating_prompt` until they either rate or decline.

### Cloth Registrar
- **Adder**: Validate controlled vocab (`category`, `warmth_level`, `formality`, `body_zone`). Default `user_id` to `"123"` and only set `last_worn_date` when supplied.
- **Deleter**: Use `demo_wardrobe_tool` to disambiguate descriptions; confirm before deleting when multiple matches exist.
- **Registrar Router**: Ask clarifying questions instead of guessing when “add vs delete” intent is unclear.

## Retry & Error Handling

- Gemini retries happen automatically, but tools may still raise errors (e.g., missing DB). Surface actionable error messages upstream so the CLI can guide the user (“Run scripts/create_demo_wardrobe_db.py to seed data”).
- If a tool fails mid-flow, agents should return structured `notes` with the failure instead of falling back silently; the router can then apologize or request new input.

Keeping these contracts front-and-center prevents regressions when adjusting prompts or swapping models. Update this page whenever you tweak an agent instruction block.

