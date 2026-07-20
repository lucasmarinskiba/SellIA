"""Affiliate Automation — Computer Use integration for platform automation."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AutomationTask:
    """Single automation task for Computer Use."""
    task_id: str
    platform: str  # hotmart|meli|amazon|beacons|instagram|tiktok
    action: str  # create_campaign|upload_post|schedule_email|add_links
    description: str
    cu_instructions: str  # Specific instructions for Computer Use
    expected_duration_minutes: int


class AffiliateAutomationOrchestrator:
    """Orchestrate Computer Use for affiliate marketing automation."""

    def __init__(self):
        self.tasks: List[AutomationTask] = []
        self.completed_tasks: List[str] = []

    def create_hotmart_promotion_campaign(
        self, product_id: str, campaign_name: str, promotion_text: str
    ) -> AutomationTask:
        """Create Hotmart product promotion campaign via Computer Use."""
        task = AutomationTask(
            task_id=f"hotmart_campaign_{product_id}",
            platform="hotmart",
            action="create_campaign",
            description=f"Create promotion campaign for {product_id}",
            cu_instructions=f"""
1. Navigate to Hotmart affiliate dashboard
2. Find product {product_id}
3. Create new campaign: "{campaign_name}"
4. Add promotion text: "{promotion_text}"
5. Configure tracking parameters
6. Generate affiliate link
7. Copy link to clipboard
8. Return link
            """.strip(),
            expected_duration_minutes=5,
        )
        self.tasks.append(task)
        return task

    def upload_social_media_post(
        self, platform: str, content: str, image_url: Optional[str] = None
    ) -> AutomationTask:
        """Upload post to social media platform."""
        task = AutomationTask(
            task_id=f"{platform}_post_{len(self.tasks)}",
            platform=platform,
            action="upload_post",
            description=f"Upload post to {platform}",
            cu_instructions=f"""
1. Navigate to {platform} dashboard
2. Click create/new post
3. Add content: "{content}"
{f'4. Upload image from: {image_url}' if image_url else ''}
4. Add affiliate link in bio/description
5. Schedule/publish
6. Verify post appears
            """.strip(),
            expected_duration_minutes=3,
        )
        self.tasks.append(task)
        return task

    def add_affiliate_links_to_bio(
        self, platform: str, links: List[Dict[str, str]]
    ) -> AutomationTask:
        """Add affiliate links to profile bio/link aggregator."""
        task = AutomationTask(
            task_id=f"{platform}_bio_{len(self.tasks)}",
            platform=platform,
            action="add_links",
            description=f"Add affiliate links to {platform} profile",
            cu_instructions=f"""
1. Navigate to {platform} profile settings
2. Go to link/bio section
3. Add links:
{chr(10).join([f'   - {l["name"]}: {l["url"]}' for l in links])}
4. Save changes
5. Verify links display correctly
6. Test click functionality
            """.strip(),
            expected_duration_minutes=4,
        )
        self.tasks.append(task)
        return task

    def schedule_email_campaign(
        self,
        email_list: str,
        subject: str,
        body: str,
        affiliate_links: List[str],
        send_time: str,
    ) -> AutomationTask:
        """Schedule email campaign via email platform."""
        task = AutomationTask(
            task_id=f"email_campaign_{len(self.tasks)}",
            platform="email",
            action="schedule_email",
            description="Schedule email campaign",
            cu_instructions=f"""
1. Navigate to email platform (e.g., ConvertKit, ActiveCampaign)
2. Create new broadcast
3. Add subject: "{subject}"
4. Add body: "{body}"
5. Insert affiliate links:
{chr(10).join([f'   - {link}' for link in affiliate_links])}
6. Select list: {email_list}
7. Schedule for: {send_time}
8. Preview and confirm
9. Schedule send
            """.strip(),
            expected_duration_minutes=5,
        )
        self.tasks.append(task)
        return task

    def create_landing_page(
        self, platform: str, product_name: str, affiliate_link: str
    ) -> AutomationTask:
        """Create landing page for affiliate offer."""
        task = AutomationTask(
            task_id=f"landing_page_{product_name}",
            platform=platform,
            action="create_landing_page",
            description=f"Create landing page for {product_name}",
            cu_instructions=f"""
1. Navigate to landing page builder (e.g., Leadpages, Unbounce)
2. Choose template matching product type
3. Add product details for: {product_name}
4. Create compelling headline
5. Add benefit bullets
6. Add CTA button pointing to: {affiliate_link}
7. Configure form if needed
8. Publish
9. Test link functionality
            """.strip(),
            expected_duration_minutes=10,
        )
        self.tasks.append(task)
        return task

    def execute_task(self, task: AutomationTask) -> Dict[str, Any]:
        """Execute automation task via Computer Use."""
        result = {
            "task_id": task.task_id,
            "status": "pending",
            "platform": task.platform,
            "action": task.action,
            "cu_instructions": task.cu_instructions,
            "expected_duration_minutes": task.expected_duration_minutes,
            "notes": "Task queued for Computer Use execution",
        }

        logger.info(f"Queued automation task: {task.task_id}")
        return result

    def get_pending_tasks(self) -> List[AutomationTask]:
        """Get tasks not yet executed."""
        return [t for t in self.tasks if t.task_id not in self.completed_tasks]

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark task as completed."""
        if task_id not in self.completed_tasks:
            self.completed_tasks.append(task_id)
            logger.info(f"Marked complete: {task_id}")
            return True
        return False


class PlatformAutomationAdapter:
    """Adapt automation tasks to specific platforms."""

    @staticmethod
    def get_platform_commands(platform: str) -> Dict[str, str]:
        """Get platform-specific command templates."""
        commands = {
            "hotmart": {
                "dashboard_url": "https://app.hotmart.com/affiliate",
                "create_campaign": "Click 'New Campaign' > Fill details > Generate link",
                "export_stats": "Go to Stats > Filter period > Export CSV",
            },
            "mercadolibre": {
                "dashboard_url": "https://www.mercadolibre.com/affiliates",
                "find_products": "Search products by category > Apply filters",
                "copy_link": "Click 'Copy link' > Paste where needed",
            },
            "amazon": {
                "dashboard_url": "https://affiliate-program.amazon.com/",
                "search_products": "Use ASIN lookup > Get affiliate link",
                "track_clicks": "Dashboard > Performance > Click-through rate",
            },
            "instagram": {
                "dashboard_url": "https://instagram.com/",
                "add_link": "Edit profile > Business tools > Links",
                "schedule_post": "Create post > Advanced options > Schedule",
            },
            "tiktok": {
                "dashboard_url": "https://www.tiktok.com/creator",
                "add_link": "Creator Fund > Link in bio",
                "track_views": "Analytics > Videos > View counts",
            },
        }
        return commands.get(platform, {})

    @staticmethod
    def generate_cu_instruction(
        platform: str, action: str, params: Dict[str, str]
    ) -> str:
        """Generate Computer Use instruction for platform action."""
        if platform == "hotmart" and action == "create_campaign":
            return f"""
Go to Hotmart affiliate dashboard:
1. Click on product: {params.get('product_id')}
2. Create campaign: {params.get('campaign_name')}
3. Add description: {params.get('description')}
4. Generate link and copy to clipboard
            """.strip()

        elif platform == "instagram" and action == "post":
            return f"""
Create Instagram post:
1. Open Instagram
2. Tap Create (+ icon)
3. Select image/video: {params.get('content')}
4. Add caption: {params.get('caption')}
5. Add link in bio: {params.get('link')}
6. Post/Schedule
            """.strip()

        return "Platform/action combination not yet configured"
