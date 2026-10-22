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
    "AdvertisingStrategySpecialist",
    "AltMetricsConnector",
    "CompetitorAnalysisSpecialist",
    "CompetitorSignal",
    "ContentDistributionSpecialist",
    "ContentResearchSpecialist",
    "CrunchBaseConnector",
    "CustomerDataConnector",
    "CustomerReachSpecialist",
    # Data Sources
    "DataSourceOrchestrator",
    "DecisionContext",
    "DecisionContextBuilder",
    "GoogleTrendsConnector",
    "InfluencerSpecialist",
    "LinkedInConnector",
    "MarketDataConnector",
    "MarketInsight",
    "MarketIntelligenceSpecialist",
    # Specialists
    "MarketResearchSpecialist",
    "NewsAPIConnector",
    "PositioningSpecialist",
    "PricingDataConnector",
    "RedditConnector",
    "ResearchAgent",
    "ResearchBackedAction",
    # Research Brain
    "ResearchBrain",
    "ResearchCUMetrics",
    # Bridge
    "ResearchInsightPacket",
    "ResearchInsightsCoordinator",
    "ResearchSignal",
    "ResearchToActionTranslator",
    "SEMrushConnector",
    "SocialListeningConnector",
    "SpecialistAgent",
    "TrendAlert",
    "TwitterConnector",
    "initialize_data_sources",
    "initialize_research_brain",
]
