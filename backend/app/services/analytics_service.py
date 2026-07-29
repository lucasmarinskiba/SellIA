"""
Analytics Service
- Funnel metrics (new → contacted → engaged → qualified → won)
- Lead source ROI
- Email delivery metrics
- Workflow performance
- Lead scoring distribution
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead, WorkflowExecution, LeadSource, EmailLog

logger = logging.getLogger(__name__)

# ============================================================
# ANALYTICS SERVICE
# ============================================================
class AnalyticsService:
    """Calculate key business metrics."""

    async def get_lead_funnel(self, session: AsyncSession) -> dict:
        """Sales funnel: count leads at each stage."""
        statuses = ["new", "contacted", "engaged", "qualified", "won", "bounced", "unsubscribed", "lost"]

        funnel = {}
        for status in statuses:
            stmt = select(func.count(Lead.id)).where(Lead.status == status)
            result = await session.execute(stmt)
            count = result.scalar() or 0
            funnel[status] = count

        total = sum(funnel.values())

        # Calculate conversion rates
        conversion_rates = {}
        if total > 0:
            for status in statuses:
                conversion_rates[status] = round((funnel[status] / total) * 100, 2)

        return {
            "funnel": funnel,
            "total": total,
            "conversion_rates": conversion_rates,
            "flow": "new → contacted → engaged → qualified → won"
        }

    async def get_email_metrics(self, session: AsyncSession) -> dict:
        """Email delivery performance."""
        stmt = select(
            func.count(EmailLog.id).label("total_sent"),
            func.sum(func.cast(EmailLog.status == "delivered", func.Integer)).label("delivered"),
            func.sum(func.cast(EmailLog.status == "opened", func.Integer)).label("opened"),
            func.sum(func.cast(EmailLog.status == "clicked", func.Integer)).label("clicked"),
            func.sum(func.cast(EmailLog.status == "bounced", func.Integer)).label("bounced"),
        )

        result = await session.execute(stmt)
        row = result.first()

        total = row[0] or 0
        delivered = row[1] or 0
        opened = row[2] or 0
        clicked = row[3] or 0
        bounced = row[4] or 0

        def safe_rate(numerator, denominator):
            return round((numerator / denominator) * 100, 2) if denominator > 0 else 0

        return {
            "total_sent": total,
            "delivered": delivered,
            "delivery_rate": safe_rate(delivered, total),
            "opened": opened,
            "open_rate": safe_rate(opened, delivered),
            "clicked": clicked,
            "click_rate": safe_rate(clicked, opened),
            "bounced": bounced,
            "bounce_rate": safe_rate(bounced, total)
        }

    async def get_lead_source_analytics(self, session: AsyncSession) -> dict:
        """ROI by lead source."""
        stmt = select(
            Lead.source,
            func.count(Lead.id).label("total_leads"),
            func.avg(Lead.score).label("avg_score"),
            func.sum(func.cast(Lead.status == "engaged", func.Integer)).label("engaged_count"),
            func.sum(func.cast(Lead.status == "qualified", func.Integer)).label("qualified_count"),
            func.sum(func.cast(Lead.status == "won", func.Integer)).label("won_count"),
        ).group_by(Lead.source)

        result = await session.execute(stmt)
        rows = result.all()

        sources = {}
        for row in rows:
            source = row[0] or "unknown"
            total = row[1] or 0
            avg_score = row[2] or 0
            engaged = row[3] or 0
            qualified = row[4] or 0
            won = row[5] or 0

            def safe_rate(num, den):
                return round((num / den) * 100, 2) if den > 0 else 0

            sources[source] = {
                "total_leads": total,
                "avg_score": round(avg_score, 1),
                "engaged": engaged,
                "engagement_rate": safe_rate(engaged, total),
                "qualified": qualified,
                "qualification_rate": safe_rate(qualified, total),
                "won": won,
                "conversion_rate": safe_rate(won, total)
            }

        return {
            "by_source": sources,
            "total_leads": sum(s["total_leads"] for s in sources.values())
        }

    async def get_workflow_performance(self, session: AsyncSession) -> dict:
        """Workflow step performance."""
        stmt = select(
            WorkflowExecution.workflow_id,
            WorkflowExecution.step_number,
            func.count(WorkflowExecution.id).label("total"),
            func.sum(func.cast(WorkflowExecution.email_status == "sent", func.Integer)).label("sent"),
            func.sum(func.cast(WorkflowExecution.email_status == "opened", func.Integer)).label("opened"),
            func.sum(func.cast(WorkflowExecution.email_status == "clicked", func.Integer)).label("clicked"),
            func.sum(func.cast(WorkflowExecution.email_status == "bounced", func.Integer)).label("bounced"),
        ).group_by(WorkflowExecution.workflow_id, WorkflowExecution.step_number)

        result = await session.execute(stmt)
        rows = result.all()

        workflows = {}
        for row in rows:
            wf_id = row[0]
            step = row[1]
            total = row[2] or 0
            sent = row[3] or 0
            opened = row[4] or 0
            clicked = row[5] or 0
            bounced = row[6] or 0

            def safe_rate(num, den):
                return round((num / den) * 100, 2) if den > 0 else 0

            if wf_id not in workflows:
                workflows[wf_id] = {}

            workflows[wf_id][f"step_{step}"] = {
                "total": total,
                "sent": sent,
                "open_rate": safe_rate(opened, sent),
                "click_rate": safe_rate(clicked, sent),
                "bounce_rate": safe_rate(bounced, total)
            }

        return {"by_workflow": workflows}

    async def get_lead_score_distribution(self, session: AsyncSession) -> dict:
        """Lead scoring histogram."""
        buckets = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }

        leads_stmt = select(Lead.score)
        result = await session.execute(leads_stmt)
        scores = [row[0] for row in result.all() if row[0] is not None]

        for score in scores:
            if score <= 20:
                buckets["0-20"] += 1
            elif score <= 40:
                buckets["21-40"] += 1
            elif score <= 60:
                buckets["41-60"] += 1
            elif score <= 80:
                buckets["61-80"] += 1
            else:
                buckets["81-100"] += 1

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        return {
            "distribution": buckets,
            "total_leads": len(scores),
            "avg_score": avg_score,
            "max_score": max_score,
            "min_score": min_score
        }

    async def get_time_series_metrics(
        self,
        session: AsyncSession,
        days: int = 30
    ) -> dict:
        """Daily metrics for time series."""
        cutoff = datetime.now() - timedelta(days=days)

        # Leads created per day
        stmt = select(
            func.date(Lead.created_at),
            func.count(Lead.id)
        ).where(Lead.created_at >= cutoff).group_by(func.date(Lead.created_at))

        result = await session.execute(stmt)
        leads_by_day = {str(row[0]): row[1] for row in result.all()}

        # Emails sent per day
        stmt = select(
            func.date(EmailLog.sent_at),
            func.count(EmailLog.id)
        ).where(EmailLog.sent_at >= cutoff).group_by(func.date(EmailLog.sent_at))

        result = await session.execute(stmt)
        emails_by_day = {str(row[0]): row[1] for row in result.all()}

        return {
            "leads_by_day": leads_by_day,
            "emails_by_day": emails_by_day,
            "period_days": days
        }

    async def get_lead_health_scores(self, session: AsyncSession) -> dict:
        """Lead health segmentation."""
        # Get all leads with recent activity
        stmt = select(
            Lead.id,
            Lead.name,
            Lead.email,
            Lead.company,
            Lead.score,
            Lead.status,
            Lead.last_contacted
        )

        result = await session.execute(stmt)
        leads = result.all()

        hot = []      # score ≥ 70, contacted < 3 days ago
        warm = []     # score 40-69, contacted < 7 days ago
        cold = []     # score < 40 OR contacted > 7 days ago
        dead = []     # status in [bounced, unsubscribed, lost]

        now = datetime.now()

        for lead in leads:
            lead_id, name, email, company, score, status, last_contacted = lead

            if status in ["bounced", "unsubscribed", "lost"]:
                dead.append({
                    "id": lead_id,
                    "name": name,
                    "email": email,
                    "company": company,
                    "score": score,
                    "status": status
                })
            else:
                days_since = (now - last_contacted).days if last_contacted else 999

                if (score or 0) >= 70 and days_since <= 3:
                    hot.append({
                        "id": lead_id,
                        "name": name,
                        "company": company,
                        "score": score,
                        "days_since_contact": days_since
                    })
                elif 40 <= (score or 0) < 70 and days_since <= 7:
                    warm.append({
                        "id": lead_id,
                        "name": name,
                        "company": company,
                        "score": score,
                        "days_since_contact": days_since
                    })
                else:
                    cold.append({
                        "id": lead_id,
                        "name": name,
                        "company": company,
                        "score": score,
                        "days_since_contact": days_since
                    })

        return {
            "hot": {"count": len(hot), "leads": hot},
            "warm": {"count": len(warm), "leads": warm},
            "cold": {"count": len(cold), "leads": cold},
            "dead": {"count": len(dead), "leads": dead},
            "total": len(hot) + len(warm) + len(cold) + len(dead)
        }

# ============================================================
# GLOBAL SERVICE
# ============================================================
analytics_service: AnalyticsService = None

async def init_analytics_service() -> AnalyticsService:
    """Initialize service."""
    global analytics_service
    analytics_service = AnalyticsService()
    return analytics_service

async def get_analytics_service() -> AnalyticsService:
    """Get service."""
    global analytics_service
    if not analytics_service:
        analytics_service = AnalyticsService()
    return analytics_service
