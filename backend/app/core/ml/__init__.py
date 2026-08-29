"""ML Engine — Production-ready machine learning for SellIA."""

# NOTE: these were absolute imports (`from ml_engine import ...`) with no
# package prefix — always broken, since Python has no top-level `ml_engine`/
# `market_analysis_engine`/`financial_analysis` module. Any code path that
# did `import app.core.ml` (or anything importing from it) has always raised
# ModuleNotFoundError. Fixed to relative imports pointing at the real
# sibling files.
from .ml_engine import (
    SupervisedLearner,
    UnsupervisedLearner,
    ReinforcementLearner,
    FeatureEngineer,
    ModelEvaluator,
)
from .market_analysis_engine import (
    CompetitiveIntelligence,
    MarketTrendsAnalyzer,
    OwnAnalyzer,
    SWOTAnalyzer,
    ForecastingEngine,
)
from .financial_analysis import (
    BudgetPlanner,
    CostAnalyzer,
    ProfitMarginCalculator,
    AssetsLiabilitiesTracker,
    CashFlowProjector,
    SensitivityAnalyzer,
)

# The neural_networks re-export block that used to live here (35+ classes:
# NeuralNetworkBase, ActivationFunction, SalesPredictionNetwork, ...) has
# been removed. None of those classes exist anywhere in
# app/core/ml/neural_networks/ (which only has sellias_neural_brain.py with
# 3 unrelated classes) — this was aspirational/scaffold code for a neural
# network taxonomy that was never actually built, not a broken import path.
# Re-add this block once that subsystem exists for real.

__all__ = [
    "SupervisedLearner",
    "UnsupervisedLearner",
    "ReinforcementLearner",
    "FeatureEngineer",
    "ModelEvaluator",
    "CompetitiveIntelligence",
    "MarketTrendsAnalyzer",
    "OwnAnalyzer",
    "SWOTAnalyzer",
    "ForecastingEngine",
    "BudgetPlanner",
    "CostAnalyzer",
    "ProfitMarginCalculator",
    "AssetsLiabilitiesTracker",
    "CashFlowProjector",
    "SensitivityAnalyzer",
]
