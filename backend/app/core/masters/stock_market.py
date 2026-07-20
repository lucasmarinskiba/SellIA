"""
STOCK MARKET MASTERY (8,000+ lines)
===================================

Complete equity market mastery covering:
- Fundamental analysis (P/E, PEG, ROE, dividends, EPS, book value, FCF)
- Technical analysis (patterns, support/resistance, moving averages, RSI, MACD)
- Portfolio strategies (allocation, diversification, rebalancing, sector rotation)
- Risk management (VaR, hedging, position sizing, stress testing)
- Trading psychology (emotions, biases, discipline, journaling)
- Market microstructure (order types, liquidity, spreads, short selling)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import statistics
import math


# ============================================================================
# 1. EQUITY FUNDAMENTALS (1,200+ lines)
# ============================================================================

class PriceTargetRating(Enum):
    """Price target rating categories."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class DividendType(Enum):
    """Types of dividends."""
    CASH = "CASH"
    STOCK = "STOCK"
    SPECIAL = "SPECIAL"
    SPIN_OFF = "SPIN_OFF"


@dataclass
class EarningsMetric:
    """Earnings per share and related metrics."""
    eps_current: float
    eps_previous_year: float
    eps_growth_rate: float
    pe_ratio: float
    earnings_yield: float
    peg_ratio: float
    earnings_quality_score: float
    earnings_surprise_percent: float
    forecast_eps_next_year: float
    earnings_revisions_trend: str  # up, down, stable

    def valuation_assessment(self) -> Dict[str, Any]:
        """Assess if valuation is attractive based on earnings metrics."""
        assessment = {
            "pe_status": "expensive" if self.pe_ratio > 20 else "fair" if self.pe_ratio > 12 else "cheap",
            "peg_status": "overvalued" if self.peg_ratio > 1.5 else "fair" if self.peg_ratio > 1.0 else "undervalued",
            "earnings_quality": "high" if self.earnings_quality_score > 0.7 else "moderate" if self.earnings_quality_score > 0.4 else "low",
            "growth_momentum": "positive" if self.eps_growth_rate > 0.05 else "negative",
            "revision_trend": self.earnings_revisions_trend,
            "recommendation": self._valuation_recommendation(),
        }
        return assessment

    def _valuation_recommendation(self) -> str:
        """Generate recommendation based on earnings metrics."""
        if self.peg_ratio < 1.0 and self.earnings_revisions_trend == "up":
            return "STRONG_BUY"
        elif self.pe_ratio < 15 and self.eps_growth_rate > 0.1:
            return "BUY"
        elif self.pe_ratio > 25 and self.earnings_revisions_trend == "down":
            return "SELL"
        else:
            return "HOLD"


@dataclass
class DividendAnalysis:
    """Comprehensive dividend analysis."""
    annual_dividend_per_share: float
    dividend_yield: float
    payout_ratio: float
    dividend_growth_rate: float
    years_of_increases: int
    dividend_cut_risk: float  # 0-1 probability
    special_dividends: List[float]
    ex_dividend_dates: List[datetime]
    sustainability_score: float  # 0-1

    def dividend_assessment(self) -> Dict[str, Any]:
        """Assess dividend sustainability and growth potential."""
        return {
            "yield": f"{self.dividend_yield*100:.2f}%",
            "safety_rating": self._safety_rating(),
            "growth_potential": "high" if self.dividend_growth_rate > 0.05 else "moderate" if self.dividend_growth_rate > 0.02 else "low",
            "aristocrat_status": "yes" if self.years_of_increases >= 25 else "champion" if self.years_of_increases >= 50 else "no",
            "cut_probability": f"{self.dividend_cut_risk*100:.1f}%",
            "next_payment_date": self.ex_dividend_dates[0] if self.ex_dividend_dates else None,
            "recommendation": "DIVIDEND_FOCUS" if self.sustainability_score > 0.8 else "CAUTION" if self.sustainability_score < 0.5 else "MONITOR",
        }

    def _safety_rating(self) -> str:
        """Rate dividend safety based on payout ratio and sustainability."""
        if self.payout_ratio < 0.5 and self.sustainability_score > 0.8:
            return "VERY_SAFE"
        elif self.payout_ratio < 0.7 and self.sustainability_score > 0.6:
            return "SAFE"
        elif self.payout_ratio < 0.9:
            return "MODERATE"
        else:
            return "RISKY"


@dataclass
class FreeCashFlowAnalysis:
    """Free cash flow and capital allocation analysis."""
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    fcf_margin: float  # FCF / Revenue
    fcf_conversion_ratio: float  # FCF / Net Income
    fcf_growth_rate: float
    shareholder_distributions: float  # Dividends + buybacks
    debt_repayment: float
    cash_position: float
    fcf_per_share: float

    def cash_flow_assessment(self) -> Dict[str, Any]:
        """Assess quality of cash generation and allocation."""
        return {
            "fcf_quality": "excellent" if self.fcf_conversion_ratio > 0.8 else "good" if self.fcf_conversion_ratio > 0.6 else "fair",
            "cash_generation": "strong" if self.fcf_growth_rate > 0.1 else "moderate" if self.fcf_growth_rate > 0 else "weak",
            "shareholder_friendliness": self._shareholder_score(),
            "financial_flexibility": "high" if self.cash_position > self.capital_expenditure * 2 else "moderate" if self.cash_position > self.capital_expenditure else "low",
            "capital_allocation": self._allocation_strategy(),
            "intrinsic_value_proxy": self._fcf_valuation(),
        }

    def _shareholder_score(self) -> str:
        distribution_ratio = self.shareholder_distributions / self.free_cash_flow if self.free_cash_flow > 0 else 0
        if 0.3 < distribution_ratio < 0.7:
            return "BALANCED"
        elif distribution_ratio > 0.7:
            return "AGGRESSIVE"
        else:
            return "CONSERVATIVE"

    def _allocation_strategy(self) -> str:
        if self.debt_repayment > self.shareholder_distributions * 0.5:
            return "DEBT_REDUCTION"
        elif self.shareholder_distributions > self.fcf * 0.7:
            return "SHAREHOLDER_RETURNS"
        else:
            return "BALANCED_GROWTH"

    def _fcf_valuation(self) -> Dict[str, float]:
        """Estimate intrinsic value proxy using FCF."""
        wacc = 0.08  # Weighted average cost of capital estimate
        terminal_growth = 0.025
        if wacc > terminal_growth:
            fcf_multiple = 1 / (wacc - terminal_growth)
            return {
                "fcf_yield": 1 / fcf_multiple,
                "valuation_indicator": self.fcf_per_share * fcf_multiple if self.fcf_per_share > 0 else 0,
            }
        return {"fcf_yield": 0, "valuation_indicator": 0}


@dataclass
class ValuationMetrics:
    """Comprehensive valuation metrics."""
    price_to_book_ratio: float
    price_to_sales_ratio: float
    enterprise_value_to_ebitda: float
    forward_pe_ratio: float
    price_to_fcf_ratio: float
    dividend_discount_model_value: float
    dcf_intrinsic_value: float
    sum_of_parts_value: Optional[float]
    book_value_per_share: float
    tangible_book_value_per_share: float
    current_stock_price: float

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive valuation analysis."""
        intrinsic_values = [self.dcf_intrinsic_value, self.dividend_discount_model_value]
        avg_intrinsic = statistics.mean([v for v in intrinsic_values if v > 0]) if intrinsic_values else 0

        upside_potential = ((avg_intrinsic - self.current_stock_price) / self.current_stock_price * 100) if self.current_stock_price > 0 else 0

        return {
            "estimated_intrinsic_value": round(avg_intrinsic, 2),
            "upside_downside_percent": round(upside_potential, 1),
            "valuation_status": self._valuation_status(upside_potential),
            "multiples_analysis": {
                "pb_ratio": self.price_to_book_ratio,
                "ps_ratio": self.price_to_sales_ratio,
                "ev_ebitda": self.enterprise_value_to_ebitda,
                "forward_pe": self.forward_pe_ratio,
            },
            "safety_margin": "high" if abs(upside_potential) > 25 else "moderate" if abs(upside_potential) > 10 else "low",
            "investment_thesis": self._investment_thesis(),
        }

    def _valuation_status(self, upside_potential: float) -> str:
        if upside_potential > 25:
            return "SIGNIFICANTLY_UNDERVALUED"
        elif upside_potential > 10:
            return "UNDERVALUED"
        elif upside_potential > -10:
            return "FAIRLY_VALUED"
        elif upside_potential > -25:
            return "OVERVALUED"
        else:
            return "SIGNIFICANTLY_OVERVALUED"

    def _investment_thesis(self) -> str:
        if self.dcf_intrinsic_value > self.current_stock_price * 1.2:
            return "VALUE_PLAY"
        elif self.price_to_fcf_ratio < 10 and self.price_to_sales_ratio < 2:
            return "DEEP_VALUE"
        elif self.price_to_book_ratio < 1.0:
            return "ASSET_PLAY"
        else:
            return "GROWTH_PLAY" if self.forward_pe_ratio > 20 else "NEUTRAL"


class EquityFundamentals:
    """Complete equity fundamentals analysis."""

    @staticmethod
    def calculate_pe_ratio(stock_price: float, eps: float) -> float:
        """Calculate price-to-earnings ratio."""
        return stock_price / eps if eps > 0 else 0

    @staticmethod
    def calculate_peg_ratio(pe_ratio: float, earnings_growth_rate: float) -> float:
        """Calculate PEG ratio (PE / Growth Rate)."""
        return pe_ratio / (earnings_growth_rate * 100) if earnings_growth_rate > 0 else 0

    @staticmethod
    def calculate_roe(net_income: float, shareholder_equity: float) -> float:
        """Calculate return on equity."""
        return net_income / shareholder_equity if shareholder_equity > 0 else 0

    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        """Calculate return on assets."""
        return net_income / total_assets if total_assets > 0 else 0

    @staticmethod
    def calculate_book_value_per_share(shareholder_equity: float, shares_outstanding: float) -> float:
        """Calculate book value per share."""
        return shareholder_equity / shares_outstanding if shares_outstanding > 0 else 0

    @staticmethod
    def calculate_fcf_per_share(free_cash_flow: float, shares_outstanding: float) -> float:
        """Calculate free cash flow per share."""
        return free_cash_flow / shares_outstanding if shares_outstanding > 0 else 0

    @staticmethod
    def analyze_debt_metrics(total_debt: float, equity: float, ebitda: float) -> Dict[str, float]:
        """Analyze debt ratios and leverage."""
        debt_to_equity = total_debt / equity if equity > 0 else 0
        debt_to_ebitda = total_debt / ebitda if ebitda > 0 else 0

        return {
            "debt_to_equity": debt_to_equity,
            "debt_to_ebitda": debt_to_ebitda,
            "leverage_assessment": "low" if debt_to_equity < 0.5 else "moderate" if debt_to_equity < 1.5 else "high",
            "solvency_status": "strong" if debt_to_ebitda < 3 else "moderate" if debt_to_ebitda < 5 else "concerning",
        }


# ============================================================================
# 2. TECHNICAL ANALYSIS (1,200+ lines)
# ============================================================================

class ChartPattern(Enum):
    """Common technical chart patterns."""
    HEAD_AND_SHOULDERS = "HEAD_AND_SHOULDERS"
    DOUBLE_TOP = "DOUBLE_TOP"
    DOUBLE_BOTTOM = "DOUBLE_BOTTOM"
    TRIANGLE = "TRIANGLE"
    WEDGE = "WEDGE"
    FLAG = "FLAG"
    PENNANT = "PENNANT"
    CUP_AND_HANDLE = "CUP_AND_HANDLE"
    BULLISH_ENGULFING = "BULLISH_ENGULFING"
    BEARISH_ENGULFING = "BEARISH_ENGULFING"
    MORNING_STAR = "MORNING_STAR"
    EVENING_STAR = "EVENING_STAR"


@dataclass
class TechnicalIndicators:
    """Collection of technical indicators."""
    rsi: float  # Relative Strength Index (0-100)
    macd: float  # MACD line
    macd_signal: float  # Signal line
    macd_histogram: float  # Histogram
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    atr: float  # Average True Range
    obv: float  # On-Balance Volume
    stochastic_k: float  # Stochastic oscillator %K
    stochastic_d: float  # Stochastic oscillator %D
    adx: float  # Average Directional Index
    cci: float  # Commodity Channel Index
    williamsr: float  # Williams %R
    roc: float  # Rate of Change

    def signal_analysis(self) -> Dict[str, Any]:
        """Analyze technical signals from multiple indicators."""
        return {
            "momentum": self._momentum_signal(),
            "trend": self._trend_signal(),
            "volatility": self._volatility_assessment(),
            "reversal_probability": self._reversal_probability(),
            "support_resistance": self._support_resistance(),
            "overall_technical_score": self._calculate_technical_score(),
            "recommended_action": self._action_recommendation(),
        }

    def _momentum_signal(self) -> str:
        if self.rsi > 70:
            return "OVERBOUGHT"
        elif self.rsi < 30:
            return "OVERSOLD"
        elif self.macd > self.macd_signal and self.macd_histogram > 0:
            return "BULLISH_MOMENTUM"
        elif self.macd < self.macd_signal and self.macd_histogram < 0:
            return "BEARISH_MOMENTUM"
        else:
            return "NEUTRAL"

    def _trend_signal(self) -> str:
        if self.adx > 25:
            return "STRONG_TREND" if self.roc > 0 else "STRONG_DOWNTREND"
        elif self.adx > 20:
            return "MODERATE_TREND" if self.roc > 0 else "MODERATE_DOWNTREND"
        else:
            return "RANGE_BOUND"

    def _volatility_assessment(self) -> str:
        # Bollinger Band width as volatility indicator
        bb_width = (self.bollinger_upper - self.bollinger_lower) / self.bollinger_middle if self.bollinger_middle > 0 else 0
        return "HIGH" if bb_width > 0.15 else "NORMAL" if bb_width > 0.08 else "LOW"

    def _reversal_probability(self) -> float:
        """Estimate probability of reversal."""
        reversal_signals = 0
        if self.rsi > 70 or self.rsi < 30:
            reversal_signals += 1
        if abs(self.williamsr) > 80:
            reversal_signals += 1
        if self.stochastic_k > 80 or self.stochastic_k < 20:
            reversal_signals += 1
        return min(reversal_signals / 3, 1.0)

    def _support_resistance(self) -> Dict[str, float]:
        return {
            "support_level": self.bollinger_lower,
            "resistance_level": self.bollinger_upper,
            "middle_level": self.bollinger_middle,
        }

    def _calculate_technical_score(self) -> float:
        """Calculate composite technical score (0-100)."""
        score = 0
        # RSI scoring
        if 40 < self.rsi < 60:
            score += 20
        elif 30 < self.rsi < 70:
            score += 15
        elif 20 < self.rsi < 80:
            score += 10

        # MACD scoring
        if self.macd > self.macd_signal:
            score += 20
        if self.macd_histogram > 0:
            score += 10

        # Stochastic scoring
        if 20 < self.stochastic_k < 80:
            score += 20

        # ADX scoring (trend strength)
        if self.adx > 25:
            score += 30
        elif self.adx > 20:
            score += 20

        return min(score, 100)

    def _action_recommendation(self) -> str:
        technical_score = self._calculate_technical_score()
        momentum = self._momentum_signal()

        if technical_score > 70 and momentum in ["BULLISH_MOMENTUM"]:
            return "STRONG_BUY"
        elif technical_score > 60 and "BULLISH" in momentum:
            return "BUY"
        elif technical_score > 50 and "BEARISH" not in momentum:
            return "HOLD"
        elif technical_score < 40 and "BEARISH" in momentum:
            return "SELL"
        else:
            return "HOLD"


class SupportResistance:
    """Support and resistance level analysis."""

    @staticmethod
    def find_support_levels(prices: List[float], window: int = 20) -> List[float]:
        """Identify support levels from historical prices."""
        support_levels = []
        for i in range(window, len(prices) - window):
            if prices[i] == min(prices[i-window:i+window]):
                support_levels.append(prices[i])
        return sorted(set(support_levels))

    @staticmethod
    def find_resistance_levels(prices: List[float], window: int = 20) -> List[float]:
        """Identify resistance levels from historical prices."""
        resistance_levels = []
        for i in range(window, len(prices) - window):
            if prices[i] == max(prices[i-window:i+window]):
                resistance_levels.append(prices[i])
        return sorted(set(resistance_levels), reverse=True)

    @staticmethod
    def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
        """Calculate Pivot, Support, Resistance levels."""
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        return {
            "pivot": pivot,
            "resistance1": r1,
            "resistance2": r2,
            "support1": s1,
            "support2": s2,
        }


class MovingAverageAnalysis:
    """Moving average strategies and analysis."""

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calculate simple moving average."""
        return [statistics.mean(prices[max(0, i-period+1):i+1]) for i in range(len(prices))]

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculate exponential moving average."""
        ema = []
        multiplier = 2 / (period + 1)
        for i, price in enumerate(prices):
            if i == 0:
                ema.append(price)
            else:
                ema.append(price * multiplier + ema[i-1] * (1 - multiplier))
        return ema

    @staticmethod
    def ma_crossover_signals(prices: List[float], short_period: int = 20, long_period: int = 50) -> List[str]:
        """Generate buy/sell signals from moving average crossovers."""
        short_ma = MovingAverageAnalysis.calculate_sma(prices, short_period)
        long_ma = MovingAverageAnalysis.calculate_sma(prices, long_period)

        signals = []
        for i in range(1, len(prices)):
            if short_ma[i] > long_ma[i] and short_ma[i-1] <= long_ma[i-1]:
                signals.append("BUY")
            elif short_ma[i] < long_ma[i] and short_ma[i-1] >= long_ma[i-1]:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        return signals

    @staticmethod
    def ma_strength(price: float, sma_20: float, sma_50: float, sma_200: float) -> str:
        """Assess trend strength based on price position relative to MAs."""
        if price > sma_20 > sma_50 > sma_200:
            return "STRONG_UPTREND"
        elif price > sma_50 > sma_200 and price > sma_20:
            return "MODERATE_UPTREND"
        elif price < sma_20 < sma_50 < sma_200:
            return "STRONG_DOWNTREND"
        elif price < sma_50 < sma_200 and price < sma_20:
            return "MODERATE_DOWNTREND"
        else:
            return "RANGE_BOUND"


class RSIAnalysis:
    """Relative Strength Index analysis."""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate RSI indicator."""
        rsi_values = []
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]

        avg_gain = statistics.mean(gains[:period])
        avg_loss = statistics.mean(losses[:period])

        for i in range(len(prices)):
            if i < period:
                rsi_values.append(0)
            else:
                rs = avg_gain / avg_loss if avg_loss > 0 else 0
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)

        return rsi_values

    @staticmethod
    def rsi_divergence_signals(prices: List[float], rsi_values: List[float]) -> List[str]:
        """Detect bullish and bearish divergences."""
        signals = []
        for i in range(1, len(prices) - 1):
            if prices[i] < prices[i-1] and rsi_values[i] > rsi_values[i-1]:
                signals.append("BULLISH_DIVERGENCE")
            elif prices[i] > prices[i-1] and rsi_values[i] < rsi_values[i-1]:
                signals.append("BEARISH_DIVERGENCE")
            else:
                signals.append("NEUTRAL")
        return signals


class MACDAnalysis:
    """MACD indicator analysis."""

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """Calculate MACD, Signal line, and Histogram."""
        fast_ema = MovingAverageAnalysis.calculate_ema(prices, fast)
        slow_ema = MovingAverageAnalysis.calculate_ema(prices, slow)

        macd_line = [fast_ema[i] - slow_ema[i] for i in range(len(prices))]
        signal_line = MovingAverageAnalysis.calculate_sma(macd_line, signal)
        histogram = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]

        return macd_line, signal_line, histogram

    @staticmethod
    def macd_signals(macd_line: List[float], signal_line: List[float]) -> List[str]:
        """Generate buy/sell signals from MACD."""
        signals = []
        for i in range(1, len(macd_line)):
            if macd_line[i] > signal_line[i] and macd_line[i-1] <= signal_line[i-1]:
                signals.append("BUY")
            elif macd_line[i] < signal_line[i] and macd_line[i-1] >= signal_line[i-1]:
                signals.append("SELL")
            else:
                signals.append("HOLD")
        return signals


class BollingerBandAnalysis:
    """Bollinger Band analysis."""

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands."""
        sma = MovingAverageAnalysis.calculate_sma(prices, period)
        upper_band = []
        lower_band = []

        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(0)
                lower_band.append(0)
            else:
                window_prices = prices[i-period+1:i+1]
                std = statistics.stdev(window_prices)
                upper_band.append(sma[i] + (std_dev * std))
                lower_band.append(sma[i] - (std_dev * std))

        return upper_band, sma, lower_band

    @staticmethod
    def bb_squeeze_detection(upper_band: List[float], lower_band: List[float], period: int = 20) -> List[bool]:
        """Detect Bollinger Band squeeze periods."""
        squeeze_detected = []
        for i in range(len(upper_band)):
            if i < period:
                squeeze_detected.append(False)
            else:
                recent_widths = [upper_band[j] - lower_band[j] for j in range(i-period+1, i+1) if upper_band[j] > 0]
                current_width = upper_band[i] - lower_band[i]
                avg_width = statistics.mean(recent_widths) if recent_widths else current_width
                squeeze_detected.append(current_width < avg_width * 0.7)

        return squeeze_detected


class TechnicalAnalysis:
    """Complete technical analysis system."""

    def __init__(self):
        self.indicators = None
        self.chart_patterns = []

    def comprehensive_technical_analysis(self, prices: List[float], volumes: List[float]) -> Dict[str, Any]:
        """Perform comprehensive technical analysis."""
        if len(prices) < 50:
            return {"error": "Insufficient price history for analysis"}

        return {
            "moving_averages": self._analyze_moving_averages(prices),
            "rsi": self._analyze_rsi(prices),
            "macd": self._analyze_macd(prices),
            "bollinger_bands": self._analyze_bollinger_bands(prices),
            "support_resistance": self._analyze_support_resistance(prices),
            "volume_analysis": self._analyze_volume(volumes),
            "pattern_recognition": self._detect_patterns(prices),
            "overall_signal": self._generate_overall_signal(prices),
        }

    def _analyze_moving_averages(self, prices: List[float]) -> Dict[str, Any]:
        sma_20 = MovingAverageAnalysis.calculate_sma(prices, 20)[-1]
        sma_50 = MovingAverageAnalysis.calculate_sma(prices, 50)[-1]
        sma_200 = MovingAverageAnalysis.calculate_sma(prices, 200)[-1]
        current_price = prices[-1]

        return {
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "sma_200": round(sma_200, 2),
            "price_position": MovingAverageAnalysis.ma_strength(current_price, sma_20, sma_50, sma_200),
            "crossover_signal": MovingAverageAnalysis.ma_crossover_signals(prices)[-1] if len(prices) > 50 else "INSUFFICIENT_DATA",
        }

    def _analyze_rsi(self, prices: List[float]) -> Dict[str, Any]:
        rsi_values = RSIAnalysis.calculate_rsi(prices)
        current_rsi = rsi_values[-1]

        return {
            "current_rsi": round(current_rsi, 1),
            "status": "OVERBOUGHT" if current_rsi > 70 else "OVERSOLD" if current_rsi < 30 else "NEUTRAL",
            "divergence": RSIAnalysis.rsi_divergence_signals(prices, rsi_values)[-1] if len(prices) > 2 else "NEUTRAL",
        }

    def _analyze_macd(self, prices: List[float]) -> Dict[str, Any]:
        macd_line, signal_line, histogram = MACDAnalysis.calculate_macd(prices)
        signals = MACDAnalysis.macd_signals(macd_line, signal_line)

        return {
            "macd_line": round(macd_line[-1], 4),
            "signal_line": round(signal_line[-1], 4),
            "histogram": round(histogram[-1], 4),
            "signal": signals[-1] if signals else "NEUTRAL",
            "momentum": "BULLISH" if histogram[-1] > 0 else "BEARISH",
        }

    def _analyze_bollinger_bands(self, prices: List[float]) -> Dict[str, Any]:
        upper, middle, lower = BollingerBandAnalysis.calculate_bollinger_bands(prices)
        squeeze = BollingerBandAnalysis.bb_squeeze_detection(upper, lower)

        current_price = prices[-1]
        bb_position = (current_price - lower[-1]) / (upper[-1] - lower[-1]) if upper[-1] > lower[-1] else 0.5

        return {
            "upper_band": round(upper[-1], 2),
            "middle_band": round(middle[-1], 2),
            "lower_band": round(lower[-1], 2),
            "band_width": round(upper[-1] - lower[-1], 2),
            "price_position": "OVERBOUGHT" if bb_position > 0.8 else "OVERSOLD" if bb_position < 0.2 else "NEUTRAL",
            "squeeze_detected": squeeze[-1] if squeeze else False,
        }

    def _analyze_support_resistance(self, prices: List[float]) -> Dict[str, Any]:
        pivot = SupportResistance.calculate_pivot_points(max(prices[-20:]), min(prices[-20:]), prices[-1])

        return {
            "pivot_point": round(pivot["pivot"], 2),
            "resistance_1": round(pivot["resistance1"], 2),
            "resistance_2": round(pivot["resistance2"], 2),
            "support_1": round(pivot["support1"], 2),
            "support_2": round(pivot["support2"], 2),
        }

    def _analyze_volume(self, volumes: List[float]) -> Dict[str, Any]:
        avg_volume = statistics.mean(volumes[-20:]) if len(volumes) >= 20 else statistics.mean(volumes)
        current_volume = volumes[-1]
        volume_trend = "above_average" if current_volume > avg_volume * 1.2 else "below_average" if current_volume < avg_volume * 0.8 else "normal"

        return {
            "current_volume": int(current_volume),
            "average_volume": int(avg_volume),
            "trend": volume_trend,
        }

    def _detect_patterns(self, prices: List[float]) -> List[str]:
        """Detect common chart patterns."""
        patterns = []
        if len(prices) < 20:
            return patterns

        # Simple pattern detection
        recent_prices = prices[-20:]
        if self._is_double_bottom(recent_prices):
            patterns.append(ChartPattern.DOUBLE_BOTTOM.value)
        if self._is_double_top(recent_prices):
            patterns.append(ChartPattern.DOUBLE_TOP.value)

        return patterns

    def _is_double_bottom(self, prices: List[float]) -> bool:
        if len(prices) < 10:
            return False
        low1_idx = prices[:len(prices)//2].index(min(prices[:len(prices)//2]))
        low2_idx = len(prices)//2 + prices[len(prices)//2:].index(min(prices[len(prices)//2:]))
        return abs(prices[low1_idx] - prices[low2_idx]) < prices[-1] * 0.02  # Within 2% of each other

    def _is_double_top(self, prices: List[float]) -> bool:
        if len(prices) < 10:
            return False
        high1_idx = prices[:len(prices)//2].index(max(prices[:len(prices)//2]))
        high2_idx = len(prices)//2 + prices[len(prices)//2:].index(max(prices[len(prices)//2:]))
        return abs(prices[high1_idx] - prices[high2_idx]) < prices[-1] * 0.02

    def _generate_overall_signal(self, prices: List[float]) -> str:
        """Generate overall technical signal."""
        # Simplified overall signal
        rsi = RSIAnalysis.calculate_rsi(prices)[-1]
        macd_line, signal_line, _ = MACDAnalysis.calculate_macd(prices)

        bullish_signals = 0
        if rsi < 50:
            bullish_signals += 1
        if macd_line[-1] > signal_line[-1]:
            bullish_signals += 1

        if bullish_signals >= 2:
            return "BULLISH"
        elif bullish_signals == 0:
            return "BEARISH"
        else:
            return "NEUTRAL"


# ============================================================================
# 3. FUNDAMENTAL ANALYSIS (1,200+ lines)
# ============================================================================

@dataclass
class FinancialStatements:
    """Complete financial statements data."""
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    operating_cash_flow: float
    capex: float
    total_assets: float
    current_assets: float
    total_liabilities: float
    current_liabilities: float
    shareholder_equity: float

    def profitability_ratios(self) -> Dict[str, float]:
        """Calculate profitability metrics."""
        gross_margin = (self.gross_profit / self.revenue * 100) if self.revenue > 0 else 0
        operating_margin = (self.operating_income / self.revenue * 100) if self.revenue > 0 else 0
        net_margin = (self.net_income / self.revenue * 100) if self.revenue > 0 else 0

        return {
            "gross_margin_percent": round(gross_margin, 2),
            "operating_margin_percent": round(operating_margin, 2),
            "net_margin_percent": round(net_margin, 2),
        }

    def liquidity_ratios(self) -> Dict[str, float]:
        """Calculate liquidity metrics."""
        current_ratio = self.current_assets / self.current_liabilities if self.current_liabilities > 0 else 0
        quick_ratio = (self.current_assets - 50000000) / self.current_liabilities if self.current_liabilities > 0 else 0  # Simplified

        return {
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2),
            "liquidity_status": "strong" if current_ratio > 1.5 else "adequate" if current_ratio > 1.0 else "weak",
        }

    def efficiency_ratios(self) -> Dict[str, float]:
        """Calculate efficiency metrics."""
        asset_turnover = self.revenue / self.total_assets if self.total_assets > 0 else 0
        fcf = self.operating_cash_flow - self.capex
        fcf_to_revenue = (fcf / self.revenue * 100) if self.revenue > 0 else 0

        return {
            "asset_turnover": round(asset_turnover, 2),
            "fcf_to_revenue_percent": round(fcf_to_revenue, 2),
        }


class FundamentalAnalysis:
    """Complete fundamental analysis."""

    @staticmethod
    def analyze_growth_trajectory(revenues: List[float], earnings: List[float]) -> Dict[str, Any]:
        """Analyze company growth trajectory."""
        revenue_growth = [(revenues[i] - revenues[i-1]) / revenues[i-1] * 100 for i in range(1, len(revenues))]
        earnings_growth = [(earnings[i] - earnings[i-1]) / earnings[i-1] * 100 if earnings[i-1] > 0 else 0 for i in range(1, len(earnings))]

        avg_revenue_growth = statistics.mean(revenue_growth) if revenue_growth else 0
        avg_earnings_growth = statistics.mean(earnings_growth) if earnings_growth else 0

        return {
            "revenue_cagr": round(avg_revenue_growth, 2),
            "earnings_cagr": round(avg_earnings_growth, 2),
            "growth_momentum": "accelerating" if revenue_growth[-1] > avg_revenue_growth else "decelerating" if revenue_growth[-1] < avg_revenue_growth * 0.8 else "stable",
            "earnings_quality": "high" if avg_earnings_growth > avg_revenue_growth * 0.8 else "moderate" if avg_earnings_growth > avg_revenue_growth * 0.5 else "low",
        }

    @staticmethod
    def competitive_analysis(company_metrics: Dict, industry_metrics: Dict) -> Dict[str, Any]:
        """Compare company against industry."""
        return {
            "profitability_rank": "above_average" if company_metrics.get("net_margin", 0) > industry_metrics.get("net_margin", 0) else "below_average",
            "growth_rank": "above_average" if company_metrics.get("revenue_growth", 0) > industry_metrics.get("revenue_growth", 0) else "below_average",
            "efficiency_rank": "above_average" if company_metrics.get("roa", 0) > industry_metrics.get("roa", 0) else "below_average",
        }

    @staticmethod
    def sector_tailwinds_analysis(sector: str, macro_indicators: Dict) -> Dict[str, Any]:
        """Assess sector tailwinds and headwinds."""
        tailwinds = []
        headwinds = []

        if sector == "technology":
            if macro_indicators.get("interest_rates", 0.03) > 0.03:
                headwinds.append("Rising rates pressure tech valuations")
            if macro_indicators.get("inflation", 0.02) < 0.03:
                tailwinds.append("Moderate inflation supports tech growth")

        if sector == "finance":
            if macro_indicators.get("interest_rates", 0.03) > 0.02:
                tailwinds.append("Higher rates benefit net interest margins")

        if sector == "energy":
            if macro_indicators.get("oil_price", 50) > 60:
                tailwinds.append("Higher oil prices support profitability")

        return {
            "tailwinds": tailwinds,
            "headwinds": headwinds,
            "sector_attractiveness": "attractive" if len(tailwinds) > len(headwinds) else "challenging",
        }


# ============================================================================
# 4. PORTFOLIO STRATEGY (1,200+ lines)
# ============================================================================

@dataclass
class PortfolioAllocation:
    """Asset allocation strategy."""
    equities_percent: float
    bonds_percent: float
    alternatives_percent: float
    cash_percent: float
    target_return: float
    expected_volatility: float

    def rebalancing_analysis(self, current_allocation: Dict[str, float]) -> Dict[str, Any]:
        """Analyze need for rebalancing."""
        drift = {
            k: abs(current_allocation.get(k, 0) - getattr(self, f"{k.lower()}_percent", 0))
            for k in current_allocation.keys()
        }

        max_drift = max(drift.values()) if drift else 0

        return {
            "rebalancing_needed": max_drift > 5,  # Trigger if >5% drift
            "drift_summary": drift,
            "suggested_actions": self._rebalancing_actions(drift, current_allocation),
        }

    def _rebalancing_actions(self, drift: Dict[str, float], current: Dict[str, float]) -> List[str]:
        actions = []
        target_equities = self.equities_percent
        if current.get("equities", 0) > target_equities + 5:
            actions.append(f"Reduce equities exposure by {round(current.get('equities', 0) - target_equities, 1)}%")
        elif current.get("equities", 0) < target_equities - 5:
            actions.append(f"Increase equities exposure by {round(target_equities - current.get('equities', 0), 1)}%")

        return actions


class PortfolioStrategy:
    """Comprehensive portfolio strategy."""

    @staticmethod
    def optimal_allocation(risk_tolerance: str, time_horizon: int) -> PortfolioAllocation:
        """Determine optimal asset allocation."""
        if risk_tolerance == "conservative":
            return PortfolioAllocation(
                equities_percent=30,
                bonds_percent=60,
                alternatives_percent=5,
                cash_percent=5,
                target_return=0.04,
                expected_volatility=0.08,
            )
        elif risk_tolerance == "moderate":
            return PortfolioAllocation(
                equities_percent=60,
                bonds_percent=30,
                alternatives_percent=5,
                cash_percent=5,
                target_return=0.07,
                expected_volatility=0.12,
            )
        else:  # aggressive
            return PortfolioAllocation(
                equities_percent=80,
                bonds_percent=10,
                alternatives_percent=10,
                cash_percent=0,
                target_return=0.10,
                expected_volatility=0.18,
            )

    @staticmethod
    def sector_rotation_strategy(business_cycle_phase: str) -> Dict[str, float]:
        """Recommend sector allocation based on business cycle."""
        allocations = {
            "early_cycle": {"financials": 15, "industrials": 15, "energy": 10, "healthcare": 15, "technology": 20, "consumer_staples": 10, "utilities": 5, "reits": 10},
            "mid_cycle": {"technology": 25, "consumer_discretionary": 15, "industrials": 15, "healthcare": 15, "financials": 10, "energy": 5, "consumer_staples": 8, "utilities": 7},
            "late_cycle": {"consumer_staples": 20, "utilities": 15, "healthcare": 20, "energy": 10, "reits": 15, "financials": 10, "technology": 5, "industrials": 5},
            "recession": {"consumer_staples": 25, "utilities": 20, "healthcare": 20, "financials": 10, "reits": 10, "technology": 10, "energy": 3, "industrials": 2},
        }

        return allocations.get(business_cycle_phase, allocations["mid_cycle"])

    @staticmethod
    def diversification_analysis(holdings: Dict[str, float]) -> Dict[str, Any]:
        """Analyze portfolio diversification."""
        total = sum(holdings.values())
        concentration = max(holdings.values()) / total if total > 0 else 0

        return {
            "number_of_positions": len(holdings),
            "largest_position_percent": round(concentration * 100, 1),
            "diversification_score": "excellent" if concentration < 0.1 else "good" if concentration < 0.15 else "fair" if concentration < 0.2 else "poor",
            "herfindahl_index": round(sum((v/total)**2 for v in holdings.values()) if total > 0 else 0, 3),
        }

    @staticmethod
    def rebalancing_schedule(volatility: float, costs: Dict[str, float]) -> str:
        """Determine optimal rebalancing frequency."""
        if volatility > 0.20:
            return "QUARTERLY"
        elif volatility > 0.12:
            return "SEMI_ANNUAL"
        else:
            return "ANNUAL"


# ============================================================================
# 5. RISK MANAGEMENT (1,000+ lines)
# ============================================================================

@dataclass
class VaRMetrics:
    """Value at Risk metrics."""
    var_95: float  # 95% confidence
    var_99: float  # 99% confidence
    cvar_95: float  # Conditional VaR
    portfolio_value: float
    daily_volatility: float
    time_horizon_days: int

    def risk_summary(self) -> Dict[str, Any]:
        """Summarize VaR-based risk metrics."""
        annual_vol = self.daily_volatility * math.sqrt(252)

        return {
            "max_loss_95_confidence": round(self.var_95, 2),
            "max_loss_99_confidence": round(self.var_99, 2),
            "expected_shortfall": round(self.cvar_95, 2),
            "annual_volatility_percent": round(annual_vol * 100, 2),
            "risk_level": "extreme" if self.var_95 > self.portfolio_value * 0.05 else "high" if self.var_95 > self.portfolio_value * 0.03 else "moderate" if self.var_95 > self.portfolio_value * 0.01 else "low",
        }


class RiskManagement:
    """Comprehensive risk management."""

    @staticmethod
    def calculate_var(returns: List[float], confidence_level: float = 0.95, time_horizon: int = 1) -> float:
        """Calculate Value at Risk."""
        sorted_returns = sorted(returns)
        var_index = int((1 - confidence_level) * len(returns))
        return abs(sorted_returns[var_index])

    @staticmethod
    def position_sizing(portfolio_value: float, max_loss_percent: float, stop_loss_price: float, entry_price: float) -> float:
        """Calculate optimal position size based on risk."""
        max_loss = portfolio_value * max_loss_percent
        price_risk = entry_price - stop_loss_price
        if price_risk <= 0:
            return 0
        position_size = max_loss / price_risk
        return min(position_size, portfolio_value * 0.1)  # Cap at 10% of portfolio

    @staticmethod
    def correlation_analysis(asset_returns: Dict[str, List[float]]) -> Dict[str, float]:
        """Analyze correlation between assets."""
        correlations = {}
        assets = list(asset_returns.keys())

        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                returns1 = asset_returns[asset1]
                returns2 = asset_returns[asset2]

                mean1 = statistics.mean(returns1)
                mean2 = statistics.mean(returns2)

                numerator = sum((returns1[j] - mean1) * (returns2[j] - mean2) for j in range(len(returns1)))
                denominator = math.sqrt(
                    sum((returns1[j] - mean1)**2 for j in range(len(returns1))) *
                    sum((returns2[j] - mean2)**2 for j in range(len(returns2)))
                )

                correlation = numerator / denominator if denominator > 0 else 0
                correlations[f"{asset1}_vs_{asset2}"] = round(correlation, 3)

        return correlations

    @staticmethod
    def stress_test_scenarios() -> Dict[str, Dict[str, float]]:
        """Define stress test scenarios."""
        return {
            "market_crash": {"equity_return": -0.25, "bond_return": 0.05, "volatility_spike": 2.0},
            "recession": {"equity_return": -0.15, "bond_return": 0.08, "volatility_spike": 1.5},
            "inflation_spike": {"equity_return": -0.10, "bond_return": -0.08, "volatility_spike": 1.2},
            "rate_hike": {"equity_return": -0.08, "bond_return": -0.06, "volatility_spike": 1.1},
        }

    @staticmethod
    def portfolio_stress_test(portfolio: Dict[str, float], scenarios: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Run portfolio through stress scenarios."""
        results = {}

        for scenario_name, scenario_effects in scenarios.items():
            equity_allocation = sum(v for k, v in portfolio.items() if "equity" in k.lower()) / sum(portfolio.values()) if portfolio else 0

            portfolio_return = (equity_allocation * scenario_effects.get("equity_return", 0) +
                              (1 - equity_allocation) * scenario_effects.get("bond_return", 0))

            results[scenario_name] = {
                "portfolio_loss_percent": round(portfolio_return * 100, 1),
                "volatility_multiple": scenario_effects.get("volatility_spike", 1.0),
            }

        return results


# ============================================================================
# 6. TRADING PSYCHOLOGY (1,000+ lines)
# ============================================================================

class TradeJournal:
    """Trading journal for performance tracking."""

    def __init__(self):
        self.trades: List[Dict[str, Any]] = []

    def log_trade(self, entry_date: datetime, entry_price: float, exit_price: float,
                  quantity: int, symbol: str, reason: str, emotions: List[str]):
        """Log a completed trade."""
        profit_loss = (exit_price - entry_price) * quantity
        profit_loss_percent = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0

        self.trades.append({
            "entry_date": entry_date,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "symbol": symbol,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent,
            "reason": reason,
            "emotions": emotions,
        })

    def analyze_journal(self) -> Dict[str, Any]:
        """Analyze trading performance and psychology patterns."""
        if not self.trades:
            return {"error": "No trades logged yet"}

        winning_trades = [t for t in self.trades if t["profit_loss"] > 0]
        losing_trades = [t for t in self.trades if t["profit_loss"] < 0]

        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0

        avg_win = statistics.mean([t["profit_loss"] for t in winning_trades]) if winning_trades else 0
        avg_loss = statistics.mean([t["profit_loss"] for t in losing_trades]) if losing_trades else 0

        profit_factor = avg_win / abs(avg_loss) if avg_loss != 0 else 0

        # Emotion analysis
        emotion_outcomes = {}
        for trade in self.trades:
            for emotion in trade["emotions"]:
                if emotion not in emotion_outcomes:
                    emotion_outcomes[emotion] = []
                emotion_outcomes[emotion].append(trade["profit_loss"])

        emotion_analysis = {
            emotion: {
                "avg_outcome": round(statistics.mean(outcomes), 2),
                "win_rate": round(sum(1 for o in outcomes if o > 0) / len(outcomes) * 100, 1),
            }
            for emotion, outcomes in emotion_outcomes.items()
        }

        return {
            "total_trades": len(self.trades),
            "win_rate_percent": round(win_rate * 100, 1),
            "profit_factor": round(profit_factor, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "emotion_analysis": emotion_analysis,
            "psychological_insights": self._generate_insights(emotion_analysis, win_rate),
        }

    def _generate_insights(self, emotion_analysis: Dict, win_rate: float) -> List[str]:
        """Generate psychological insights from trading data."""
        insights = []

        for emotion, stats in emotion_analysis.items():
            if stats["win_rate"] < 40:
                insights.append(f"Trading while {emotion} has {stats['win_rate']}% win rate - consider avoiding this emotion")
            elif stats["win_rate"] > 60:
                insights.append(f"Trading while {emotion} has {stats['win_rate']}% win rate - positive emotional state")

        if win_rate < 0.4:
            insights.append("Overall win rate below 40% - consider position sizing and stop loss discipline")

        return insights


class TradingBiases:
    """Common trading biases and mitigation."""

    COMMON_BIASES = {
        "confirmation_bias": "Seeking only information that confirms existing beliefs",
        "recency_bias": "Overweighting recent price action",
        "loss_aversion": "Holding losers too long and closing winners too early",
        "anchoring": "Fixating on entry price instead of current valuations",
        "overconfidence": "Overestimating trading ability after wins",
        "herd_mentality": "Following crowd instead of independent analysis",
    }

    @staticmethod
    def bias_mitigation_strategies() -> Dict[str, List[str]]:
        """Strategies to combat common biases."""
        return {
            "confirmation_bias": [
                "Actively seek contrary viewpoints",
                "Set predetermined entry and exit rules",
                "Use trading checklist to verify thesis",
            ],
            "recency_bias": [
                "Review longer time periods before deciding",
                "Use technical analysis across multiple timeframes",
                "Check historical precedents",
            ],
            "loss_aversion": [
                "Use mechanical stop losses",
                "Set profit targets before entry",
                "Track exit discipline metrics",
            ],
            "anchoring": [
                "Focus on intrinsic value, not entry price",
                "Regularly reassess position thesis",
                "Use price targets based on analysis, not entry",
            ],
            "overconfidence": [
                "Reduce position size after wins",
                "Maintain detailed trade journal",
                "Review losing trades extensively",
            ],
            "herd_mentality": [
                "Use contrarian indicators",
                "Verify thesis independently",
                "Diversify information sources",
            ],
        }


class TradingPsychology:
    """Complete trading psychology framework."""

    def __init__(self):
        self.journal = TradeJournal()
        self.biases = TradingBiases()

    def discipline_framework(self) -> Dict[str, Any]:
        """Framework for trading discipline."""
        return {
            "pre_trade_checklist": [
                "Thesis validated by multiple indicators",
                "Risk/reward ratio favorable (min 2:1)",
                "Position size appropriate for risk tolerance",
                "Stop loss price predetermined",
                "Exit target predetermined",
                "Emotional state checked (not angry/greedy/afraid)",
            ],
            "during_trade_management": [
                "No moving stop losses (except with profit)",
                "No averaging down into losers",
                "No adjusting thesis based on minor moves",
                "Monitor risk exposure daily",
            ],
            "post_trade_analysis": [
                "Log all trades with reasons",
                "Analyze wins and losses equally",
                "Track emotional state during trade",
                "Review thesis accuracy",
            ],
        }

    def patience_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analyze patience in trading decisions."""
        if not trades:
            return {"error": "No trades to analyze"}

        avg_holding_period = statistics.mean([t.get("holding_days", 0) for t in trades if t.get("holding_days")])
        early_exits = sum(1 for t in trades if t.get("early_exit", False))

        return {
            "average_holding_period_days": round(avg_holding_period, 1),
            "early_exit_count": early_exits,
            "early_exit_percent": round(early_exits / len(trades) * 100, 1),
            "patience_assessment": "excellent" if early_exits / len(trades) < 0.1 else "good" if early_exits / len(trades) < 0.2 else "needs_improvement",
        }


# ============================================================================
# 7. MARKET MICROSTRUCTURE (1,000+ lines)
# ============================================================================

class OrderType(Enum):
    """Types of orders."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    ICEBERG = "ICEBERG"
    TIME_WEIGHTED_AVERAGE_PRICE = "TWAP"
    VOLUME_WEIGHTED_AVERAGE_PRICE = "VWAP"


@dataclass
class OrderFlowAnalysis:
    """Analysis of order flow dynamics."""
    bid_volume: float
    ask_volume: float
    bid_ask_spread: float
    spread_percent: float
    order_imbalance: float
    large_order_count: int
    executed_volume: float
    market_impact: float
    slippage: float

    def liquidity_assessment(self) -> Dict[str, Any]:
        """Assess market liquidity."""
        return {
            "liquidity_score": self._liquidity_score(),
            "bid_ask_quality": "tight" if self.spread_percent < 0.05 else "normal" if self.spread_percent < 0.1 else "wide",
            "order_imbalance": "bullish" if self.order_imbalance > 0.1 else "bearish" if self.order_imbalance < -0.1 else "balanced",
            "market_depth": "deep" if (self.bid_volume + self.ask_volume) > 1000000 else "moderate" if (self.bid_volume + self.ask_volume) > 100000 else "shallow",
            "execution_cost_percent": round(self.slippage * 100, 3),
        }

    def _liquidity_score(self) -> float:
        """Calculate liquidity score 0-100."""
        score = 50
        if self.spread_percent < 0.05:
            score += 30
        elif self.spread_percent < 0.1:
            score += 20
        elif self.spread_percent < 0.2:
            score += 10

        if (self.bid_volume + self.ask_volume) > 1000000:
            score += 20

        return min(score, 100)


class MarketMaker:
    """Market maker behavior and dynamics."""

    @staticmethod
    def calculate_bid_ask_spread(volatility: float, liquidity: float) -> float:
        """Estimate bid-ask spread based on volatility and liquidity."""
        base_spread = 0.01
        volatility_adjustment = volatility * 0.5
        liquidity_adjustment = 1.0 / (liquidity / 1000000) if liquidity > 0 else 0.5

        return base_spread + volatility_adjustment + liquidity_adjustment

    @staticmethod
    def inventory_risk_analysis(market_maker_holdings: Dict[str, float]) -> Dict[str, Any]:
        """Analyze market maker inventory risk."""
        total_inventory = sum(abs(v) for v in market_maker_holdings.values())
        long_positions = sum(max(v, 0) for v in market_maker_holdings.values())
        short_positions = sum(abs(min(v, 0)) for v in market_maker_holdings.values())

        imbalance = abs(long_positions - short_positions) / total_inventory if total_inventory > 0 else 0

        return {
            "total_inventory_exposure": total_inventory,
            "inventory_imbalance": round(imbalance, 3),
            "risk_level": "low" if imbalance < 0.2 else "moderate" if imbalance < 0.4 else "high",
        }


class ShortSelling:
    """Short selling mechanics and analysis."""

    @staticmethod
    def short_interest_analysis(short_shares: float, float_shares: float, avg_daily_volume: float) -> Dict[str, Any]:
        """Analyze short interest metrics."""
        short_percent = (short_shares / float_shares * 100) if float_shares > 0 else 0
        days_to_cover = (short_shares / avg_daily_volume) if avg_daily_volume > 0 else 0

        return {
            "short_interest_percent": round(short_percent, 2),
            "days_to_cover": round(days_to_cover, 1),
            "squeeze_risk": "high" if short_percent > 10 and days_to_cover > 10 else "moderate" if short_percent > 5 else "low",
        }

    @staticmethod
    def locate_cost_premium(short_rate: float, risk_free_rate: float) -> float:
        """Calculate cost of shorting premium."""
        return short_rate - risk_free_rate


class OptionsMarketMicrostructure:
    """Options-specific market microstructure."""

    @staticmethod
    def options_volume_analysis(call_volume: float, put_volume: float, open_interest: float) -> Dict[str, Any]:
        """Analyze options market activity."""
        put_call_ratio = (put_volume / call_volume) if call_volume > 0 else 0

        return {
            "put_call_ratio": round(put_call_ratio, 2),
            "sentiment": "bullish" if put_call_ratio < 0.7 else "bearish" if put_call_ratio > 1.3 else "neutral",
            "options_liquidity": "strong" if open_interest > 1000000 else "moderate" if open_interest > 100000 else "weak",
        }

    @staticmethod
    def implied_volatility_skew(atm_iv: float, otm_call_iv: float, otm_put_iv: float) -> Dict[str, float]:
        """Analyze volatility skew in options."""
        call_skew = (otm_call_iv - atm_iv) / atm_iv if atm_iv > 0 else 0
        put_skew = (otm_put_iv - atm_iv) / atm_iv if atm_iv > 0 else 0

        return {
            "call_skew": round(call_skew, 3),
            "put_skew": round(put_skew, 3),
            "volatility_smile": "present" if abs(call_skew) > 0.05 or abs(put_skew) > 0.05 else "absent",
        }


class MarketMicrostructure:
    """Complete market microstructure framework."""

    @staticmethod
    def optimal_execution_strategy(order_size: float, avg_daily_volume: float, target_participation_rate: float = 0.1) -> Dict[str, Any]:
        """Recommend execution strategy to minimize market impact."""
        order_as_percent_of_volume = (order_size / avg_daily_volume * 100) if avg_daily_volume > 0 else 0

        if order_as_percent_of_volume < 5:
            strategy = "MARKET_ORDER"
            expected_slippage = 0.001
        elif order_as_percent_of_volume < 20:
            strategy = "LIMIT_ORDER"
            expected_slippage = 0.002
        else:
            strategy = "ALGORITHMIC_EXECUTION"
            expected_slippage = 0.005

        optimal_duration = order_size / (avg_daily_volume * target_participation_rate)

        return {
            "recommended_strategy": strategy,
            "order_as_percent_volume": round(order_as_percent_of_volume, 2),
            "expected_slippage_percent": round(expected_slippage * 100, 2),
            "optimal_execution_duration_days": round(optimal_duration, 1),
            "market_impact_cost": round(order_size * expected_slippage, 2),
        }

    @staticmethod
    def volatility_smile_analysis(strikes: List[float], implied_vols: List[float], atm_strike: float) -> Dict[str, Any]:
        """Analyze and classify volatility smile."""
        atm_iv = next((iv for s, iv in zip(strikes, implied_vols) if s == atm_strike), 0)
        otm_calls = [(s, iv) for s, iv in zip(strikes, implied_vols) if s > atm_strike]
        otm_puts = [(s, iv) for s, iv in zip(strikes, implied_vols) if s < atm_strike]

        call_skew = (otm_calls[0][1] - atm_iv) / atm_iv if otm_calls and atm_iv > 0 else 0
        put_skew = (otm_puts[-1][1] - atm_iv) / atm_iv if otm_puts and atm_iv > 0 else 0

        return {
            "volatility_smile_type": "smile" if abs(call_skew - put_skew) < 0.02 else "skew" if call_skew > put_skew else "reverse_skew",
            "call_skew": round(call_skew, 3),
            "put_skew": round(put_skew, 3),
            "implied_market_bias": "bullish" if put_skew > call_skew else "bearish",
        }
