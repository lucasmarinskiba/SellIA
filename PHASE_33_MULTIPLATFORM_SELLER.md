# Phase 33: Multi-Platform Seller Automation Engine

**Vision**: SellIA becomes the world's best automated seller across Mercado Libre, Amazon, and Hotmart. AI-driven product optimization, dynamic pricing, FOOM triggers, SEO ranking domination, inventory sync, and review management.

**Launch Target**: Oct 2027  
**Status**: Architecture Phase  
**Expected Impact**: $50M+ annual GMV from platform integrations  
**Timeline**: 16 weeks (Oct-Dec 2027)

---

## Strategic Overview

### 3 Platform Strategies

**1. Mercado Libre (LATAM E-commerce Leader)**
- 85M+ active users across LATAM
- Best seller badge drives 40%+ more sales
- Strong SEO in regional search
- Dynamic pricing wars (10+ competitors per category)
- Review-driven ranking algorithm

**2. Amazon (Global Marketplace)**
- 300M+ active users
- A9 search algorithm (keyword-driven ranking)
- Best seller status = 35% sales lift
- Amazon's Choice badge (review score + price optimization)
- FBA (Fulfillment by Amazon) integration required

**3. Hotmart (Digital Products Platform)**
- 2M+ active buyers for digital products
- Affiliate network (creators → promoters)
- FOMO-native (pre-launch, limited seats, early-bird pricing)
- Organic growth via affiliate reviews
- High margins (40-70% for sellers)

---

## Architecture

### 4 Core Systems

#### 1. Platform Sync Engine
**Problem**: Inventory scattered across 3 platforms; need real-time sync without overselling

```
┌─────────────────────────────────────────┐
│  Master Inventory Service (SellIA)      │
│  ├─ Product SKU mapping (cross-platform) │
│  ├─ Stock levels (real-time)             │
│  └─ Reserved inventory (from sales)      │
└────────────┬────────────────────────────┘
     │       │       │
     ▼       ▼       ▼
  ML API   Amazon  Hotmart
  (sync)   SP-API  API
```

**Key Features**:
- Unify product catalog (1 product = 3 listings)
- Real-time stock sync (within 5 min)
- Prevent overselling (reserve across platforms)
- Handle returns/cancellations (restock automation)
- Bulk listing creation (CSV → 3 platforms)

**Database**:
```sql
products (master catalog)
├─ id, sku, title, description
├─ cost, price_base
├─ stock_total, stock_reserved
└─ created_at, updated_at

platform_listings
├─ id, product_id, platform (ML/AMZN/HOTMART)
├─ platform_sku, listing_url
├─ status (active, inactive, delisted)
├─ current_stock (as of last sync)
└─ last_sync_at

stock_movements
├─ id, product_id, platform
├─ movement_type (sale, return, restock, sync)
├─ quantity_delta
├─ timestamp
```

#### 2. Dynamic Pricing Engine
**Problem**: Price too high → no sales; too low → lost margin. Competitors repricing every 2 hours.

```
Competitor Price Data →
  ├─ Mercado Libre (ML API scan)
  ├─ Amazon (SP-API)
  └─ Hotmart (web scrape)
    │
    ▼
Pricing Algorithm
  ├─ Cost + margin target
  ├─ Competitor prices
  ├─ Demand (sales velocity)
  ├─ Inventory level
  ├─ Season/promotions
  └─ Best seller status → price floor
    │
    ▼
Auto-reprice (2-4x daily)
```

**Strategies**:
1. **Undercut Competitors** (-5% to -15%): Race to Best Seller
2. **Maintain Margin** (cost * 1.5-2x): High inventory, low urgency
3. **Scarcity Premium** (cost * 2.5-3x): Low stock, high demand
4. **Seasonal Surge** (cost * 3-4x): Holiday/event pricing
5. **First Mover Discount** (cost * 1.3x): New listings, build reviews

**ML Model**:
```
Inputs: [competitor_price, demand_score, inventory_level, days_in_season]
Output: optimal_price
Training: Historical sales data (price → units sold)
Goal: Maximize (margin * volume) subject to Best Seller constraint
```

#### 3. FOOM Trigger System (Per-Platform)
**Problem**: Default listings are boring. Need psychology-driven urgency.

**Mercado Libre FOOM**:
- Scarcity counter ("Only 3 left at this price!")
- Bestseller badge + ranking position (#1 in category)
- Social proof ("500+ sales this week")
- Limited-time offer stamp
- Free shipping badge (urgency)
- Seller rating highlight (4.9/5 stars)

**Amazon FOOM**:
- Amazon's Choice badge (drives visibility + trust)
- Lightning Deal (time-limited price)
- Best Seller status badge
- Customer review count + star rating
- "Limited time offer" banner
- Stock countdown ("Only 5 left at this price")
- Prime badge (2-day shipping)

**Hotmart FOOM**:
- Pre-launch timer (days until launch)
- Early-bird price (first 100 customers)
- Limited seats (capacity countdown)
- Affiliate commission highlight
- Student/bulk discount badges
- 7-day money-back guarantee badge
- Creator testimonial carousel

**Implementation**:
```python
class FOOMTriggerEngine:
    def generate_ml_description(product, inventory, sales_velocity):
        triggers = []
        if inventory < 10:
            triggers.append(f"🔥 Only {inventory} left!")
        if sales_velocity > 50/day:
            triggers.append(f"⭐ {sales_velocity:.0f} sold this week")
        if product.rank == 1:
            triggers.append("🥇 #1 Best Seller in category")
        return format_urgency_message(triggers)
    
    def generate_amazon_title(product):
        # Amazon A9 algorithm: keyword-rich + urgency
        return f"{product.title} | Best Seller | Free Shipping | 4.9★"
    
    def generate_hotmart_hook(product, pre_launch_days):
        if pre_launch_days > 0:
            return f"🚀 Launching in {pre_launch_days} days | Early bird gets 40% off"
        return f"⏰ Limited to 500 buyers | Grab yours before it sells out"
```

#### 4. SEO & Ranking Optimization Engine
**Problem**: Product lost in 100k+ listings on each platform. Need #1 ranking.

**Mercado Libre Ranking Factors**:
1. Sales velocity (volume + recency)
2. Rating (stars from reviews, 4.5+)
3. Price competitiveness
4. Shipping speed (full/express)
5. Listing quality (photos, description)
6. Seller rating (4.8+)

**Amazon A9 Ranking Factors**:
1. Conversion rate (CTR × purchase rate)
2. Review count + average rating (4.5+)
3. Sales velocity (units/day)
4. Keyword relevance (title, bullet points, search terms)
5. Price (top offers first)
6. FBA (Amazon-handled shipping boost)
7. Backend search terms (A9 indexes hidden keywords)

**Hotmart Ranking Factors**:
1. Conversion rate (visitor → buyer)
2. Sales velocity (units/day)
3. Review rating (5-star average)
4. Affiliate commission (higher = more promoters)
5. Refund rate (low = trustworthy)
6. Creator engagement (responsiveness)
7. Category position (trending up/down)

**Optimization Strategy**:

```
Phase 1: Keyword Research (Week 1-2)
├─ Search volume analysis (target high-volume, low-competition keywords)
├─ Competitor keyword analysis (reverse-engineer top 3 listings)
└─ Long-tail keyword discovery (3-5 word combinations)

Phase 2: Listing Optimization (Week 3-4)
├─ Title rewrite (keyword-rich, urgency-driven, A9 optimized)
├─ Description rewrite (benefit-focused, AIDA framework)
├─ Bullet points (5 key benefits + keywords)
├─ Photo optimization (lifestyle + product detail shots)
├─ Attribute filling (all dropdown fields)
└─ Backend keywords (Amazon-specific hidden search terms)

Phase 3: Review Acceleration (Week 5-8)
├─ Follow-up email (day 2-7 post-purchase)
│   ├─ Thank you + product tips
│   ├─ Request for review (direct link)
│   └─ Incentive: 10% off next purchase (ML/AMZN compliant)
├─ Review monitoring (flag negative, escalate to CS)
├─ Response strategy (reply to all reviews within 24h)
└─ Review generation: Target 50+ 5-star reviews/month

Phase 4: Sales Velocity Boost (Week 9-12)
├─ Launch discount (40-50% off first week)
├─ Advertise campaign (Mercado Ads, Amazon Sponsored Products)
├─ Influencer seeding (free product for review)
├─ Social media push (cross-promote to SellIA followers)
└─ Email blast (existing customers → cross-sell)

Phase 5: Sustained Ranking (Week 13-16)
├─ Dynamic pricing (maintain price edge vs competitors)
├─ Inventory management (stock out = ranking killer)
├─ Feedback loop (analyze search term performance)
└─ Continuous A/B testing (title variations, price points)
```

**Database**:
```sql
keyword_research
├─ id, product_id, platform
├─ keyword, search_volume, competition_level
├─ position_current, position_target
├─ ranking_trend (moving up/down)

listing_versions
├─ id, product_id, platform
├─ version_num, title, description
├─ a_b_test_group (control/treatment)
├─ conversion_rate, avg_rating
├─ created_at, active_until

review_tracking
├─ id, product_id, order_id, platform
├─ reviewer_name, rating (1-5)
├─ review_text
├─ flagged (negative, spam)
├─ seller_response
├─ created_at
```

#### 5. Best Seller Ranking Optimizer
**Challenge**: Need #1 Best Seller badge to dominate category. Race is fierce.

**Mercado Libre Best Seller Requirements**:
- Top 10 in category by sales (30 days)
- 4.5+ average rating
- <1% negative feedback
- Fast shipping (express option)
- Regular sales (no 7+ day gaps)
- No policy violations

**Amazon Best Seller Requirements**:
- Top position by units sold (rolling 30 days)
- 4+ average rating
- <5% return rate
- Competitive pricing (usually top 5 price)
- In stock consistently

**Strategy**:
```
Monitor competitor positions hourly
├─ If competitor rank > ours: Undercut price by 5-10% (max 4x daily)
├─ If high inventory + low sales: Flash sale (30-50% off)
├─ If low inventory + high demand: Limit sales per customer (artificial scarcity)
├─ If approaching Best Seller: Invest in ads (guarantee volume spike)
└─ Once Best Seller: Optimize price (higher margin is OK with badge)

Review velocity target: 5+ reviews/day (minimum to maintain ranking)
Sales velocity target: 50+ units/day (per category size)
Rating maintenance: Keep 4.7+ (respond to all complaints)
```

---

## API Integration Details

### Mercado Libre OAuth + REST API

```python
class MercadoLibreService:
    def __init__(self, user_id: str):
        self.client_id = os.getenv("ML_CLIENT_ID")
        self.client_secret = os.getenv("ML_CLIENT_SECRET")
        self.access_token = self.refresh_token(user_id)  # OAuth flow
    
    def create_listing(self, product: Product) -> dict:
        """POST /items - Create product listing"""
        payload = {
            "title": generate_ml_title(product),  # FOOM-optimized
            "category_id": "MLA123456",  # ML category code
            "price": calculate_price(product),
            "currency_id": "ARS",  # Argentine Peso (example)
            "available_quantity": product.stock,
            "condition": "new",
            "listing_type_id": "gold_pro",  # Best for sales
            "description": {
                "plain_text": generate_ml_description(product),  # Include urgency
            },
            "pictures": [{"source": img_url} for img_url in product.images],
            "attributes": [
                {"id": "BRAND", "value_name": product.brand},
                {"id": "MODEL", "value_name": product.model},
                # ... more attributes
            ],
            "shipping": {
                "mode": "me2",  # Seller manages shipping
                "local_pick_up": True,
                "free_shipping": product.offer_free_shipping,
            },
        }
        return self.post("/items", payload)
    
    def sync_inventory(self, product_id: str, new_stock: int) -> dict:
        """PUT /items/{item_id} - Update stock"""
        return self.put(f"/items/{product_id}", {"available_quantity": new_stock})
    
    def get_sales(self, listing_id: str, days: int = 30) -> List[dict]:
        """GET /orders/search - Fetch sales for ranking analysis"""
        return self.get(f"/orders/search", {
            "seller_id": self.seller_id,
            "order_status": "payment_received",
            "sort": "date_desc",
        })
    
    def get_competitor_prices(self, category_id: str) -> List[dict]:
        """GET /sites/MLA/search - Scrape top competitors"""
        results = self.get(f"/sites/MLA/search", {
            "category": category_id,
            "sort": "price_asc",
            "limit": 50,
        })
        return [
            {"seller": r["seller"]["nickname"], "price": r["price"], "sales": r["orders_count"]}
            for r in results["results"][:10]
        ]
    
    def update_title_description(self, item_id: str, title: str, description: str) -> dict:
        """PUT /items/{item_id} - A/B test listing variations"""
        return self.put(f"/items/{item_id}", {
            "title": title,
            "description": {"plain_text": description},
        })
```

### Amazon SP-API (Selling Partner API)

```python
class AmazonService:
    def __init__(self, seller_id: str):
        self.region = "na"  # North America
        self.access_token = self.get_auth_token()  # LWA flow
    
    def create_listing(self, product: Product) -> dict:
        """FeedAPI - Bulk create/update listings"""
        feed_data = {
            "TemplateType": "Flat File Inventory",
            "sku": product.sku,
            "product_id": product.ean,
            "product_id_type": "EAN",
            "item_type": "FlatFileInventoryLoader",
            "title": generate_amazon_title(product),  # A9-optimized
            "brand": product.brand,
            "description": generate_amazon_description(product),  # FOOM-driven
            "bullet_point_1": product.key_benefits[0],
            "bullet_point_2": product.key_benefits[1],
            # ... up to 5 bullet points
            "quantity": product.stock,
            "price": calculate_amazon_price(product),
            "item_type_keyword": product.category,
            "generic_keywords": "keyword1,keyword2,keyword3",  # SEO
            "platinum_keywords": "premium keyword1,premium keyword2",  # A9
            "search_terms": "hidden1 hidden2 hidden3",  # Backend keywords
            "gift_wrap_available": "true" if product.is_giftable else "false",
            "shipping_weight": product.weight_kg,
            "shipping_weight_unit_of_measure": "KG",
        }
        return self.submit_feed(feed_data)
    
    def update_inventory(self, sku: str, quantity: int) -> dict:
        """CatalogAPI - Update stock in real-time"""
        return self.put(f"/catalogs/2020-12-01/items/{sku}", {
            "fulfillmentAvailability": [{
                "fulfillmentChannelCode": "DEFAULT",
                "quantity": quantity,
            }]
        })
    
    def get_competitiveness_metrics(self, sku: str) -> dict:
        """ProductsAPI - Get ranking insights"""
        return self.get(f"/products/pricing/v0/competitivePrice", {
            "SellerSKU": sku,
            "MarketplaceId": "ATVPDKIKX0DER",  # US
        })
    
    def get_reviews(self, asin: str) -> List[dict]:
        """ProductsAPI - Fetch customer reviews"""
        return self.get(f"/products/pricing/v0/productReviews", {
            "ASIN": asin,
            "MarketplaceId": "ATVPDKIKX0DER",
        })
    
    def create_sponsored_campaign(self, product_sku: str, daily_budget: float, keywords: List[str]) -> dict:
        """Advertising API - Auto-launch ads for ranking boost"""
        return self.post(f"/sp/campaigns/v2", {
            "name": f"Auto-Rank {product_sku}",
            "portfolioId": self.portfolio_id,
            "campaignType": "sponsoredProducts",
            "targetingType": "manual",
            "state": "enabled",
            "budget": {
                "budget": daily_budget,
                "budgetType": "DAILY",
            },
            "ads": [{"adGroupId": self.ad_group_id, "sku": product_sku}],
            "keywords": [{"text": kw, "matchType": "broad"} for kw in keywords],
        })
```

### Hotmart API

```python
class HotmartService:
    def __init__(self, seller_id: str):
        self.api_key = os.getenv("HOTMART_API_KEY")
        self.base_url = "https://api.hotmart.com/payment/api/v1"
    
    def create_product(self, product: Product) -> dict:
        """POST /products - Create digital product listing"""
        payload = {
            "name": generate_hotmart_name(product),  # FOOM hook
            "description": generate_hotmart_hook(product),
            "short_description": product.tagline,
            "category_id": product.hotmart_category,
            "price": calculate_hotmart_price(product),
            "currency": "BRL",  # Brazilian Real
            "material_file_url": product.digital_file_url,
            "preview_url": product.demo_url,
            "images": [{"url": img} for img in product.images],
            "support_email": product.support_email,
            "faq": [
                {"question": "Pode usar em comercial?", "answer": product.commercial_use_allowed},
                # ... more FAQs
            ],
            "access_type": "IMMEDIATE",  # Instant delivery (digital)
            "max_cap": 500 if product.is_limited else None,  # Scarcity
            "validity": 365,  # Access validity (days)
            "upsell_ids": product.upsell_ids,  # Cross-sell recommendations
        }
        return self.post(f"{self.base_url}/products", payload, headers={"Authorization": self.api_key})
    
    def update_early_bird_pricing(self, product_id: str, early_bird_price: float, limit: int) -> dict:
        """PUT /products/{id}/pricing - Limited-time early bird offer"""
        return self.put(f"{self.base_url}/products/{product_id}", {
            "early_bird_price": early_bird_price,
            "early_bird_limit": limit,  # First N buyers get discount
            "early_bird_expiry": (datetime.now() + timedelta(days=7)).isoformat(),
        }, headers={"Authorization": self.api_key})
    
    def generate_affiliate_links(self, product_id: str, creator_list: List[str]) -> dict:
        """POST /affiliates - Create affiliate promotion links"""
        affiliates = []
        for creator in creator_list:
            affiliate = self.post(f"{self.base_url}/affiliates", {
                "product_id": product_id,
                "affiliate_email": creator,
                "commission_percentage": 40,  # 40% commission to creators
            }, headers={"Authorization": self.api_key})
            affiliates.append(affiliate)
        return affiliates
    
    def get_sales_analytics(self, product_id: str, days: int = 30) -> dict:
        """GET /products/{id}/sales - Sales velocity + conversion data"""
        return self.get(f"{self.base_url}/products/{product_id}/sales", {
            "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
            "end_date": datetime.now().isoformat(),
        }, headers={"Authorization": self.api_key})
    
    def create_pre_launch_campaign(self, product_id: str, launch_date: str) -> dict:
        """Setup pre-launch landing page with countdown timer"""
        return self.post(f"{self.base_url}/products/{product_id}/pre-launch", {
            "launch_date": launch_date,
            "early_bird_discount": 0.40,  # 40% off
            "early_bird_limit": 100,  # First 100 customers
            "enable_waitlist": True,
            "enable_countdown": True,
        }, headers={"Authorization": self.api_key})
```

---

## Database Schema (15+ Tables)

```sql
-- Platform Integration
products (master catalog)
platform_listings (per-platform SKU mapping)
inventory_sync_log (audit trail of stock changes)

-- Pricing & Competition
price_history (track price changes over time)
competitor_prices (competitor monitoring)
pricing_rules (dynamic pricing rules per segment)
pricing_changes (audit: who changed what when)

-- SEO & Ranking
keyword_research (keyword data + rankings)
listing_versions (A/B tested titles/descriptions)
ranking_tracker (daily position tracking per platform)
search_term_performance (which keywords drive sales)

-- Reviews & Ratings
customer_reviews (pulled from each platform)
review_requests (email campaigns asking for reviews)
review_responses (seller responses to reviews)

-- Sales & Orders
orders_unified (all platform orders in one place)
platform_orders_sync (raw order data from each platform)

-- FOOM & Marketing
foom_messages (generated urgency messages)
campaign_performance (ad/promo results per platform)
affiliate_tracking (Hotmart affiliate performance)

-- Seller Metrics
seller_rankings (best seller position tracker)
platform_seller_health (rating, policy violations, etc)
competitive_position (vs top 10 competitors)
```

---

## Implementation Roadmap (16 Weeks)

### Phase 1: Foundations (Weeks 1-4)
- [ ] API integrations (ML, Amazon, Hotmart OAuth)
- [ ] Product sync engine (unify 3 platforms)
- [ ] Inventory sync (real-time stock updates)
- [ ] Order sync (pull all sales into unified DB)
- [ ] Seller dashboard (multi-platform overview)

### Phase 2: Pricing & Ranking (Weeks 5-8)
- [ ] Dynamic pricing engine (hourly repricing)
- [ ] Competitor price monitoring
- [ ] Best seller ranking optimizer
- [ ] Keyword research engine (find high-volume keywords)
- [ ] Listing optimization (title/description A/B tests)

### Phase 3: FOOM & Reviews (Weeks 9-12)
- [ ] FOOM trigger system (urgency messages per platform)
- [ ] Review monitoring + auto-response
- [ ] Review request automation (post-purchase email)
- [ ] Negative review escalation (CS alert)
- [ ] Rating maintenance strategy

### Phase 4: Scaling & Optimization (Weeks 13-16)
- [ ] Advertising automation (Mercado Ads, Amazon Sponsored)
- [ ] Pre-launch campaigns (Hotmart countdown + early-bird)
- [ ] Influencer seeding (free product for review)
- [ ] Social media integration (cross-promote)
- [ ] Analytics dashboard (ROI per product/platform)

---

## Success Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Best Seller rank | #1 in 3+ categories | Week 12 |
| Product listings synced | 100+ across 3 platforms | Week 2 |
| Inventory accuracy | 99.5% (no overselling) | Week 4 |
| Dynamic pricing | 2-4 reprices/day per product | Week 6 |
| Review velocity | 50+ reviews/month per product | Week 10 |
| Customer rating | 4.7+ average across platforms | Week 12 |
| GMV | $50M+ annual from platforms | Month 4 |
| Margin optimization | +15-20% via dynamic pricing | Week 8 |
| Conversion rate | 8-12% (platform average 2-3%) | Week 16 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API rate limits | Queue system + backoff retry |
| Stock overselling | Real-time inventory cache (Redis) |
| Price wars (race to zero) | Minimum margin floor enforced |
| Review manipulation | Platform compliance (no fake reviews) |
| Seller policy violations | Auto-audit for violations |
| Competitor retaliation | Rotate strategies (price/promo/ads) |

---

## Financial Projection

**Conservative Estimate**:
- 100 products × 3 platforms = 300 listings
- Avg product: $50 (digital) to $500 (physical)
- Conversion rate: 5% → 12% (with FOOM)
- Traffic: 10k visitors/day per platform
- GMV Year 1: $50M (conservative, growth focused)
- GMV Year 2: $200M+ (scaling, marketplace effect)

**Revenue**:
- Commission: 10-15% of GMV = $5-7.5M Y1
- Affiliate network (Hotmart): $2-3M Y1
- Ad spend ROI: 3x return = $3-5M Y1
- **Total Y1: $10-15M revenue**

---

## Next Steps

1. **Confirm Phase 33 build approval** (yes/no)
2. **Choose starting platform** (recommend: Hotmart first, fastest to revenue)
3. **Gather API credentials** (ML, Amazon, Hotmart)
4. **Build Phase 33 Backend** (4 core systems + integrations)
5. **Build Phase 33 Frontend** (seller dashboard + optimization tools)
6. **Go live** (test with 5-10 products first)

