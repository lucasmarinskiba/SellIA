"""
Platform-Specific Handlers — Implementaciones detalladas para cada plataforma.

Cada handler encapsula la lógica específica de plataforma para:
- Autenticación
- Publicación de productos
- Respuesta a inquiries
- Manejo de compras
- Captura de leads

Usa Computer Use + visión para no depender de APIs (escalabilidad infinita).
"""

import logging
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import asdict

logger = logging.getLogger(__name__)


# ============================================================================
# MERCADO LIBRE HANDLER — Marketplace LATAM Leader
# ============================================================================

class MercadoLibreComputerUseHandler:
    """
    Automatización completa de Mercado Libre vía Computer Use.

    Tareas principales:
    - Publica productos (5-10 min por producto con fotos)
    - Responde preguntas (2 min por respuesta)
    - Cierra ventas (confirm pago → envío)
    - Monitorea inventory (sync horario con BD)

    Plataforma: Argentina, México, Brasil, Colombia, Perú, etc.
    Volumen: 100M+ usuarios, 2M+ vendedores
    """

    def __init__(self, browser_utils):
        """Inicializa handler Mercado Libre."""
        self.browser_utils = browser_utils
        self.base_url = "https://www.mercadolibre.com.ar"
        self.is_authenticated = False

    async def authenticate(self, email: str, password: str) -> bool:
        """
        Login a Mercado Libre.

        Flujo:
        1. Navega a login
        2. Ingresa email
        3. Ingresa password
        4. Confirma autenticación (puede requerir 2FA)
        5. Verifica acceso a dashboard vendedor
        """
        try:
            logger.info(f"Authenticating Mercado Libre: {email}")

            # 1. Navega a login
            await self.browser_utils.screenshot_and_analyze()
            # En producción: await computer_use.navigate("https://www.mercadolibre.com.ar/login")

            # 2. Espera campo email
            await self.browser_utils.wait_for_element("Email input field", timeout=10)

            # 3. Ingresa credenciales
            await self.browser_utils.type_in_field("Email field", email)
            await self.browser_utils.type_in_field("Password field", password)

            # 4. Click login
            await self.browser_utils.click_by_vision("Login button or Continue button")

            # 5. Espera dashboard
            await self.browser_utils.wait_for_element("Seller dashboard or Account page", timeout=15)

            logger.info("Mercado Libre authentication successful")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"Mercado Libre auth failed: {str(e)}")
            return False

    async def post_product(
        self,
        name: str,
        description: str,
        price: float,
        quantity: int,
        category: str,
        photos: List[str] = None,
        shipping_method: str = "standard",
    ) -> Dict[str, Any]:
        """
        Publica producto en Mercado Libre.

        Campos:
        1. Categoría (dropdown)
        2. Título (búsqueda optimizada)
        3. Descripción (formato con beneficios)
        4. Precio
        5. Cantidad
        6. Fotos
        7. Método envío
        8. Garantía (opcional)

        Retorna: {
            "success": bool,
            "product_id": "MLV123456",
            "product_url": "https://mercadolibre.com.ar/item/MLV123456",
            "duration_seconds": 5.3,
        }
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"Posting product to Mercado Libre: {name}")

            if not self.is_authenticated:
                raise RuntimeError("Not authenticated")

            # 1. Navega a crear producto
            await self.browser_utils.screenshot_and_analyze()
            # await computer_use.navigate(f"{self.base_url}/mylogin/seller")

            # Busca botón "Crear publicación" o "Vender"
            await self.browser_utils.click_by_vision("Vender button or Create listing button")

            # 2. Selecciona categoría
            await self.browser_utils.wait_for_element("Category selector", timeout=10)
            await self.browser_utils.click_by_vision(f"Category: {category}")

            # 3. Rellena información básica
            await self.browser_utils.type_in_field("Title/Titulo field", name)
            await self.browser_utils.type_in_field("Price/Precio field", str(price))
            await self.browser_utils.type_in_field("Quantity field", str(quantity))

            # 4. Rellena descripción
            await self.browser_utils.click_by_vision("Description textarea")
            await self.browser_utils.type_in_field("Description field", description)

            # 5. Sube fotos
            if photos:
                for i, photo_path in enumerate(photos[:10]):  # Máximo 10 fotos
                    await self.browser_utils.click_by_vision("Upload photo button or Add photo")
                    # En producción: upload file via Computer Use
                    logger.info(f"Uploading photo {i+1}/{len(photos)}")
                    await asyncio.sleep(2)  # Espera upload

            # 6. Selecciona método envío
            await self.browser_utils.click_by_vision("Shipping method dropdown or Envío")
            await self.browser_utils.click_by_vision(f"Shipping: {shipping_method}")

            # 7. Publica
            await self.browser_utils.click_by_vision("Publish button or Publicar button", )
            await self.browser_utils.wait_for_element(
                "Success message or Product published confirmation",
                timeout=15,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Product posted successfully in {duration:.1f}s")

            return {
                "success": True,
                "product_name": name,
                "price": price,
                "duration_seconds": duration,
            }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Failed to post product: {str(e)}")
            return {
                "success": False,
                "product_name": name,
                "error": str(e),
                "duration_seconds": duration,
            }

    async def respond_to_questions(self) -> List[Dict[str, Any]]:
        """
        Monitorea sección de preguntas y responde automáticamente.

        Flujo:
        1. Navega a Preguntas en dashboard
        2. Para cada pregunta sin respuesta:
           a. Lee pregunta
           b. Genera respuesta via LLM
           c. Publica respuesta
           d. Marca como resuelta

        Retorna: Lista de preguntas respondidas.
        """
        try:
            logger.info("Checking Mercado Libre questions")

            # 1. Navega a preguntas
            await self.browser_utils.screenshot_and_analyze()
            # await computer_use.navigate(f"{self.base_url}/mylogin/questions")

            # 2. Espera lista de preguntas
            await self.browser_utils.wait_for_element("Questions list or Preguntas section", timeout=10)

            # 3. Extrae preguntas sin respuesta
            questions = []

            # TODO: Usar visión para detectar preguntas
            # Pseudocódigo:
            # screenshot = await screenshot_and_analyze()
            # questions = parse_questions_from_screenshot(screenshot)

            # 4. Responde cada pregunta
            for i, question in enumerate(questions):
                try:
                    # Click en pregunta
                    await self.browser_utils.click_by_vision(f"Question {i+1}")

                    # Lee pregunta completa
                    screenshot = await self.browser_utils.screenshot_and_analyze()

                    # Genera respuesta (aquí se integraría LLM)
                    response_text = "Hola! Gracias por tu pregunta. "
                    # En producción: response_text = await llm.generate_response(question)

                    # Escribe respuesta
                    await self.browser_utils.click_by_vision("Response textarea or Responder")
                    await self.browser_utils.type_in_field("Response field", response_text)

                    # Publica
                    await self.browser_utils.click_by_vision("Publish response button or Responder button")

                    logger.info(f"Responded to question {i+1}")

                except Exception as e:
                    logger.error(f"Error responding to question: {str(e)}")

            logger.info(f"Responded to {len(questions)} questions")
            return questions

        except Exception as e:
            logger.error(f"Error checking questions: {str(e)}")
            return []

    async def handle_purchase_and_shipping(self, order_id: str) -> bool:
        """
        Maneja compra después del pago.

        Flujo:
        1. Confirma pago recibido
        2. Genera etiqueta envío (DHL, FedEx, etc)
        3. Actualiza tracking
        4. Envía notificaciones
        5. Solicita calificación

        Retorna: True si éxito.
        """
        try:
            logger.info(f"Handling purchase: {order_id}")

            # 1. Navega a órdenes
            await self.browser_utils.screenshot_and_analyze()

            # 2. Busca orden
            await self.browser_utils.click_by_vision(f"Order {order_id} or Click order")

            # 3. Confirma pago
            await self.browser_utils.click_by_vision("Confirm payment button or Confirmar pago")

            # 4. Genera envío
            await self.browser_utils.click_by_vision("Generate shipping label or Generar envío")

            # 5. Espera shipping label
            await self.browser_utils.wait_for_element("Shipping label generated", timeout=10)

            # 6. Notifica comprador
            await self.browser_utils.click_by_vision("Notify buyer button")

            logger.info(f"Purchase handled successfully: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling purchase: {str(e)}")
            return False


# ============================================================================
# SHOPIFY HANDLER — Owned E-Commerce Store
# ============================================================================

class ShopifyComputerUseHandler:
    """
    Automatización de Shopify (tienda propia SaaS).

    Tareas:
    - Crea/actualiza productos
    - Sincroniza inventory
    - Procesa órdenes
    - Responde customer inquiries
    - Analiza tráfico/conversión
    """

    def __init__(self, browser_utils):
        """Inicializa handler Shopify."""
        self.browser_utils = browser_utils
        self.store_url = None
        self.is_authenticated = False

    async def authenticate(self, store_url: str, email: str, password: str) -> bool:
        """
        Login a Shopify.

        Flujo:
        1. Navega a admin.shopify.com
        2. Ingresa email
        3. Ingresa password
        4. Confirma 2FA si aplica
        5. Verifica acceso a dashboard
        """
        try:
            logger.info(f"Authenticating Shopify: {email}")

            self.store_url = store_url

            # 1. Navega a Shopify login
            await self.browser_utils.screenshot_and_analyze()

            # 2. Ingresa credenciales
            await self.browser_utils.type_in_field("Email field", email)
            await self.browser_utils.type_in_field("Password field", password)

            # 3. Login
            await self.browser_utils.click_by_vision("Login button")

            # 4. Espera 2FA si aplica
            await asyncio.sleep(2)
            screenshot = await self.browser_utils.screenshot_and_analyze()

            if "2fa" in str(screenshot).lower() or "two-factor" in str(screenshot).lower():
                logger.info("2FA required, waiting for manual confirmation")
                # En producción, escalará a usuario
                return False

            # 5. Verifica acceso
            await self.browser_utils.wait_for_element("Shopify dashboard or Products page", timeout=10)

            logger.info("Shopify authentication successful")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"Shopify auth failed: {str(e)}")
            return False

    async def create_product(
        self,
        name: str,
        description: str,
        price: float,
        sku: str,
        quantity: int,
        photos: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea producto en Shopify.

        Campos:
        - Título
        - Descripción
        - Precio
        - SKU
        - Cantidad
        - Fotos
        - Colecciones (opcional)

        Retorna: {
            "success": bool,
            "product_id": "gid://shopify/Product/1234567890",
            "handle": "iphone-15-pro",
            "url": "https://store.myshopify.com/products/iphone-15-pro",
        }
        """
        try:
            logger.info(f"Creating Shopify product: {name}")

            if not self.is_authenticated:
                raise RuntimeError("Not authenticated")

            # 1. Navega a productos
            await self.browser_utils.screenshot_and_analyze()

            # 2. Busca "Add product" o "Create"
            await self.browser_utils.click_by_vision("Add product button or Create product")

            # 3. Rellena información
            await self.browser_utils.type_in_field("Product title field", name)
            await self.browser_utils.type_in_field("Product description field", description)

            # 4. Rellena pricing
            await self.browser_utils.click_by_vision("Pricing section or Price")
            await self.browser_utils.type_in_field("Price field", str(price))

            # 5. Rellena inventory
            await self.browser_utils.click_by_vision("Inventory section or Stock")
            await self.browser_utils.type_in_field("SKU field", sku)
            await self.browser_utils.type_in_field("Quantity field", str(quantity))

            # 6. Sube fotos
            if photos:
                await self.browser_utils.click_by_vision("Add media or Upload images")
                for photo in photos[:5]:
                    # await upload_file_via_computer_use(photo)
                    await asyncio.sleep(1)

            # 7. Guarda
            await self.browser_utils.click_by_vision("Save product button or Save")
            await self.browser_utils.wait_for_element("Product saved or Success message", timeout=15)

            logger.info(f"Shopify product created: {name}")
            return {"success": True, "product_name": name}

        except Exception as e:
            logger.error(f"Failed to create Shopify product: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_inventory(self, sku: str, new_quantity: int) -> bool:
        """
        Actualiza inventory para SKU específico.

        Flujo:
        1. Busca producto por SKU
        2. Abre página de producto
        3. Actualiza cantidad en inventory
        4. Guarda
        """
        try:
            logger.info(f"Updating inventory for SKU {sku}: {new_quantity}")

            # 1. Busca producto
            await self.browser_utils.click_by_vision("Search bar or Search products")
            await self.browser_utils.type_in_field("Search field", sku)

            # 2. Click en producto
            await self.browser_utils.click_by_vision(f"Product with SKU {sku}")

            # 3. Abre inventory
            await self.browser_utils.click_by_vision("Inventory or Stock section")

            # 4. Actualiza cantidad
            await self.browser_utils.type_in_field("Quantity field", str(new_quantity))

            # 5. Guarda
            await self.browser_utils.click_by_vision("Save button")

            logger.info(f"Inventory updated for SKU {sku}")
            return True

        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
            return False

    async def process_order(self, order_number: str) -> bool:
        """
        Procesa orden (fulfillment).

        Flujo:
        1. Abre orden
        2. Confirma pago
        3. Genera packing slip
        4. Coordina envío
        5. Envía email de confirmación
        """
        try:
            logger.info(f"Processing order: {order_number}")

            # 1. Busca orden
            await self.browser_utils.click_by_vision("Orders section")
            await self.browser_utils.type_in_field("Search field", order_number)

            # 2. Abre orden
            await self.browser_utils.click_by_vision(f"Order {order_number}")

            # 3. Confirma pago
            if not await self.browser_utils.click_by_vision("Mark as paid button"):
                logger.warning("Order already paid")

            # 4. Fulfillment
            await self.browser_utils.click_by_vision("Fulfill order button")
            await self.browser_utils.click_by_vision("Confirm fulfillment or Create shipment")

            logger.info(f"Order processed: {order_number}")
            return True

        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            return False


# ============================================================================
# FACEBOOK HANDLER — Marketplace + Messenger
# ============================================================================

class FacebookComputerUseHandler:
    """
    Automatización de Facebook Marketplace + Messenger.

    Tareas:
    - Publica listados en Marketplace
    - Responde inquiries via Messenger
    - Negocia precios
    - Cierra transacciones
    """

    def __init__(self, browser_utils):
        """Inicializa handler Facebook."""
        self.browser_utils = browser_utils
        self.is_authenticated = False

    async def authenticate(self, email: str, password: str) -> bool:
        """Login a Facebook."""
        try:
            logger.info("Authenticating to Facebook")

            await self.browser_utils.screenshot_and_analyze()

            # Ingresa credenciales
            await self.browser_utils.type_in_field("Email or phone field", email)
            await self.browser_utils.type_in_field("Password field", password)

            # Login
            await self.browser_utils.click_by_vision("Log In button")
            await self.browser_utils.wait_for_element("Facebook feed or Home", timeout=10)

            logger.info("Facebook authentication successful")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"Facebook auth failed: {str(e)}")
            return False

    async def post_to_marketplace(
        self,
        title: str,
        description: str,
        price: float,
        category: str,
        photos: List[str] = None,
        location: str = None,
    ) -> Dict[str, Any]:
        """
        Publica en Facebook Marketplace.

        Campos:
        - Título
        - Descripción
        - Precio
        - Categoría
        - Fotos
        - Ubicación
        - Condición (nuevo/usado)
        """
        try:
            logger.info(f"Posting to Facebook Marketplace: {title}")

            if not self.is_authenticated:
                raise RuntimeError("Not authenticated")

            # 1. Navega a Marketplace
            await self.browser_utils.click_by_vision("Marketplace icon or Marketplace")

            # 2. Busca "Sell something"
            await self.browser_utils.click_by_vision("Sell something button or Create new listing")

            # 3. Rellena campos
            await self.browser_utils.type_in_field("Item name field", title)
            await self.browser_utils.type_in_field("Description field", description)
            await self.browser_utils.type_in_field("Price field", str(price))

            # 4. Selecciona categoría
            await self.browser_utils.click_by_vision("Category dropdown")
            await self.browser_utils.click_by_vision(f"Category: {category}")

            # 5. Sube fotos
            if photos:
                await self.browser_utils.click_by_vision("Add photo button")
                for photo in photos[:10]:
                    # await upload_file(photo)
                    await asyncio.sleep(1)

            # 6. Ingresa ubicación
            if location:
                await self.browser_utils.type_in_field("Location field", location)

            # 7. Publica
            await self.browser_utils.click_by_vision("List item button or Publish")

            logger.info(f"Facebook Marketplace item posted: {title}")
            return {"success": True, "title": title}

        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            return {"success": False, "error": str(e)}

    async def monitor_and_respond_inquiries(self) -> List[Dict[str, Any]]:
        """
        Monitorea Messenger inquiries y responde.

        Flujo:
        1. Abre Marketplace dashboard
        2. Checkea "Inbox" o "Messages"
        3. Para cada nuevo mensaje:
           a. Lee mensaje
           b. Genera respuesta
           c. Envía respuesta
        """
        try:
            logger.info("Checking Facebook Messenger inquiries")

            # 1. Navega a Marketplace
            await self.browser_utils.click_by_vision("Marketplace icon")

            # 2. Busca "Messages" o "Inbox"
            await self.browser_utils.click_by_vision("Messages or Inbox")

            # 3. Espera lista de mensajes
            await self.browser_utils.wait_for_element("Messages list", timeout=10)

            messages = []
            # TODO: Extraer mensajes via visión

            # 4. Responde cada uno
            for msg in messages:
                await self.browser_utils.click_by_vision(f"Message from {msg.get('sender')}")

                # Genera respuesta
                response = "Thanks for your interest!"
                # En producción: response = await llm.generate_response(msg)

                # Envía
                await self.browser_utils.type_in_field("Message input field", response)
                await self.browser_utils.click_by_vision("Send button")

            return messages

        except Exception as e:
            logger.error(f"Error checking messages: {str(e)}")
            return []


# ============================================================================
# WHATSAPP HANDLER — Direct Messaging
# ============================================================================

class WhatsAppComputerUseHandler:
    """
    Automatización de WhatsApp Web.

    Tareas:
    - Envía mensajes outbound a leads
    - Responde inquiries
    - Envía catálogos de productos
    - Califica leads
    - Envía actualizaciones de envío
    """

    def __init__(self, browser_utils):
        """Inicializa handler WhatsApp."""
        self.browser_utils = browser_utils
        self.is_authenticated = False

    async def authenticate(self) -> bool:
        """
        Autentica WhatsApp Web.

        Flujo:
        1. Navega a web.whatsapp.com
        2. Escanea QR con teléfono
        3. Verifica autenticación
        """
        try:
            logger.info("Authenticating WhatsApp Web")

            # 1. Navega a WhatsApp Web
            await self.browser_utils.screenshot_and_analyze()

            # 2. Espera QR
            await self.browser_utils.wait_for_element("QR code", timeout=30)

            logger.info("WhatsApp QR displayed. Scan with your phone.")
            logger.info("Waiting for authentication...")

            # 3. Espera autenticación (puede tardar)
            await self.browser_utils.wait_for_element("Chat list or Conversations", timeout=60)

            logger.info("WhatsApp Web authenticated")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"WhatsApp auth failed: {str(e)}")
            return False

    async def send_message(self, phone_number: str, message: str) -> bool:
        """
        Envía mensaje de WhatsApp.

        Flujo:
        1. Busca contacto por teléfono
        2. Abre chat
        3. Escribe mensaje
        4. Envía
        """
        try:
            logger.info(f"Sending WhatsApp message to {phone_number}")

            if not self.is_authenticated:
                raise RuntimeError("Not authenticated")

            # 1. Click en "New chat" o busca
            await self.browser_utils.click_by_vision("New chat button or Search")

            # 2. Ingresa teléfono
            await self.browser_utils.type_in_field("Search or phone field", phone_number)

            # 3. Selecciona contacto
            await self.browser_utils.click_by_vision(f"Contact {phone_number}")

            # 4. Escribe mensaje
            await self.browser_utils.type_in_field("Message input field", message)

            # 5. Envía
            await self.browser_utils.click_by_vision("Send button or Paper airplane")

            logger.info(f"Message sent to {phone_number}")
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    async def send_product_catalog(
        self,
        phone_number: str,
        products: List[Dict[str, Any]],
    ) -> bool:
        """
        Envía catálogo de productos formateado.

        Formato:
        ```
        📦 CATÁLOGO DE PRODUCTOS

        1️⃣ iPhone 15 Pro - $1,200
        Descripción: Latest Apple phone with A17 Pro

        2️⃣ Samsung Galaxy S24 - $1,000
        Descripción: Premium Android experience

        Escriba el número para más info o comprar
        ```
        """
        try:
            logger.info(f"Sending product catalog to {phone_number}")

            # Formatea catálogo
            catalog = "📦 CATÁLOGO DE PRODUCTOS\n\n"
            for i, product in enumerate(products, 1):
                catalog += f"{i}️⃣ {product.get('name')} - ${product.get('price')}\n"
                catalog += f"   {product.get('description')}\n\n"

            catalog += "Escriba el número para más info o comprar"

            # Envía
            return await self.send_message(phone_number, catalog)

        except Exception as e:
            logger.error(f"Error sending catalog: {str(e)}")
            return False

    async def lead_qualification_sequence(self, phone_number: str) -> bool:
        """
        Secuencia de 5 mensajes para calificar lead.

        1. Saludo + pregunta de interés
        2. Budget check
        3. Timeline/urgencia
        4. Envía producto relevante
        5. Call-to-action cierre

        Espaciado: 30s entre mensajes
        """
        try:
            logger.info(f"Starting lead qualification sequence: {phone_number}")

            sequence = [
                "¡Hola! Te escribo porque tenemos una oferta especial.",
                "¿Cuál es tu presupuesto aproximado?",
                "¿Necesitas esto urgente o tienes tiempo?",
                "Perfecto, tengo exactamente lo que buscas.",
                "¿Podemos coordinarnos una videollamada hoy?",
            ]

            for i, msg in enumerate(sequence):
                await self.send_message(phone_number, msg)
                if i < len(sequence) - 1:
                    await asyncio.sleep(30)  # Espera 30s entre mensajes

            logger.info(f"Lead qualification sequence completed: {phone_number}")
            return True

        except Exception as e:
            logger.error(f"Error in qualification sequence: {str(e)}")
            return False


# ============================================================================
# EMAIL HANDLER — Gmail / Outlook
# ============================================================================

class EmailComputerUseHandler:
    """
    Automatización de Email (Gmail / Outlook).

    Tareas:
    - Envía cold emails a leads
    - Secuencias de nutrición (3-5 emails)
    - Responde replies
    - Trackea opens/clicks
    """

    def __init__(self, browser_utils):
        """Inicializa handler Email."""
        self.browser_utils = browser_utils
        self.is_authenticated = False
        self.email_service = "gmail"  # o "outlook"

    async def authenticate(self, email: str, password: str) -> bool:
        """Login a Gmail o Outlook."""
        try:
            logger.info(f"Authenticating email: {email}")

            # 1. Navega a login
            if self.email_service == "gmail":
                url = "https://mail.google.com"
            else:
                url = "https://outlook.office.com"

            await self.browser_utils.screenshot_and_analyze()

            # 2. Ingresa credenciales
            await self.browser_utils.type_in_field("Email field", email)
            await self.browser_utils.type_in_field("Password field", password)

            # 3. Login
            await self.browser_utils.click_by_vision("Next button or Sign in")
            await self.browser_utils.wait_for_element("Inbox or Email list", timeout=15)

            logger.info("Email authentication successful")
            self.is_authenticated = True
            return True

        except Exception as e:
            logger.error(f"Email auth failed: {str(e)}")
            return False

    async def send_campaign_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachments: List[str] = None,
    ) -> bool:
        """
        Envía email individual.

        Flujo:
        1. Click Compose
        2. Ingresa "To"
        3. Ingresa Subject
        4. Ingresa Body (con tracking pixel)
        5. Adjunta archivos
        6. Envía
        """
        try:
            logger.info(f"Sending email to {recipient}")

            if not self.is_authenticated:
                raise RuntimeError("Not authenticated")

            # 1. Click Compose
            await self.browser_utils.click_by_vision("Compose button or New email")

            # 2. Ingresa destinatario
            await self.browser_utils.type_in_field("To field", recipient)

            # 3. Ingresa subject
            await self.browser_utils.type_in_field("Subject field", subject)

            # 4. Ingresa cuerpo
            await self.browser_utils.click_by_vision("Email body or Message field")
            await self.browser_utils.type_in_field("Body field", body)

            # 5. Adjunta (opcional)
            if attachments:
                await self.browser_utils.click_by_vision("Attach files button")
                for attachment in attachments:
                    # await upload_file(attachment)
                    await asyncio.sleep(1)

            # 6. Envía
            await self.browser_utils.click_by_vision("Send button")

            logger.info(f"Email sent to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def send_nurture_sequence(
        self,
        recipient: str,
        sequence_name: str,
        emails: List[Dict[str, str]],
    ) -> int:
        """
        Envía secuencia de nutrición (3-5 emails espaciados en el tiempo).

        Formato emails:
        [
            {"subject": "...", "body": "..."},
            {"subject": "...", "body": "..."},
            ...
        ]

        Retorna: cantidad de emails enviados.
        """
        try:
            logger.info(f"Starting nurture sequence '{sequence_name}' to {recipient}")

            sent_count = 0
            delays = [0, 3600, 86400]  # 0s, 1h, 24h

            for i, email in enumerate(emails):
                if i > 0:
                    delay = delays[min(i - 1, len(delays) - 1)]
                    logger.info(f"Waiting {delay}s before next email")
                    await asyncio.sleep(delay)

                success = await self.send_campaign_email(
                    recipient=recipient,
                    subject=email.get("subject"),
                    body=email.get("body"),
                )

                if success:
                    sent_count += 1

            logger.info(f"Nurture sequence completed: {sent_count}/{len(emails)} emails sent")
            return sent_count

        except Exception as e:
            logger.error(f"Error in nurture sequence: {str(e)}")
            return 0


# ============================================================================
# HANDLER FACTORY
# ============================================================================

class PlatformHandlerFactory:
    """Factory para crear handlers de plataforma."""

    def __init__(self, browser_utils):
        """Inicializa factory."""
        self.browser_utils = browser_utils

    def get_handler(self, platform: str):
        """Retorna handler para plataforma."""
        if platform.lower() in ["mercado_libre", "mercadolibre", "ml"]:
            return MercadoLibreComputerUseHandler(self.browser_utils)
        elif platform.lower() in ["shopify", "shop"]:
            return ShopifyComputerUseHandler(self.browser_utils)
        elif platform.lower() in ["facebook", "fb"]:
            return FacebookComputerUseHandler(self.browser_utils)
        elif platform.lower() in ["whatsapp", "wa"]:
            return WhatsAppComputerUseHandler(self.browser_utils)
        elif platform.lower() in ["email", "gmail", "outlook"]:
            return EmailComputerUseHandler(self.browser_utils)
        else:
            raise ValueError(f"Unknown platform: {platform}")


# ============================================================================

if __name__ == "__main__":
    logger.info("Platform handlers module loaded")
