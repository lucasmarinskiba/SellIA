# Research Brain Quick Start Guide

Get your 52+ research agents and 10 specialists operational in minutes.

---

## Installation (5 minutes)

### 1. Verify Module Structure
```bash
ls -la backend/app/core/research/
# Should see:
# ├── __init__.py
# ├── research_brain.py (1,200+ lines)
# ├── data_sources.py (800+ lines)
# └── research_to_cu_bridge.py (600+ lines)
```

### 2. Module Dependencies
No new external dependencies required! Uses only:
- Python 3.9+ (async/await)
- aiohttp (already in project)
- dataclasses (built-in)
- asyncio (built-in)

### 3. Initialize Research Brain

Add to your main app initialization:

```python
# app/main.py
from app.core.research import initialize_research_brain, initialize_data_sources

@app.on_event("startup")
async def startup_research_brain():
    # Initialize research brain
    app.state.research_brain = await initialize_research_brain()
    
    # Initialize data sources
    app.state.data_sources = await initialize_data_sources()
    
    logger.info("Research Brain initialized - 52+ agents active")

@app.on_event("shutdown")
async def shutdown_research():
    if hasattr(app.state, 'data_sources'):
        await app.state.data_sources.close_session()
```

---

## Basic Usage (10 minutes)

### A. Run Market Research

```python
from app.core.research import ResearchBrain

async def analyze_market():
    research_brain = app.state.research_brain
    
    # Execute research
    signals = await research_brain.research(
        query="market_opportunity_analysis",
        context={
            "region": "LATAM",
            "industry": "SaaS",
            "company_size": "mid_market"
        }
    )
    
    # Synthesize results
    insights = research_brain.synthesize_signals(signals)
    
    return {
        "total_signals": insights["total_signals"],
        "confidence": insights["avg_confidence"],
        "insights": insights["by_type"]
    }
```

### B. Get Competitor Intelligence

```python
async def track_competitors():
    data_sources = app.state.data_sources
    
    # Get competitor intelligence
    competitor_data = await data_sources.get_competitor_intelligence(
        competitor_domain="competitor.com"
    )
    
    return {
        "keywords": competitor_data["keywords"],
        "backlinks": competitor_data["backlinks"],
        "mentions": competitor_data["web_mentions"]
    }
```

### C. Get Market Trends

```python
async def get_market_trends():
    data_sources = app.state.data_sources
    
    # Get trending topics
    trends = await data_sources.get_trending_topics()
    
    # Get market intelligence
    market = await data_sources.get_market_intelligence()
    
    return {
        "trending_topics": trends[:5],
        "market_conditions": market["market_conditions"],
        "news": market["news"][:3]
    }
```

### D. Get Real-Time Alerts

```python
async def monitor_alerts():
    data_sources = app.state.data_sources
    
    # Get real-time alerts
    alerts = await data_sources.get_real_time_alerts()
    
    # Filter critical alerts
    critical = [a for a in alerts if a["urgency"] == "high"]
    
    return {
        "total_alerts": len(alerts),
        "critical_alerts": critical
    }
```

---

## Integration with Computer Use (15 minutes)

### A. Connect Research to Computer Use Decisions

```python
from app.core.research import ResearchInsightsCoordinator

async def qualify_lead_with_research(lead_data):
    research_brain = app.state.research_brain
    cu_orchestrator = app.state.cu_orchestrator
    
    # Create coordinator
    coordinator = ResearchInsightsCoordinator(research_brain, cu_orchestrator)
    
    # Get research-backed decision
    result = await coordinator.coordinate_lead_qualification(lead_data)
    
    # Extract insights
    context = result["context"]
    actions = result["recommended_actions"]
    
    # Execute actions through Computer Use
    for action in actions:
        await cu_orchestrator.execute_action(action)
    
    return result
```

### B. Research-Backed Campaign Execution

```python
async def execute_campaign_with_research(campaign_data):
    coordinator = ResearchInsightsCoordinator(
        app.state.research_brain,
        app.state.cu_orchestrator
    )
    
    # Get research-backed campaign strategy
    result = await coordinator.coordinate_campaign_execution(campaign_data)
    
    # Extract recommendations
    actions = result["recommended_actions"]
    
    # Recommended channels
    channels = [a.target_audience.get("platform") for a in actions]
    
    # Content guidance
    messaging = [a.content_guidance for a in actions]
    
    return {
        "recommended_channels": channels,
        "messaging_guidance": messaging,
        "actions": actions
    }
```

### C. Real-Time Decision Context

```python
async def get_decision_context():
    coordinator = ResearchInsightsCoordinator(
        app.state.research_brain,
        app.state.cu_orchestrator
    )
    
    # Get real-time market context
    market_context = await coordinator.get_real_time_market_context()
    
    return {
        "market_insights": market_context["market_insights"],
        "competitor_alerts": market_context["competitor_alerts"],
        "trend_alerts": market_context["trend_alerts"],
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## API Endpoints (20 minutes)

Add these endpoints to your FastAPI app:

```python
from fastapi import APIRouter, HTTPException
from app.core.research import ResearchInsightsCoordinator

research_router = APIRouter(prefix="/api/research", tags=["research"])

@research_router.get("/health")
async def research_health():
    """Get research brain health"""
    return app.state.research_brain.get_brain_health()

@research_router.get("/trends")
async def get_trends():
    """Get trending topics and market trends"""
    return await app.state.data_sources.get_trending_topics()

@research_router.get("/alerts")
async def get_alerts():
    """Get real-time market alerts"""
    return await app.state.data_sources.get_real_time_alerts()

@research_router.post("/analyze-lead")
async def analyze_lead(lead: dict):
    """Get research-backed lead analysis"""
    coordinator = ResearchInsightsCoordinator(
        app.state.research_brain,
        app.state.cu_orchestrator
    )
    return await coordinator.coordinate_lead_qualification(lead)

@research_router.post("/analyze-competitor")
async def analyze_competitor(domain: str):
    """Get competitor intelligence"""
    return await app.state.data_sources.get_competitor_intelligence(domain)

@research_router.get("/market-intelligence")
async def market_intelligence():
    """Get comprehensive market intelligence"""
    return await app.state.data_sources.get_market_intelligence()

@research_router.post("/optimize-campaign")
async def optimize_campaign(campaign: dict):
    """Get research-backed campaign optimization"""
    coordinator = ResearchInsightsCoordinator(
        app.state.research_brain,
        app.state.cu_orchestrator
    )
    return await coordinator.coordinate_campaign_execution(campaign)

# Register router
app.include_router(research_router)
```

---

## Key Agent Categories

### Market Research (8 agents)
- Demographic analysis
- Psychographic profiling
- Geographic segmentation
- Behavioral patterns
- Market sizing
- Industry benchmarks

**Use for:** Understanding your market and customers

### Competitive Intelligence (12 agents)
- Competitor pricing
- Product analysis
- Messaging audit
- Growth tracking
- Sentiment analysis

**Use for:** Staying ahead of competitors

### Content & SEO (8 agents)
- Keyword research
- Trending topics
- Content gaps
- SEO opportunities

**Use for:** Content strategy and visibility

### Advertising (10 agents)
- Audience targeting
- Creative strategy
- Budget optimization
- Campaign performance

**Use for:** Running effective campaigns

### Sales & Distribution (8 agents)
- Channel effectiveness
- Customer journey
- Funnel optimization
- Conversion analysis

**Use for:** Optimizing sales processes

### Market Intelligence (6 agents)
- Trend detection
- News monitoring
- Opportunity scouting
- Threat detection

**Use for:** Real-time market awareness

### Positioning (4 agents)
- Brand positioning
- Value proposition
- Brand health
- Reputation management

**Use for:** Strengthening brand

---

## Real-Time Monitoring Setup (10 minutes)

### Enable Continuous Market Monitoring

```python
import asyncio
from app.core.research import ResearchInsightsCoordinator

async def monitor_market_continuously():
    """Monitor market 24/7 and alert on critical changes"""
    coordinator = ResearchInsightsCoordinator(
        app.state.research_brain,
        app.state.cu_orchestrator
    )
    
    while True:
        try:
            # Get real-time market context
            market_context = await coordinator.get_real_time_market_context()
            
            # Process market insights
            for insight in market_context["market_insights"]:
                if insight.urgency == "critical":
                    # Alert sales team
                    await notify_team({
                        "type": "market_insight",
                        "insight": insight.insight,
                        "action_required": insight.action_required
                    })
            
            # Process competitor alerts
            for alert in market_context["competitor_alerts"]:
                if alert.impact_level == "critical":
                    await notify_team({
                        "type": "competitor_alert",
                        "competitor": alert.competitor_id,
                        "signal": alert.signal_type
                    })
            
            # Process trend alerts
            for trend in market_context["trend_alerts"]:
                if trend.opportunity:
                    await notify_team({
                        "type": "trend_alert",
                        "trend": trend.trend_name,
                        "direction": trend.direction
                    })
            
            # Sleep before next check (check every hour)
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Market monitoring error: {e}")
            await asyncio.sleep(300)

# Start monitoring on app startup
asyncio.create_task(monitor_market_continuously())
```

---

## Common Use Cases

### 1. Pre-Call Research
```python
async def pre_call_research(prospect_id: str):
    """Get research insights before sales call"""
    coordinator = ResearchInsightsCoordinator(...)
    result = await coordinator.coordinate_engagement_strategy({
        "id": prospect_id
    })
    return result["recommended_actions"]
```

### 2. Win/Loss Analysis
```python
async def analyze_loss(deal_data: dict):
    """Analyze why deal was lost with market research"""
    signals = await research_brain.research(
        "deal_loss_analysis",
        {"deal": deal_data}
    )
    return research_brain.synthesize_signals(signals)
```

### 3. Competitive Response
```python
async def respond_to_competitor(competitor_action: dict):
    """Get research-backed response strategy"""
    signals = await research_brain.research(
        "competitive_response",
        {"competitor_action": competitor_action}
    )
    return research_brain.synthesize_signals(signals)
```

### 4. Content Planning
```python
async def plan_content_month(month: str):
    """Get content recommendations from research"""
    result = await data_sources.get_keyword_intelligence("")
    trends = await data_sources.get_trending_topics()
    return {
        "keywords": result,
        "trends": trends
    }
```

### 5. Customer Retention
```python
async def retention_strategy(customer_id: str):
    """Get retention insights for at-risk customer"""
    coordinator = ResearchInsightsCoordinator(...)
    result = await coordinator.coordinate_customer_retention({
        "id": customer_id
    })
    return result
```

---

## Troubleshooting

### Issue: No signals returned
**Solution:** Check that agents are initialized and data sources are connected
```python
health = app.state.research_brain.get_brain_health()
print(health)  # Should show 52+ agents
```

### Issue: Low confidence signals
**Solution:** Combine multiple agents for validation
```python
signals = await research_brain.research(
    "query",
    context,
    agent_ids=["agent.market_research", "agent.competitor_analysis"]
)
```

### Issue: Data source unavailable
**Solution:** Check data source health
```python
health = await data_sources.health_check()
print(health["sources"])  # See which sources have issues
```

---

## Next Steps

1. **Deploy** - Add research modules to your app
2. **Integrate** - Connect to Computer Use Orchestrator
3. **Test** - Run sample queries and monitor
4. **Optimize** - Fine-tune agent confidence scores
5. **Monitor** - Setup real-time alerting

---

## Support Resources

- **Full Implementation Guide:** `RESEARCH_BRAIN_IMPLEMENTATION.md`
- **Brain Evolution Guide:** `BRAIN_EVOLUTION_GUIDE.md`
- **Code Location:** `backend/app/core/research/`
- **API Reference:** See implementation guide section 8

---

**Status:** Production-Ready  
**Last Updated:** 2026-07-03  
**Version:** 1.0
