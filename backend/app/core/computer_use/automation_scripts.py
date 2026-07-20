"""Automation scripts — Computer Use + browser = controla cualquier plataforma."""

from typing import Dict, List, Any


class AutomationScripts:
    """Scripts para cada plataforma."""

    @staticmethod
    def mercadolibre_create_listing(product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script: MercadoLibre listar producto."""
        return [
            {"type": "navigate", "params": {"url": "https://www.mercadolibre.com.ar"}},
            {"type": "wait", "params": {"selector": "a[href*='vender']"}},
            {"type": "click", "params": {"selector": "a[href*='vender']"}},
            {"type": "wait", "params": {"selector": "input[name='titulo']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='titulo']": product.get("name"),
                "input[name='precio']": str(product.get("price")),
                "textarea[name='descripcion']": product.get("description"),
                "input[name='cantidad']": str(product.get("stock", 1)),
            }}},
            {"type": "click", "params": {"selector": "button[type='submit']"}},
            {"type": "wait", "params": {"selector": "div[class*='success']", "timeout": 5000}},
            {"type": "screenshot", "params": {"filename": "mercadolibre_listing.png"}},
        ]

    @staticmethod
    def shopify_create_product(product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script: Shopify crear producto."""
        return [
            {"type": "navigate", "params": {"url": "https://admin.shopify.com/products"}},
            {"type": "wait", "params": {"selector": "button:has-text('Add product')"}},
            {"type": "click", "params": {"selector": "button:has-text('Add product')"}},
            {"type": "wait", "params": {"selector": "input[name='title']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[name='title']": product.get("name"),
                "input[name='price']": str(product.get("price")),
                "textarea": product.get("description"),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Save')"}},
        ]

    @staticmethod
    def meta_ads_create_campaign(campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script: Meta Ads crear campaña."""
        return [
            {"type": "navigate", "params": {"url": "https://ads.facebook.com"}},
            {"type": "wait", "params": {"selector": "button:has-text('Create')"}},
            {"type": "click", "params": {"selector": "button:has-text('Create')"}},
            {"type": "click", "params": {"selector": "button:has-text('Campaign')"}},
            {"type": "wait", "params": {"selector": "input[placeholder*='campaign name']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='campaign name']": campaign.get("name"),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Continue')"}},
            {"type": "screenshot", "params": {"filename": "meta_campaign.png"}},
        ]

    @staticmethod
    def generic_fill_and_submit(form_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script genérico: llenar formulario cualquier sitio + submit."""
        script = [
            {"type": "navigate", "params": {"url": form_config.get("url")}},
            {"type": "wait", "params": {"selector": form_config.get("wait_selector", "form")}},
        ]

        # Llenar campos
        fields = form_config.get("fields", {})
        if fields:
            script.append({"type": "fill_form", "params": {"fields": fields}})

        # Submit
        script.append({"type": "click", "params": {"selector": form_config.get("submit_selector", "button[type='submit']")}})

        return script

    @staticmethod
    def google_ads_create_campaign(campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script: Google Ads crear campaña."""
        return [
            {"type": "navigate", "params": {"url": "https://ads.google.com"}},
            {"type": "wait", "params": {"selector": "button:has-text('+ New campaign')"}},
            {"type": "click", "params": {"selector": "button:has-text('+ New campaign')"}},
            {"type": "wait", "params": {"selector": "input[placeholder*='Campaign name']"}},
            {"type": "fill_form", "params": {"fields": {
                "input[placeholder*='Campaign name']": campaign.get("name"),
                "input[type='number']": str(campaign.get("budget", 100)),
            }}},
        ]

    @staticmethod
    def instagram_schedule_post(post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Script: Instagram programar post."""
        return [
            {"type": "navigate", "params": {"url": "https://instagram.com"}},
            {"type": "click", "params": {"selector": "button[aria-label='Create']"}},
            {"type": "wait", "params": {"selector": "input[type='file']"}},
            {"type": "click", "params": {"selector": "input[type='file']"}},
            # Nota: upload de archivo requiere input type=file
            {"type": "fill_form", "params": {"fields": {
                "textarea[placeholder*='caption']": post.get("caption", ""),
            }}},
            {"type": "click", "params": {"selector": "button:has-text('Schedule')"}},
        ]
