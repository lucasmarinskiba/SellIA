"""Market Analysis Engine — Competitive Intel, Trends, Forecasting."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class MarketPhase(str, Enum):
    EMERGING = "emerging"
    GROWTH = "growth"
    MATURE = "mature"
    DECLINE = "decline"


class TrendDirection(str, Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"


@dataclass
class CompetitorProfile:
    """Profile of competitor."""

    competitor_id: str
    name: str
    market_share: float
    pricing_strategy: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recent_moves: List[Dict[str, Any]] = field(default_factory=list)
    estimated_revenue: Optional[float] = None
    customer_satisfaction: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketTrend:
    """Market trend data."""

    metric_name: str
    values: List[float]
    timestamps: List[datetime]
    direction: TrendDirection
    strength: float  # 0.0 to 1.0
    slope: float
    forecast_next_30_days: List[float] = field(default_factory=list)


class CompetitiveIntelligence:
    """Track competitor pricing, strategies, market moves."""

    def __init__(self):
        self.competitors: Dict[str, CompetitorProfile] = {}
        self.price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.move_log: List[Dict[str, Any]] = []

    def add_competitor(self, profile: CompetitorProfile) -> None:
        """Register competitor."""
        self.competitors[profile.competitor_id] = profile
        logger.info(f"Added competitor: {profile.name}")

    def track_price_change(self, competitor_id: str, price: float, timestamp: Optional[datetime] = None) -> None:
        """Track price changes over time."""
        if competitor_id not in self.price_history:
            self.price_history[competitor_id] = []

        timestamp = timestamp or datetime.utcnow()
        self.price_history[competitor_id].append((timestamp, price))

        # Log if significant price change
        if len(self.price_history[competitor_id]) > 1:
            prev_price = self.price_history[competitor_id][-2][1]
            change_pct = ((price - prev_price) / prev_price) * 100
            if abs(change_pct) > 5:
                self.log_move(competitor_id, "price_change", {"from": prev_price, "to": price, "change_pct": change_pct})

    def log_move(self, competitor_id: str, move_type: str, details: Dict[str, Any]) -> None:
        """Log strategic move."""
        move = {
            "competitor_id": competitor_id,
            "type": move_type,
            "timestamp": datetime.utcnow(),
            "details": details,
        }
        self.move_log.append(move)

        if competitor_id in self.competitors:
            self.competitors[competitor_id].recent_moves.append(move)

        logger.info(f"Logged move for {competitor_id}: {move_type}")

    def get_price_trends(self, competitor_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Analyze price trends for competitor."""
        if competitor_id not in self.price_history:
            return None

        history = self.price_history[competitor_id]
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [(t, p) for t, p in history if t >= cutoff]

        if len(recent) < 2:
            return None

        prices = [p for _, p in recent]
        slope, intercept, r_value, _, _ = stats.linregress(range(len(prices)), prices)

        return {
            "competitor_id": competitor_id,
            "period_days": days,
            "num_observations": len(recent),
            "avg_price": float(np.mean(prices)),
            "min_price": float(np.min(prices)),
            "max_price": float(np.max(prices)),
            "price_volatility": float(np.std(prices)),
            "trend_slope": float(slope),
            "r_squared": float(r_value**2),
            "direction": "uptrend" if slope > 0 else "downtrend" if slope < 0 else "stable",
        }

    def competitive_positioning(self) -> Dict[str, Any]:
        """Analyze overall competitive landscape."""
        if not self.competitors:
            return {}

        market_shares = [c.market_share for c in self.competitors.values()]
        total_share = sum(market_shares)

        return {
            "num_competitors": len(self.competitors),
            "hhi_index": float(sum(s**2 for s in market_shares)),  # Herfindahl index
            "market_concentration": "concentrated" if total_share > 0.8 else "fragmented",
            "top_competitors": [
                c.name for c in sorted(self.competitors.values(), key=lambda x: x.market_share, reverse=True)[:3]
            ],
            "competitive_intensity": len(self.move_log) / max(1, (datetime.utcnow() - self.move_log[0]["timestamp"]).days)
            if self.move_log
            else 0,
        }


class MarketTrendsAnalyzer:
    """Analyze seasonal patterns, demand curves, growth rates."""

    def __init__(self):
        self.trends: Dict[str, MarketTrend] = {}
        self.seasonality_patterns: Dict[str, Dict[str, float]] = {}

    def add_trend_data(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
    ) -> MarketTrend:
        """Add trend data and analyze."""
        if len(values) < 2:
            raise ValueError("Need at least 2 data points")

        # Calculate trend
        slope, intercept, r_value, _, _ = stats.linregress(range(len(values)), values)

        # Determine direction
        if slope > np.std(values) * 0.1:
            direction = TrendDirection.UPTREND
        elif slope < -np.std(values) * 0.1:
            direction = TrendDirection.DOWNTREND
        else:
            direction = TrendDirection.SIDEWAYS

        # Calculate trend strength
        trend_strength = abs(r_value)

        trend = MarketTrend(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            direction=direction,
            strength=float(trend_strength),
            slope=float(slope),
        )

        self.trends[metric_name] = trend
        logger.info(f"Added trend: {metric_name} ({direction.value}, strength={trend_strength:.2f})")

        return trend

    def detect_seasonality(self, metric_name: str, period: int = 12) -> Dict[str, float]:
        """Detect seasonal patterns (e.g., monthly for annual data)."""
        if metric_name not in self.trends:
            return {}

        values = self.trends[metric_name].values
        if len(values) < period * 2:
            return {}

        seasonal_factors = {}
        overall_mean = np.mean(values)

        for i in range(period):
            seasonal_values = values[i::period]
            seasonal_mean = np.mean(seasonal_values)
            seasonal_factors[f"season_{i}"] = float(seasonal_mean / overall_mean)

        self.seasonality_patterns[metric_name] = seasonal_factors
        logger.info(f"Detected seasonality for {metric_name}: {period} periods")

        return seasonal_factors

    def forecast_trend(self, metric_name: str, periods: int = 30) -> List[float]:
        """Forecast future values using linear regression + seasonality."""
        if metric_name not in self.trends:
            return []

        trend = self.trends[metric_name]
        values = trend.values
        slope = trend.slope
        intercept = np.mean(values) - slope * (len(values) / 2)

        forecast = []
        seasonal_factors = self.seasonality_patterns.get(metric_name, {})

        for i in range(periods):
            x = len(values) + i
            forecast_value = slope * x + intercept

            # Apply seasonality if available
            if seasonal_factors:
                season_idx = i % len(seasonal_factors)
                season_key = f"season_{season_idx}"
                if season_key in seasonal_factors:
                    forecast_value *= seasonal_factors[season_key]

            forecast.append(float(forecast_value))

        self.trends[metric_name].forecast_next_30_days = forecast[:30]
        return forecast

    def growth_rate(self, metric_name: str) -> Optional[float]:
        """Calculate compound growth rate."""
        if metric_name not in self.trends:
            return None

        values = self.trends[metric_name].values
        if len(values) < 2:
            return None

        start_value = values[0]
        end_value = values[-1]
        periods = len(values) - 1

        if start_value <= 0:
            return None

        cagr = (pow(end_value / start_value, 1 / periods) - 1) * 100
        return float(cagr)


class OwnAnalyzer:
    """Analyze seller's historical performance."""

    def __init__(self, seller_id: str):
        self.seller_id = seller_id
        self.sales_history: List[Dict[str, Any]] = []
        self.conversion_rate: float = 0.0
        self.avg_deal_value: float = 0.0
        self.sales_velocity: float = 0.0  # deals per day
        self.customer_satisfaction: float = 0.0

    def add_sales_records(self, records: List[Dict[str, Any]]) -> None:
        """Add historical sales records."""
        self.sales_history.extend(records)
        self._calculate_metrics()

    def _calculate_metrics(self) -> None:
        """Calculate key performance metrics."""
        if not self.sales_history:
            return

        # Conversion rate
        total_leads = len([s for s in self.sales_history if s.get("type") == "lead"])
        total_sales = len([s for s in self.sales_history if s.get("type") == "sale"])
        self.conversion_rate = (total_sales / total_leads) if total_leads > 0 else 0.0

        # Average deal value
        deal_values = [s.get("value", 0) for s in self.sales_history if s.get("type") == "sale"]
        self.avg_deal_value = float(np.mean(deal_values)) if deal_values else 0.0

        # Sales velocity
        if self.sales_history:
            time_span = (self.sales_history[-1].get("timestamp", datetime.utcnow()) - self.sales_history[0].get(
                "timestamp", datetime.utcnow()
            )).days
            self.sales_velocity = total_sales / max(1, time_span)

        # Customer satisfaction
        ratings = [s.get("rating", 5) for s in self.sales_history if "rating" in s]
        self.customer_satisfaction = float(np.mean(ratings)) if ratings else 5.0

        logger.info(
            f"Seller {self.seller_id} metrics: CR={self.conversion_rate:.2%}, ADV=${self.avg_deal_value:.2f}, Velocity={self.sales_velocity:.2f}"
        )

    def performance_summary(self) -> Dict[str, Any]:
        """Get seller performance summary."""
        return {
            "seller_id": self.seller_id,
            "total_records": len(self.sales_history),
            "conversion_rate": float(self.conversion_rate),
            "average_deal_value": float(self.avg_deal_value),
            "sales_velocity": float(self.sales_velocity),
            "customer_satisfaction": float(self.customer_satisfaction),
            "trend": self._identify_performance_trend(),
        }

    def _identify_performance_trend(self) -> str:
        """Identify if seller is improving or declining."""
        if len(self.sales_history) < 10:
            return "insufficient_data"

        recent = self.sales_history[-5:]
        historical = self.sales_history[:-5]

        recent_rate = len([s for s in recent if s.get("type") == "sale"]) / len(recent)
        hist_rate = len([s for s in historical if s.get("type") == "sale"]) / len(historical)

        if recent_rate > hist_rate * 1.1:
            return "improving"
        elif recent_rate < hist_rate * 0.9:
            return "declining"
        return "stable"


class SWOTAnalyzer:
    """Strengths, Weaknesses, Opportunities, Threats analysis."""

    def __init__(self):
        self.swot_analyses: Dict[str, Dict[str, List[str]]] = {}

    def analyze_market(self, market_id: str, seller_profile: Dict[str, Any], competitive_intel: CompetitiveIntelligence,
                       market_trends: MarketTrendsAnalyzer) -> Dict[str, List[str]]:
        """Comprehensive SWOT analysis for seller in market."""

        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }

        # Strengths
        if seller_profile.get("conversion_rate", 0) > 0.20:
            swot["strengths"].append("High conversion rate")
        if seller_profile.get("customer_satisfaction", 0) > 4.5:
            swot["strengths"].append("Excellent customer satisfaction")
        if seller_profile.get("market_share", 0) > 0.15:
            swot["strengths"].append("Strong market share")

        # Weaknesses
        if seller_profile.get("conversion_rate", 0) < 0.10:
            swot["weaknesses"].append("Low conversion rate")
        if seller_profile.get("sales_velocity", 0) < 0.5:
            swot["weaknesses"].append("Slow sales velocity")
        if seller_profile.get("avg_deal_value", 0) < 1000:
            swot["weaknesses"].append("Low average deal value")

        # Opportunities
        for trend_name, trend in market_trends.trends.items():
            if trend.direction == TrendDirection.UPTREND:
                swot["opportunities"].append(f"Growth in {trend_name} market")

        if len(competitive_intel.competitors) < 5:
            swot["opportunities"].append("Fragmented market - room for consolidation")

        # Threats
        if len(competitive_intel.competitors) > 10:
            swot["threats"].append("Intense competition")

        for competitor in competitive_intel.competitors.values():
            if competitor.market_share > seller_profile.get("market_share", 0) * 2:
                swot["threats"].append(f"Dominant competitor: {competitor.name}")

        self.swot_analyses[market_id] = swot
        logger.info(f"SWOT analysis for {market_id}: {len(swot['opportunities'])} opportunities, {len(swot['threats'])} threats")

        return swot


class ForecastingEngine:
    """Predict demand, prices, market conditions."""

    def __init__(self):
        self.forecast_models: Dict[str, Any] = {}
        self.predictions: Dict[str, List[float]] = {}

    def forecast_demand(self, historical_demand: List[float], periods: int = 90) -> Dict[str, Any]:
        """Forecast demand using exponential smoothing."""
        if len(historical_demand) < 3:
            return {"error": "Insufficient historical data"}

        # Simple exponential smoothing
        alpha = 0.3  # Smoothing factor
        forecasts = []
        last_value = historical_demand[-1]

        for _ in range(periods):
            forecast = alpha * last_value + (1 - alpha) * (np.mean(historical_demand[-3:]))
            forecasts.append(float(forecast))
            last_value = forecast

        # Calculate confidence intervals
        residuals = np.array(historical_demand) - np.mean(historical_demand)
        std_error = np.std(residuals)

        return {
            "forecast": forecasts[:30],  # 30-day forecast
            "mean_forecast": float(np.mean(forecasts[:30])),
            "confidence_lower": float(np.mean(forecasts[:30]) - 1.96 * std_error),
            "confidence_upper": float(np.mean(forecasts[:30]) + 1.96 * std_error),
            "trend": "uptrend" if np.mean(forecasts[:15]) > np.mean(forecasts[15:30]) else "downtrend",
        }

    def forecast_prices(self, historical_prices: List[float], periods: int = 90) -> Dict[str, Any]:
        """Forecast price movements."""
        if len(historical_prices) < 3:
            return {"error": "Insufficient historical data"}

        # ARIMA-like simple forecast
        recent_trend = (historical_prices[-1] - historical_prices[-5]) / 5
        forecasts = []

        for i in range(periods):
            forecast = historical_prices[-1] + recent_trend * (i + 1)
            forecasts.append(float(forecast))

        volatility = np.std(np.diff(historical_prices))

        return {
            "forecast": forecasts[:30],
            "mean_price": float(np.mean(forecasts[:30])),
            "price_volatility": float(volatility),
            "risk_level": "high" if volatility > np.mean(historical_prices) * 0.1 else "moderate",
        }

    def forecast_market_phase(self, growth_rate: float, market_maturity: float) -> MarketPhase:
        """Predict current/future market phase."""
        if growth_rate > 20:
            return MarketPhase.GROWTH
        elif growth_rate > 5:
            return MarketPhase.EMERGING if market_maturity < 0.3 else MarketPhase.MATURE
        else:
            return MarketPhase.DECLINE if growth_rate < -5 else MarketPhase.MATURE
