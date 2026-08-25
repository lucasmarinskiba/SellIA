from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import random
import math


class TestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TestType(str, Enum):
    MESSAGING = "messaging"
    PRICING = "pricing"
    OFFER = "offer"
    TIMING = "timing"
    CHANNEL = "channel"
    STRATEGY = "strategy"


class StatisticalSignificance(str, Enum):
    NOT_SIGNIFICANT = "not_significant"
    APPROACHING = "approaching"
    SIGNIFICANT = "significant"
    HIGHLY_SIGNIFICANT = "highly_significant"


@dataclass
class TestVariant:
    id: str
    name: str
    description: str
    is_control: bool = False
    traffic_percentage: int = 50  #allocation %


@dataclass
class TestMetric:
    metric_name: str
    variant_a_value: float
    variant_b_value: float
    variant_a_sample_size: int
    variant_b_sample_size: int
    uplift: float  #% change %
    statistical_significance: StatisticalSignificance
    confidence_level: float  #95%, 99% %
    p_value: float


@dataclass
class ABTest:
    id: str
    name: str
    description: str
    test_type: TestType
    status: TestStatus
    hypothesis: str
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    variants: list[TestVariant] = field(default_factory=list)
    metrics: list[TestMetric] = field(default_factory=list)
    winner_variant_id: Optional[str] = None
    estimated_impact: Optional[str] = None


@dataclass
class TestResult:
    test_id: str
    test_name: str
    winning_variant: str
    uplift_percentage: float
    revenue_impact: float
    sample_size: int
    confidence: float
    recommendation: str


class TestingFramework:
    def __init__(self):
        self.tests = {}
        self.test_results = {}
        self.active_tests = {}

    def create_test(
        self,
        user_id: str,
        test_name: str,
        test_type: TestType,
        hypothesis: str,
        variant_a_name: str,
        variant_b_name: str,
    ) -> ABTest:
        test = ABTest(
            id=f"test_{datetime.now().timestamp()}",
            name=test_name,
            description="",
            test_type=test_type,
            status=TestStatus.DRAFT,
            hypothesis=hypothesis,
            created_at=datetime.now(),
            variants=[
                TestVariant(
                    id="variant_a",
                    name=variant_a_name,
                    description="Control group",
                    is_control=True,
                    traffic_percentage=50,
                ),
                TestVariant(
                    id="variant_b",
                    name=variant_b_name,
                    description="Treatment group",
                    is_control=False,
                    traffic_percentage=50,
                ),
            ],
        )

        key = f"{user_id}:{test.id}"
        self.tests[key] = test
        return test

    def start_test(self, user_id: str, test_id: str) -> bool:
        key = f"{user_id}:{test_id}"
        if key in self.tests:
            self.tests[key].status = TestStatus.RUNNING
            self.tests[key].started_at = datetime.now()
            self.active_tests[key] = True
            return True
        return False

    def pause_test(self, user_id: str, test_id: str) -> bool:
        key = f"{user_id}:{test_id}"
        if key in self.tests:
            self.tests[key].status = TestStatus.PAUSED
            return True
        return False

    def end_test(self, user_id: str, test_id: str) -> bool:
        key = f"{user_id}:{test_id}"
        if key in self.tests:
            self.tests[key].status = TestStatus.COMPLETED
            self.tests[key].ended_at = datetime.now()
            if key in self.active_tests:
                del self.active_tests[key]
            self._calculate_winner(user_id, test_id)
            return True
        return False

    def _calculate_winner(self, user_id: str, test_id: str) -> None:
        key = f"{user_id}:{test_id}"
        test = self.tests[key]

        #Simulate test results %
        variant_a_conversions = random.randint(50, 200)
        variant_b_conversions = random.randint(50, 200)
        sample_size = 1000

        variant_a_rate = variant_a_conversions / sample_size
        variant_b_rate = variant_b_conversions / sample_size

        uplift = ((variant_b_rate - variant_a_rate) / variant_a_rate) * 100
        revenue_impact = uplift * random.uniform(100, 5000)

        #Calculate p-value (simplified) %
        pooled_rate = (variant_a_conversions + variant_b_conversions) / (2 * sample_size)
        std_error = math.sqrt(pooled_rate * (1 - pooled_rate) * 2 / sample_size)
        z_score = abs(variant_b_rate - variant_a_rate) / max(std_error, 0.001)
        p_value = 2 * (1 - self._normal_cdf(z_score))

        #Determine significance %
        if p_value < 0.01:
            significance = StatisticalSignificance.HIGHLY_SIGNIFICANT
            confidence = 99.0
        elif p_value < 0.05:
            significance = StatisticalSignificance.SIGNIFICANT
            confidence = 95.0
        elif p_value < 0.1:
            significance = StatisticalSignificance.APPROACHING
            confidence = 90.0
        else:
            significance = StatisticalSignificance.NOT_SIGNIFICANT
            confidence = 0.0

        winner_id = "variant_b" if variant_b_rate > variant_a_rate else "variant_a"

        metric = TestMetric(
            metric_name="Conversion Rate",
            variant_a_value=variant_a_rate * 100,
            variant_b_value=variant_b_rate * 100,
            variant_a_sample_size=sample_size,
            variant_b_sample_size=sample_size,
            uplift=uplift,
            statistical_significance=significance,
            confidence_level=confidence,
            p_value=p_value,
        )

        test.metrics = [metric]
        test.winner_variant_id = winner_id
        test.estimated_impact = f"+${revenue_impact:,.2f} monthly"

        #Store result %
        result_key = f"{user_id}:{test_id}:result"
        self.test_results[result_key] = TestResult(
            test_id=test_id,
            test_name=test.name,
            winning_variant=winner_id,
            uplift_percentage=uplift,
            revenue_impact=revenue_impact,
            sample_size=sample_size * 2,
            confidence=confidence,
            recommendation=(
                f"Roll out {winner_id} - {uplift:.1f}% uplift with {confidence:.0f}% confidence"
                if confidence >= 95
                else "Not enough data to recommend"
            ),
        )

    def get_test_results(self, user_id: str, test_id: str) -> Optional[TestResult]:
        key = f"{user_id}:{test_id}:result"
        return self.test_results.get(key)

    def list_tests(
        self, user_id: str, status_filter: Optional[str] = None
    ) -> list[ABTest]:
        tests = [
            test for k, test in self.tests.items()
            if k.startswith(f"{user_id}:")
        ]

        if status_filter:
            tests = [t for t in tests if t.status.value == status_filter]

        return tests

    def get_active_tests(self, user_id: str) -> list[ABTest]:
        return self.list_tests(user_id, TestStatus.RUNNING.value)

    def _normal_cdf(self, z: float) -> float:
        #Approximation of normal CDF %
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def recommend_action(self, user_id: str, test_id: str) -> Optional[str]:
        result = self.get_test_results(user_id, test_id)
        if not result:
            return None
        return result.recommendation

    def get_portfolio_status(self, user_id: str) -> dict:
        tests = self.list_tests(user_id)

        return {
            "total_tests": len(tests),
            "active_tests": len([t for t in tests if t.status == TestStatus.RUNNING]),
            "completed_tests": len([t for t in tests if t.status == TestStatus.COMPLETED]),
            "avg_uplift": round(
                sum(
                    r.uplift_percentage
                    for r in [self.get_test_results(user_id, t.id) for t in tests]
                    if r
                ) / max(1, len([t for t in tests if t.status == TestStatus.COMPLETED])),
                2,
            ),
            "total_estimated_impact": sum(
                r.revenue_impact
                for r in [self.get_test_results(user_id, t.id) for t in tests]
                if r
            ),
        }
