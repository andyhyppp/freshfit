# FreshFit: Smart Outfit & Laundry Planner PRD

## 1. Project Summary

- **Goal**: Help users decide what to wear and when to do laundry by combining wardrobe inventory, daily context (weather, schedule, occasion), and personal preferences—while showcasing Google’s Agent Developer Kit (ADK) as the orchestration backbone.
- **Primary users**: Busy professionals and students who want fast outfit decisions and gentle laundry nudges without maintaining spreadsheets.
- **Guiding principles**: keep the MVP data-light, explainable, and easy to demo within the Google ADK agent framework.
- **Capstone context**: Built for the Kaggle × Google ADK capstone. Keep everything simple and working


## 2. Success Criteria

- When user request a outfit suggestion, delivers up to three context-aware outfit options with short explanations and >70% acceptance rate and get average 4 stars out of 5.
- Travel mode covers multi-day trips with capsule wardrobes that avoid duplicate outfits while minimizing packed items.

## 3. In-Scope Feature Map

- **Daily Outfit & Planning**: A1 Occasion-aware suggestions; A2 “Explain this outfit”; A3 Multiple options (top 3); A4 Travel capsule planning.
- **Wardrobe & Laundry**: B1 Last-worn tracking.
- **Preference & Learning**: C1 1–5 star ratings; C2 Preference learning; C3 “Never suggest this again.”
- **UX & History**: D1 Quick text-based clothing add; D2 “What I wore” history log.
- **Observability & Explanation**: E2 Explanation agent; E3 Simple metrics/evaluation.

## 4. Feature Specifications

### A. Daily Outfit & Planning

#### A1. Occasion-Aware Suggestions

- **What**: Suggest outfits using weather (temperature, precipitation), occasion tags (WFH, office, gym, date, travel, etc.), and wardrobe availability.
- **User story**: “I’m going to the office today, it might rain. Suggest what to wear.”
- **Core behavior**:
  - User selects date (default today) and occasion tag.
  - Context Collector + Wardrobe Cataloger run in parallel to gather weather + wardrobe signals.
  - Sequential Designer calls Outfit Designer once both upstream agents finish.

#### A2. “Explain This Outfit”

- **What**: Every suggested outfit includes a 1–2 sentence explanation referencing context and item attributes.
- **User story**: “Why this combination?” → “It’s 10–18 °C with rain, you have an office meeting at 2 PM, so we picked warm layers, a smart-casual top, and waterproof shoes.”
- **Core behavior**: Explanation Agent uses context, item metadata (warmth, formality), and scoring signals to produce natural-language justification for each option.

#### A3. Multiple Options (Top 3)

- **What**: Present up to three ranked outfit options instead of forcing a single choice.
- **Core behavior**: Outfit Designer + Preference Agent create multiple candidates, score by context fit and preference, and supply top 2–3 with explanations. User may accept one or reject all.

#### A4. Travel Mode – Capsule Wardrobe Planner

- **What**: Build a small mix-and-match wardrobe for a trip (e.g., 4-day conference).
- **User input**: Destination, start/end dates, primary dress code.
- **Behavior**:
  - Gather destination weather for entire range.
  - Greedy algorithm chooses minimal tops/bottoms/shoes/outerwear covering all contexts.
  - Output includes per-day outfits and packing list (text only for MVP).

### B. Wardrobe & Laundry

#### B1. Last-Worn Tracking

- Update each item’s `last_worn_date` whenever an outfit is confirmed.
- Ensures the system can rotate outfits intelligently and avoid repeating the same combinations on consecutive days.

### C. Preference & Learning

#### C1. 1–5 Star Ratings

- Evening prompt (or post-wear) captures rating + optional tags or notes (too warm, too formal, loved it). Stores `outfit_id`, date, rating, and comments in history DB.

#### C2. Preference Learning

- Define lightweight “context signatures” (occasion + temperature buckets). Track avg ratings per item pair or feature. During suggestion, compute preference scores using historical ratings for similar contexts and blend with context-fit score.

#### C3. “Never Suggest This Again”

- User can blacklist full outfits or specific pairings. Feedback Agent records combos and generator filters them from future results.

### D. UX & History

#### D1. Quick Add Clothing

- Minimal form: name, category (top/bottom/shoes/outerwear/dress/accessory), color, warmth level, formality, optional core flag. Stored with unique item ID.

#### D2. “What I Wore” History Log

- Maintain chronological log containing date, outfit summary, and rating for user retrospection and debugging.

### E. Observability & Explanation

#### E2. Explanation Agent

- Converts decision traces into human-friendly sentences for both daily and travel scenarios, reinforcing trust and transparency.

#### E3. Metrics & Evaluation

- Log key events (suggestion shown, accepted, rejected, rating given). Metrics Agent computes acceptance rate, average rating, and banned combo count; expose via console or lightweight chart.

## 5. Data Model & Tooling

### 5.1 SQLite Schema (Capstone MVP)

- `wardrobe_items`: `item_id` (PK), `name`, `category`, `color`, `warmth_level`, `formality`, `core_item` (bool), `last_worn_date`, `image_url` (nullable), `notes`.
- `outfit_history`: `event_id` (PK), `event_type` (`suggested`, `accepted`, `rejected`, `travel_plan`), `date`, `occasion_tag`, `weather_bucket`, `items` (JSON array of item_ids), `rank`, `context_signature`, `generated_by_agent`, `travel_id` (nullable), `explanation_text`, `fallback_reason` (nullable).
- `ratings`: `rating_id` (PK), `event_id` (FK), `submitted_at`, `stars`, `feedback_tags` (JSON), `free_text`.
- `banned_combos`: `ban_id` (PK), `scope` (`outfit` or `pair`), `items` (JSON), `reason`, `created_at`, `expires_at` (nullable).
- `preference_features`: `feature_id`, `context_signature`, `item_pair`, `avg_rating`, `support_count`, `last_updated`.
- `metrics_rollup`: `metric_date`, `suggestions_shown`, `accepted_count`, `rejected_count`, `avg_rating`.

### 5.2 Core Tools (via Google ADK)

- **Wardrobe Tool** (`wardrobe_db`): CRUD on clothing items and a `mark_worn` action that updates `last_worn_date`.
- **Outfit History & Ratings Tool** (`history_db`): `log_outfit`, `get_history`, `save_banned_combo`, `get_banned_combos`.
- **Preference Tool** (`prefs_db`): `update_preferences_from_history`, `get_preference_score`.
- **Context Tool**: `get_weather(location, date_range)` via Google Weather API + `get_occasion(date)` via Calendar or user input.
- **Metrics Tool**: `log_event`, `compute_metrics` for acceptance rate, Avg rating, etc.
- **(V2)** `VisionIngest Tool`: optional Google Vision / PaLM multimodal ingestion for wardrobe images or receipts (kept in backlog by design).

## 6. Agentic Framework & Flows

### 6.1 Agent Roles (ADK Graph)

- **Parallel Intake Agent**: fan-outs Context Collector + Wardrobe Cataloger, merges their outputs, and surfaces retry metadata back to the Sequential Designer.
- **Context Collector**: builds context objects per request—daily (`date`, `location`, `temperature_range`, `precipitation`, `occasion_tag`) or travel (`destination`, `trip_purpose`,`start_date`, `end_date`, `avg_temp`, `dress_code`).
- **Wardrobe Cataloger**: manages adds/edits, filters clean/available items, updates wear data, and provides subsets (e.g., “clean items suitable for 10–18 °C and business casual”).
- **Outfit Designer**: combines context + wardrobe subsets to produce candidate outfits while respecting banned combos and category completeness.
- **Preference & Ranking Agent**: scores candidates using historical ratings and context rules, guarantees each slate includes ≥1 previously loved outfit (≥4 stars) and ≥1 fresh combo, and returns the final top 3.
- **Explanation Agent**: annotates each option with concise reasoning; uses same mechanism for travel capsules.
- **Laundry Advisor (backlog)**: future agent that will watch wardrobe usage signals (e.g., days since last worn) to surface laundry nudges once that feature returns to scope.
- **Feedback & Learning Agent**: prompts users for 1–5 star ratings + optional tags after selections, captures “never suggest” events, updates preferences, and persists feedback.

### 6.2 Example Flows

1. **Daily Outfit Suggestion**
   - User request → Parallel Intake Agent (Context Collector + Wardrobe Cataloger in parallel) → Outfit Designer (candidate set) → Preference & Ranking Agent.
   - Preference & Ranking Agent enforces variety: at least one option the user previously rated ≥4 stars in a similar context, at least one never-before-worn combo, and the final slot balances exploration vs. exploitation so the carousel feels fresh.
   - Explanation Agent annotates the three choices → User selects an outfit → Wardrobe Cataloger marks items worn → Feedback & Learning Agent immediately (or at end of day) prompts for a 1–5 star rating + optional tags and saves the preference.

2. **Travel Mode**
   - User provides trip details → Parallel Intake Agent gathers travel context + wardrobe subset → Outfit Designer (travel mode) builds capsule → Preference Agent biases toward high-rated pieces → Explanation Agent articulates capsule rationale → Output includes packing list and per-day plan.

## 7. Kaggle + Google ADK Fit

### 7.1 Runtime & Artifacts

- Primary store remains the SQLite DB defined above. All agents/tools run locally via Google ADK, and nightly snapshots are kept as `.db` files for reproducibility.
- Instead of packaging CSVs, the repo will include:
  - The SQLite database (read-only copy for reviewers).
  - Documentation on how to run the orchestrator locally with mock weather/calendar responses.

### 7.2 Evaluation & Metrics

- **Primary metric**: next-day outfit acceptance rate predicted vs. actual, evaluated locally via Brier score and calibration curves.
- **Secondary metrics**: average rating of accepted outfits (goal ≥4.0) and travel coverage (% of trip days covered without repeated outfits).
- **Baselines**: weather/occasion heuristic without learning, plus a “popular items” recommender.

### 7.3 Roadmap & Nice-to-Haves

- **V1 (Capstone deliverable)**: General agentic framework based on Google adk, SQLite-backed tools, daily/travel flows, explanations, preference learning
- **V2 (Post-capstone backlog)**:
  - Laundry Advisor + core-item hints that resurrect `wears_since_wash`/usage tracking once data volume warrants it.
  - `VisionIngest Tool` using Google Vision or PaLM multimodal to parse closet photos/receipts into structured wardrobe entries.
  - Multimodal chat/voice interface leveraging ADK speech tools for hands-free outfit requests.
  - Potential monetization through contextual ads or affiliate offers from apparel brands. When FreshFit notices a gap (e.g., no waterproof boots in the wardrobe), the Recommendation Agent can suggest specific items, surface brand promotions, or provide “buy” links. All ads should be optional, clearly labeled, and based on user-consented signals so they align with ADK safety policies.

## 8. Risks & Mitigations

- **Data sparsity**: bootstrap with heuristic rules and encourage quick-add wardrobe entries; evaluate preference learning with smoothing.
- **Tool failures (weather/calendar)**: capture `fallback_reason`, default to recent weather averages, and surface friendly user messaging.
- **Privacy**: store wardrobe descriptors only (no PII), enable export/delete on demand, and document ADK compliance checks.

## 9. Summary

FreshFit delivers a multi-agent, explainable wardrobe assistant backed by a simple SQLite schema and Google ADK tools. The project balances practical daily utility (contextual outfit suggestions today, laundry nudges in a future release) with analytical rigor (preference learning, metrics, Kaggle-ready datasets) suitable for a Kaggle capstone focused on the Google ADK ecosystem.
