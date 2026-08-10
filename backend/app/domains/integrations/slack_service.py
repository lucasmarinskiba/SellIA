"""Slack integration for alerts and notifications."""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SlackMessageType(str, Enum):
    """Message types with color-coded blocks."""
    ESCALATION = "escalation"  # Red - urgent action needed
    DEAL_CLOSED = "deal_closed"  # Green - win celebration
    CHURN_WARNING = "churn_warning"  # Orange - at-risk customer
    EXPANSION_OPPORTUNITY = "expansion_opportunity"  # Blue - upsell alert
    ANOMALY = "anomaly"  # Yellow - unusual activity
    MILESTONE = "milestone"  # Purple - achievement


class SlackService:
    """Slack webhook integration for real-time alerts."""

    def __init__(self, webhook_url: str):
        """
        Initialize Slack service.

        Args:
            webhook_url: Slack incoming webhook URL (from Slack app settings)
        """
        self.webhook_url = webhook_url
        self.color_map = {
            SlackMessageType.ESCALATION: "#FF0000",  # Red
            SlackMessageType.DEAL_CLOSED: "#00AA00",  # Green
            SlackMessageType.CHURN_WARNING: "#FFA500",  # Orange
            SlackMessageType.EXPANSION_OPPORTUNITY: "#0099FF",  # Blue
            SlackMessageType.ANOMALY: "#FFFF00",  # Yellow
            SlackMessageType.MILESTONE: "#9900FF",  # Purple
        }

    async def send_message(
        self,
        message_type: SlackMessageType,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        channel: str = "#sales-alerts",
    ) -> bool:
        """Send formatted message to Slack."""
        try:
            blocks = self._build_message_blocks(
                message_type, title, content, metadata
            )

            payload = {
                "channel": channel,
                "blocks": blocks,
                "username": "SellIA Bot",
                "icon_emoji": ":robot_face:",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()

            logger.info(f"Slack message sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False

    def _build_message_blocks(
        self,
        message_type: SlackMessageType,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build Slack message blocks."""
        color = self.color_map.get(message_type, "#CCCCCC")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {title}" if message_type == SlackMessageType.ESCALATION else f"📊 {title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": content},
            },
        ]

        # Add metadata as fields
        if metadata:
            fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*{k}*\n{v}",
                }
                for k, v in metadata.items()
            ]
            blocks.append(
                {
                    "type": "section",
                    "fields": fields[:10],  # Max 10 fields
                }
            )

        # Add timestamp
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"__{datetime.utcnow().isoformat()}__",
                    }
                ],
            }
        )

        return blocks

    async def send_escalation_alert(
        self, lead_name: str, company: str, reason: str, deal_size: float
    ) -> bool:
        """Send escalation alert."""
        return await self.send_message(
            SlackMessageType.ESCALATION,
            f"ESCALATION: {lead_name}",
            f"Lead *{lead_name}* at *{company}* requires human intervention.\n*Reason:* {reason}\n*Deal Size:* ${deal_size:,.0f}",
            {
                "Lead": lead_name,
                "Company": company,
                "Deal Size": f"${deal_size:,.0f}",
            },
        )

    async def send_deal_closed_alert(
        self, lead_name: str, company: str, deal_size: float, agent_name: str
    ) -> bool:
        """Send deal closed celebration alert."""
        return await self.send_message(
            SlackMessageType.DEAL_CLOSED,
            f"🎉 DEAL CLOSED: {lead_name}",
            f"Deal with *{lead_name}* at *{company}* is CLOSED! 🎊\n*Amount:* ${deal_size:,.0f}\n*Closed by:* {agent_name}",
            {"Lead": lead_name, "Amount": f"${deal_size:,.0f}"},
        )

    async def send_churn_warning(
        self, customer_name: str, company: str, churn_probability: float, days_until_churn: int
    ) -> bool:
        """Send churn risk warning."""
        return await self.send_message(
            SlackMessageType.CHURN_WARNING,
            f"⚠️ CHURN RISK: {customer_name}",
            f"Customer *{customer_name}* at *{company}* is at risk of churning.\n*Churn Probability:* {churn_probability*100:.1f}%\n*Days to Churn:* {days_until_churn}",
            {"Probability": f"{churn_probability*100:.1f}%", "Timeline": f"{days_until_churn} days"},
        )

    async def send_expansion_opportunity(
        self, customer_name: str, company: str, expansion_value: float, recommended_product: str
    ) -> bool:
        """Send expansion opportunity alert."""
        return await self.send_message(
            SlackMessageType.EXPANSION_OPPORTUNITY,
            f"💰 EXPANSION OPPORTUNITY: {customer_name}",
            f"Customer *{customer_name}* is ready to expand!\n*Potential Value:* ${expansion_value:,.0f}\n*Recommended:* {recommended_product}",
            {"Customer": customer_name, "Opportunity": f"${expansion_value:,.0f}"},
        )
