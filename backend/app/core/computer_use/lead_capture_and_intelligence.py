"""
Lead Capture & Intelligence Integration — Extrae y enriquece leads automáticamente.

Sistema captura leads estructurados de múltiples fuentes:
1. Formularios web (contact, demo, newsletter, waitlist)
2. Directorios (LinkedIn, Google Maps, Yellow Pages, industry databases)
3. Mensajes (WhatsApp, Facebook Messenger, email)
4. Comportamiento web (visitantes sin identificar)
5. Social media (Instagram, TikTok, LinkedIn comments)

Después enriquece con:
- Email finder (Hunter.io, Clearbit, RocketReach)
- Verificación de email
- Social media profiles
- Datos empresariales (industria, tamaño, revenue)
- Historial de compra
- Intent signals (herramientas como Clearbit, 6sense)

Resultado: Lead 360° listo para sales/marketing.
"""

import logging
import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class WebFormData:
    """Datos extraídos de formulario web."""
    form_url: str
    form_name: str
    fields: Dict[str, str]  # {"email": "user@example.com", "name": "John"}
    submission_time: datetime = field(default_factory=datetime.utcnow)
    success: bool = False


@dataclass
class LeadScore:
    """Score de calidad y potencial del lead."""
    overall_score: float  # 0-100
    data_completeness: float  # % de campos
    email_verified: bool
    phone_verified: bool
    budget_range: Optional[str] = None  # "5k-10k", "10k-50k", etc
    intent_level: str = "unknown"  # "high", "medium", "low"
    engagement_score: float = 0.0
    conversion_probability: float = 0.0  # ML prediction


@dataclass
class EnrichedLead:
    """Lead enriquecido con datos adicionales."""
    # Core data
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None

    # Company data
    company_size: Optional[str] = None  # "1-10", "11-50", "51-200", etc
    industry: Optional[str] = None
    company_website: Optional[str] = None
    annual_revenue: Optional[str] = None
    company_linkedin: Optional[str] = None

    # Social profiles
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None

    # Behavior & intent
    sources: List[str] = field(default_factory=list)  # ["web_form", "linkedin", etc]
    interests: List[str] = field(default_factory=list)
    budget_range: Optional[str] = None
    timeline: Optional[str] = None

    # Quality metrics
    score: LeadScore = field(default_factory=lambda: LeadScore(
        overall_score=0.0,
        data_completeness=0.0,
        email_verified=False,
        phone_verified=False,
    ))

    # Timestamps
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    enriched_at: Optional[datetime] = None


# ============================================================================
# WEB FORM AUTOMATION
# ============================================================================

class WebFormFiller:
    """Automatiza llenado de formularios web."""

    def __init__(self, browser_utils):
        """Inicializa form filler."""
        self.browser_utils = browser_utils
        self.form_submissions: List[WebFormData] = []

    async def fill_and_submit_form(
        self,
        form_url: str,
        form_data: Dict[str, str],
        form_name: str = "unnamed_form",
    ) -> bool:
        """
        Navega a formulario, rellena y envía.

        Ejemplo:
            form_data = {
                "first_name": "Juan",
                "email": "juan@example.com",
                "phone": "+34 123 456 789",
                "company": "Mi Empresa",
                "message": "Estoy interesado en vuestros servicios",
            }
        """
        try:
            logger.info(f"Filling form: {form_name} at {form_url}")

            # 1. Navega a formulario
            await self.browser_utils.screenshot_and_analyze()
            # await computer_use.navigate(form_url)

            # 2. Espera formulario cargue
            await self.browser_utils.wait_for_element("Form or Input field", timeout=10)

            # 3. Detecta campos automáticamente
            screenshot = await self.browser_utils.screenshot_and_analyze()
            detected_fields = self._detect_form_fields(screenshot)

            logger.info(f"Detected fields: {list(detected_fields.keys())}")

            # 4. Rellena campos detectados
            for field_name, field_value in form_data.items():
                if field_name in detected_fields:
                    # Busca campo por nombre/label
                    await self.browser_utils.type_in_field(field_name, field_value)
                    logger.info(f"Filled {field_name}")

            # 5. Busca y clickea botón submit
            submit_buttons = ["submit", "send", "confirm", "enviar", "continue"]
            submitted = False

            for btn_text in submit_buttons:
                if await self.browser_utils.click_by_vision(f"{btn_text} button"):
                    submitted = True
                    break

            if not submitted:
                logger.warning("Could not find submit button")
                return False

            # 6. Espera confirmación
            await self.browser_utils.wait_for_element(
                "Success message or Thank you page",
                timeout=10,
            )

            # 7. Log submission
            self.form_submissions.append(WebFormData(
                form_url=form_url,
                form_name=form_name,
                fields=form_data,
                success=True,
            ))

            logger.info(f"Form submitted successfully: {form_name}")
            return True

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            self.form_submissions.append(WebFormData(
                form_url=form_url,
                form_name=form_name,
                fields=form_data,
                success=False,
            ))
            return False

    def _detect_form_fields(self, screenshot: Dict[str, Any]) -> Dict[str, str]:
        """
        Detecta campos en formulario usando visión.

        Retorna: {"email": "email_input_id", "name": "name_field", ...}
        """
        # En producción, usaría Claude Vision para detectar campos
        # Por ahora, retorna mapping genérico

        fields = {
            "email": "email",
            "first_name": "name",
            "last_name": "surname",
            "phone": "phone",
            "company": "company",
            "message": "message",
            "subject": "subject",
        }

        return fields

    async def auto_fill_common_forms(
        self,
        urls: List[str],
        lead_data: Dict[str, str],
    ) -> List[bool]:
        """
        Rellena múltiples formularios automáticamente.

        Útil para: registrarse en múltiples plataformas, leadgen, etc.
        """
        results = []

        for url in urls:
            success = await self.fill_and_submit_form(
                form_url=url,
                form_data=lead_data,
                form_name=url.split("/")[-1],
            )
            results.append(success)

        return results


# ============================================================================
# LEAD SCRAPING FROM DIRECTORIES
# ============================================================================

class DirectoryScraper:
    """
    Scrape de directorios (LinkedIn, Google Maps, Yellow Pages, industry databases).

    NO VIOLA ToS si se respeta robots.txt y rate limiting.
    """

    def __init__(self, browser_utils):
        """Inicializa scraper."""
        self.browser_utils = browser_utils
        self.scraped_leads: List[EnrichedLead] = []

    async def scrape_google_maps(
        self,
        query: str,
        location: str,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Scrape de Google Maps — extrae nombres, teléfonos, direcciones de negocios.

        Ejemplo:
            query = "Real estate agents"
            location = "San Francisco, CA"
            Retorna: [
                {"name": "John Smith Real Estate", "phone": "+1 123 456 7890", ...},
                ...
            ]
        """
        try:
            logger.info(f"Scraping Google Maps: {query} in {location}")

            # 1. Navega a Google Maps
            await self.browser_utils.screenshot_and_analyze()
            # await computer_use.navigate("https://maps.google.com")

            # 2. Busca
            await self.browser_utils.type_in_field("Search field", f"{query} {location}")
            await self.browser_utils.click_by_vision("Search button or Enter key")

            # 3. Espera resultados
            await self.browser_utils.wait_for_element("Search results or Business listings", timeout=15)

            # 4. Scrape resultados
            businesses = []

            for i in range(min(max_results, 50)):
                try:
                    # Click en listado
                    await self.browser_utils.click_by_vision(f"Business listing {i+1}")

                    # Extrae info
                    screenshot = await self.browser_utils.screenshot_and_analyze()

                    business = self._parse_business_info(screenshot)
                    if business:
                        businesses.append(business)

                    # Rate limiting
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"Error scraping business {i+1}: {str(e)}")

            logger.info(f"Scraped {len(businesses)} businesses from Google Maps")
            return businesses

        except Exception as e:
            logger.error(f"Error scraping Google Maps: {str(e)}")
            return []

    def _parse_business_info(self, screenshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae info de negocio de screenshot."""
        # En producción, usaría Claude Vision
        return {
            "name": None,
            "phone": None,
            "email": None,
            "address": None,
            "website": None,
            "rating": None,
        }

    async def scrape_yellow_pages(
        self,
        business_type: str,
        location: str,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """Scrape Yellow Pages (US) para contactos de negocios."""
        try:
            logger.info(f"Scraping Yellow Pages: {business_type} in {location}")

            # Similar a Google Maps
            # Navega → busca → scrape resultados

            return []

        except Exception as e:
            logger.error(f"Error scraping Yellow Pages: {str(e)}")
            return []

    async def scrape_linkedin_search(
        self,
        search_query: str,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Scrape de búsqueda LinkedIn — perfiles de personas.

        Búsquedas soportadas:
        - Por rol: "Sales Manager"
        - Por industria: "Technology"
        - Por empresa: "Apple"
        - Por ubicación: "San Francisco"

        NOTA: LinkedIn tiene protecciones contra scraping. Usar API oficial es preferible.
        """
        try:
            logger.info(f"Scraping LinkedIn: {search_query}")

            # 1. Navega a LinkedIn
            await self.browser_utils.screenshot_and_analyze()

            # 2. Busca
            await self.browser_utils.type_in_field("Search field", search_query)
            await self.browser_utils.click_by_vision("Search or People tab")

            # 3. Espera resultados
            await self.browser_utils.wait_for_element("Search results", timeout=10)

            # 4. Scrape perfiles
            profiles = []

            for i in range(min(max_results, 50)):
                try:
                    # Click perfil
                    await self.browser_utils.click_by_vision(f"Profile {i+1}")

                    # Extrae datos
                    screenshot = await self.browser_utils.screenshot_and_analyze()

                    profile = self._parse_linkedin_profile(screenshot)
                    if profile:
                        profiles.append(profile)

                    # Rate limiting
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.warning(f"Error scraping profile {i+1}: {str(e)}")

            logger.info(f"Scraped {len(profiles)} LinkedIn profiles")
            return profiles

        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {str(e)}")
            return []

    def _parse_linkedin_profile(self, screenshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae datos de perfil LinkedIn."""
        return {
            "name": None,
            "headline": None,
            "location": None,
            "current_company": None,
            "job_title": None,
            "email": None,  # LinkedIn oculta emails
        }


# ============================================================================
# LEAD EXTRACTION FROM MESSAGES
# ============================================================================

class MessageLeadExtractor:
    """Extrae datos de leads de mensajes (WhatsApp, Messenger, email)."""

    @staticmethod
    def extract_from_message(message_text: str) -> Dict[str, Any]:
        """
        Extrae nombre, email, teléfono, información de mensaje.

        Ejemplo:
            "Hola, me llamo Juan García. Mi email es juan@example.com
             y teléfono +34 123 456 789. Estoy interesado en vuestros servicios."

        Retorna: {
            "name": "Juan García",
            "email": "juan@example.com",
            "phone": "+34 123 456 789",
            "interests": ["services"],
        }
        """
        extracted = {
            "name": None,
            "email": None,
            "phone": None,
            "interests": [],
        }

        # Extrae email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(email_pattern, message_text)
        if emails:
            extracted["email"] = emails[0]

        # Extrae teléfono
        phone_pattern = r'[\+]?[\d\s\-\(\)]{10,}'
        phones = re.findall(phone_pattern, message_text)
        if phones:
            extracted["phone"] = phones[0]

        # Extrae nombre (primera palabra + segunda palabra si existen)
        words = message_text.split()
        if len(words) >= 2:
            # Busca patrón "Me llamo X" o similar
            for i, word in enumerate(words):
                if word.lower() in ["llamo", "name", "soy"]:
                    if i + 1 < len(words):
                        name_parts = []
                        for j in range(i + 1, min(i + 3, len(words))):
                            if words[j][0].isupper():
                                name_parts.append(words[j])
                        if name_parts:
                            extracted["name"] = " ".join(name_parts)
                        break

        return extracted

    @staticmethod
    def extract_from_email(email_subject: str, email_body: str) -> Dict[str, Any]:
        """Extrae información de email."""
        text = f"{email_subject}\n{email_body}"
        return MessageLeadExtractor.extract_from_message(text)


# ============================================================================
# LEAD ENRICHMENT
# ============================================================================

class LeadEnricher:
    """Enriquece leads con datos de terceros."""

    def __init__(self):
        """Inicializa enricher."""
        self.api_keys = {}  # En producción, cargar de vault

    async def enrich_lead(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        company: Optional[str] = None,
    ) -> EnrichedLead:
        """
        Enriquece lead usando múltiples APIs de terceros.

        Servicios soportados:
        - Hunter.io — email finder
        - Clearbit — company & person data
        - RocketReach — B2B contacts
        - ZoomInfo — enterprise data
        - Apollo.io — email & phone verification
        """
        try:
            logger.info(f"Enriching lead: {email or phone or name}")

            lead = EnrichedLead(
                email=email or "",
                first_name=name.split()[0] if name else None,
                last_name=name.split()[1] if name and len(name.split()) > 1 else None,
                phone=phone,
                company=company,
            )

            # 1. Busca email si falta
            if not email and name and company:
                email = await self._find_email_hunter(name, company)
                lead.email = email

            # 2. Verifica email
            if email:
                is_valid = await self._verify_email(email)
                lead.score.email_verified = is_valid

            # 3. Enriquece datos de empresa
            if company:
                company_data = await self._get_company_data_clearbit(company)
                if company_data:
                    lead.company_website = company_data.get("website")
                    lead.industry = company_data.get("industry")
                    lead.company_size = company_data.get("size")

            # 4. Enriquece datos personales
            if email:
                person_data = await self._get_person_data_clearbit(email)
                if person_data:
                    lead.linkedin_url = person_data.get("linkedin")
                    lead.job_title = person_data.get("title")
                    lead.location = person_data.get("location")

            # 5. Calcula score
            lead.score = self._calculate_lead_score(lead)
            lead.enriched_at = datetime.utcnow()

            logger.info(f"Lead enriched. Score: {lead.score.overall_score:.0f}")
            return lead

        except Exception as e:
            logger.error(f"Error enriching lead: {str(e)}")
            return EnrichedLead(email=email or "")

    async def _find_email_hunter(self, name: str, company: str) -> Optional[str]:
        """Busca email usando Hunter.io API."""
        try:
            # En producción: llamar a API Hunter
            # response = await http_client.get(
            #     "https://api.hunter.io/v2/email-finder",
            #     params={
            #         "domain": company.lower().replace(" ", "") + ".com",
            #         "first_name": name.split()[0],
            #         "last_name": name.split()[1] if len(name.split()) > 1 else "",
            #         "api_key": self.api_keys.get("hunter"),
            #     }
            # )
            # data = response.json()
            # return data.get("data", {}).get("email")

            return None
        except Exception as e:
            logger.warning(f"Error finding email: {str(e)}")
            return None

    async def _verify_email(self, email: str) -> bool:
        """Verifica que email sea válido."""
        try:
            # Validación básica
            if not re.match(r'[\w\.-]+@[\w\.-]+\.\w+', email):
                return False

            # En producción: usar servicio de verificación (Apollo, ZeroBounce, etc)
            return True

        except Exception as e:
            logger.warning(f"Error verifying email: {str(e)}")
            return False

    async def _get_company_data_clearbit(self, company: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de empresa de Clearbit."""
        try:
            # En producción: llamar a API Clearbit
            # response = await http_client.get(
            #     "https://company-api.clearbit.com/v1/domains/find",
            #     params={"name": company},
            #     headers={"Authorization": f"Bearer {self.api_keys.get('clearbit')}"},
            # )
            # return response.json()

            return None
        except Exception as e:
            logger.warning(f"Error getting company data: {str(e)}")
            return None

    async def _get_person_data_clearbit(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos personales de Clearbit."""
        try:
            # En producción: llamar a API Clearbit
            # response = await http_client.get(
            #     "https://person-api.clearbit.com/v2/combined/find",
            #     params={"email": email},
            #     headers={"Authorization": f"Bearer {self.api_keys.get('clearbit')}"},
            # )
            # return response.json().get("person")

            return None
        except Exception as e:
            logger.warning(f"Error getting person data: {str(e)}")
            return None

    def _calculate_lead_score(self, lead: EnrichedLead) -> LeadScore:
        """
        Calcula score de lead (0-100).

        Factores:
        - Completitud de datos (email, name, company, phone)
        - Verificación de email
        - Intent signals
        - Engagement
        """
        score = 0.0
        weights = {}

        # Completitud (40%)
        fields_filled = sum([
            lead.email != "",
            lead.first_name is not None,
            lead.phone is not None,
            lead.company is not None,
            lead.job_title is not None,
        ])
        completeness = (fields_filled / 5) * 100
        score += completeness * 0.4
        weights["completeness"] = completeness

        # Verificación (30%)
        verification_score = 0.0
        if lead.score.email_verified:
            verification_score += 50
        if lead.score.phone_verified:
            verification_score += 50
        score += verification_score * 0.3
        weights["verification"] = verification_score

        # Engagement (20%)
        engagement = min(100, (len(lead.sources) * 20) + (len(lead.interests) * 10))
        score += engagement * 0.2
        weights["engagement"] = engagement

        # Intent (10%)
        intent_score = 0.0
        if lead.budget_range:
            intent_score += 50
        if lead.timeline:
            intent_score += 50
        score += intent_score * 0.1
        weights["intent"] = intent_score

        return LeadScore(
            overall_score=min(100, score),
            data_completeness=completeness,
            email_verified=lead.score.email_verified,
            phone_verified=lead.score.phone_verified,
        )


# ============================================================================
# LEAD CAPTURE ENGINE (Main)
# ============================================================================

class LeadCaptureEngine:
    """Motor principal de captura y enriquecimiento de leads."""

    def __init__(self, browser_utils):
        """Inicializa engine."""
        self.browser_utils = browser_utils
        self.form_filler = WebFormFiller(browser_utils)
        self.directory_scraper = DirectoryScraper(browser_utils)
        self.enricher = LeadEnricher()
        self.all_leads: List[EnrichedLead] = []

    async def capture_leads_from_forms(
        self,
        form_urls: List[str],
        lead_data: Dict[str, str],
    ) -> List[bool]:
        """Captura leads rellenando formularios."""
        return await self.form_filler.auto_fill_common_forms(form_urls, lead_data)

    async def capture_leads_from_google_maps(
        self,
        query: str,
        location: str,
        max_results: int = 50,
    ) -> List[EnrichedLead]:
        """Captura leads de Google Maps y enriquece."""
        businesses = await self.directory_scraper.scrape_google_maps(
            query, location, max_results
        )

        leads = []
        for business in businesses:
            lead = await self.enricher.enrich_lead(
                name=business.get("name"),
                phone=business.get("phone"),
                company=business.get("name"),
            )
            leads.append(lead)

        self.all_leads.extend(leads)
        return leads

    async def capture_leads_from_messages(
        self,
        messages: List[Dict[str, str]],
    ) -> List[EnrichedLead]:
        """Captura leads de mensajes y enriquece."""
        leads = []

        for msg in messages:
            extracted = MessageLeadExtractor.extract_from_message(msg.get("text", ""))

            lead = await self.enricher.enrich_lead(
                email=extracted.get("email"),
                phone=extracted.get("phone"),
                name=extracted.get("name"),
            )

            lead.sources.append("message")
            leads.append(lead)

        self.all_leads.extend(leads)
        return leads

    def export_leads(self, format: str = "json") -> str:
        """
        Exporta leads capturados.

        Formatos soportados:
        - json
        - csv
        - excel (xlsx)
        """
        if format == "json":
            return json.dumps([asdict(lead) for lead in self.all_leads], default=str, indent=2)
        elif format == "csv":
            # TODO: Implementar CSV export
            return ""
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_high_quality_leads(self, min_score: float = 70.0) -> List[EnrichedLead]:
        """Retorna leads con score >= min_score."""
        return [lead for lead in self.all_leads if lead.score.overall_score >= min_score]

    def get_leads_by_source(self, source: str) -> List[EnrichedLead]:
        """Retorna leads de fuente específica."""
        return [lead for lead in self.all_leads if source in lead.sources]

    def get_leads_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de leads capturados."""
        if not self.all_leads:
            return {
                "total_leads": 0,
                "average_score": 0.0,
                "high_quality": 0,
                "by_source": {},
            }

        avg_score = sum(lead.score.overall_score for lead in self.all_leads) / len(self.all_leads)
        high_quality = len([l for l in self.all_leads if l.score.overall_score >= 70])

        by_source = {}
        for lead in self.all_leads:
            for source in lead.sources:
                by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_leads": len(self.all_leads),
            "average_score": f"{avg_score:.1f}",
            "high_quality": high_quality,
            "verified_emails": sum(1 for l in self.all_leads if l.score.email_verified),
            "by_source": by_source,
        }


# ============================================================================

if __name__ == "__main__":
    logger.info("Lead capture & intelligence module loaded")
