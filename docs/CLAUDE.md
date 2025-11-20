# FreshFit Technical Design

## 1. Purpose & Scope
FreshFit is a multi-agent wardrobe assistant built on Google's Agent Developer Kit (ADK). This technical design translates the PRD into concrete implementation plans spanning architecture, tools, data, and evaluation. Scope covers the V1 capstone deliverable (daily outfits + travel capsules, explanations, preference learning, metrics). Laundry nudges, VisionIngest, and monetization belong to V2 and are explicitly called out as future considerations but not part of the build plan.

## 2. Success Metrics Recap
- \>=70% acceptance rate for suggested outfits with an average rating >=4.0/5 for accepted looks.


## 3. System Architecture
```
User ---> Parallel Intake Agent ----> Context Collector ----> Context Tool (weather/calendar)
  |                    |                     |
  |                    +--> Wardrobe Cataloger -- Wardrobe Tool (SQLite)
  |                    +--> (future) Context-side enrichers
  +--> Sequential Designer Agent ----> Outfit Designer
                           |           +--> Explanation Agent
                           |           +--> Preference & Ranking Agent -- Preference Tool
                           +--> Feedback & Learning Agent --> History Tool, Metrics Tool
                                                                               |
  |<------------------------------ Response + explanations --------------------+
```
- **ADK Graph**: ParallelAgent kicks off Context Collector + Wardrobe Cataloger simultaneously, then a SequentialAgent hands their outputs to Outfit Designer → Explanation → Feedback chain. Each agent is packaged as an ADK node with explicit inputs/outputs to keep flows explainable and testable.
- **Storage**: Single SQLite database with logical namespaces (wardrobe_db, history_db, prefs_db, metrics_db). Access occurs through thin tool wrappers to keep SQL centralized.
- **Runtime**: Python 3.13 environment managed through the provided `freshfit` virtualenv. Agents use lightweight Pydantic schemas for message passing to guarantee validation inside the ADK runtime.

## 4. Agent Responsibilities
| Agent | Inputs | Core logic | Outputs |
| --- | --- | --- | --- |
| Parallel Intake Agent | User intent, session state | Executes Context Collector + Wardrobe Cataloger concurrently, merges their outputs, surfaces retry metadata | Combined context + wardrobe bundle |
| Context Collector | User-supplied date/location/occasion, stored defaults | Calls Context Tool for weather + calendar, buckets temperatures, surfaces fallback_reason if APIs fail | `Context` object (`date`, `location`, `occasion_tag`, `temperature_range`, `precip_chance`, `dress_code`) |
| Wardrobe Cataloger | wardrobe cache | Pulls appropriate items, enforces category coverage + `body_zone` tags, annotates color/fabric metadata | Candidate item set + mix/match metadata |
| Outfit Designer | Context + candidate items | Assembles outfits using heuristic rules (1 top + 1 bottom or dress, optional outerwear + shoes + accessories) while blending complementary colors/fabrics per weather/occasion. Travel mode switches to greedy cover algorithm. | `OutfitCandidate[]` |
| Preference & Ranking | Candidates, context signature, preference features | Scores each outfit `score = w_context * context_fit + w_pref * preference_score + w_recency * recency_penalty`. Applies exploration guardrails: at least one previously loved (>=4 stars) option and one novel combo. | Sorted slate (top 3) with per-option explanations + reasons |
| Explanation Agent | Ranked slate, context trace, scoring factors | Generates 1-2 sentence rationales referencing weather, occasion, and item attributes. Exposes tokens + references for debugging. | Natural language explanation per option |
| Feedback & Learning | Accepted/rejected events, ratings | Logs events, prompts for star ratings, handles `never suggest this again`, updates preferences and banned combos. | History entries, updated preference features |

## 5. Tool & API Layer
### 5.1 SQLite-backed Tools
- **Wardrobe Tool (`wardrobe_db`)**
  - `list_items(filter)` returns clean+context-suitable items.
  - `add_item(payload)` for Quick Add UX.
  - `mark_worn(item_ids, date)` updates `last_worn_date`.
- **History Tool (`history_db`)**
  - `log_outfit(event)` writes to `outfit_history`.
  - `save_rating(event_id, rating_payload)` upserts `ratings`.
  - `save_banned_combo(payload)` persists bans.
  - `get_banned_combos(scope)` for generator filters.
- **Preference Tool (`prefs_db`)**
  - `update_preferences_from_history(event_id)` recomputes `preference_features` using exponential smoothing.
  - `get_preference_score(context_signature, item_pair)` returns aggregated preference and support count.
- **Metrics Tool**
  - `log_event(event)` writes to `metrics_rollup` staging rows.
  - `compute_metrics(range)` returns aggregated acceptance/rating/travel coverage.

### 5.2 External / Mocked Services
- **Weather API**: fulfilled via the `google_search` tool. Normalize responses into buckets: `cold(<10C)`, `cool(10-18C)`, `mild(18-24C)`, `warm(24-30C)`, `hot(>30C)`, plus precipitation booleans.
- **Occasion tagging**: rely on the occasion text provided in the user prompt. Do not make Calendar API calls for now; if the prompt omits an occasion, surface a fallback note and proceed with a neutral “daily casual” assumption.

### 5.3 Error Handling Strategy
- Tools return structured errors with `retryable` flag. The Parallel Intake Agent retries each worker up to 2 times with exponential backoff (1s, 3s). On persistent failure, Explanation Agent surfaces fallback reasoning ("Using yesterday's weather average because API failed").

## 6. Data Model Implementation Details
Tables follow the PRD schema with the following notes:
- `wardrobe_items`
  - Columns: `item_id` (TEXT PK), `user_id`, `name`, `category`, `color`, `warmth_level`, `formality`, `body_zone`, `fabric_profile`, `color_hex`, `core_item` (BOOL), `last_worn_date`, `notes`.
  - `warmth_level` enumerated (`light`, `medium`, `heavy`). `formality` enumerated (`casual`, `smart_casual`, `business`, `formal`).
  - `body_zone` enumerated (`upper`, `lower`, `full_body`, `shoe`, `accessory`) so Outfit Designer can balance silhouettes (e.g., ensure one upper + one lower or a single dress).
  - Add compound index on `(category, warmth_level, formality)` plus a secondary on `(body_zone, last_worn_date)` to accelerate catalog filtering and recency checks.
  - Store `last_worn_date` as ISO-8601 string and rely on it (instead of cleanliness flags) to rotate items and avoid repeats. Keep JSON exports sorted to guarantee deterministic diffs.
- `outfit_history`
  - Columns: `event_id` (PK), `event_type`, `date`, `occasion_tag`, `weather_bucket`, `items` (JSON array of sorted item_ids), `rank`, `context_signature`, `generated_by_agent`, `travel_id`, `decision_trace`, `fallback_reason`.
  - `context_signature = f"{occasion_tag}:{temp_bucket}:{precip_bool}"` where `precip_bool` is `precipitation_chance >= 0.4`.
  - `decision_trace` holds structured reasoning per agent hop for replay/debugging.
- `ratings`
  - Columns: `rating_id` (PK), `event_id` (FK), `submitted_at`, `stars` (1–5), `feedback_tags` (JSON array), `free_text`.
  - `feedback_tags` vocabulary: `too_warm`, `too_cold`, `too_formal`, `too_casual`, `loved_it`, `needs_tailoring`, `bad_fit`.
  - Create index on `(event_id)` to speed joins plus partial indexes on `stars` for analytics.
- `banned_combos`
  - Columns: `ban_id` (PK), `scope` (`outfit`, `pair`), `items` (JSON array sorted), `items_hash`, `reason`, `created_at`, `expires_at`.
  - Enforce `UNIQUE(scope, items_hash)`; a nightly cleanup job removes expired bans.
- `preference_features`
  - Columns: `feature_id` (PK), `context_signature`, `item_pair`, `avg_rating`, `support_count`, `last_updated`.
  - `avg_rating` updated via EWMA (`avg_new = (1-alpha)*avg_old + alpha*rating`, `alpha=0.2`). Only treat a pair as “trusted” when `support_count >= 3`.
- `metrics_rollup`
  - Columns: `metric_date`, `suggestions_shown`, `accepted_count`, `rejected_count`, `avg_rating`, `travel_plans`, `days_covered`, `coverage_ratio`.
  - Partition by `metric_date`; store `coverage_ratio = days_covered / NULLIF(travel_plans,0)` for capsule tracking.

## 7. Core Algorithms
### 7.1 Context Signature & Bucketization
```python
bucket_temp(temp_c):
    if temp_c < 10: return "cold"
    elif temp_c < 18: return "cool"
    elif temp_c < 24: return "mild"
    elif temp_c < 30: return "warm"
    else: return "hot"
context_signature = f"{occasion_tag}:{bucket_temp(avg_temp)}:{precip>40%}"
```
The signature drives preference lookups and ensures ratings generalize across similar contexts.

### 7.2 Candidate Generation
1. Wardrobe Cataloger filters items by:
   - Category coverage (`top`, `bottom`, `dress`, `outerwear`, `shoes`, `accessory`) with `body_zone` ensuring upper/lower pairing for separates.
   - `last_worn_date` > 1 day ago unless closet is sparse.
   - `banned_combos` removal via set membership.
2. Outfit Designer assembles combinations:
```python
for top in tops:
  for bottom in bottoms:
    if banned_pair(top, bottom): continue
    if not harmonious_colors(top.color_hex, bottom.color_hex): continue
    if not compatible_fabrics(top.fabric_profile, bottom.fabric_profile): continue
    outfit = compose(top, bottom, choose_outerwear(), choose_shoes(), choose_accessory())
    score_context(outfit)
```
3. Travel mode switches to greedy covering algorithm:
   - Build minimal set of pieces that satisfy dress code across all days.
   - Use integer programming lite: start with highest-rated core items, ensure each day has unique combos, allow reusing jeans but not repeating entire outfit.

### 7.3 Ranking Function
```
context_fit = weather_match + occasion_match + color_fabric_harmony
preference_score = avg_rating (context_signature, item_pairs)
recency_penalty = max(0, 1 - days_since_worn / cooldown)
score = 0.4*context_fit + 0.4*preference_score + 0.2*(1 - recency_penalty)
```
- `color_fabric_harmony` rewards complementary palettes (e.g., navy + camel) and compatible fabric pairings (e.g., silk blouse with wool trousers).
- Guarantee one high-confidence slot: pick highest score among outfits containing previously loved items (`avg_rating >= 4` and `support_count >=3`).
- Guarantee exploration slot: pick highest score among outfits with `support_count == 0`.
- Remaining slot chosen by pure ranking.

### 7.4 Feedback Loop
- Feedback Agent prompts user after acceptance or end-of-day via ADK message.
- Ratings updates pipeline: write to `ratings`, call `update_preferences_from_history`, update `preference_features`, recompute `metrics_rollup` nightly.
- "Never suggest this again" toggles `banned_combos` either for full outfit (store sorted list) or pair (store 2-item list). Generator filters those combos.

## 8. Orchestration Flows
### 8.1 Daily Outfit Sequence
1. User request enters the Parallel Intake Agent, which simultaneously launches Context Collector (weather + occasion) and Wardrobe Cataloger (wardrobe_db filters, body_zone metadata).
2. Parallel outputs merge into a shared context bundle.
3. Sequential Designer stack calls Outfit Designer (up to 10 candidates) → Preference & Ranking Agent (diversity guardrails) → Explanation Agent (human rationale).
4. Response returns to the user along with logging via Feedback & Learning Agent; Wardrobe Cataloger updates `last_worn_date` upon acceptance.

### 8.2 Travel Capsule Sequence
1. User provides trip details, triggering the same Parallel Intake Agent (multi-day context + wardrobe filtering).
2. Sequential Designer switches Outfit Designer into travel mode (greedy cover) before handing off to Preference & Ranking and Explanation.
3. Metrics Agent logs `travel_plan` events with coverage ratio and total item count.

## 9. Observability & Testing
- **Decision Trace Logging**: Each agent writes structured logs (input, output, decision trace) stored in `outfit_history.decision_trace` for replay.
- **Metrics Dashboards**: Daily CLI command `python -m freshfit.metrics summarize --date YYYY-MM-DD` prints acceptance, avg rating, banned combo count, laundry backlog proxies.


## 10. Security & Privacy
- Store wardrobe descriptions only; no PII beyond optional location (defaults to city-level). 
- `.env` controls API keys for weather/calendar; never store keys inside DB. 
- All ADK agents sanitize tool outputs before presenting to users to avoid leaking raw traces.

## 11. Implementation Plan
1. **Foundation** (✅ Completed)
   - Set up SQLite schema migrations + tool wrappers.
   - Implement Context Tool mocks for offline testing.
2. **Daily Flow** (✅ Completed)
   - Wardrobe Cataloger + Outfit Designer heuristics.
   - Preference & Ranking Agent with scoring weights configurable via `.env`.
   - Explanation Agent templates + evaluation script.
3. **Travel Mode** (🚧 In Progress)
   - Multi-day weather aggregation + greedy capsule algorithm.
4. **Feedback Loop + Metrics** (✅ Completed)
   - Ratings capture, banned combo handling, nightly metrics rollup job.
5. **Testing & QA** (🚧 In Progress)
   - Generate test case, include user wardrobe, request to test agent model

