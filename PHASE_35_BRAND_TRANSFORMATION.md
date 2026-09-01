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

## 2. Specialist agents (`service.py`)

Each agent = prompt (injects the relevant research) → Claude JSON → safe fallback → persisted artifact.

| Agent | Etapa | Output table |
|---|---|---|
| `DiagnosisAgent` | 0 | `bt_diagnoses` — Referent Potential Score 0-100, commoditization level, symptoms, root causes, top-3 leverage moves, 6-axis scorecard |
| `PositioningAgent` | 1 | `bt_positioning_statements` — Dunford statement, category name, POV manifesto, the enemy, one-liner |
| `BrandIdentityAgent` | 2 | `bt_brand_identities` — primary archetype, rename call, tagline, manifesto, voice do/don't, visual brief |
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
| `rediagnosis` | Re-run the diagnosis on a schedule; track Referent Potential Score over time |
| `fomo_cadence` | Generate the next cycle's FOMO activation on cadence |
| `brand_consistency_monitor` | Score sample material 0-100 vs brand voice/positioning; flag violations + fixes |
| `positioning_drift_watch` | Detect drift from the chosen category/POV |
| `competitor_narrative_watch` | Flag when competitor messaging encroaches on the owned position |

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

## 5. Wiring

- Router registered in `backend/app/main.py` (`_try_include`, defensive).
- Tables created at startup by `bootstrap.ensure_brand_transformation_tables`, called from `sellbot.py` alongside ledger/ad_budget/forecasting (migrations are disabled in this deployment).
- LLM: `claude-opus-5`, lazy anthropic client (missing key never breaks startup; agents fall back to templated output).

---

## 6. Next steps

1. ~~Wire the 5 automation types into the Redis/celery scheduler for real cadence.~~ ✅ done — see §4.
2. Feed `FOMOEngineAgent` output into the existing `fomo` / `fomo_generation` domains so playbook mechanisms become live campaigns.
3. Connect `BrandIdentityAgent` visual brief to the design/asset pipeline.
4. Cross-link `PositioningAgent` with `competitive_intelligence` for live enemy tracking.
5. Add a frontend program dashboard (stage progress + artifacts + roadmap board).
