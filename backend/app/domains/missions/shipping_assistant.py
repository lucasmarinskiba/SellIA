"""SellIA Missions — Shipping Connector Assistant

Módulo de lógica pura para recomendaciones de logística, carriers,
cotizaciones estimadas y requisitos cross-border.
"""

from typing import List, Dict, Any, Optional


# ─── Datos de carriers ─────────────────────────────────────────────────────────

CARRIER_DATA = {
    "andreani": {
        "name": "Andreani",
        "coverage": ["AR"],
        "reach": "national",
        "product_types": ["general", "fashion", "electronics", "books"],
        "integration_difficulty": "medium",
        "avg_delivery_days": {"national": 3, "international": None},
        "pricing_tier": "mid",
        "website": "https://andreani.com",
        "api_available": True,
    },
    "oca": {
        "name": "OCA",
        "coverage": ["AR"],
        "reach": "national",
        "product_types": ["general", "documents", "fashion", "home"],
        "integration_difficulty": "medium",
        "avg_delivery_days": {"national": 4, "international": None},
        "pricing_tier": "low",
        "website": "https://oca.com.ar",
        "api_available": True,
    },
    "correo_argentino": {
        "name": "Correo Argentino",
        "coverage": ["AR"],
        "reach": "national",
        "product_types": ["general", "documents", "small_parcels"],
        "integration_difficulty": "easy",
        "avg_delivery_days": {"national": 5, "international": 14},
        "pricing_tier": "low",
        "website": "https://correoargentino.com.ar",
        "api_available": False,
    },
    "dhl": {
        "name": "DHL Express",
        "coverage": ["AR", "BR", "CL", "UY", "MX", "CO", "PE", "US", "ES", "GB", "DE"],
        "reach": "international",
        "product_types": ["general", "electronics", "high_value", "documents"],
        "integration_difficulty": "hard",
        "avg_delivery_days": {"national": 2, "international": 5},
        "pricing_tier": "premium",
        "website": "https://dhl.com",
        "api_available": True,
    },
    "fedex": {
        "name": "FedEx",
        "coverage": ["AR", "BR", "CL", "UY", "MX", "CO", "PE", "US", "ES", "GB", "DE"],
        "reach": "international",
        "product_types": ["general", "electronics", "high_value", "fashion"],
        "integration_difficulty": "hard",
        "avg_delivery_days": {"national": 2, "international": 5},
        "pricing_tier": "premium",
        "website": "https://fedex.com",
        "api_available": True,
    },
    "ups": {
        "name": "UPS",
        "coverage": ["AR", "BR", "CL", "UY", "MX", "CO", "PE", "US", "ES", "GB", "DE"],
        "reach": "international",
        "product_types": ["general", "electronics", "high_value", "industrial"],
        "integration_difficulty": "hard",
        "avg_delivery_days": {"national": 2, "international": 5},
        "pricing_tier": "premium",
        "website": "https://ups.com",
        "api_available": True,
    },
}

# ─── Tarifas estimadas (ARS por kg, aproximado) ────────────────────────────────

PRICING_TIERS = {
    "low": {"base_cost_per_kg": 800, "base_cost_min": 1200},
    "mid": {"base_cost_per_kg": 1400, "base_cost_min": 2000},
    "premium": {"base_cost_per_kg": 3500, "base_cost_min": 5000},
}

# ─── Requisitos cross-border ───────────────────────────────────────────────────

CROSS_BORDER_REQUIREMENTS = {
    "BR": {
        "country_name": "Brasil",
        "language": "Portugués",
        "currency": "BRL",
        "customs_duties_pct": 60,
        "icms_tax_pct": 17,
        "required_docs": ["Factura comercial", "Certificado de origen", "DNI del destinatario (CPF)"],
        "restrictions": ["Sin envío de electrónica por correo común", "Límite de envío simplificado: USD 50"],
        "recommended_carriers": ["dhl", "fedex"],
        "estimated_clearance_days": 5,
    },
    "CL": {
        "country_name": "Chile",
        "language": "Español",
        "currency": "CLP",
        "customs_duties_pct": 6,
        "icms_tax_pct": 0,
        "required_docs": ["Factura comercial", "Certificado de origen"],
        "restrictions": ["Mercosur: exención parcial de aranceles para productos originarios"],
        "recommended_carriers": ["dhl", "fedex", "andreani"],
        "estimated_clearance_days": 3,
    },
    "UY": {
        "country_name": "Uruguay",
        "language": "Español",
        "currency": "UYU",
        "customs_duties_pct": 0,
        "icms_tax_pct": 0,
        "required_docs": ["Factura comercial"],
        "restrictions": ["Mercosur: libre comercio para productos originarios"],
        "recommended_carriers": ["andreani", "oca", "correo_argentino"],
        "estimated_clearance_days": 2,
    },
    "MX": {
        "country_name": "México",
        "language": "Español",
        "currency": "MXN",
        "customs_duties_pct": 0,
        "icms_tax_pct": 16,
        "required_docs": ["Factura comercial", "Certificado de origen", "RFC del destinatario"],
        "restrictions": ["TLC con México facilita importación de productos originarios"],
        "recommended_carriers": ["dhl", "fedex", "ups"],
        "estimated_clearance_days": 4,
    },
    "US": {
        "country_name": "Estados Unidos",
        "language": "Inglés",
        "currency": "USD",
        "customs_duties_pct": 0,
        "icms_tax_pct": 0,
        "required_docs": ["Factura comercial", "EIN o SSN del destinatario (si aplica)"],
        "restrictions": ["De minimis: exento hasta USD 800 por envío"],
        "recommended_carriers": ["dhl", "fedex", "ups"],
        "estimated_clearance_days": 2,
    },
    "ES": {
        "country_name": "España",
        "language": "Español",
        "currency": "EUR",
        "customs_duties_pct": 0,
        "icms_tax_pct": 21,
        "required_docs": ["Factura comercial", "EORI del destinatario"],
        "restrictions": ["IVA aplica sobre valor CIF + flete", "Mercosur-EU: aranceles reducidos"],
        "recommended_carriers": ["dhl", "ups"],
        "estimated_clearance_days": 3,
    },
}

# ─── Pasos de configuración por carrier ────────────────────────────────────────

CARRIER_SETUP_STEPS = {
    "andreani": [
        {"step": 1, "title": "Crear cuenta en Andreani", "description": "Registrarse en andreani.com con CUIT y datos fiscales.", "estimated_minutes": 15},
        {"step": 2, "title": "Validar identidad comercial", "description": "Subir constancia de inscripción en AFIP y comprobante de domicilio.", "estimated_minutes": 10},
        {"step": 3, "title": "Solicitar API Key", "description": "Enviar solicitud de integración API al equipo comercial de Andreani.", "estimated_minutes": 5},
        {"step": 4, "title": "Configurar cotizador", "description": "Definir zonas de envío (CABA, GBA, Interior) y tipos de servicio.", "estimated_minutes": 20},
        {"step": 5, "title": "Integrar con Shopify/ML", "description": "Instalar app de Andreani o conectar vía API al e-commerce.", "estimated_minutes": 30},
        {"step": 6, "title": "Test de envío", "description": "Generar etiqueta de prueba y rastrear un envío de prueba.", "estimated_minutes": 10},
    ],
    "dhl": [
        {"step": 1, "title": "Crear cuenta DHL Express", "description": "Registrarse en dhl.com/express como business account.", "estimated_minutes": 20},
        {"step": 2, "title": "Verificación KYC", "description": "Validar identidad fiscal y propósito del envío internacional.", "estimated_minutes": 30},
        {"step": 3, "title": "Solicitar cuenta API MyDHL", "description": "Solicitar acceso a MyDHL API para integración automatizada.", "estimated_minutes": 10},
        {"step": 4, "title": "Configurar preferencias de envío", "description": "Definir incoterms (DDP/DDU), seguro y embalaje estándar.", "estimated_minutes": 20},
        {"step": 5, "title": "Integrar con plataforma", "description": "Conectar DHL API vía plugin o custom integration.", "estimated_minutes": 45},
        {"step": 6, "title": "Declaración aduanera", "description": "Configurar HS codes por producto para despacho automático.", "estimated_minutes": 30},
    ],
    "fedex": [
        {"step": 1, "title": "Crear cuenta FedEx", "description": "Registrarse en fedex.com como business account.", "estimated_minutes": 20},
        {"step": 2, "title": "Verificación comercial", "description": "Validar datos fiscales y volumen estimado de envíos mensuales.", "estimated_minutes": 25},
        {"step": 3, "title": "Solicitar FedEx Developer Portal", "description": "Crear app en FedEx Developer para obtener API keys.", "estimated_minutes": 15},
        {"step": 4, "title": "Configurar servicios", "description": "Seleccionar servicios (International Priority, Economy, etc.).", "estimated_minutes": 20},
        {"step": 5, "title": "Integrar FedEx Ship Manager", "description": "Conectar vía FedEx Web Services o plugin de e-commerce.", "estimated_minutes": 40},
        {"step": 6, "title": "Test internacional", "description": "Simular envío internacional con documentación completa.", "estimated_minutes": 20},
    ],
    "ups": [
        {"step": 1, "title": "Crear cuenta UPS", "description": "Registrarse en ups.com como shipper business.", "estimated_minutes": 20},
        {"step": 2, "title": "Verificación fiscal", "description": "Validar CUIT/empresa para habilitar envíos internacionales.", "estimated_minutes": 25},
        {"step": 3, "title": "Solicitar UPS Developer Kit", "description": "Solicitar acceso a UPS API (XML/REST) para rate & ship.", "estimated_minutes": 15},
        {"step": 4, "title": "Configurar preferencias", "description": "Definir tipos de servicio, seguro y opciones de notificación.", "estimated_minutes": 20},
        {"step": 5, "title": "Integrar con e-commerce", "description": "Conectar UPS API o usar plugin oficial de Shopify/WooCommerce.", "estimated_minutes": 40},
        {"step": 6, "title": "Prueba de envío", "description": "Generar etiqueta de prueba y rastrear paquete de test.", "estimated_minutes": 15},
    ],
    "oca": [
        {"step": 1, "title": "Crear cuenta OCA", "description": "Registrarse en oca.com.ar con datos fiscales.", "estimated_minutes": 15},
        {"step": 2, "title": "Validar cuenta", "description": "Confirmar email y teléfono comercial.", "estimated_minutes": 10},
        {"step": 3, "title": "Solicitar integración API", "description": "Contactar a soporte de OCA para obtener credenciales de API.", "estimated_minutes": 10},
        {"step": 4, "title": "Configurar cotizador", "description": "Definir CPs de origen, destino y modalidades de entrega.", "estimated_minutes": 20},
        {"step": 5, "title": "Integrar con tienda", "description": "Instalar módulo de OCA o conectar vía API REST.", "estimated_minutes": 30},
        {"step": 6, "title": "Test de envío", "description": "Generar etiqueta y rastrear paquete de prueba.", "estimated_minutes": 10},
    ],
    "correo_argentino": [
        {"step": 1, "title": "Crear cuenta en Correo Argentino", "description": "Registrarse en correoargentino.com.ar como usuario Mi Correo.", "estimated_minutes": 15},
        {"step": 2, "title": "Verificar identidad", "description": "Validar CUIT/DNI vía trámite online o presencial.", "estimated_minutes": 20},
        {"step": 3, "title": "Solicitar Mercado Envíos (si aplica)", "description": "Para integración automática, usar Mercado Envíos con Correo Argentino.", "estimated_minutes": 10},
        {"step": 4, "title": "Configurar envíos", "description": "Definir tipos de envío (a domicilio, sucursal, internacional).", "estimated_minutes": 15},
        {"step": 5, "title": "Imprimir etiquetas manuales o auto", "description": "Configurar impresión de etiquetas o usar integración con plataforma.", "estimated_minutes": 10},
        {"step": 6, "title": "Test de envío", "description": "Realizar envío de prueba y rastreo.", "estimated_minutes": 10},
    ],
}


class ShippingConnectorAssistant:
    """Asistente de recomendaciones y configuración de carriers de envío."""

    def get_carrier_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recomendar carriers según país, alcance y tipo de producto.

        Args:
            context: dict con keys opcionales: country (str), reach (str),
                     product_type (str), volume_monthly (int).
        """
        country = context.get("country", "AR").upper()
        reach = context.get("reach", "national")  # national | international
        product_type = context.get("product_type", "general")
        volume = context.get("volume_monthly", 0)

        recommendations = []
        for slug, data in CARRIER_DATA.items():
            score = 0
            reasons = []

            # Cobertura país
            if country in data["coverage"]:
                score += 3
                reasons.append(f"Cubre {country}")
            else:
                # Si no cubre el país directamente, solo internacional
                if reach == "international" and data["reach"] == "international":
                    score += 1
                    reasons.append("Envío internacional disponible")
                else:
                    continue

            # Alcance requerido
            if reach == data["reach"]:
                score += 2
                reasons.append(f"Alcance {reach}")
            elif reach == "international" and data["reach"] == "international":
                score += 2
                reasons.append("Alcance internacional")

            # Tipo de producto
            if product_type in data["product_types"]:
                score += 2
                reasons.append(f"Apto para {product_type}")
            elif "general" in data["product_types"]:
                score += 1
                reasons.append("Apto para productos generales")

            # Volumen → premium carriers para alto volumen
            if volume > 500 and data["pricing_tier"] == "premium":
                score += 1
                reasons.append("Descuento por volumen probable")

            recommendations.append({
                "carrier_slug": slug,
                "carrier_name": data["name"],
                "score": score,
                "reasons": reasons,
                "integration_difficulty": data["integration_difficulty"],
                "avg_delivery_days": data["avg_delivery_days"].get(reach),
                "pricing_tier": data["pricing_tier"],
                "api_available": data["api_available"],
                "website": data["website"],
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    def generate_setup_steps(self, carrier: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Devolver paso a paso para configurar un carrier específico.

        Args:
            carrier: slug del carrier (andreani, dhl, fedex, ups, oca, correo_argentino).
            context: contexto adicional (no requerido para steps base).
        """
        carrier = carrier.lower()
        steps = CARRIER_SETUP_STEPS.get(carrier, [])
        data = CARRIER_DATA.get(carrier, {})

        if not steps:
            return {
                "carrier": carrier,
                "status": "error",
                "message": f"No hay pasos de configuración para '{carrier}'.",
                "steps": [],
                "total_estimated_minutes": 0,
            }

        total_minutes = sum(s["estimated_minutes"] for s in steps)
        return {
            "carrier": carrier,
            "carrier_name": data.get("name", carrier),
            "status": "ok",
            "integration_difficulty": data.get("integration_difficulty"),
            "api_available": data.get("api_available"),
            "website": data.get("website"),
            "steps": steps,
            "total_estimated_minutes": total_minutes,
            "context": context or {},
        }

    def estimate_shipping_costs(
        self,
        origin: str,
        destination: str,
        weight_kg: float,
        dimensions: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Estimar costos de envío por carrier.

        Args:
            origin: código de país de origen (ej: AR).
            destination: código de país de destino (ej: BR).
            weight_kg: peso en kilogramos.
            dimensions: dict opcional con {length_cm, width_cm, height_cm}.
        """
        origin = origin.upper()
        destination = destination.upper()
        is_international = origin != destination
        reach = "international" if is_international else "national"

        # Factor volumétrico simplificado
        volumetric_weight = weight_kg
        if dimensions:
            l = dimensions.get("length_cm", 0)
            w = dimensions.get("width_cm", 0)
            h = dimensions.get("height_cm", 0)
            volumetric_weight = max(weight_kg, (l * w * h) / 5000)

        estimates = []
        for slug, data in CARRIER_DATA.items():
            if destination not in data["coverage"] and is_international:
                # Si es internacional y el carrier no cubre destino, solo carriers internacionales
                if data["reach"] != "international":
                    continue

            tier = data["pricing_tier"]
            pricing = PRICING_TIERS.get(tier, PRICING_TIERS["mid"])

            base = pricing["base_cost_min"]
            per_kg = pricing["base_cost_per_kg"]
            cost = base + (per_kg * volumetric_weight)

            # Ajuste internacional
            if is_international:
                cost *= 2.5

            # Ajuste por volumen (estimado)
            if dimensions and (dimensions.get("length_cm", 0) > 100 or volumetric_weight > 20):
                cost *= 1.3

            estimates.append({
                "carrier_slug": slug,
                "carrier_name": data["name"],
                "estimated_cost_ars": round(cost, 2),
                "currency": "ARS",
                "estimated_delivery_days": data["avg_delivery_days"].get(reach),
                "reach": reach,
                "weight_used_kg": round(volumetric_weight, 2),
            })

        estimates.sort(key=lambda x: x["estimated_cost_ars"])
        return {
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "dimensions": dimensions,
            "estimates": estimates,
        }

    def get_cross_border_requirements(self, target_country: str) -> Dict[str, Any]:
        """Obtener requisitos aduaneros, fiscales y documentación para un país destino.

        Args:
            target_country: código ISO de 2 letras del país destino.
        """
        target_country = target_country.upper()
        data = CROSS_BORDER_REQUIREMENTS.get(target_country)

        if not data:
            return {
                "country": target_country,
                "status": "unknown",
                "message": f"No hay datos cross-border para '{target_country}'.",
                "requirements": {},
            }

        return {
            "country": target_country,
            "country_name": data["country_name"],
            "status": "ok",
            "language": data["language"],
            "currency": data["currency"],
            "customs_duties_pct": data["customs_duties_pct"],
            "local_tax_pct": data["icms_tax_pct"],
            "required_docs": data["required_docs"],
            "restrictions": data["restrictions"],
            "recommended_carriers": data["recommended_carriers"],
            "estimated_clearance_days": data["estimated_clearance_days"],
        }
