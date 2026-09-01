# Phase 35 — Brand Transformation Agents & Automations

AI agents + automations that turn commoditized, mediocre businesses into
category **references**. Covers rebranding, marketing, branding, business
restructuring, sales marketing, and business-model innovation as one staged
program.

Domain: `backend/app/domains/brand_transformation/`
Mount: `/api/v1/businesses/{business_id}/brand-transformation`

---

## 1. Research baseline (embedded in `knowledge.py`)

### FOMO / desire mechanics (`FOMO_LEVERS`)
7 levers, each with mechanism · tactics · failure mode (anti-fake) · real cases:

| Lever | Core mechanism | Exemplars |
|---|---|---|
| Artificial scarcity | Cap supply below demand on purpose | Supreme, Hermès Birkin, McRib, Ferrari |
| Social-proof velocity | Show peers/insiders already in; momentum = reason | Amazon reviews, Booking.com, GoPro |
| Exclusivity & status | Membership as identity badge | Amex Centurion, Soho House, Clubhouse, SNKRS |
| Identity & tribe | Sell a worldview + an enemy, not a product | Patagonia, Harley, Liquid Death, Tesla |
| Anticipation & ritual | Engineer the wait + a repeating cue | Apple keynotes, Glossier/Yeezy drops |
| Loss & urgency framing | Frame offer as something being taken away | Course launches, grandfather pricing |
| Velocity of novelty | Constant small newness → attention + talk | Oreo, Spotify Wrapped, Nike collabs |

### Iconic brand origin playbooks (`BRAND_ORIGIN_PLAYBOOKS`)
12 teardowns of "simple product → billions" — the **real engine**, not the myth:

- **McDonald's** — not food; a franchised operating system + real estate.
- **Coca-Cola** — distribution ubiquity + owned emotional occasion + formula mythology.
- **Red Bull** — a media company that funds itself by selling a can.
- **Starbucks** — the "third place": reprice a commodity by selling context + ritual.
- **Nike** — attach the product to who the customer wants to become.
- **Supreme** — constrain supply, own a cadence, let resale be the ad budget.
- **Apple** — vertical control + ceremony + taste → set price instead of taking it.
- **Tesla** — a point of view + a waitlist replaces a marketing budget.
- **Instagram/TikTok/YouTube** — two-sided attention loop; each user raises value for the next.
- **Liquid Death** — in a commodity, an extreme distinctive voice IS the differentiation.
- **Decathlon** — own the whole chain → win on value.
- **Gucci/Versace** — protecting price + scarcity IS the product for status goods.

### Strategy frameworks (`FRAMEWORKS`)
Jung 12 archetypes · Play Bigger category design · Dunford positioning (5 components) ·
Hormozi value equation · Business Model Canvas · Gassmann 55 patterns · Blue Ocean ERRC ·
growth loops · E-E-A-T authority · brand-voice system.

---

### Quality bar (`knowledge.QUALITY_BAR` + `CLICHE_BLOCKLIST`)
Concrete rubric injected into every agent's system prompt: specific-over-generic,
23-phrase cliché blocklist ("synergy", "world-class", "game-changer"…), explicit
definitions of *ocurrencia* (non-obvious but defensible) and *elocuencia* (short
rhythmic sentences, concrete imagery, no hedging), causal-not-decorative
reasoning, name-your-sources.

---

## 2. Specialist agents (`service.py`)

**Two-pass pipeline** (`_draft_then_refine`): every agent does
DRAFT → adversarial self-critique against the quality bar → REFINED final
(same JSON keys, sharper prose, clichés cut, precedent added) → safe fallback →
persisted artifact. Two Claude calls per agent; the refine pass is skipped if the
draft already fell back. Refine also appends `confidence` (0-100 self-assessed
rigor) and `frameworks_applied` (names actually used) to every artifact.

The three creative agents (positioning, brand identity, FOMO) also emit
`alternative_angles` — 2-3 *genuinely different* strategic bets with a
"when to pick" condition, so the user picks rather than gets one take.

| Agent | Etapa | Output table |
|---|---|---|
| `DiagnosisAgent` | 0 | `bt_diagnoses` — **v2, multi-lens.** Headline score + commoditization level, then: `commoditization_analysis` (price/product/distribution/brand each 0-5 + the tell), `scorecard` (6 axes scored against `REFERENT_SCORECARD_RUBRIC` — explicit 0-5 definitions per axis), `referent_gap` (per axis: current → what a referent looks like → the closing move), `closest_precedent` (which of the 12 origin playbooks fits + what transfers / what doesn't), `moat_assessment` (has/buildable moat + type from `MOAT_TYPES`), `quick_wins` (≤30d) vs `structural_moves` (6-12mo), `kill_criteria` (when *not* to chase referent status). Accepts optional structured evidence (pricing, channels, margin, repeat rate, customer quotes…); `evidence_quality` (thin/partial/solid) caps `confidence` at 55/75/92. `GET …/agents/diagnosis/history` for score trend. |
| `PositioningAgent` | 1 | `bt_positioning_statements` — **v2, category-design workshop.** `alternatives_matrix` (per alternative: why tolerated / what customer keeps / loses), `attribute_value_proof` (attribute → value → the proof point that makes it believable), `enemy_analysis` (enemy + per-check ENEMY TEST results + pass/fail), `pov_validation` (who nods / bristles / cost to hold + 0-2 scores on polarising·defensible·actionable·ownable·durable), `category_decision` (`play_in_existing` vs `design_new`, justified by the CATEGORY-KING TEST, + name candidates), `reframe` (FROM→TO), full messaging kit (`positioning_statement`, `one_liner`, `elevator_pitch` 30s, 3 `messaging_pillars` w/ proof), `migration_risks` (who repositioning loses + acceptable? + mitigation). Consumes the prior diagnosis's `referent_gap` / `closest_precedent` / `moat_assessment`. |
| `BrandIdentityAgent` | 2 | `bt_brand_identities` — **v2, full identity system.** `archetype_analysis` (shortlist, each scored 0-2 on positioning-fit / differentiation-in-category / founder-authenticity, then primary+secondary+blend%), `story_spine` (world→problem(=the enemy)→insight→mission, reused by GTM), `verbal_identity` (voice attributes w/ "sounds like / not", use+ban lexicon incl. cliché blocklist, rhythm, humour, first-line rule), 5 `sample_rewrites` across touchpoints, `naming` (keep/rename/add-descriptor decision + candidates scored 0-2 on 6 `NAMING_CRITERIA` + the deciding question), actionable `visual_brief` (palette *roles*, type pairing rationale, imagery do/don't, logo direction, 5 moodboard search terms), `brand_architecture` (endorsement model + future-product naming), `identity_consistency_rules` (5 non-negotiables → feed `brand_consistency_monitor`), `taglines_alt` (3). Consumes positioning via `_positioning_digest`. |
| `BusinessModelAgent` | 3 | `bt_business_model_redesigns` — new canvas, applied patterns, grand-slam offer, pricing architecture, ERRC grid |
| `FOMOEngineAgent` | 4 | `bt_fomo_playbooks` — 4-6 tuned mechanisms w/ implementation + KPI + anti-fake guardrail, launch ritual, cadence |
| `GoToMarketAgent` | 5 | `bt_gtm_plans` — primary growth loop, channel map, lightning-strike launch, funnel, 90-day plan |
| `RestructuringAgent` | 6 | `bt_restructuring_plans` — kill/keep/scale, org redesign, 3 core processes, promise KPIs |

---

## 3. Staged program (`orchestrator.py` — `TransformationOrchestrator`)

`bt_transformation_programs` tracks one business through 8 etapas. Each stage's
artifact is fed forward as context to the next. Etapa 7 (`roadmap`) synthesizes
everything into a **90 / 180 / 365-day roadmap** + review ritual + metrics board.

Etapas: `diagnosis → positioning → brand_identity → business_model → fomo_engine → gtm → restructuring → roadmap`

Endpoints:
- `POST /programs` — create (needs business profile)
- `POST /programs/{id}/stages/{stage_key}/run` — run one etapa, advance pointer
- `POST /programs/{id}/run-all` — run every etapa end-to-end
- `GET /programs/{id}` — state, completed stages, artifacts, roadmap, metrics board

Single agents also callable directly: `POST /agents/{diagnosis|positioning|brand-identity|business-model|fomo-engine|gtm|restructuring}`.

Reference (no auth cost beyond login): `GET /stages`, `/knowledge/fomo-levers`, `/knowledge/brand-origins`, `/knowledge/frameworks`.

---

## 4. Automations (`bt_automations` + `run_automation`)

| Type | What it does |
|---|---|
| `rediagnosis` | Re-run diagnosis; loads prior diagnosis, feeds prior score+symptoms into the prompt, persists `score_delta` + `compared_to_diagnosis_id`, returns `trend` (improving/flat/declining) + what's still unaddressed |
| `fomo_cadence` | Generate ONLY the next cycle's shippable activation — one lead mechanism + ritual beat + copy hook |
| `brand_consistency_monitor` | Grade sample material 0-100 vs the brand voice system + cliché blocklist; per-violation offending phrase + rewrite + single priority fix |
| `positioning_drift_watch` | Flag when messaging stops fighting the stated enemy / drifts back to feature-listing |
| `competitor_narrative_watch` | Flag competitor encroachment on the owned position + how to counter |

`POST /automations` to create, `POST /automations/{id}/run` to execute now.

**Scheduled execution (wired):** Celery task
`app.tasks.brand_transformation_tasks.run_due_brand_automations`, beat key
`brand-transformation-automations`, fires **hourly**. Each `bt_automations` row
only runs when its own `schedule` interval has elapsed since `last_run_at`
(`hourly` / `daily` / `weekly` / `monthly` (30d, default) / `quarterly` (90d);
30-min slack so jitter never skips a cycle). Task module added to
`celery_app._modules` and `brand_transformation.models` to the worker's mapper
import list.

---

## 4b. AI availability & provenance

`service._resolve_api_key()` reads `settings.ANTHROPIC_API_KEY` then env
`ANTHROPIC_API_KEY` / `CLAUDE_API_KEY` / `ANTHROPIC_KEY` / `ANTHROPIC_AUTH_TOKEN`,
passed explicitly to `anthropic.Anthropic()`. With no key, `_ask_json`
short-circuits to fallback and logs ONE loud error.

Every artifact records `generated_by` (`"llm"` | `"fallback"` | `"unknown"`) so
templated output is never mistaken for AI. Automation results carry `llm_used`.
`GET …/brand-transformation/health` → `{llm_available, model, agents_mode}`.

> **Prod status (2026-09-01):** Railway backend has **no Anthropic key** →
> `agents_mode: "fallback"`, every artifact `generated_by: "fallback"`. Set
> `ANTHROPIC_API_KEY` on the Railway service to switch to `"ai"`.

## 5. Wiring

- Router registered in `backend/app/main.py` (`_try_include`, defensive).
- Tables created at startup by `bootstrap.ensure_brand_transformation_tables`, called from `sellbot.py` alongside ledger/ad_budget/forecasting (migrations are disabled in this deployment). Bootstrap also runs idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` patches for the post-v1 columns (`confidence`, `frameworks_applied`, `alternative_angles`, `score_delta`, `compared_to_diagnosis_id`).
- LLM: `claude-opus-5`, lazy anthropic client (missing key never breaks startup; agents fall back to templated output).

---

## 6. Next steps

1. ~~Wire the 5 automation types into the Redis/celery scheduler for real cadence.~~ ✅ done — see §4.
2. Feed `FOMOEngineAgent` output into the existing `fomo` / `fomo_generation` domains so playbook mechanisms become live campaigns.
3. Connect `BrandIdentityAgent` visual brief to the design/asset pipeline.
4. Cross-link `PositioningAgent` with `competitive_intelligence` for live enemy tracking.
5. Add a frontend program dashboard (stage progress + artifacts + roadmap board).
