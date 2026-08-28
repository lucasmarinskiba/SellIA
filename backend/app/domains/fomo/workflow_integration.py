"""FOMO Workflow Integration - Trigger workflows from FOMO campaigns"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class FOOMWorkflowTrigger(str, Enum):
    CAMPAIGN_STARTED = "fomo_campaign_started"
    CAMPAIGN_COMPLETED = "fomo_campaign_completed"
    VISITOR_ARRIVED = "fomo_visitor_arrived"
    PURCHASE_DETECTED = "fomo_purchase_detected"
    CART_ABANDONED = "fomo_cart_abandoned"
    CART_RECOVERED = "fomo_cart_recovered"
    CONVERSION_MILESTONE = "fomo_conversion_milestone"
    REVENUE_MILESTONE = "fomo_revenue_milestone"


class WorkflowActionType(str, Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    CREATE_TASK = "create_task"
    ADD_TAG = "add_tag"
    UPDATE_CONTACT = "update_contact"
    TRIGGER_NOTIFICATION = "trigger_notification"
    WEBHOOK_POST = "webhook_post"
    SLACK_MESSAGE = "slack_message"
    CONDITIONAL_ACTION = "conditional_action"


class FOOMToWorkflowIntegration:
    """Map FOMO events to workflow triggers"""

    @staticmethod
    def create_visitor_workflow_trigger(campaign_id: str, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create workflow trigger for new visitor"""
        return {
            "workflow_trigger": FOOMWorkflowTrigger.VISITOR_ARRIVED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "visitor_id": visitor_data.get("session_id"),
                "page_url": visitor_data.get("page_url"),
                "source": visitor_data.get("referrer"),
                "device_type": visitor_data.get("device_type", "desktop"),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "new_visitor_welcome",
                    "conditions": [
                        {"field": "first_visit", "operator": "equals", "value": True}
                    ]
                }
            ]
        }

    @staticmethod
    def create_purchase_workflow_trigger(
        campaign_id: str,
        purchase_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow trigger for purchase completion"""
        return {
            "workflow_trigger": FOOMWorkflowTrigger.PURCHASE_DETECTED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "order_id": purchase_data.get("order_id"),
                "customer_email": purchase_data.get("customer_email"),
                "customer_id": purchase_data.get("customer_id"),
                "order_value": float(purchase_data.get("order_value", 0)),
                "product_ids": purchase_data.get("product_ids", []),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "post_purchase_thank_you",
                    "delay_minutes": 5,
                },
                {
                    "type": WorkflowActionType.ADD_TAG.value,
                    "tag": "purchased",
                    "delay_minutes": 0,
                },
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "post_purchase_recommendation",
                    "delay_minutes": 1440,  # 1 day later
                }
            ]
        }

    @staticmethod
    def create_cart_abandoned_workflow_trigger(
        campaign_id: str,
        cart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow trigger for abandoned cart"""
        return {
            "workflow_trigger": FOOMWorkflowTrigger.CART_ABANDONED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "cart_id": cart_data.get("cart_id"),
                "customer_email": cart_data.get("customer_email"),
                "customer_id": cart_data.get("customer_id"),
                "cart_value": float(cart_data.get("cart_value", 0)),
                "products": cart_data.get("products", []),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "cart_abandoned_1",
                    "delay_minutes": 5,
                },
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "cart_abandoned_2_social_proof",
                    "delay_minutes": 120,
                },
                {
                    "type": WorkflowActionType.SEND_SMS.value,
                    "template_id": "cart_abandoned_3_sms",
                    "delay_minutes": 1440,
                    "conditions": [
                        {"field": "has_phone", "operator": "equals", "value": True}
                    ]
                }
            ]
        }

    @staticmethod
    def create_cart_recovered_workflow_trigger(
        campaign_id: str,
        recovery_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow trigger for cart recovery"""
        return {
            "workflow_trigger": FOOMWorkflowTrigger.CART_RECOVERED.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "order_id": recovery_data.get("order_id"),
                "customer_email": recovery_data.get("customer_email"),
                "recovery_source": recovery_data.get("recovery_source"),  # email/sms/direct
                "recovered_value": float(recovery_data.get("recovered_value", 0)),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.ADD_TAG.value,
                    "tag": "cart_recovered",
                    "delay_minutes": 0,
                },
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "thank_you_cart_recovered",
                    "delay_minutes": 5,
                }
            ]
        }

    @staticmethod
    def create_conversion_milestone_trigger(
        campaign_id: str,
        milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow trigger when conversion milestone is reached"""
        milestone_number = milestone_data.get("milestone_number")
        return {
            "workflow_trigger": FOOMWorkflowTrigger.CONVERSION_MILESTONE.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "milestone_number": milestone_number,
            "payload": {
                "conversions": milestone_data.get("conversions"),
                "revenue": float(milestone_data.get("revenue", 0)),
                "time_to_milestone_minutes": milestone_data.get("time_to_milestone_minutes"),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.SLACK_MESSAGE.value,
                    "channel": "#fomo-alerts",
                    "message": f"🎉 Campaign {{campaign_name}} reached {milestone_number} conversions!",
                    "delay_minutes": 0,
                },
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": f"milestone_{milestone_number}_celebrate",
                    "recipient": "campaign_owner",
                    "delay_minutes": 5,
                }
            ]
        }

    @staticmethod
    def create_revenue_milestone_trigger(
        campaign_id: str,
        milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow trigger when revenue milestone is reached"""
        milestone_amount = milestone_data.get("milestone_amount")
        return {
            "workflow_trigger": FOOMWorkflowTrigger.REVENUE_MILESTONE.value,
            "campaign_id": campaign_id,
            "timestamp": datetime.utcnow().isoformat(),
            "milestone_amount": milestone_amount,
            "payload": {
                "total_revenue": float(milestone_data.get("total_revenue", 0)),
                "conversions": milestone_data.get("conversions"),
                "time_to_milestone_minutes": milestone_data.get("time_to_milestone_minutes"),
            },
            "workflow_actions": [
                {
                    "type": WorkflowActionType.SEND_EMAIL.value,
                    "template_id": "revenue_milestone_notification",
                    "recipient": "campaign_owner",
                    "delay_minutes": 0,
                }
            ]
        }


class WorkflowConditionBuilder:
    """Build complex conditional logic for workflow actions"""

    @staticmethod
    def build_customer_segment_condition(segment: str) -> Dict[str, Any]:
        """Build condition for customer segment"""
        segments = {
            "high_value": {"lifetime_value": {"operator": "gte", "value": 1000}},
            "repeat_customer": {"purchase_count": {"operator": "gte", "value": 2}},
            "new_customer": {"purchase_count": {"operator": "equals", "value": 1}},
            "at_risk": {"days_since_purchase": {"operator": "gte", "value": 90}},
            "vip": {"tags": {"operator": "contains", "value": "vip"}},
        }
        return segments.get(segment, {})

    @staticmethod
    def build_behavior_condition(behavior: str) -> Dict[str, Any]:
        """Build condition based on user behavior"""
        behaviors = {
            "high_engagement": {
                "emails_opened": {"operator": "gte", "value": 5},
                "links_clicked": {"operator": "gte", "value": 2}
            },
            "browsed_but_not_purchased": {
                "page_views": {"operator": "gte", "value": 3},
                "purchases": {"operator": "equals", "value": 0}
            },
            "cart_abandoner": {
                "carts_abandoned": {"operator": "gte", "value": 1},
                "purchases": {"operator": "lt", "value": 1}
            },
            "quick_buyer": {
                "time_to_purchase_minutes": {"operator": "lte", "value": 30}
            }
        }
        return behaviors.get(behavior, {})

    @staticmethod
    def build_time_based_condition(condition: str) -> Dict[str, Any]:
        """Build time-based conditions"""
        conditions = {
            "business_hours": {
                "hour_of_day": {"operator": "gte", "value": 9, "operator_max": "lte", "value_max": 17},
                "day_of_week": {"operator": "not_in", "value": ["Saturday", "Sunday"]}
            },
            "peak_hours": {
                "hour_of_day": {"operator": "gte", "value": 18, "operator_max": "lte", "value_max": 21}
            },
            "night_time": {
                "hour_of_day": {"operator": "lt", "value": 9}
            }
        }
        return conditions.get(condition, {})


class WorkflowActionSequence:
    """Define multi-step workflow sequences triggered by FOMO"""

    @staticmethod
    def cart_abandonment_sequence() -> List[Dict[str, Any]]:
        """Complete 3-email cart abandonment workflow"""
        return [
            {
                "step": 1,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "cart_abandoned_1",
                "delay_minutes": 5,
                "subject": "Olvidaste tu carrito 🛒",
            },
            {
                "step": 2,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "cart_abandoned_2_social_proof",
                "delay_minutes": 120,
                "subject": "2 personas más compraron esto",
                "condition": {
                    "cart_recovered": False,  # Only send if cart not recovered
                    "email_opened": True  # Only if first email was opened
                }
            },
            {
                "step": 3,
                "action_type": WorkflowActionType.SEND_SMS.value,
                "template_id": "cart_abandoned_3_sms",
                "delay_minutes": 1440,
                "condition": {
                    "cart_recovered": False,
                    "has_phone": True,
                }
            }
        ]

    @staticmethod
    def post_purchase_sequence() -> List[Dict[str, Any]]:
        """Complete post-purchase workflow"""
        return [
            {
                "step": 1,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "post_purchase_thank_you",
                "delay_minutes": 5,
            },
            {
                "step": 2,
                "action_type": WorkflowActionType.ADD_TAG.value,
                "tag": "purchased",
                "delay_minutes": 0,
            },
            {
                "step": 3,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "post_purchase_recommendation",
                "delay_minutes": 1440,
                "condition": {
                    "email_opened_previous": True
                }
            },
            {
                "step": 4,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "post_purchase_review_request",
                "delay_minutes": 10080,  # 7 days
                "condition": {
                    "order_delivered": True
                }
            }
        ]

    @staticmethod
    def churn_prevention_sequence() -> List[Dict[str, Any]]:
        """Churn prevention workflow for at-risk customers"""
        return [
            {
                "step": 1,
                "action_type": WorkflowActionType.SEND_EMAIL.value,
                "template_id": "win_back_offer",
                "delay_minutes": 0,
                "subject": "Oferta especial solo para ti",
            },
            {
                "step": 2,
                "action_type": WorkflowActionType.SEND_SMS.value,
                "template_id": "win_back_reminder",
                "delay_minutes": 120,
                "condition": {"email_not_opened": True}
            },
            {
                "step": 3,
                "action_type": WorkflowActionType.SLACK_MESSAGE.value,
                "channel": "#sales",
                "message": "Customer {{customer_name}} at risk - consider outreach",
                "delay_minutes": 1440,
                "condition": {"no_conversion_after_offer": True}
            }
        ]
