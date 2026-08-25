from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import random


class MetricType(str, Enum):
    LEAD_COUNT = "lead_count"
    CONVERSION_RATE = "conversion_rate"
    REVENUE = "revenue"
    AGENT_PERFORMANCE = "agent_performance"
    PIPELINE_VALUE = "pipeline_value"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    RESPONSE_TIME = "response_time"
    CLOSE_RATE = "close_rate"


class TimeRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    timestamp: datetime
    value: float
    unit: str
    trend: Optional[float] = None  # change %


@dataclass
class KPICard:
    label: str
    metric_type: MetricType
    current_value: float
    unit: str
    target: Optional[float] = None
    trend: float = 0.0  # percentage
    trend_direction: str = "neutral"  # up, down, neutral
    last_updated: datetime = field(default_factory=datetime.now)
    sparkline_data: list[float] = field(default_factory=list)


@dataclass
class AgentPerformance:
    agent_id: str
    agent_name: str
    status: str  #active, idle, offline %
    tasks_completed: int
    success_rate: float  #0-100 %
    avg_response_time: float  #seconds %
    leads_generated: int
    conversions: int
    revenue_attributed: float
    efficiency_score: float  #0-100 %


@dataclass
class SegmentMetrics:
    segment_name: str
    total_users: int
    active_users: int
    avg_leads_per_user: float
    avg_revenue_per_user: float
    avg_conversion_rate: float
    churn_rate: float
    expansion_rate: float


@dataclass
class PipelineMetrics:
    total_pipeline_value: float
    opportunities_in_stage: dict[str, int]  #stage -> count %
    avg_deal_size: float
    days_in_pipeline: float
    forecast_confidence: float  #0-100 %


@dataclass
class AnalyticsDashboard:
    user_id: str
    segment: str
    time_range: TimeRange
    kpi_cards: list[KPICard]
    agent_performance: list[AgentPerformance]
    segment_benchmarks: SegmentMetrics
    pipeline: PipelineMetrics
    generated_at: datetime = field(default_factory=datetime.now)


class PerformanceDashboardEngine:
    def __init__(self):
        self.metrics_cache = {}

    def get_dashboard(
        self,
        user_id: str,
        segment: str,
        time_range: TimeRange = TimeRange.MONTH,
    ) -> AnalyticsDashboard:
        kpis = self._generate_kpis(user_id, segment, time_range)
        agents = self._get_agent_performance(user_id)
        benchmarks = self._get_segment_benchmarks(segment)
        pipeline = self._get_pipeline_metrics(user_id)

        return AnalyticsDashboard(
            user_id=user_id,
            segment=segment,
            time_range=time_range,
            kpi_cards=kpis,
            agent_performance=agents,
            segment_benchmarks=benchmarks,
            pipeline=pipeline,
        )

    def _generate_kpis(
        self, user_id: str, segment: str, time_range: TimeRange
    ) -> list[KPICard]:
        kpis = []

        lead_value = self._get_metric_value(user_id, MetricType.LEAD_COUNT, time_range)
        kpis.append(
            KPICard(
                label="Total Leads",
                metric_type=MetricType.LEAD_COUNT,
                current_value=lead_value,
                unit="leads",
                target=100 if segment == "early" else 500,
                trend=random.uniform(-5, 15),
                trend_direction="up" if random.random() > 0.3 else "neutral",
                sparkline_data=[
                    self._get_metric_value(user_id, MetricType.LEAD_COUNT, TimeRange.TODAY)
                    for _ in range(7)
                ],
            )
        )

        conversion_rate = self._get_metric_value(
            user_id, MetricType.CONVERSION_RATE, time_range
        )
        kpis.append(
            KPICard(
                label="Conversion Rate",
                metric_type=MetricType.CONVERSION_RATE,
                current_value=conversion_rate,
                unit="%",
                target=5.0,
                trend=random.uniform(-2, 8),
                trend_direction="up" if random.random() > 0.4 else "neutral",
            )
        )

        revenue = self._get_metric_value(user_id, MetricType.REVENUE, time_range)
        kpis.append(
            KPICard(
                label="Revenue",
                metric_type=MetricType.REVENUE,
                current_value=revenue,
                unit="USD",
                target=5000 if segment in ["early", "active"] else 50000,
                trend=random.uniform(-10, 25),
                trend_direction="up" if random.random() > 0.2 else "neutral",
            )
        )

        pipeline_value = self._get_metric_value(
            user_id, MetricType.PIPELINE_VALUE, time_range
        )
        kpis.append(
            KPICard(
                label="Pipeline Value",
                metric_type=MetricType.PIPELINE_VALUE,
                current_value=pipeline_value,
                unit="USD",
                target=15000,
                trend=random.uniform(-5, 20),
                trend_direction="up",
            )
        )

        return kpis

    def _get_agent_performance(self, user_id: str) -> list[AgentPerformance]:
        agents = [
            AgentPerformance(
                agent_id="lead_scout",
                agent_name="Lead Scout",
                status="active",
                tasks_completed=random.randint(50, 200),
                success_rate=round(random.uniform(75, 95), 1),
                avg_response_time=round(random.uniform(2, 15), 1),
                leads_generated=random.randint(10, 100),
                conversions=random.randint(1, 20),
                revenue_attributed=round(random.uniform(100, 5000), 2),
                efficiency_score=round(random.uniform(70, 95), 1),
            ),
            AgentPerformance(
                agent_id="closer_bot",
                agent_name="Closer Bot",
                status="active",
                tasks_completed=random.randint(30, 100),
                success_rate=round(random.uniform(80, 98), 1),
                avg_response_time=round(random.uniform(1, 8), 1),
                leads_generated=0,
                conversions=random.randint(5, 50),
                revenue_attributed=round(random.uniform(500, 10000), 2),
                efficiency_score=round(random.uniform(75, 98), 1),
            ),
            AgentPerformance(
                agent_id="coach_agent",
                agent_name="Coach Agent",
                status="active",
                tasks_completed=random.randint(20, 80),
                success_rate=round(random.uniform(85, 99), 1),
                avg_response_time=round(random.uniform(5, 20), 1),
                leads_generated=0,
                conversions=0,
                revenue_attributed=0,
                efficiency_score=round(random.uniform(80, 95), 1),
            ),
            AgentPerformance(
                agent_id="analytics_engine",
                agent_name="Analytics Engine",
                status="active",
                tasks_completed=random.randint(100, 500),
                success_rate=round(random.uniform(95, 99.9), 1),
                avg_response_time=round(random.uniform(0.5, 5), 1),
                leads_generated=0,
                conversions=0,
                revenue_attributed=0,
                efficiency_score=round(random.uniform(90, 99), 1),
            ),
        ]
        return agents

    def _get_segment_benchmarks(self, segment: str) -> SegmentMetrics:
        benchmarks = {
            "ultra_early": SegmentMetrics(
                segment_name="Ultra Early",
                total_users=150,
                active_users=45,
                avg_leads_per_user=5.2,
                avg_revenue_per_user=150.0,
                avg_conversion_rate=1.5,
                churn_rate=0.25,
                expansion_rate=0.15,
            ),
            "early": SegmentMetrics(
                segment_name="Early",
                total_users=500,
                active_users=300,
                avg_leads_per_user=25.0,
                avg_revenue_per_user=1200.0,
                avg_conversion_rate=3.5,
                churn_rate=0.18,
                expansion_rate=0.35,
            ),
            "active": SegmentMetrics(
                segment_name="Active",
                total_users=1200,
                active_users=1050,
                avg_leads_per_user=80.0,
                avg_revenue_per_user=5000.0,
                avg_conversion_rate=6.0,
                churn_rate=0.08,
                expansion_rate=0.42,
            ),
            "converter": SegmentMetrics(
                segment_name="Converter",
                total_users=800,
                active_users=750,
                avg_leads_per_user=200.0,
                avg_revenue_per_user=15000.0,
                avg_conversion_rate=8.5,
                churn_rate=0.05,
                expansion_rate=0.55,
            ),
            "power_user": SegmentMetrics(
                segment_name="Power User",
                total_users=300,
                active_users=295,
                avg_leads_per_user=500.0,
                avg_revenue_per_user=50000.0,
                avg_conversion_rate=12.0,
                churn_rate=0.02,
                expansion_rate=0.70,
            ),
            "dormant": SegmentMetrics(
                segment_name="Dormant",
                total_users=600,
                active_users=80,
                avg_leads_per_user=2.0,
                avg_revenue_per_user=50.0,
                avg_conversion_rate=0.5,
                churn_rate=0.80,
                expansion_rate=0.05,
            ),
        }
        return benchmarks.get(segment, benchmarks["early"])

    def _get_pipeline_metrics(self, user_id: str) -> PipelineMetrics:
        return PipelineMetrics(
            total_pipeline_value=round(random.uniform(5000, 100000), 2),
            opportunities_in_stage={
                "prospecting": random.randint(10, 50),
                "qualification": random.randint(5, 30),
                "proposal": random.randint(3, 20),
                "negotiation": random.randint(1, 10),
                "won": random.randint(0, 5),
            },
            avg_deal_size=round(random.uniform(500, 5000), 2),
            days_in_pipeline=round(random.uniform(15, 60), 1),
            forecast_confidence=round(random.uniform(70, 95), 1),
        )

    def _get_metric_value(
        self, user_id: str, metric_type: MetricType, time_range: TimeRange
    ) -> float:
        ranges = {
            MetricType.LEAD_COUNT: (10, 500),
            MetricType.CONVERSION_RATE: (0.5, 15.0),
            MetricType.REVENUE: (100, 50000),
            MetricType.PIPELINE_VALUE: (1000, 100000),
        }
        min_val, max_val = ranges.get(metric_type, (0, 100))
        return round(random.uniform(min_val, max_val), 2)
