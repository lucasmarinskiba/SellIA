# Phase 30: Churn Prevention + ABM Intent Scoring

**Launch Date**: Jan 25, 2027  
**Target Impact**: -30% churn (-$X to retained), +25% expansion revenue, +$2M net annual

---

## Problem

Enterprise customers churn when:
1. They stop engaging (no usage signals)
2. Cheaper alternatives appear
3. Implementation fails
4. Economic downturn forces cuts
5. New competitor wins mindshare

**Cost of churn**: 1 lost customer @ $150k ACV = $150k lost + acquisition cost for replacement

**Solution**: Predict churn 90 days early, intervene with personalized retention playbook

---

## Architecture

### 4 Engines

#### 1. ChurnPredictionModel
- **Input**: Customer engagement data (features)
  - Login frequency (last 30 days)
  - Feature adoption (% features used)
  - Support ticket volume (trend)
  - Payment history (late/failed attempts)
  - Team size changes
  - Competitor activity near account
  - Pricing tier (margin indicator)
  - Time since last success event
  
- **Model**: XGBoost binary classifier
  - Target: Customer will churn in 90 days
  - AUC: 0.82+
  - Output: Churn probability (0-1)
  - Thresholds:
    - High risk (>0.7): Immediate outreach
    - Medium risk (0.5-0.7): Check-in + offer
    - Low risk (<0.5): Monitor

- **Output**: Churn risk score + top 3 churn reasons (SHAP values)

#### 2. ExpansionOpportunityDetector
- **Input**: Customer data + usage patterns
  - Current spend
  - Feature adoption gaps
  - Team growth (hiring signals)
  - New department usage
  - Neighboring customer wins (similar profile)
  - Time in product (stickiness indicator)
  
- **Logic**:
  - Identify underutilized features → upsell candidates
  - Detect team growth → seat expansion opportunity
  - Find cross-sell gaps → new product fit
  - Quantify expansion ROI per opportunity
  
- **Output**: Expansion opportunities ranked by likelihood + revenue potential

#### 3. ABMIntentScorer
- **Input**: Real-time engagement signals
  - Page views (product page, pricing, competitors)
  - Email opens (rate + timing)
  - Demo requests (intent signal)
  - Content consumption (whitepapers, case studies)
  - Social mentions
  - Website search queries
  - Competitive activity (alerts)
  
- **Score**: 0-100 intent level
  - 80+: Buy signal (immediate outreach)
  - 60-80: Consideration (nurture)
  - 40-60: Awareness (content)
  - <40: Not interested (monitor)
  
- **Output**: Intent score + reason (top 3 signals)

#### 4. RetentionPlaybookGenerator
- **Input**: Churn reason + customer segment + engagement history
- **Outputs**:
  - Personalized win-back message (why they should stay)
  - Specific value prop (based on their usage gaps)
  - Concession offer (discount, free month, etc)
  - Alternative solution (if switching is their issue)
  - Executive message (CEO + CEO if account > $1M)
  
- **Channel**: Email + in-app + phone
- **Timing**: Triggered when churn risk >0.7

---

## Database Schema (6 Tables, 12+ Indexes)

### churn_predictions
- id (UUID)
- customer_id (FK deals.customer_id)
- churn_probability (float 0-1)
- churn_reasons (JSONB: top 3 factors + scores)
- predicted_churn_date (date)
- created_at (datetime)
- **Indexes**: idx_customer_risk, idx_probability, idx_date

### expansion_opportunities
- id (UUID)
- customer_id (FK)
- opportunity_type (upsell, cross_sell, seat_expansion, feature_adoption)
- base_feature (what they're using)
- adjacent_feature (what they should buy)
- revenue_potential (float)
- likelihood_score (0-1)
- recommended_message (text)
- created_at
- **Indexes**: idx_customer_opp, idx_type, idx_revenue

### abm_intent_scores
- id (UUID)
- account_id (FK deals.id)
- intent_score (0-100)
- top_signals (JSONB: [{"signal": "page_views", "weight": 0.4, "value": "15"}])
- trending (up/down/flat)
- updated_at
- **Indexes**: idx_account_intent, idx_score

### retention_campaigns
- id (UUID)
- customer_id (FK)
- churn_prediction_id (FK)
- campaign_type (win_back, value_add, competitive_offer)
- playbook_message (text)
- offer_type (discount_pct, free_month, feature_unlock)
- offer_value (int or string)
- sent_at (datetime)
- opened_at (datetime nullable)
- clicked_at
- converted (boolean)
- converted_at
- **Indexes**: idx_customer_campaign, idx_type, idx_sent

### win_back_playbooks
- id (UUID)
- churn_reason (payment_issue, feature_gap, competitor, price, implementation_issue)
- segment (SMB, mid_market, enterprise, by_industry)
- message_template (text)
- offer_template (text)
- executive_escalation_message (text)
- success_rate (float: historical conversion %)
- created_at
- **Indexes**: idx_reason_segment, idx_success_rate

### customer_engagement_metrics
- id (UUID)
- customer_id (FK)
- metric_date (date)
- login_count (int)
- features_used_pct (float 0-1)
- support_tickets_count (int)
- nps_score (0-10)
- health_score (0-100: composite)
- created_at
- **Indexes**: idx_customer_date, idx_health_score

---

## Churn Probability Model (XGBoost)

**Target Variable**: Churned in next 90 days (0/1)

**Features (20+)**:
```
Input Features:
- days_since_login (recency)
- login_count_30d (frequency)
- features_used_pct (adoption)
- support_tickets_last_30d
- support_ticket_trend_90d (up = bad)
- payment_failed_count_1y
- days_since_successful_implementation
- team_size (current vs historical)
- team_size_change_pct
- nps_score
- nps_trend_90d
- competitor_mentions_last_30d
- competitive_threat_score
- pricing_tier (proxy for revenue/margin)
- account_age_months
- feature_adoption_trend
- response_time_satisfaction
- executive_engagement_score
- product_roadmap_interest (from support tickets)
- expansion_product_interest

Categorical:
- industry
- region
- tier (SMB/mid/enterprise)
- product_line
- acquisition_channel
```

**Model Training**:
- Train on 18+ months historical data
- 80/20 train/test split
- Cross-validation: 5-fold
- Target AUC: 0.82+
- Retrain monthly (new churn signals)

**Prediction Frequency**: Daily for all customers

**Output Format**:
```json
{
  "customer_id": "cust-001",
  "churn_probability": 0.78,
  "risk_level": "HIGH",
  "top_churn_reasons": [
    {"reason": "No login for 45 days", "impact": 0.35},
    {"reason": "Support ticket volume down 60%", "impact": 0.28},
    {"reason": "Competitive threat detected", "impact": 0.15}
  ],
  "predicted_churn_date": "2027-03-15",
  "retention_offer_suggested": "6-month extension at 30% discount"
}
```

---

## Expansion Opportunity Logic

**Detect underutilized features**:
- Customer using "reporting" but not "automation"
- Similar companies (by size/industry) use both
- Automation = +$20k annual value for similar customer
- → Upsell opportunity: "$20k revenue potential"

**Detect team growth**:
- Team grew from 10 → 15 people last quarter
- Seats purchased: 10 → still 10 (not scaling)
- → 5 open seats × $2k/person = $10k opportunity

**Detect cross-sell**:
- Customer using Product A (CRM) but not Product B (Marketing)
- 60% of Product A customers also use Product B
- → Cross-sell message

**Detect adjacent features**:
- Customer uses "basic reporting" (standard tier)
- Should upgrade to "custom reporting" (premium)
- Premium tier = +$15k annually
- → Upsell opportunity

**Ranking by likelihood × value**:
- Opportunity A: 0.7 likelihood × $20k = $14k expected value
- Opportunity B: 0.5 likelihood × $30k = $15k expected value
- Opportunity C: 0.3 likelihood × $10k = $3k expected value
- **Rank**: B > A > C

---

## Retention Playbook Examples

### High-Risk Churn Pattern 1: "No Usage"
**Trigger**: No login for 45 days + was active 6+ months

**Playbook**:
```
Subject: "We haven't heard from you, [Name]"

Body:
"Hi [Name],

It's been a while since you've logged in. We wanted to check in and see 
how [Product] is working for [Company].

Looking at your account, we noticed you've been getting great value from 
[Feature X] but haven't explored [Feature Y] yet—which could save 
[Department] another [X] hours/month.

Question: What would help you get back on track?
- Implementation issue?
- Missing feature?
- Just need a refresher?

Let's schedule a quick 15-min call to get you unstuck.

Best,
[Customer Success Manager]"

Offer: "Free premium features for 3 months"
Executive escalation: CFO → SVP Operations (if $1M+ deal)
```

### High-Risk Churn Pattern 2: "Competitive Threat"
**Trigger**: Competitor mentioned 3+ times in support tickets + low engagement

**Playbook**:
```
Subject: "Exclusive: How [Company] is beating [Competitor] with [Feature]"

Body:
"Hi [Name],

I noticed [Competitor] has been mentioned in your recent support tickets. 
Totally understand—competitive landscape is tough.

Here's what we've seen: Companies that switched FROM [Competitor] TO us 
report [Specific Metric: +40% faster implementation, +60% team adoption].

Your industry peer, [Similar Company], had the same hesitation but 
switched last year. Happy to intro you.

One question: What matters most to you that [Competitor] is missing?
- Speed? (We're 3x faster)
- Cost? (We're 40% cheaper at your scale)
- Features? (We support X, Y, Z)

Let's talk through your specific needs.

Best,
[Sales Leader]"

Offer: "Match competitor's pricing + add 5 premium features free"
Executive escalation: CRO/VP Sales (competitive deals)
```

### High-Risk Churn Pattern 3: "Price Sensitivity"
**Trigger**: Payment failed 2+ times + is SMB tier + volume declining

**Playbook**:
```
Subject: "We've adjusted pricing for [Company]"

Body:
"Hi [Name],

I see your recent payment issues. Let's make this easy.

We've adjusted your plan for the next 6 months:
- Reduced to 50% of current cost
- Same access to all features
- No commitment—month-to-month

Let's revisit in 6 months when you've grown (I know you're hiring 🚀).

Any questions? Reply directly or hop on a 10-min call.

Best,
[Customer Success Manager]"

Offer: "50% discount 6 months, then reassess"
Condition: Engagement commitment (1 training call/month)
```

---

## Win-Back Campaign Mechanics

**Workflow**:
1. Churn model predicts churn risk >0.7
2. System queries win_back_playbooks for matching reason + segment
3. Retrieves best playbook (by historical success rate)
4. Personalizes message (customer name, usage data, specific features)
5. Sends via email + in-app + SMS
6. Tracks: sent, open, click, response, conversion
7. If no response in 3 days → escalate to CSM phone call
8. If no response in 7 days → executive escalation

**Success Metric**: Converted = Customer re-engages + doesn't churn within 30 days

---

## API Endpoints (6)

```
POST /api/v1/churn/predictions/{customer_id}
  - Get churn prediction for customer
  - Returns: probability, risk_level, reasons, suggested_offer

POST /api/v1/churn/expansion-opportunities/{customer_id}
  - Get expansion opportunities
  - Returns: opportunities ranked by expected value

POST /api/v1/churn/abm-intent-score/{account_id}
  - Get current ABM intent score
  - Returns: score, trending, top_signals

POST /api/v1/churn/retention-campaign/{customer_id}
  - Launch retention campaign
  - Returns: campaign_id, message, offer

GET /api/v1/churn/win-back-playbooks
  - List available playbooks by reason + segment
  - Returns: playbooks with success rates

POST /api/v1/churn/healthcheck/{customer_id}
  - Get overall customer health
  - Returns: health_score, churn_risk, expansion_potential, trends
```

---

## Frontend Components (5)

### 1. ChurnRiskDashboard
- Live churn predictions (all customers)
- Red/yellow/green by risk level
- Sorted: highest risk first
- Drill-down: click customer → see reasons

### 2. ExpansionOpportunitiesPanel
- Ranked opportunities per customer
- Expected value per opportunity
- One-click playbook launch

### 3. RetentionPlaybookBuilder
- Preview personalized message
- Choose offer (discount %, free month, feature unlock)
- A/B test message variations
- Send + track

### 4. ABMIntentDashboard
- Real-time intent scores (0-100)
- Trending up/down/flat
- Top signals breakdown
- Engagement timeline (last 30 days)

### 5. CustomerHealthScorecard
- Overall health score (0-100)
- Churn risk + expansion potential
- Trend arrows (improving vs declining)
- Recommended action

---

## Integration with Prior Phases

**Phase 27**: Deal intelligence (stakeholder mapping, engagement tracking)
→ **Phase 30 uses**: Deal health data as input to churn model

**Phase 28**: Email + proposal automation
→ **Phase 30 uses**: Email sending infrastructure for win-back campaigns

**Phase 29**: Voice + playbooks
→ **Phase 30 uses**: Call transcripts as engagement signal for churn model

**Phase 31**: Psychology sales
→ **Phase 30 uses**: Objection handling playbook for competitive churn reason

**FOOM**: Double-engine
→ **Phase 30 uses**: Urgency triggers for win-back campaigns ("pricing increase", "last chance")

---

## Expected Impact (Year 1)

**Churn Reduction**:
- Baseline churn rate: 12% annually
- With Phase 30: 8.4% annually (-30%)
- 100 customers × $150k ACV × 3.6% churn prevention = $540k saved

**Expansion Revenue**:
- Expansion rate baseline: 8%
- With Phase 30: 10% (+25%)
- 100 customers × $150k × 2% additional expansion = $300k new ARR

**Win-Back Campaigns**:
- Target: 30% of high-risk customers
- Expected conversion: 40%
- 30 customers × 40% × $150k = $1.8M re-activated

**Total Year 1**: $540k (churn savings) + $300k (expansion) + $1.8M (win-back) = **$2.64M net revenue impact**

---

## Success Metrics

| Metric | Baseline | Target | Gain |
|--------|----------|--------|------|
| Churn rate | 12% | 8.4% | -30% |
| Expansion rate | 8% | 10% | +25% |
| Win-back conversion | — | 40% | +$1.8M |
| Time to detect churn | — | 90 days early | Proactive |
| CSM productivity | 1:50 ratio | 1:80 ratio | +60% |
| Revenue retention | — | +$2.64M Y1 | 5x ROI |

---

## Timeline

**Week 1-2**: Data pipeline + feature engineering
**Week 3-4**: Model training + tuning (AUC 0.82+)
**Week 5-6**: Expansion detector + ABM scorer build
**Week 7-8**: Playbook generator + API endpoints
**Week 9**: Frontend components
**Week 10-11**: Integration testing (50+ tests)
**Week 12**: UAT + production rollout

**Launch**: Jan 25, 2027
