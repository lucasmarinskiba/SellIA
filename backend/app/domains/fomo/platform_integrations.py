"""Platform Integrations: Instagram, TikTok, Google Shopping"""

from datetime import datetime, timedelta
from typing import List, Dict
import asyncio


class InstagramIntegration:
    def __init__(self, user_token: str):
        self.token = user_token

    async def generate_story_template(
        self, product_name: str, image_url: str, stock: int, total: int
    ) -> Dict:
        urgency = stock / total
        if urgency < 0.1:
            text = f"🔥🔥🔥 ÚLTIMO"
            color = "#dc2626"
        elif urgency < 0.3:
            text = f"🔥 Solo {stock} quedan"
            color = "#ea580c"
        else:
            text = f"📦 {stock}/{total}"
            color = "#0891b2"

        return {
            "type": "story",
            "image_url": image_url,
            "elements": [
                {"type": "text", "content": product_name, "position": "bottom_left", "size": 24},
                {"type": "text", "content": text, "position": "top", "size": 32, "color": color},
                {"type": "link_sticker", "url": "https://shop.example.com", "label": "COMPRAR"},
            ],
        }

    async def schedule_carousel_post(
        self, product_id: str, images: List[str], caption: str, scheduled_time: datetime
    ) -> str:
        # Would integrate with Instagram API
        return f"post_{product_id}_{int(scheduled_time.timestamp())}"

    async def auto_generate_7day_campaign(
        self, product_id: str, product_name: str, images: List[str], stock: int, price: float
    ):
        """Generate 7-day Instagram campaign"""
        campaign = [
            {"day": 1, "type": "story", "content": f"🔥 {product_name} ya disponible"},
            {"day": 2, "type": "reel", "content": f"Unboxing: {product_name}"},
            {"day": 3, "type": "carousel", "content": f"Detalles de {product_name}"},
            {"day": 4, "type": "story", "content": "35 personas compraron 👀"},
            {"day": 5, "type": "post", "content": f"Testimonios: {product_name}"},
            {"day": 6, "type": "story", "content": "⏰ 50% OFF mañana"},
            {"day": 7, "type": "reel", "content": f"Último día: ${price}"},
        ]
        return campaign


class TikTokIntegration:
    def __init__(self, user_token: str):
        self.token = user_token

    def generate_hook_variants(self, product_name: str, price: float, stock: int) -> List[str]:
        return [
            f"Solo {stock} en stock de {product_name} 🔥",
            f"TODOS están comprando {product_name} AHORA 👀",
            f"Primeros 50 = ENVÍO GRATIS 📦",
            f"Mañana sube a ${price * 1.3}... hoy ${price} 📈",
            f"Se agotó en Amazon pero aquí hay {product_name}",
            f"45K personas compraron {product_name} este mes 🚀",
        ]

    async def auto_generate_daily_videos(
        self, product_id: str, product_name: str, schedule_days: int = 7
    ):
        """Generate TikTok videos daily"""
        for day in range(1, schedule_days + 1):
            if day <= 3:
                video_type = "unboxing"
            elif day <= 5:
                video_type = "testimonial"
            else:
                video_type = "countdown"

            task = {
                "product_id": product_id,
                "video_type": video_type,
                "day": day,
                "status": "pending",
            }
            # Queue for video generation
            await asyncio.sleep(0.01)


class GoogleShoppingIntegration:
    def __init__(self, merchant_id: str, api_key: str):
        self.merchant_id = merchant_id
        self.api_key = api_key

    def create_foom_feed(self, products: List[Dict], campaign_name: str) -> List[Dict]:
        """Create feed with FOOM annotations"""
        feed_items = []

        for product in products:
            stock = product.get("stock", 0)
            urgency = "high" if stock < 5 else "medium" if stock < 20 else "low"

            title = product["title"]
            if urgency == "high":
                title += " | ¡Solo quedan 3!"
            elif urgency == "medium":
                title += " | Stock limitado"

            item = {
                "id": str(product["id"]),
                "title": title,
                "description": f"{product['description']}\n⚠️ Stock: {stock}",
                "price": str(product["price"]),
                "saleprice": str(product["price"] * 0.85),
                "customLabels": {
                    "label_0": urgency.upper(),
                    "label_1": "HOT" if urgency == "high" else "NEW",
                },
            }
            feed_items.append(item)

        return feed_items
