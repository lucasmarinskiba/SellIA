# SellIA SEO Platform — Complete Documentation

## Overview

SellIA's SEO Platform delivers **business-measurable** organic traffic growth through four integrated domains:

1. **SEO Intelligence** — Strategic keyword & competitive analysis
2. **FOMO+SEO** — Psychological copy optimization combining urgency with SEO metrics
3. **SEO Auto-Optimization** — Automatic title/meta/content optimization with rank tracking
4. **SEO Specialist Agents** — Content generation, backlinks, reviews, calendar, entities, multi-location, topical clusters, and a cross-domain audit orchestrator

Together, they form a closed loop: analyze → optimize → measure → repeat. Domain 4 (`seo_agents`) is what answers "what does SellIA need to actually rank a user's products/services" — it turns the first three domains' *analysis* into concrete *content, outreach, and structure*.

---

## 1. SEO Intelligence Domain

**Purpose:** Track keyword performance, page health, competitor strength, and generate prioritized recommendations.

### Models

#### Keyword
```python
- search_volume: int  # Monthly searches
- difficulty: 0-100 scale
- competition: normalized bid price
- intent: transactional / informational / navigational
- trend: positive / stable / declining
- current_rank: position in SERP (1-100)
```

**Use Case:** Track which keywords drive traffic; identify underserving opportunities (low difficulty + high volume).

#### Ranking
```python
- impressions: daily Google Search Console data
- clicks: daily GSC data
- ctr: impressions → clicks ratio
```

**Use Case:** Monitor SERP performance over time; detect rank drops before traffic impact.

#### PageOptimization
```python
- seo_score: 0-100 (title/meta/H1 optimization level)
- core_web_vitals: LCP/FID/CLS measured by Lighthouse
- organic_traffic: monthly sessions from GA4
- indexed_pages: count in Google Index
```

**Use Case:** Dashboard showing which pages need attention; rank all pages on one metric.

#### CompetitorAnalysis
```python
- domain_authority: Moz DA or similar
- backlink_count: referring domains
- estimated_monthly_revenue: from traffic × keyword CPC
```

**Use Case:** Identify competitor strengths; spot gaps in their backlink profile.

#### SEORecommendation
```python
- priority: critical / high / medium / low
- impact: projected traffic increase %
- status: pending / approved / implemented / failed
```

**Use Case:** Prioritized action list for marketing; track what was tried and impact.

### Service Methods

**KeywordService:**
- `add_keyword(business_id, keyword, difficulty, volume, intent)` — track new keyword
- `update_rank(keyword_id, new_rank)` — daily rank check
- `list_keywords(business_id, sorted_by="traffic")` — current watchlist
- `get_trending_keywords(business_id, days=30)` — rising opportunities

**PageOptimizationService:**
- `create_page(business_id, url, keyword_target)` — add page to tracking
- `update_page(page_id, seo_score, organic_traffic)` — sync metrics
- `seo_health(business_id)` — dashboard: overall_score, indexed_pages, top performers, bottom performers

**CompetitorAnalysisService:**
- `analyze_competitor(business_id, domain)` — one-time deep analysis
- `update_analysis(competitor_id, new_backlinks, new_revenue)` — ongoing tracking
- `list_competitors(business_id)` — all tracked competitors

**SEORecommendationService:**
- `create_recommendation(business_id, type, impact_pct, priority)` — propose action
- `list_recommendations(business_id, priority="high")` — sorted backlog
- `update_status(recommendation_id, status, execution_date)` — mark done + track timing

### API Endpoints

```
POST   /api/v1/businesses/{business_id}/seo/keywords
       — Add keyword (keyword, difficulty, volume, intent)
       
GET    /api/v1/businesses/{business_id}/seo/keywords
       — List keywords (query: sort_by=traffic|difficulty|trend)
       
GET    /api/v1/businesses/{business_id}/seo/keywords/trending
       — Top 10 rising keywords (last 30 days)

POST   /api/v1/businesses/{business_id}/seo/pages
       — Track page (url, keyword_target)
       
PATCH  /api/v1/businesses/{business_id}/seo/pages/{page_id}
       — Update metrics (seo_score, organic_traffic)
       
GET    /api/v1/businesses/{business_id}/seo/health
       — Dashboard (overall_score, page_count, indexed, top_performers)

POST   /api/v1/businesses/{business_id}/seo/competitors
       — Add competitor (domain)
       
GET    /api/v1/businesses/{business_id}/seo/competitors
       — List all (sorted by DA)

POST   /api/v1/businesses/{business_id}/seo/recommendations
       — Propose action (type, priority, impact_pct)
       
GET    /api/v1/businesses/{business_id}/seo/recommendations
       — Backlog (query: priority, status)
       
PATCH  /api/v1/businesses/{business_id}/seo/recommendations/{rec_id}
       — Update status + track timing
```

---

## 2. FOMO+SEO Domain

**Purpose:** Generate psychological copy combining FOMO triggers with SEO metrics; A/B test via CTR/conversion rate.

### Models

#### FOMOSEOCopy
```python
- urgency_trigger: "Today", "Just X left", "Ends tonight"
- social_proof_element: "500+ customers", "9.8/10 rating"
- scarcity_message: "Only 3 spots", "Rare find"

- title: (50-60 chars optimal)
- meta: (150-160 chars optimal)
- keyword: presence in both + density check

- ctr_score: 0-100 (power words, urgency, social proof)
- conversion_score: 0-100 (based on A/B winner)
- seo_score: 0-100 (keyword + length compliance)
```

**Scoring:**
- SEO: title length (50-60 optimal = 100), meta length (150-160 optimal = 100), keyword presence
- CTR: power words like "Best" +15%, urgency +20%, social proof +15%, baseline 50
- Conversion: empirical from A/B test, automatic winner selection

#### A_B_TestCopy
```python
- variant_a: original copy
- variant_b: alternative (usually higher CTR projected)

- ctr_a: measured clicks / impressions
- ctr_b: measured clicks / impressions
- conversion_rate_a: conversions / clicks
- conversion_rate_b: conversions / clicks

- winner: auto-determined by higher conversion_rate
- winner_confidence: if variant B > 20% above A
```

**Use Case:** Launch two title/meta combos; system picks winner after 100+ conversions; auto-pause loser.

#### CopyPerformanceMetric
```python
- impressions: daily Google Search Console
- clicks: daily GSC
- conversions: from GA4 event tracking
- ctr: clicks / impressions
- avg_position: average SERP rank
```

**Use Case:** Track copy performance over time; detect seasonal decay.

### Service Methods

**FOMOSEOCopyService:**
- `_calculate_seo_score(title, meta, keyword)` — normalize to 0-100
  - Title: +50 if 50-60 chars, scale linearly outside range
  - Meta: +50 if 150-160 chars, scale linearly
  - Keyword: +50 if present in both title + meta
- `_calculate_ctr_score(urgency, social_proof, power_words)` — +baseline 50 + modifiers
  - Urgency trigger: +20
  - Social proof: +15
  - Power words ("Best", "Free", "Proven"): +15
- `generate_copy(business_id, keyword, urgency_level, social_proof)` — create FOMOSEOCopy
- `list_copy(business_id, sorted_by="ctr_score")` — all copy variants ranked
- `get_copy(copy_id)` — one variant + performance metrics

**A_B_TestService:**
- `create_test(business_id, variant_a, variant_b)` — launch test
- `update_results(test_id, impressions_a, clicks_a, conversions_a, impressions_b, clicks_b, conversions_b)` — feed data
  - Calculates CTR and conversion_rate for both
  - Auto-determines winner: variant with higher conversion_rate wins
  - Sets winner_confidence if winner margin > 20%
- `list_tests(business_id, status="active")` — ongoing + completed

### API Endpoints

```
POST   /api/v1/businesses/{business_id}/fomo-seo/generate
       — Create copy (keyword, urgency, social_proof)
       → title, meta, ctr_score, seo_score, conversion_score
       
GET    /api/v1/businesses/{business_id}/fomo-seo/copy
       — List all copy variants (query: sorted_by=ctr_score|seo_score)

POST   /api/v1/businesses/{business_id}/fomo-seo/ab-test
       — Launch A/B test (variant_a, variant_b)
       → test_id, estimated_duration_days
       
PATCH  /api/v1/businesses/{business_id}/fomo-seo/ab-test/{test_id}
       — Update test results (impressions, clicks, conversions for both variants)
       → ctr_a, ctr_b, conversion_rate_a, conversion_rate_b, winner
       
GET    /api/v1/businesses/{business_id}/fomo-seo/ab-test
       — List all tests (query: status=active|completed)
```

**Example Response:**
```json
{
  "copy_id": "abc123",
  "title": "Best SEO Tools 2024 | Rank #1 Fast",
  "meta": "Proven SEO tools trusted by 5,000+ marketers. Start free trial today →",
  "urgency_trigger": "Today",
  "social_proof": "5000+ users",
  "ctr_score": 78,
  "seo_score": 92,
  "conversion_score": 0,
  "message": "Ready to A/B test — generate high-CTR variant B to compare"
}
```

---

## 3. SEO Auto-Optimization Domain

**Purpose:** Automatically suggest + execute + measure SEO optimizations; aggregate impact across all pages.

### Models

#### OptimizationTask
```python
- task_type: title_rewrite | meta_optimize | keyword_inject | speed_improve | structure_enhance
- priority: critical / high / medium / low
- status: pending → in_progress → completed | failed

- proposed_title, proposed_meta, proposed_h1: specific changes
- potential_impact: high / medium / low
- estimated_traffic_lift_pct: 0-100

- pre_optimization_rank, post_optimization_rank: rank before/after
- rank_improvement: pre - post (positive = better)
- traffic_change_pct: % increase in organic sessions
```

**Use Case:** Automation that reads pending recommendations → creates task → marks as executed → tracks results.

#### TitleOptimization
```python
- variant_a, variant_b, variant_c: three title candidates
- variant_a_projected_ctr, _b, _c: CTR projection (baseline 2.5%)
  - Baseline: 2.5%
  - Variant A (year indicator "2024"): +15% → 2.88%
  - Variant B (superlative "Best"): +25% → 3.13%
  - Variant C (structured guide): +18% → 2.95%
- selected_variant: chosen for deployment
```

**Use Case:** Run 3 title variations through CTR predictor; pick B for deployment; track actual CTR.

#### MetaOptimization
```python
- variant_a, variant_b: two meta candidates
- variant_a_projected_ctr, variant_b_projected_ctr: CTR projection
  - Baseline: 2.0%
  - Variant A (descriptive): +20% → 2.4%
  - Variant B (CTA-driven "Free trial today"): +35% → 2.7%
- selected_variant: chosen for deployment
```

**Use Case:** Automatically generate 2 versions; select B (CTA version) as default.

#### ContentOptimization
```python
- keyword_target, current_keyword_density, word_count
- recommended_word_count: optimal length for keyword
- recommendations: {"add_h2": ["How to Use", "Benefits"], "add_internal_links": 3}
- readability_score, engagement_score: 0-100
```

**Use Case:** Analyze page; suggest H2 additions + internal links + word count expansion.

### Service Methods

**TitleOptimizationService:**
- `generate_title_variants(business_id, page_url, current_title, keyword_target)` → 3 variants with CTR projections
- `select_variant(optimization_id, variant)` → mark chosen for deployment

**MetaOptimizationService:**
- `generate_meta_variants(business_id, page_url, current_meta, keyword_target, call_to_action)` → 2 variants
- (select variant is optional; B recommended by default)

**ContentOptimizationService:**
- `analyze_content(business_id, page_url, keyword_target, word_count, keyword_density, readability_score)` → recommendations + scoring

**OptimizationTaskService:**
- `create_task(business_id, page_url, task_type, priority)` → status=pending
- `execute_task(task_id, applied_by)` → status=in_progress, sets applied_at
- `track_results(task_id, pre_rank, post_rank, traffic_change_pct)` → status=completed, calculates rank_improvement
- `list_pending_tasks(business_id, priority=None)` → all pending for this business
- `impact_dashboard(business_id)` → aggregates:
  - completed_tasks: count
  - total_rank_improvement: sum of all rank improvements
  - avg_traffic_lift_pct: mean traffic change
  - tasks_by_type: grouped count

### API Endpoints

```
POST   /api/v1/businesses/{business_id}/seo-optimization/titles/generate
       — Generate 3 title variants (page_url, current_title, keyword_target)
       → variant_a/b/c + projected CTR for each

POST   /api/v1/businesses/{business_id}/seo-optimization/meta/generate
       — Generate 2 meta variants (page_url, current_meta, keyword_target, cta)
       → variant_a/b + projected CTR for each, "recommended": "variant_b"

POST   /api/v1/businesses/{business_id}/seo-optimization/content/analyze
       — Analyze + recommend (page_url, keyword_target, word_count, keyword_density, readability)
       → recommendations, recommended_word_count, engagement_score

POST   /api/v1/businesses/{business_id}/seo-optimization/tasks
       — Create optimization task (page_url, task_type, priority)
       → task_id, status=pending, estimated_impact

GET    /api/v1/businesses/{business_id}/seo-optimization/tasks/pending
       — List pending tasks (query: priority)
       → total_pending, tasks[].{task_id, type, priority, page, impact}

PATCH  /api/v1/businesses/{business_id}/seo-optimization/tasks/{task_id}/execute
       — Mark task applied (executed_by)
       → status=in_progress, applied_at

PATCH  /api/v1/businesses/{business_id}/seo-optimization/tasks/{task_id}/results
       — Record results (pre_rank, post_rank, traffic_change_pct)
       → rank_improvement, traffic_lift_pct, status=completed

GET    /api/v1/businesses/{business_id}/seo-optimization/dashboard
       — Impact summary
       → completed_tasks, total_rank_improvement, avg_traffic_lift_pct, tasks_by_type
```

---

## 4. Integration: Complete Workflow

### Workflow 1: Daily Optimization Loop

```
1. SEO Intelligence → list keywords with difficulty < 50 and search_volume > 100
2. SEO Intelligence → seo_health() → find pages with seo_score < 70
3. For each low-scoring page:
   a. SEO Auto-Optimization → generate_title_variants()
   b. SEO Auto-Optimization → generate_meta_variants()
   c. Create optimization task (type=title_rewrite or meta_optimize, priority=medium)
4. SEO Auto-Optimization → list_pending_tasks() → review queue
5. Execute approved tasks
6. After 2 weeks: track_results() → measure rank + traffic change
```

### Workflow 2: FOMO Copy Campaign

```
1. SEO Intelligence → get_trending_keywords() → select top 3 rising keywords
2. For each keyword:
   a. FOMO+SEO → generate_copy(keyword, urgency="high", social_proof="5000+ users")
   b. Use returned title + meta for A/B test setup
   c. FOMO+SEO → create_test(variant_a=current_copy, variant_b=generated_copy)
3. Deploy both variants in GA/GSC tracking
4. After 100 conversions per variant:
   a. FOMO+SEO → update_results() with impression/click/conversion data
   b. System auto-selects winner
   c. Pause loser; expand winner to 100% traffic
```

### Workflow 3: Competitor Gap Analysis

```
1. SEO Intelligence → list_competitors()
2. For each competitor:
   a. analyze_competitor(domain) → DA, backlinks, estimated revenue
   b. Compare backlink domains to own backlink list
   c. Identify unlinked domains (competitor has, we don't)
3. Create SEO recommendations for outreach to those domains
4. Track approval + execution timeline
```

---

## 5. Deployment & Performance

### Caching Strategy

**High-traffic endpoints (cache 1 hour):**
- `GET /seo/keywords` → list_keywords() called per-view
- `GET /seo/health` → aggregates 50+ pages in seo_score calculation
- `GET /seo/competitors` → static list, refreshed daily via analytics sync
- `GET /fomo-seo/copy` → all copy for a business (100+ records)
- `GET /seo-optimization/dashboard` → aggregates 1000+ tasks

**Medium-traffic endpoints (cache 15 min):**
- `GET /seo/keywords/trending` → ranked list, expensive sort
- `PATCH /seo-optimization/tasks/{id}/results` → only after manual data entry (rare)

**No cache (always fresh):**
- `POST` endpoints (create new data)
- `PATCH` endpoints with immediate impact (update_page, update_status)

### Database Optimization

**Indexes:**
- `keywords(business_id, difficulty)` — filter by difficulty
- `page_optimization(business_id, seo_score)` — sort by health
- `optimization_task(business_id, status, priority)` — list pending
- `fomo_seo_copy(business_id, ctr_score)` — ranked by performance

**Query optimization:**
- `seo_health()` uses `SELECT COUNT(*), MIN(seo_score), MAX(seo_score)` (avoid full scan)
- `impact_dashboard()` uses `SUM(rank_improvement), AVG(traffic_change_pct)` in DB, not Python
- `list_competitors()` joins `analysis` only once (avoid N+1)

---

## 6. Testing

**Unit tests** verify:
- Scoring algorithms (SEO + CTR + conversion)
- Task state transitions (pending → in_progress → completed)
- Dashboard aggregations

**Integration tests** verify:
- A/B test winner selection (variant B > A's conversion rate)
- Rank improvement calculation (pre=15, post=8 → improvement=7)
- Title variant generation (3 variants, all 50-60 chars, variant B highest CTR)

---

## 7. Monitoring

**Key metrics:**
- SEO Health Score: avg seo_score across all pages (target ≥ 80)
- Organic Traffic MoM: % increase (baseline + optimization impact)
- Average Rank: mean position across tracked keywords (target < 15)
- A/B Test Win Rate: % of tests where variant B wins (target ≥ 60%)
- Optimization Execution Rate: completed tasks / created tasks (target ≥ 80%)

**Alerts:**
- If avg seo_score drops 10+ points in 7 days → content removed or penalized
- If A/B test winner has < 20% confidence → inconclusive, extend test
- If optimization task pending > 30 days → escalate for review

---

## 8. SEO Specialist Agents Domain (`seo_agents`)

**Purpose:** Answer "what does SellIA need to actually rank a user's products/services" — turns analysis from domains 1-3 into concrete content, outreach, structure, and a single prioritized action plan. 8 services, 32 endpoints, all under `/api/v1/businesses/{business_id}/seo-agents/*`.

### 8.1 Content Generation (`ContentGenerationService`)

Generates SEO-optimized product/service copy via Claude (`claude-opus-5`): title (50-60 chars), meta (150-160 chars), H1, 2000+ word body, H2 sections, internal link suggestions.

`seo_score` formula: title length band (+35 max), meta length band (+35 max), keyword in title (+15), keyword in meta (+10), keyword ≥3x in body (+10) — capped at 100.

```
POST /content/generate   — content_type, target_keyword, product_name, product_description, tone
GET  /content            — list (cached 1h)
GET  /content/{id}       — full body + H2s + internal links
```

### 8.2 Keyword Gap Analysis (`CompetitorKeywordService`)

`opportunity_score = search_volume * (1 - difficulty/100) * rank_gap_factor` — `rank_gap_factor` is 1.5x when a competitor ranks for a keyword the business doesn't, 1.0x otherwise.

```
POST /keywords/analyze-gap              — keyword, search_volume, difficulty, business_rank, competitor ranks
GET  /keywords/gaps                     — ranked by opportunity (cached 15min)
POST /keywords/identify-opportunities   — top 10 gaps -> KeywordOpportunity records
GET  /dashboard                         — content_generated, avg_seo_score, keyword_opportunities, estimated_monthly_traffic
```

### 8.3 Backlink Strategy (`BacklinkStrategyService`)

`relevance_score` = niche/domain keyword overlap ratio (0-100). `priority_score = DA*0.6 + relevance*0.4` — weighted so a highly relevant DA30 blog can outrank an irrelevant DA70 directory for actual outreach value. Outreach funnel: `identified → contacted → negotiating → acquired/rejected`.

```
POST  /backlinks/opportunities        — domain, opportunity_type, domain_authority, niche/domain keywords
GET   /backlinks/opportunities        — ranked by priority (cached 1h)
PATCH /backlinks/opportunities/{id}   — advance funnel status
```

### 8.4 Review Orchestration (`ReviewOrchestrationService`)

`create_campaign` (pending→sent) → `record_review` (→completed) auto-refreshes a `ReviewAggregate` rollup (total, average, star buckets) on every completed review — feeds `schema.org` `AggregateRating` markup directly.

```
POST  /reviews/campaigns              — solicit review from a customer
PATCH /reviews/campaigns/{id}/record  — record rating (1-5) + refresh aggregate
GET   /reviews/campaigns              — list, filterable by status
GET   /reviews/aggregate              — AggregateRating rollup (cached 1h)
```

### 8.5 Content Calendar (`ContentCalendarService`)

`generate_calendar` spaces one entry per keyword by `cadence_days`, stopping once the schedule would exceed the `days` window. `content_type` rotates round-robin: `blog_post → landing_page → guide → video`. `priority` derives from keyword opportunity score: ≥70 high, ≥40 medium, else low.

```
POST  /calendar/generate    — target_keywords, days, cadence_days, keyword_opportunities
GET   /calendar               — publication order (cached 30min)
GET   /calendar/upcoming      — due within N days
PATCH /calendar/{id}          — update status, link generated content
```

### 8.6 Entity & Knowledge Graph (`EntityOptimizationService`)

Builds JSON-LD `schema.org` markup per entity type (`Organization`, `Person`, `Product`, `LocalBusiness`); `sameAs` populated from external links (Wikipedia, Wikidata, socials) for knowledge-graph recognition signals. Schema regenerates automatically when links change.

```
POST  /entities              — entity_type, entity_name, external_links, co_mention_targets
GET   /entities                — list (cached 1h)
PATCH /entities/{id}          — update links/targets/status, regenerates schema
```

### 8.7 Multi-Location SEO (`MultiLocationSEOService`)

Builds `LocalBusiness` JSON-LD per location and auto-generates location-intent keywords (`"{service} in {city}"`, `"{service} near me"`, `"best {service} {city}"`, `"{city} {service}"`). Tracks NAP (Name/Address/Phone) citation confirmation across 5 directories (`google_business`, `yelp`, `facebook`, `bing_places`, `apple_maps`) — `nap_consistent` is true only when **all** are confirmed.

```
POST  /locations                    — location_name, address, city, service_type, ...
GET   /locations                     — list (cached 1h)
PATCH /locations/{id}/citations      — confirm/unconfirm one directory
GET   /locations/citation-report     — NAP coverage % across all locations (cached 1h)
```

### 8.8 Topical Clusters / Link Building (`TopicalClusterService`)

`authority_score` = 10 points per cluster subtopic, capped at 100. `internal_linking_map` is hub-and-spoke: every cluster subtopic links back to its pillar. `add_cluster_topic` grows a cluster and regenerates both the map and the score.

```
POST  /clusters                — pillar_topic, cluster_topics, pillar_content_id
GET   /clusters                 — ranked by authority (cached 1h)
PATCH /clusters/{id}/topics    — add a subtopic
GET   /clusters/{id}/linking-map — hub-and-spoke linking map
```

### 8.9 Cross-Domain Audit Orchestrator (`SEOAuditOrchestrator`)

One read-only call that fans out across **all four SEO domains** (`seo_intelligence`, `fomo_seo`, `seo_optimization`, and all 8 `seo_agents` services) and returns a single prioritized action plan.

```
GET /audit   — cached 30min (fans out ~10 queries)
```

**Threshold rules** (evaluated against the aggregated metrics, sorted critical→high→medium→low):

| Trigger | Priority | Category |
|---|---|---|
| `critical_issues > 0` | critical | page_health |
| `overall_score < 70` | high | page_health |
| keyword gaps exist | high | keyword_gaps (names top-opportunity keyword) |
| backlink opportunities exist | medium | backlinks (names top-priority domain) |
| `review_total < 10` | medium | reviews |
| any location not fully NAP-consistent | medium | local_seo |
| pending optimization tasks exist | medium | optimization |
| content exists but no topical clusters | low | content_structure |
| nothing scheduled in next 14 days | low | content_calendar |

**Example response:**
```json
{
  "business_id": "...",
  "metrics": {
    "seo_health": {"overall_score": 62, "critical_issues": 1},
    "keyword_gap_count": 4,
    "backlink_opportunity_count": 2,
    "review_total": 6,
    "location_total": 3,
    "location_fully_consistent": 1,
    "...": "..."
  },
  "action_plan": [
    {"category": "page_health", "priority": "critical", "action": "Fix 1 page(s) with critical SEO issues (optimization_score < 30)", "impact_estimate": "high"},
    {"category": "page_health", "priority": "high", "action": "Overall SEO health score is 62/100 — run content generation on underperforming pages", "impact_estimate": "high"},
    {"category": "keyword_gaps", "priority": "high", "action": "Generate content for 4 high-opportunity keyword gap(s) — top target: 'best crm for startups' (opportunity 88)", "impact_estimate": "high"},
    {"category": "reviews", "priority": "medium", "action": "Only 6 reviews collected — launch review solicitation campaigns to reach 10+ for AggregateRating eligibility", "impact_estimate": "medium"},
    {"category": "local_seo", "priority": "medium", "action": "2 location(s) have inconsistent NAP citations — confirm remaining directory listings", "impact_estimate": "medium"}
  ]
}
```

### 8.10 Complete Workflow: Onboarding a New Business

```
1. GET /audit → establish baseline (likely near-empty: no content, no locations, no clusters)
2. For each product/service:
   a. POST /content/generate → SEO-optimized product page
   b. POST /keywords/analyze-gap → confirm target keyword vs competitors
3. POST /clusters → group products into pillar/cluster topics for internal linking
4. If multi-location: POST /locations for each branch/service area
5. POST /calendar/generate → schedule ongoing content for the next 90 days
6. POST /reviews/campaigns → solicit reviews from first customers
7. POST /backlinks/opportunities → seed outreach targets from competitor backlink analysis
8. GET /audit weekly → re-run, watch action_plan shrink as items get addressed
```
