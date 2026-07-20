"""Outreach Orchestrator — Auto-contact leads via multiple channels.

Envía primer mensaje frío → sigue si no responde → personaliza por lead.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OutreachChannel(str, Enum):
    """Canales de outreach."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    SMS = "sms"


class OutreachCampaign:
    """Campaña de outreach a leads."""

    def __init__(
        self,
        campaign_id: str,
        name: str,
        target_quality: str,  # hot, warm, cold
        channel: OutreachChannel,
        message_template: str,
        follow_up_days: int = 3,
    ):
        self.campaign_id = campaign_id
        self.name = name
        self.target_quality = target_quality
        self.channel = channel
        self.message_template = message_template
        self.follow_up_days = follow_up_days

        self.status = "draft"  # draft, active, paused, completed
        self.created_at = datetime.utcnow()
        self.stats = {
            "sent": 0,
            "opened": 0,
            "clicked": 0,
            "replied": 0,
            "conversion": 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "channel": self.channel.value,
            "status": self.status,
            "stats": self.stats,
            "created_at": self.created_at.isoformat(),
        }


class OutreachOrchestrator:
    """Orquesta outreach a múltiples leads."""

    # Message templates por quality
    TEMPLATES = {
        "hot": {
            "subject": "Quick question about {company}",
            "body": """Hi {name},

I noticed {company} is in {industry}. We help companies like yours {value_prop}.

Quick question: {question}

{cta}

Best,
{sender}""",
        },
        "warm": {
            "subject": "Thought of you - {topic}",
            "body": """Hi {name},

Saw you work at {company}. We're helping {audience} with {solution}.

Figured you might find this interesting:
{resource}

Open to chat?

{cta}

{sender}""",
        },
        "cold": {
            "subject": "Quick insight for {company}",
            "body": """Hi {name},

One thing we see with {company_size} companies in {industry}:
{insight}

We help teams fix this. Worth a quick chat?

{cta}

{sender}""",
        },
    }

    def __init__(self):
        self.logger = logger
        self.campaigns: Dict[str, OutreachCampaign] = {}
        self.outreach_log: List[Dict[str, Any]] = []

    async def create_campaign(
        self,
        name: str,
        target_quality: str,
        channel: OutreachChannel,
        message_template: Optional[str] = None,
    ) -> OutreachCampaign:
        """Crea campaña de outreach."""
        try:
            campaign_id = f"camp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # Usar template default si no se proporciona
            if not message_template:
                message_template = self.TEMPLATES.get(target_quality, self.TEMPLATES["cold"])["body"]

            campaign = OutreachCampaign(
                campaign_id=campaign_id,
                name=name,
                target_quality=target_quality,
                channel=channel,
                message_template=message_template,
            )

            self.campaigns[campaign_id] = campaign

            self.logger.info(f"Campaign created: {campaign_id} ({name})")

            return campaign

        except Exception as e:
            self.logger.error(f"Error creating campaign: {e}")
            raise

    async def send_outreach(
        self,
        campaign: OutreachCampaign,
        lead: Any,  # Lead object
        sender_name: str,
        sender_email: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía mensaje inicial a lead."""
        try:
            # Personalizar template
            message = self._personalize_message(
                template=campaign.message_template,
                lead=lead,
                sender_name=sender_name,
            )

            # Enviar por channel
            if campaign.channel == OutreachChannel.EMAIL:
                success, msg_id = await self._send_email(
                    to=lead.email,
                    subject=f"Quick question about {lead.company}",
                    body=message,
                )

            elif campaign.channel == OutreachChannel.WHATSAPP:
                success, msg_id = await self._send_whatsapp(
                    phone=lead.phone,
                    message=message,
                )

            elif campaign.channel == OutreachChannel.LINKEDIN:
                success, msg_id = await self._send_linkedin(
                    profile_url=lead.linkedin_url,
                    message=message,
                )

            else:
                return False, None

            # Log
            if success:
                campaign.stats["sent"] += 1
                self.outreach_log.append({
                    "campaign_id": campaign.campaign_id,
                    "lead_id": lead.lead_id,
                    "channel": campaign.channel.value,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "sent",
                })

                self.logger.info(f"Outreach sent to {lead.email} via {campaign.channel.value}")

                return True, msg_id

            return False, None

        except Exception as e:
            self.logger.error(f"Error sending outreach: {e}")
            return False, None

    async def send_follow_up(
        self,
        campaign: OutreachCampaign,
        lead: Any,
        follow_up_number: int = 1,
    ) -> Tuple[bool, Optional[str]]:
        """Envía follow-up si no respondió."""
        try:
            follow_up_messages = [
                f"Just circling back on my earlier message - still interested?",
                f"Quick follow-up: did you get a chance to look at this?",
                f"Last one: would love to connect this week",
            ]

            if follow_up_number > len(follow_up_messages):
                self.logger.warning(f"Too many follow-ups for lead {lead.email}")
                return False, None

            message = follow_up_messages[follow_up_number - 1]

            if campaign.channel == OutreachChannel.EMAIL:
                success, msg_id = await self._send_email(
                    to=lead.email,
                    subject=f"Re: Quick question about {lead.company}",
                    body=message,
                )

            elif campaign.channel == OutreachChannel.WHATSAPP:
                success, msg_id = await self._send_whatsapp(
                    phone=lead.phone,
                    message=message,
                )

            else:
                return False, None

            if success:
                campaign.stats["sent"] += 1

            return success, msg_id

        except Exception as e:
            self.logger.error(f"Error sending follow-up: {e}")
            return False, None

    def _personalize_message(
        self,
        template: str,
        lead: Any,
        sender_name: str,
    ) -> str:
        """Personaliza mensaje con datos del lead."""
        context = {
            "name": lead.name.split()[0],  # First name
            "company": lead.company,
            "industry": lead.industry,
            "company_size": lead.company_size,
            "title": lead.title,
            "value_prop": "reduce costs and improve efficiency",
            "question": "would this help your team?",
            "cta": "→ Let's chat for 15 min?",
            "sender": sender_name,
            "topic": "sales automation",
            "audience": "B2B companies",
            "solution": "streamline their sales",
            "resource": "https://yoursite.com/case-study",
            "insight": "they're losing deals due to slow follow-up",
        }

        message = template
        for key, value in context.items():
            message = message.replace(f"{{{key}}}", value)

        return message

    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía email (mock)."""
        # En prod: usar SendGrid, Mailgun, etc
        self.logger.info(f"Email queued: {to} | {subject}")
        return True, f"email_{to}"

    async def _send_whatsapp(
        self,
        phone: str,
        message: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía WhatsApp (mock)."""
        self.logger.info(f"WhatsApp queued: {phone}")
        return True, f"whatsapp_{phone}"

    async def _send_linkedin(
        self,
        profile_url: str,
        message: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía LinkedIn message (mock)."""
        self.logger.info(f"LinkedIn queued: {profile_url}")
        return True, f"linkedin_{profile_url}"


def get_outreach_orchestrator() -> OutreachOrchestrator:
    return OutreachOrchestrator()
