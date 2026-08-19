"""Offline-triggered sequences — automations that fire based on physical visit outcomes."""

import logging
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domains.analytics.offline_models import OfflineConversion, VisitType

logger = logging.getLogger(__name__)


class OfflineTriggerType(str, Enum):
    """Triggers that fire based on offline conversion events."""
    VISIT_COMPLETED = "visit_completed"
    DEMO_COMPLETED = "demo_completed"
    TOUR_COMPLETED = "tour_completed"
    APPOINTMENT_NO_SHOW = "appointment_no_show"
    VISIT_NO_PURCHASE = "visit_no_purchase"
    PURCHASE_COMPLETED = "purchase_completed"
    HIGH_DWELL_TIME = "high_dwell_time"


class OfflineSequenceTemplate(str, Enum):
    """Predefined sequences triggered by offline events."""
    POST_VISIT_THANK_YOU = "post_visit_thank_you"
    POST_DEMO_SUMMARY = "post_demo_summary"
    POST_DEMO_PROPOSAL = "post_demo_proposal"
    POST_DEMO_TRIAL = "post_demo_trial"
    POST_TOUR_PROPOSAL = "post_tour_proposal"
    POST_TOUR_REFERENCE = "post_tour_reference"
    ABANDON_VISIT = "abandon_visit"
    ABANDONED_DEMO = "abandoned_demo"
    WIN_BACK = "win_back"
    REFERRAL_ASK = "referral_ask"


class OfflineSequenceService:
    """Service for managing offline-triggered sequences."""

    TEMPLATE_BY_VISIT_TYPE = {
        VisitType.WALK_IN: OfflineSequenceTemplate.POST_VISIT_THANK_YOU,
        VisitType.SCHEDULED_DEMO: OfflineSequenceTemplate.POST_DEMO_SUMMARY,
        VisitType.SCHEDULED_TOUR: OfflineSequenceTemplate.POST_TOUR_PROPOSAL,
        VisitType.SCHEDULED_APPOINTMENT: OfflineSequenceTemplate.POST_VISIT_THANK_YOU,
        VisitType.QR_SCAN: OfflineSequenceTemplate.POST_VISIT_THANK_YOU,
    }

    EMAIL_DELAYS = {
        OfflineSequenceTemplate.POST_VISIT_THANK_YOU: 1,
        OfflineSequenceTemplate.POST_DEMO_SUMMARY: 2,
        OfflineSequenceTemplate.POST_DEMO_PROPOSAL: 24,
        OfflineSequenceTemplate.POST_TOUR_PROPOSAL: 24,
        OfflineSequenceTemplate.ABANDON_VISIT: 48,
    }

    @staticmethod
    def get_sequence_for_offline_event(
        offline_conversion: OfflineConversion,
        purchased: bool = False
    ) -> Optional[OfflineSequenceTemplate]:
        """Determine sequence based on visit outcome."""
        visit_type = offline_conversion.visit_type

        if purchased or offline_conversion.purchased:
            return None

        if visit_type == VisitType.SCHEDULED_DEMO:
            return OfflineSequenceTemplate.POST_DEMO_SUMMARY
        elif visit_type == VisitType.SCHEDULED_TOUR:
            return OfflineSequenceTemplate.POST_TOUR_PROPOSAL

        if visit_type in (VisitType.WALK_IN, VisitType.QR_SCAN):
            if offline_conversion.dwell_minutes and offline_conversion.dwell_minutes > 30:
                return OfflineSequenceTemplate.WIN_BACK
            else:
                return OfflineSequenceTemplate.ABANDON_VISIT

        return OfflineSequenceTemplate.POST_VISIT_THANK_YOU

    @staticmethod
    def create_offline_triggered_automation(
        business_id: UUID,
        offline_conversion_id: UUID,
        sequence_template: OfflineSequenceTemplate,
        delay_hours: Optional[int] = None,
        db: Optional[Session] = None
    ) -> dict:
        """Create automation execution for offline-triggered sequence."""
        if not db:
            raise ValueError("Database session required")

        if not delay_hours:
            delay_hours = OfflineSequenceService.EMAIL_DELAYS.get(sequence_template, 1)

        logger.info(
            f"Creating {sequence_template.value} automation for offline_conversion {offline_conversion_id}"
        )

        return {
            "status": "created",
            "sequence": sequence_template.value,
            "offline_conversion_id": str(offline_conversion_id),
            "delay_hours": delay_hours,
        }

    @staticmethod
    def get_sequence_step_count(sequence_template: OfflineSequenceTemplate) -> int:
        """Get number of steps in sequence."""
        step_counts = {
            OfflineSequenceTemplate.POST_VISIT_THANK_YOU: 1,
            OfflineSequenceTemplate.POST_DEMO_SUMMARY: 3,
            OfflineSequenceTemplate.POST_DEMO_PROPOSAL: 2,
            OfflineSequenceTemplate.POST_TOUR_PROPOSAL: 3,
            OfflineSequenceTemplate.ABANDON_VISIT: 2,
            OfflineSequenceTemplate.WIN_BACK: 2,
        }
        return step_counts.get(sequence_template, 1)

    @staticmethod
    def should_trigger_referral_sequence(
        offline_conversion: OfflineConversion,
        satisfaction_threshold: float = 4.0
    ) -> bool:
        """Determine if offline visit warrants referral request."""
        if offline_conversion.purchased:
            return True

        if offline_conversion.dwell_minutes and offline_conversion.dwell_minutes > 45:
            return True

        return False
