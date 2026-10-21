"""
Research Brain Module - 52+ Agents + 10 Specialists
Real-time market intelligence and competitor tracking for Computer Use Orchestrator
"""

from .data_sources import (
    AltMetricsConnector,
    CrunchBaseConnector,
    CustomerDataConnector,
    DataSourceOrchestrator,
    GoogleTrendsConnector,
    LinkedInConnector,
    MarketDataConnector,
    NewsAPIConnector,
    PricingDataConnector,
    RedditConnector,
    SEMrushConnector,
    SocialListeningConnector,
    TwitterConnector,
    initialize_data_sources,
)
from .research_brain import (
    AdvertisingStrategySpecialist,
    CompetitorAnalysisSpecialist,
    CompetitorSignal,
    ContentDistributionSpecialist,
    ContentResearchSpecialist,
    CustomerReachSpecialist,
    InfluencerSpecialist,
    MarketInsight,
    MarketIntelligenceSpecialist,
    # Specialists
    MarketResearchSpecialist,
    PositioningSpecialist,
    ResearchAgent,
    ResearchBrain,
    ResearchSignal,
    SpecialistAgent,
    TrendAlert,
    initialize_research_brain,
)
from .research_to_cu_bridge import (
    DecisionContext,
    DecisionContextBuilder,
    ResearchBackedAction,
    ResearchCUMetrics,
    ResearchInsightPacket,
    ResearchInsightsCoordinator,
    ResearchToActionTranslator,
)

__all__ = [
    # Research Brain
    "ResearchBrain",
    "ResearchAgent",
    "SpecialistAgent",
    "ResearchSignal",
    "MarketInsight",
    "CompetitorSignal",
    "TrendAlert",
    "initialize_research_brain",
    # Specialists
    "MarketResearchSpecialist",
    "CompetitorAnalysisSpecialist",
    "ContentResearchSpecialist",
    "AdvertisingStrategySpecialist",
    "CustomerReachSpecialist",
    "PositioningSpecialist",
    "InfluencerSpecialist",
    "ContentDistributionSpecialist",
    "MarketIntelligenceSpecialist",
    # Data Sources
    "DataSourceOrchestrator",
    "GoogleTrendsConnector",
    "SEMrushConnector",
    "TwitterConnector",
    "LinkedInConnector",
    "CrunchBaseConnector",
    "NewsAPIConnector",
    "RedditConnector",
    "AltMetricsConnector",
    "PricingDataConnector",
    "MarketDataConnector",
    "SocialListeningConnector",
    "CustomerDataConnector",
    "initialize_data_sources",
    # Bridge
    "ResearchInsightPacket",
    "ResearchBackedAction",
    "DecisionContext",
    "ResearchToActionTranslator",
    "DecisionContextBuilder",
    "ResearchInsightsCoordinator",
    "ResearchCUMetrics",
]
