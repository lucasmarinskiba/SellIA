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
    "ActivationFunction",
    "ActiveLearner",
    "AnomalyDetector",
    "BaggingEngine",
    "BoostingEngine",
    "BudgetAllocationNetwork",
    "ChannelOptimizationNetwork",
    "ChannelRecommender",
    "ChurnPredictionNetwork",
    "CommunicationPatternRecognizer",
    "CompetitorPatternRecognizer",
    "ContactTimingNetwork",
    "CrossModalAttention",
    "CustomerBehaviorRecognizer",
    "DemandForecastingNetwork",
    # Ensemble
    "EnsemblePredictor",
    # Attention
    "FeatureAttention",
    "FeatureImportanceNetwork",
    "FewShotLearner",
    "LeadQualityNetwork",
    # Pattern Recognition
    "MarketPatternRecognizer",
    "MessageTimingNetwork",
    "MessageToneRecommender",
    "MetaLearningEngine",
    "ModelSelector",
    "NetworkConfig",
    # Base
    "NeuralNetworkBase",
    # Learning
    "OnlineLearningEngine",
    "PriceElasticityNetwork",
    # Optimization
    "PricingOptimizationNetwork",
    "PricingRecommender",
    "SalesMethodRecommender",
    # Prediction
    "SalesPredictionNetwork",
    "SpatialAttention",
    # Recommendations
    "StrategyRecommender",
    "TemporalAttention",
    "TrainingConfig",
    "TransferLearningEngine",
    "UncertaintyEstimator",
]
