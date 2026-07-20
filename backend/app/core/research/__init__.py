"""
Research Brain Module - 52+ Agents + 10 Specialists
Real-time market intelligence and competitor tracking for Computer Use Orchestrator
"""

from .research_brain import (
    ResearchBrain,
    ResearchAgent,
    SpecialistAgent,
    ResearchSignal,
    MarketInsight,
    CompetitorSignal,
    TrendAlert,
    initialize_research_brain,
    # Specialists
    MarketResearchSpecialist,
    CompetitorAnalysisSpecialist,
    ContentResearchSpecialist,
    AdvertisingStrategySpecialist,
    CustomerReachSpecialist,
    PositioningSpecialist,
    InfluencerSpecialist,
    ContentDistributionSpecialist,
    MarketIntelligenceSpecialist,
)

from .data_sources import (
    DataSourceOrchestrator,
    GoogleTrendsConnector,
    SEMrushConnector,
    TwitterConnector,
    LinkedInConnector,
    CrunchBaseConnector,
    NewsAPIConnector,
    RedditConnector,
    AltMetricsConnector,
    PricingDataConnector,
    MarketDataConnector,
    SocialListeningConnector,
    CustomerDataConnector,
    initialize_data_sources,
)

from .research_to_cu_bridge import (
    ResearchInsightPacket,
    ResearchBackedAction,
    DecisionContext,
    ResearchToActionTranslator,
    DecisionContextBuilder,
    ResearchInsightsCoordinator,
    ResearchCUMetrics,
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
