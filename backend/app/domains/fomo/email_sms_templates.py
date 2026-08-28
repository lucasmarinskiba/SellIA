"""Email & SMS Templates for FOMO Automations"""

from typing import Dict, List, Any
from enum import Enum


class TemplateType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class CartAbandonmentTemplates:
    """3-step cart abandonment recovery sequence"""

    @staticmethod
    def email_1_immediate() -> Dict[str, Any]:
        """Step 1: Immediate reminder (sent within 5 minutes)"""
        return {
            "id": "cart_abandoned_1",
            "type": "email",
            "name": "Cart Abandoned - Immediate Reminder",
            "subject_line": "Olvidaste tu carrito 🛒",
            "preview_text": "Completa tu compra ahora",
            "from_name": "SellIA",
            "body": """
<h1>Completá tu compra</h1>
<p>Notar que dejaste {{product_count}} {{product_count_plural}} en tu carrito.</p>

<div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
  <h3>{{product_name}}</h3>
  <p>Precio: ${{product_price}}</p>
  <p>Cantidad: {{quantity}}</p>
  <strong>Total del carrito: ${{total_price}}</strong>
</div>

<p><strong>{{visitor_count}} personas están comprando esto AHORA</strong> - No dejes que se agote</p>

<a href="{{checkout_url}}" style="background: #FF6B6B; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Completar Compra →
</a>

<p style="font-size: 12px; color: #999;">
  Válido por 24 horas. Después se elimina tu carrito.
</p>
            """,
            "variables": [
                "product_name", "product_count", "product_count_plural",
                "product_price", "quantity", "total_price",
                "visitor_count", "checkout_url"
            ],
            "send_delay_minutes": 5,
            "open_rate_expected": 0.42,
            "click_rate_expected": 0.18,
        }

    @staticmethod
    def email_2_social_proof() -> Dict[str, Any]:
        """Step 2: Social proof + scarcity (sent 2 hours later)"""
        return {
            "id": "cart_abandoned_2_social_proof",
            "type": "email",
            "name": "Cart Abandoned - Social Proof",
            "subject_line": "2 personas más compraron esto - {{product_name}}",
            "preview_text": "Último inventario disponible",
            "from_name": "SellIA",
            "body": """
<h1>{{product_name}} - Inventario limitado</h1>

<p>Desde que dejaste tu carrito, <strong>2 personas más</strong> compraron esto.</p>

<div style="background: #fff3cd; padding: 16px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #ffc107;">
  <strong>⚠️ Solo {{remaining_stock}} quedan</strong>
  <p>En stock: {{available_stock}} unidades</p>
</div>

<p><strong>⭐ 4.8/5 estrellas</strong> (284 reviews)</p>

<div style="display: flex; gap: 20px; margin: 20px 0;">
  <div>
    <strong>${{product_price}}</strong>
    <p style="color: #999; font-size: 12px;">Precio hoy</p>
  </div>
  <div>
    <strong>${{original_price}}</strong>
    <p style="color: #999; font-size: 12px; text-decoration: line-through;">Precio normal</p>
  </div>
</div>

<a href="{{checkout_url}}" style="background: #FF6B6B; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Asegurar Ahora - Stock Limitado →
</a>

<p style="font-size: 12px; color: #999;">
  Entrega en 24-48 horas. Garantía de 30 días.
</p>
            """,
            "variables": [
                "product_name", "remaining_stock", "available_stock",
                "product_price", "original_price", "checkout_url"
            ],
            "send_delay_minutes": 120,
            "open_rate_expected": 0.35,
            "click_rate_expected": 0.22,
        }

    @staticmethod
    def email_3_final_discount() -> Dict[str, Any]:
        """Step 3: Final discount offer (sent 24 hours later)"""
        return {
            "id": "cart_abandoned_3_final_discount",
            "type": "email",
            "name": "Cart Abandoned - Final Discount",
            "subject_line": "50% OFF - Solo para ti - Expira en 2 horas ⏰",
            "preview_text": "Código exclusivo: COMPLETA50",
            "from_name": "SellIA",
            "body": """
<h1>⚡ Último intento - 50% OFF</h1>

<p>No queremos perder tu compra. Te damos <strong>50% de descuento</strong> - solo para ti.</p>

<div style="background: #ff6b6b; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
  <strong style="font-size: 24px;">COMPLETA50</strong>
  <p>Descuento automático en checkout</p>
</div>

<table style="width: 100%; margin: 20px 0;">
  <tr>
    <td>Subtotal</td>
    <td style="text-align: right;">${{subtotal}}</td>
  </tr>
  <tr>
    <td><strong>Con descuento (50%)</strong></td>
    <td style="text-align: right; color: #10b981; font-weight: bold;">${{discounted_price}}</td>
  </tr>
  <tr style="border-top: 1px solid #ddd; padding-top: 10px;">
    <td><strong>Ahorras</strong></td>
    <td style="text-align: right; color: #10b981;"><strong>${{savings}}</strong></td>
  </tr>
</table>

<div style="background: #fef2f2; padding: 12px; border-radius: 6px; margin: 16px 0; border-left: 4px solid #dc2626;">
  <strong>⏰ Esta oferta expira en 2 horas</strong>
  <p>Después, precio normal</p>
</div>

<a href="{{checkout_url}}" style="background: #10b981; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold; font-size: 16px;">
  Completar con 50% OFF →
</a>

<p style="font-size: 12px; color: #999; margin-top: 20px;">
  Garantía: Si no estás satisfecho en 30 días, te devolvemos el dinero.
</p>
            """,
            "variables": [
                "subtotal", "discounted_price", "savings", "checkout_url"
            ],
            "send_delay_minutes": 1440,
            "open_rate_expected": 0.52,
            "click_rate_expected": 0.35,
        }

    @staticmethod
    def sms_final_push() -> Dict[str, Any]:
        """SMS Step 3: Last push (sent 24 hours later, concurrent with email)"""
        return {
            "id": "cart_abandoned_3_sms",
            "type": "sms",
            "name": "Cart Abandoned - SMS Final Push",
            "body": "⚡ {{product_name}} - 50% OFF. Código: COMPLETA50. Expira en 2h. {{checkout_url}}",
            "character_limit": 160,
            "send_delay_minutes": 1440,
            "delivery_rate_expected": 0.98,
            "click_rate_expected": 0.28,
        }


class FlashSaleTemplates:
    """Flash sale campaign sequence"""

    @staticmethod
    def email_launch() -> Dict[str, Any]:
        return {
            "id": "flash_sale_launch",
            "type": "email",
            "name": "Flash Sale - Launch",
            "subject_line": "⚡ VENTA RELÁMPAGO: {{discount}}% OFF - Solo 24 horas",
            "preview_text": "Empieza AHORA",
            "body": """
<h1>⚡ VENTA RELÁMPAGO</h1>
<p>{{discount}}% OFF en {{product_count}} productos seleccionados</p>

<div style="background: #FF6B6B; color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
  <div style="font-size: 48px; font-weight: bold;">{{discount}}%</div>
  <div style="font-size: 18px;">EN PRODUCTOS SELECCIONADOS</div>
  <div style="font-size: 14px; margin-top: 10px;">⏰ SOLO 24 HORAS</div>
</div>

<a href="{{shop_url}}" style="background: #10b981; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Ver Ofertas →
</a>
            """,
            "variables": ["discount", "product_count", "shop_url"],
            "send_delay_minutes": 0,
        }

    @staticmethod
    def email_reminder_4h() -> Dict[str, Any]:
        return {
            "id": "flash_sale_reminder_4h",
            "type": "email",
            "name": "Flash Sale - 4 Hour Reminder",
            "subject_line": "{{discount}}% OFF - {{time_left}} horas restantes",
            "preview_text": "Apúrate, quedan pocas horas",
            "body": """
<h1>⏰ Quedan {{time_left}} horas</h1>
<p>La venta relámpago termina pronto. {{sold_percent}}% ya vendido.</p>

<div style="background: #fef2f2; padding: 16px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #dc2626;">
  <strong>Ofertas más populares:</strong>
  <ul>
    <li>{{top_product_1}} - {{discount}}% OFF</li>
    <li>{{top_product_2}} - {{discount}}% OFF</li>
    <li>{{top_product_3}} - {{discount}}% OFF</li>
  </ul>
</div>

<a href="{{shop_url}}" style="background: #FF6B6B; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Comprar Ahora →
</a>
            """,
            "variables": ["discount", "time_left", "sold_percent", "top_product_1", "top_product_2", "top_product_3", "shop_url"],
            "send_delay_minutes": 240,
        }

    @staticmethod
    def sms_1h_warning() -> Dict[str, Any]:
        return {
            "id": "flash_sale_sms_1h",
            "type": "sms",
            "name": "Flash Sale - 1 Hour Warning",
            "body": "⚡ ÚLTIMAS OFERTAS: {{discount}}% OFF. {{sold_percent}}% agotado. Termina en 1h. {{shop_url}}",
            "send_delay_minutes": 1380,
        }

    @staticmethod
    def sms_30min_final() -> Dict[str, Any]:
        return {
            "id": "flash_sale_sms_30min",
            "type": "sms",
            "name": "Flash Sale - 30 Min Final Push",
            "body": "⚡⚡ ÚLTIMO LLAMADO: {{discount}}% OFF. Sale en 30 minutos. {{shop_url}}",
            "send_delay_minutes": 1410,
        }


class PostPurchaseTemplates:
    """Post-purchase sequences"""

    @staticmethod
    def email_thank_you() -> Dict[str, Any]:
        return {
            "id": "post_purchase_thank_you",
            "type": "email",
            "name": "Post Purchase - Thank You",
            "subject_line": "¡Gracias por tu compra! 🎉",
            "preview_text": "Tu orden {{order_id}} está confirmada",
            "body": """
<h1>¡Gracias {{customer_name}}!</h1>
<p>Tu pedido <strong>#{{order_id}}</strong> está confirmado.</p>

<div style="background: #f0fdf4; padding: 16px; border-radius: 6px; margin: 20px 0;">
  <strong>Entrega esperada: {{delivery_date}}</strong>
  <p>Tracking: {{tracking_url}}</p>
</div>

<p><strong>¿Necesitas ayuda?</strong></p>
<a href="{{support_url}}">Contactar soporte</a>
            """,
            "variables": ["order_id", "customer_name", "delivery_date", "tracking_url", "support_url"],
            "send_delay_minutes": 5,
        }

    @staticmethod
    def email_product_recommendation() -> Dict[str, Any]:
        return {
            "id": "post_purchase_recommendation",
            "type": "email",
            "name": "Post Purchase - Recommendation",
            "subject_line": "Productos que te pueden interesar 💡",
            "preview_text": "Recomendaciones personalizadas",
            "body": """
<h1>Basado en tu compra...</h1>
<p>Encontramos productos que te pueden interesar:</p>

<div style="margin: 20px 0;">
  <h3>{{recommended_product_1}}</h3>
  <p>Precio: ${{price_1}}</p>
  <a href="{{url_1}}">Ver más →</a>
</div>

<div style="margin: 20px 0;">
  <h3>{{recommended_product_2}}</h3>
  <p>Precio: ${{price_2}}</p>
  <a href="{{url_2}}">Ver más →</a>
</div>
            """,
            "variables": ["recommended_product_1", "price_1", "url_1", "recommended_product_2", "price_2", "url_2"],
            "send_delay_minutes": 1440,
        }


class TrialExpiryTemplates:
    """Trial expiring soon sequences"""

    @staticmethod
    def email_7day_warning() -> Dict[str, Any]:
        return {
            "id": "trial_expiring_7day",
            "type": "email",
            "name": "Trial Expiring - 7 Days",
            "subject_line": "Tu trial termina en 7 días - Mejora ahora y guarda 30%",
            "preview_text": "30% OFF en planes anuales",
            "body": """
<h1>Tu trial de {{product}} termina en 7 días</h1>

<p>Mejora ahora y desbloquea:</p>
<ul>
  <li>Acceso ilimitado</li>
  <li>Soporte prioritario</li>
  <li>Integraciones avanzadas</li>
</ul>

<div style="background: #fff3cd; padding: 16px; border-radius: 6px; margin: 20px 0;">
  <strong>Oferta especial: 30% OFF en planes anuales</strong>
  <p>Solo para usuarios en trial</p>
</div>

<a href="{{upgrade_url}}" style="background: #3b82f6; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Mejorar Ahora - 30% OFF →
</a>
            """,
            "variables": ["product", "upgrade_url"],
            "send_delay_minutes": 0,  # Sent 7 days before expiry
        }

    @staticmethod
    def email_1day_final() -> Dict[str, Any]:
        return {
            "id": "trial_expiring_1day",
            "type": "email",
            "name": "Trial Expiring - 1 Day",
            "subject_line": "ÚLTIMO DÍA: Tu acceso a {{product}} expira mañana",
            "preview_text": "No pierdas acceso",
            "body": """
<h1>⏰ Último día de trial</h1>
<p>Tu acceso a {{product}} expira mañana.</p>

<a href="{{upgrade_url}}" style="background: #FF6B6B; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: bold;">
  Activar Ahora →
</a>
            """,
            "variables": ["product", "upgrade_url"],
            "send_delay_minutes": 0,  # Sent 1 day before expiry
        }


class TemplateLibrary:
    """Complete template library with categorization"""

    @staticmethod
    def get_all_templates() -> Dict[str, List[Dict[str, Any]]]:
        return {
            "cart_abandonment": [
                CartAbandonmentTemplates.email_1_immediate(),
                CartAbandonmentTemplates.email_2_social_proof(),
                CartAbandonmentTemplates.email_3_final_discount(),
                CartAbandonmentTemplates.sms_final_push(),
            ],
            "flash_sale": [
                FlashSaleTemplates.email_launch(),
                FlashSaleTemplates.email_reminder_4h(),
                FlashSaleTemplates.sms_1h_warning(),
                FlashSaleTemplates.sms_30min_final(),
            ],
            "post_purchase": [
                PostPurchaseTemplates.email_thank_you(),
                PostPurchaseTemplates.email_product_recommendation(),
            ],
            "trial_expiry": [
                TrialExpiryTemplates.email_7day_warning(),
                TrialExpiryTemplates.email_1day_final(),
            ],
        }

    @staticmethod
    def get_template_by_id(template_id: str) -> Dict[str, Any]:
        """Fetch template by ID"""
        all_templates = TemplateLibrary.get_all_templates()
        for category, templates in all_templates.items():
            for template in templates:
                if template.get("id") == template_id:
                    return template
        return {}

    @staticmethod
    def get_templates_by_category(category: str) -> List[Dict[str, Any]]:
        """Get all templates in category"""
        all_templates = TemplateLibrary.get_all_templates()
        return all_templates.get(category, [])
