"""Neural Networks for SellIA Brain — Deep Learning Predictions & Optimization."""

from .base_networks import (
    NeuralNetworkBase,
    ActivationFunction,
    NetworkConfig,
    TrainingConfig,
)
from .prediction_networks import (
    SalesPredictionNetwork,
    ChurnPredictionNetwork,
    DemandForecastingNetwork,
    LeadQualityNetwork,
    ContactTimingNetwork,
    PriceElasticityNetwork,
)
from .optimization_networks import (
    PricingOptimizationNetwork,
    ChannelOptimizationNetwork,
    MessageTimingNetwork,
    BudgetAllocationNetwork,
    FeatureImportanceNetwork,
)
from .pattern_recognition import (
    MarketPatternRecognizer,
    CustomerBehaviorRecognizer,
    CompetitorPatternRecognizer,
    CommunicationPatternRecognizer,
    AnomalyDetector,
)
from .recommendation_networks import (
    StrategyRecommender,
    SalesMethodRecommender,
    PricingRecommender,
    ChannelRecommender,
    MessageToneRecommender,
)
from .learning_networks import (
    OnlineLearningEngine,
    TransferLearningEngine,
    MetaLearningEngine,
    FewShotLearner,
    ActiveLearner,
)
from .attention_mechanisms import (
    FeatureAttention,
    TemporalAttention,
    SpatialAttention,
    CrossModalAttention,
)
from .ensemble_networks import (
    EnsemblePredictor,
    UncertaintyEstimator,
    ModelSelector,
    BoostingEngine,
    BaggingEngine,
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
