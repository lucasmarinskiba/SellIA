"""Neural Networks for SellIA Brain — Deep Learning Predictions & Optimization."""

from .attention_mechanisms import (
    CrossModalAttention,
    FeatureAttention,
    SpatialAttention,
    TemporalAttention,
)
from .base_networks import (
    ActivationFunction,
    NetworkConfig,
    NeuralNetworkBase,
    TrainingConfig,
)
from .ensemble_networks import (
    BaggingEngine,
    BoostingEngine,
    EnsemblePredictor,
    ModelSelector,
    UncertaintyEstimator,
)
from .learning_networks import (
    ActiveLearner,
    FewShotLearner,
    MetaLearningEngine,
    OnlineLearningEngine,
    TransferLearningEngine,
)
from .optimization_networks import (
    BudgetAllocationNetwork,
    ChannelOptimizationNetwork,
    FeatureImportanceNetwork,
    MessageTimingNetwork,
    PricingOptimizationNetwork,
)
from .pattern_recognition import (
    AnomalyDetector,
    CommunicationPatternRecognizer,
    CompetitorPatternRecognizer,
    CustomerBehaviorRecognizer,
    MarketPatternRecognizer,
)
from .prediction_networks import (
    ChurnPredictionNetwork,
    ContactTimingNetwork,
    DemandForecastingNetwork,
    LeadQualityNetwork,
    PriceElasticityNetwork,
    SalesPredictionNetwork,
)
from .recommendation_networks import (
    ChannelRecommender,
    MessageToneRecommender,
    PricingRecommender,
    SalesMethodRecommender,
    StrategyRecommender,
)

__all__ = [
    # Base
    "NeuralNetworkBase",
    "ActivationFunction",
    "NetworkConfig",
    "TrainingConfig",
    # Prediction
    "SalesPredictionNetwork",
    "ChurnPredictionNetwork",
    "DemandForecastingNetwork",
    "LeadQualityNetwork",
    "ContactTimingNetwork",
    "PriceElasticityNetwork",
    # Optimization
    "PricingOptimizationNetwork",
    "ChannelOptimizationNetwork",
    "MessageTimingNetwork",
    "BudgetAllocationNetwork",
    "FeatureImportanceNetwork",
    # Pattern Recognition
    "MarketPatternRecognizer",
    "CustomerBehaviorRecognizer",
    "CompetitorPatternRecognizer",
    "CommunicationPatternRecognizer",
    "AnomalyDetector",
    # Recommendations
    "StrategyRecommender",
    "SalesMethodRecommender",
    "PricingRecommender",
    "ChannelRecommender",
    "MessageToneRecommender",
    # Learning
    "OnlineLearningEngine",
    "TransferLearningEngine",
    "MetaLearningEngine",
    "FewShotLearner",
    "ActiveLearner",
    # Attention
    "FeatureAttention",
    "TemporalAttention",
    "SpatialAttention",
    "CrossModalAttention",
    # Ensemble
    "EnsemblePredictor",
    "UncertaintyEstimator",
    "ModelSelector",
    "BoostingEngine",
    "BaggingEngine",
]
