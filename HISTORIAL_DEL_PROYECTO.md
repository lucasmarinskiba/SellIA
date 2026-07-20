# HISTORIAL DEL PROYECTO — SellIA (Agente IA - Vendedor Automático)

> **Documento de Arquitectura y Evolución del Proyecto**
> 
> **Fecha de generación:** 2026-05-14
> **Versión:** 1.0.0
> **Estado:** En desarrollo activo

---

## 1. PORTADA

### 1.1 Nombre del Proyecto

**SellIA** — *Agente IA - Vendedor Automático*

### 1.2 Descripción General

SellIA es una plataforma integral de agentes de inteligencia artificial que automatiza el ciclo completo de ventas: desde la captación de clientes, cualificación de leads, cierre de ventas, post-venta, retención y fidelización, hasta la logística de entregas. La plataforma opera como una "empresa virtual" donde un Director de IA (CEO virtual) coordina múltiples departamentos, monitorea objetivos estratégicos, evalúa KPIs en tiempo real y toma decisiones autónomas basadas en datos.

La arquitectura sigue un enfoque de **Domain-Driven Design (DDD)** con dominios desacoplados, cada uno con sus propios modelos, esquemas, servicios y rutas API. El sistema soporta múltiples canales de comunicación (WhatsApp, Instagram, Telegram, Messenger, Webchat, MercadoLibre, Amazon, Shopify, TikTok, Meta Ads, Google Ads, LinkedIn, Beacons, Email) y genera contenido multimodal mediante más de 25 proveedores de IA generativa.

### 1.3 Stack Tecnológico Completo

| Capa | Tecnología | Versión / Detalle |
|------|-----------|-------------------|
| **Backend** | Python + FastAPI | Python 3.12+, FastAPI async |
| **ORM** | SQLAlchemy 2.0 | AsyncSession, declarative base |
| **Frontend** | Next.js 15 | App Router, React Server Components |
| **Estilos** | Tailwind CSS + shadcn/ui | Componentes custom adicionales |
| **Base de Datos** | PostgreSQL 16 | Alpine Linux image |
| **Cache / Colas** | Redis 7 | Broker de Celery, rate limiting, sesiones |
| **Workers** | Celery + Celery Beat | Tareas periódicas y en background |
| **Agentes IA** | OpenAI GPT-4o / LangChain / LangGraph | Multi-provider LLM |
| **Contenedores** | Docker + Docker Compose | 9 servicios orchestrados |
| **Infraestructura Cloud** | Terraform + Helm + AWS EKS | VPC, EKS, RDS, ElastiCache, ALB, S3, CloudFront |
| **Observabilidad** | Prometheus + Grafana | Métricas custom, dashboards de performance y seguridad |
| **Seguridad** | OWASP ZAP + Semgrep + Trivy | SAST/DAST scanning en CI/CD |
| **Testing E2E** | Playwright | Tests de extremo a extremo |
| **CI/CD** | GitHub Actions | 5 workflows (build, ci, deploy, e2e, security-scan) |
| **Antivirus** | ClamAV | Escaneo de archivos en tiempo real |
| **Backup DB** | Custom Docker image | Backups programados con encriptación |

### 1.4 Estadísticas del Código

| Métrica | Valor |
|---------|-------|
| **Archivos Python (backend)** | ~297 archivos `.py` |
| **Archivos TypeScript/TSX (frontend)** | ~101 archivos en `frontend/src/` |
| **Dominios del backend** | 21 dominios principales |
| **Modelos de base de datos** | 80+ tablas/modelos SQLAlchemy |
| **Conectores de canales** | 18 conectores |
| **Proveedores de generación de contenido** | 27 proveedores |
| **Categorías de prompts de agentes** | 43+ archivos de categorías |
| **Tareas programadas (Celery Beat)** | 28 tareas periódicas |
| **Páginas del dashboard** | 25+ páginas |
| **Workflows de GitHub Actions** | 5 workflows |
| **Servicios Docker Compose** | 9 servicios |
| **Módulos Terraform** | 8 módulos AWS |
| **Templates Helm** | 14 templates |

---

## 2. MÓDULOS DEL BACKEND

El backend está organizado bajo `backend/app/domains/` siguiendo una arquitectura de **Domain-Driven Design**. Cada dominio encapsula sus propios modelos (`models.py`), esquemas Pydantic (`schemas.py`), servicios de negocio (`services.py`), y en muchos casos, routers API propios (`router.py`).

### 2.1 agents — Sistema de Agentes IA

**Ubicación:** `backend/app/domains/agents/`

Núcleo inteligente de la plataforma. Gestiona personalidades de agentes, configuraciones, conversaciones, orquestación y playbooks de ventas.

**Archivos principales:**
- `models.py` — `AgentPersonality`, `AgentConfig`, `AgentConversation`, `AgentMessage`, `SellIAConversation`
- `schemas.py` — DTOs para creación, actualización y respuesta de agentes
- `orchestrator.py` — Meta-agente que procesa intenciones en lenguaje natural
- `director.py` — CEO virtual (`SellIADirector`) que coordina departamentos
- `playbooks.py` — Generador de playbooks de ventas personalizados por negocio
- `context_builder.py` — Construcción de contexto enriquecido para conversaciones
- `ai_reply.py` — Generación de respuestas IA crudas
- `llm_provider.py` — Abstracción de proveedores de LLM
- `actions.py` — Ejecutor de acciones del sistema (`SellIAActionExecutor`)
- `prompts.py` — Registro central de prompts (`AGENT_PROMPTS`)
- `prompts/composer.py` — Compositor de prompts funcionales + voces expertas
- `services.py` — Servicios de negocio para agentes

**43+ Categorías de Prompts** (`backend/app/domains/agents/prompts/categories/`):

| # | Archivo | Categoría |
|---|---------|-----------|
| 01 | `01_legends.py` | Leyendas del marketing y ventas |
| 02 | `02_women.py` | Mujeres líderes y emprendedoras |
| 03 | `03_marketing.py` | Especialistas en marketing |
| 04 | `04_autopilot.py` | Agentes de piloto automático |
| 05 | `05_sales_direct.py` | Ventas directas |
| 06 | `06_sales_mgmt.py` | Gestión de ventas |
| 07 | `07_operations.py` | Operaciones |
| 08 | `08_analytics.py` | Analítica |
| 09 | `09_finance.py` | Finanzas |
| 10 | `10_pipeline.py` | Pipeline de ventas |
| 11 | `11_tiktok.py` | TikTok general |
| 12 | `12_instagram_sales.py` | Ventas por Instagram |
| 12 | `12_tiktok_communication_sales.py` | TikTok: comunicación y ventas |
| 13 | `13_platform_specialists.py` | Especialistas en plataformas |
| 13 | `13_tiktok_attention_masters.py` | TikTok: maestros de atención |
| 14 | `14_content_creators.py` | Creadores de contenido |
| 14 | `14_tiktok_niche_specialists.py` | TikTok: especialistas de nicho |
| 15 | `15_tiktok_niche_expansion.py` | TikTok: expansión de nichos |
| 16 | `16_tiktok_professional_services.py` | TikTok: servicios profesionales |
| 17 | `17_tiktok_tech_money_passions.py` | TikTok: tech, dinero, pasiones |
| 18 | `18_tiktok_sports_fitness_outdoor.py` | TikTok: deportes, fitness, outdoor |
| 19 | `19_tiktok_food_travel_family.py` | TikTok: comida, viajes, familia |
| 20 | `20_trades_blue_collar.py` | Oficios y trabajos blue-collar |
| 21 | `21_mental_wellness_spiritual.py` | Bienestar mental y espiritual |
| 22 | `22_legal_finance_accounting.py` | Legal, finanzas, contabilidad |
| 23 | `23_tech_engineering_stem.py` | Tech, ingeniería, STEM |
| 24 | `24_business_commerce_hr.py` | Negocios, comercio, RRHH |
| 25 | `25_more_professions.py` | Más profesiones |
| 26 | `26_even_more_professions.py` | Aún más profesiones |
| 27 | `27_agriculture_farming.py` | Agricultura y granjas |
| 28 | `28_transport_logistics.py` | Transporte y logística |
| 29 | `29_hospitality_tourism.py` | Hospitalidad y turismo |
| 30 | `30_education_training.py` | Educación y capacitación |
| 31 | `31_government_public.py` | Gobierno y sector público |
| 32 | `32_research_science.py` | Investigación y ciencia |
| 33 | `33_media_communications.py` | Medios y comunicaciones |
| 34 | `34_sports_recreation.py` | Deportes y recreación |
| 35 | `35_emerging_tech.py` | Tecnologías emergentes |
| 36 | `36_finance_fintech.py` | Finanzas y fintech |
| 37 | `37_arts_culture.py` | Artes y cultura |
| 38 | `38_construction_real_estate.py` | Construcción y bienes raíces |
| 39 | `39_energy_environment.py` | Energía y medio ambiente |
| 40 | `40_manufacturing_industrial.py` | Manufactura e industrial |
| 41 | `41_creative_lifestyle.py` | Creatividad y estilo de vida |
| 42 | `42_health_science_specialists.py` | Salud y especialistas científicos |
| 43 | `43_specialized_niche.py` | Nichos especializados |

### 2.2 alerts — Sistema de Alertas

**Ubicación:** `backend/app/domains/alerts/`

Gestiona reglas de alertas, alertas en tiempo real y recomendaciones inteligentes para el negocio.

**Modelos principales:** `AlertRule`, `Alert`, `Recommendation`

**Enums:** `AlertRuleType`, `AlertSeverity`, `AlertStatus`, `RecommendationType`, `RecommendationActionType`, `RecommendationStatus`

### 2.3 analytics — Analytics y Business Intelligence

**Ubicación:** `backend/app/domains/analytics/`

Métricas de funnel, cohortes, predicción de churn, predicción de LTV (Lifetime Value) y alertas de insights.

**Modelos principales:** `FunnelMetric`, `CohortMetric`, `ChurnPrediction`, `LtvPrediction`, `InsightAlert`

**Enums:** `FunnelStage`, `ChurnRiskLevel`

### 2.4 automations — Motor de Automatizaciones

**Ubicación:** `backend/app/domains/automations/`

Engine completo de workflows, secuencias de email, reglas de chatbot, generación de contenido y calendario editorial.

**Modelos principales:**
- `Workflow` — Definición de flujos de trabajo
- `WorkflowExecution` — Ejecuciones de workflows
- `WorkflowVariant` — Variantes para A/B testing
- `EmailTemplate` — Plantillas de email
- `EmailSequence` — Secuencias de emails automatizadas
- `SequenceStep` — Pasos dentro de una secuencia
- `SequenceSubscription` — Suscriptores a secuencias
- `SequenceEmailLog` — Log de envíos
- `ChatbotRule` — Reglas del chatbot
- `GeneratedContent` — Contenido generado por IA
- `ContentCalendar` — Calendario editorial

**Enums:** `WorkflowTriggerType`, `WorkflowActionType`, `WorkflowStatus`

### 2.5 bi — Business Intelligence Avanzado

**Ubicación:** `backend/app/domains/bi/`

Métricas de funnel, cohortes, predicciones de churn y LTV, alertas de insights basadas en datos.

**Modelos principales:** `FunnelMetrics`, `CohortMetrics`, `ChurnPrediction`, `LtvPrediction`, `InsightAlert`

### 2.6 businesses — Gestión de Negocios

**Ubicación:** `backend/app/domains/businesses/`

Gestión de negocios/empresas con configuración por tipo (servicios, bienes, digitales, mixto).

**Modelos principales:** `Business`

**Enums:** `BusinessType`

### 2.7 catalogs — Catálogo de Productos/Servicios

**Ubicación:** `backend/app/domains/catalogs/`

Gestión de catálogo con items de tipo producto, servicio o digital.

**Modelos principales:** `CatalogItem`

**Enums:** `CatalogItemType`

### 2.8 channels — Canales de Comunicación

**Ubicación:** `backend/app/domains/channels/`

Gestión de conexiones de canales, conversaciones omnicanal y mensajería.

**Modelos principales:**
- `ChannelConnection` — Conexiones a canales externos
- `Conversation` — Conversaciones unificadas
- `Message` — Mensajes individuales

**Enums:** `ChannelPlatform`, `ChannelStatus`, `ConversationStatus`, `MessageDirection`, `MessageStatus`

**Conectores disponibles** (`backend/app/domains/channels/connectors/`):

| Conector | Archivo | Descripción |
|----------|---------|-------------|
| WhatsApp | `whatsapp.py` | Mensajería WhatsApp Business API |
| Instagram | `instagram.py` | DM y comentarios de Instagram |
| Telegram | `telegram.py` | Bot de Telegram |
| Messenger | `messenger.py` | Facebook Messenger |
| Webchat | `webchat.py` | Widget de chat web embebible |
| MercadoLibre | `mercadolibre.py` | Integración con MercadoLibre |
| Amazon | `amazon.py` | Amazon Seller Central / MWS |
| Shopify | `shopify.py` | Tiendas Shopify |
| Beacons | `beacons.py` | Perfiles Beacons.ai |
| Email | `email.py` | Envío de emails transaccionales |
| Facebook Ads | `facebook_ads.py` | API de Facebook Ads |
| Google Ads | `google_ads.py` | Google Ads API |
| Meta Ads | `meta_ads.py` | Meta Marketing API unificado |
| TikTok | `tiktok.py` | TikTok For Business |
| TikTok Ads | `tiktok_ads.py` | TikTok Ads Manager |
| LinkedIn | `linkedin.py` | LinkedIn API |

### 2.9 conversations — Conversaciones (submódulo)

**Ubicación:** `backend/app/domains/conversations/`

Extensión del dominio de canales para gestión avanzada de conversaciones.

### 2.10 crm — Customer Relationship Management

**Ubicación:** `backend/app/domains/crm/`

Pipeline de ventas, deals/oportunidades, scoring de leads y seguimiento de actividades.

**Modelos principales:** `Pipeline`, `Deal`, `LeadScore`, `LeadActivity`

**Enums:** `LeadStage`

### 2.11 feedback — Feedback de Usuarios

**Ubicación:** `backend/app/domains/feedback/`

Sistema de feedback con votos, comentarios, mejoras del sistema, feature flags y datos de entrenamiento de ML.

**Modelos principales:** `UserFeedback`, `FeedbackVote`, `FeedbackComment`, `SystemImprovement`, `FeatureFlag`, `MLTrainingData`

**Enums:** `FeedbackType`, `FeedbackSeverity`, `FeedbackStatus`

### 2.12 finance — Finanzas

**Ubicación:** `backend/app/domains/finance/`

Facturación, recordatorios de pago, cuentas por cobrar y configuración de impuestos.

**Modelos principales:** `SalesInvoice`, `PaymentReminder`, `AccountsReceivableSnapshot`, `TaxConfig`

### 2.13 objectives — Objetivos y OKRs

**Ubicación:** `backend/app/domains/objectives/`

Departamentos, objetivos de negocio, KPIs y resultados clave (OKRs).

**Modelos principales:** `Department`, `BusinessObjective`, `KPI`, `KeyResult`

**Enums:** `ObjectiveStatus`, `ObjectivePeriod`

### 2.14 orchestration — Orquestación

**Ubicación:** `backend/app/domains/orchestration/`

Capa de orquestación de alto nivel para coordinar múltiples agentes y departamentos.

**Archivos principales:**
- `director.py` — Orquestador de nivel empresarial

### 2.15 orders — Órdenes y Pagos

**Ubicación:** `backend/app/domains/orders/`

Gestión de órdenes de compra, eventos de revenue e integraciones de pago.

**Modelos principales:** `Order`, `RevenueEvent`, `PaymentIntegration`

**Enums:** `OrderStatus`, `PaymentStatus`

### 2.16 retention — Retención y Fidelización

**Ubicación:** `backend/app/domains/retention/`

Programas de lealtad, programas de referidos, encuestas NPS y segmentación de clientes.

**Modelos principales:** `LoyaltyProgram`, `ReferralProgram`, `ReferralCode`, `ReferralUse`, `NpsCampaign`, `NpsResponse`, `CustomerSegment`

**Enums:** `ReferralStatus`, `NpsCampaignStatus`, `CustomerSegmentType`

### 2.17 security — Seguridad y Compliance

**Ubicación:** `backend/app/domains/security/`

Capa de seguridad extensa (ver sección 3 para detalle completo).

**Modelos principales:** `UserLoginLog`, `SecurityWebhook`, `SecurityConfig`, `PushSubscription`, `UserSession`, `TwoFABackupCode`, `BreachCheckLog`, `SubscriptionAccessLog`, `ChargebackAlert`, `EmailOTP`, `WebAuthnCredential`, `SecurityKey`, `TrustedDevice`, `SessionNonce`, `IPAllowlist`, `LoginAnomaly`, `DataAccessLog`, `RolePermission`, `BusinessUserRole`, `DataRetentionPolicy`, `DataRetentionLog`, `SecretRotationLog`

### 2.18 services — Servicios y Agenda

**Ubicación:** `backend/app/domains/services/`

Entrega de servicios, citas/agenda y gestión de modalidades de servicio.

**Modelos principales:** `ServiceDelivery`, `Appointment`

**Enums:** `ServiceModality`, `SolutionType`, `ServiceDeliveryStatus`, `AppointmentStatus`

### 2.19 shipments — Envíos y Logística

**Ubicación:** `backend/app/domains/shipments/`

Gestión de envíos, configuración de carriers y eventos de tracking.

**Modelos principales:** `ShipmentConfig`, `Shipment`, `ShipmentTrackingEvent`

**Enums:** `CarrierType`, `ShipmentStatus`, `ServiceType`

### 2.20 subscriptions — Suscripciones y Billing

**Ubicación:** `backend/app/domains/subscriptions/`

Sistema completo de suscripciones con múltiples proveedores de pago, incluyendo cripto y transferencias bancarias.

**Modelos principales:**
- `SubscriptionPlan` — Planes de suscripción
- `Subscription` — Suscripciones activas
- `UserAPIKey` — API keys de usuarios
- `UsageTracking` — Tracking de uso
- `PaymentTransaction` — Transacciones de pago
- `Invoice` — Facturas
- `UsageAlert` — Alertas de uso
- `BankTransferPayment` — Pagos por transferencia bancaria
- `CancellationFeedback` — Feedback de cancelación

**Enums:** `PaymentProvider`, `PaymentStatus`, `InvoiceType`, `InvoiceStatus`, `SubscriptionStatus`, `BankTransferStatus`, `CancellationReason`

**Proveedores de pago soportados:**
- Stripe (tarjetas, subscriptions)
- Payoneer / Transferencias bancarias
- MercadoPago (preapproval)
- Cripto (pagos en criptomonedas)

### 2.21 support — Soporte Técnico

**Ubicación:** `backend/app/domains/support/`

Tickets de soporte, mensajes de tickets, FAQ y base de conocimientos.

**Modelos principales:** `SupportTicket`, `TicketMessage`, `FAQ`, `KnowledgeBaseArticle`

**Enums:** `TicketStatus`, `TicketPriority`, `TicketCategory`, `MessageSenderType`

### 2.22 users — Usuarios y Autenticación

**Ubicación:** `backend/app/domains/users/`

Gestión de usuarios, perfiles y autenticación base.

**Modelos principales:** `User`

---

## 3. CAPA DE SEGURIDAD (7 CAPAS)

La plataforma implementa una arquitectura de seguridad de **7 capas** con más de 20 mecanismos de protección activos. Los archivos de seguridad se encuentran tanto en `backend/app/domains/security/` como en `backend/app/core/`.

### 3.1 Autenticación y Autorización

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **JWT + httpOnly cookies** | Tokens JWT firmados, almacenados en cookies httpOnly seguras | `app.core.security` |
| **2FA TOTP** | Time-based One-Time Password con QR codes | `app.core.security`, `app.domains.security.models` |
| **Backup codes** | 8 códigos de respaldo SHA-256 para recuperación 2FA | `app.domains.security.models.TwoFABackupCode` |
| **RBAC** | Role-Based Access Control con roles por negocio | `app.core.rbac`, `app.domains.security.models.RolePermission` |
| **RLS** | Row-Level Security para aislamiento de datos multi-tenant | `app.core.rls` |
| **WebAuthn** | Autenticación sin contraseña mediante FIDO2/WebAuthn | `app.core.webauthn_service`, `app.domains.security.models.WebAuthnCredential` |

### 3.2 Protección de Acceso

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **Rate limiting con Redis** | Límite de peticiones por endpoint con FastAPI-Limiter + Redis | `app.main` (middleware), `app.core.limit_enforcement` |
| **Geofencing** | Detección de ubicación anómala, bloqueo por país, detección de VPN | `app.core.geo_service`, `app.middleware.geo_middleware` |
| **Device fingerprint** | Huella digital de dispositivos, detección de nuevos dispositivos | `app.core.threat_intel.device_fingerprint` |
| **Country blocking** | Bloqueo de países específicos por IP | `app.core.country_block` |
| **IP Allowlist** | Lista blanca de IPs por usuario/negocio | `app.core.ip_allowlist`, `app.domains.security.models.IPAllowlist` |
| **Time access control** | Restricción de acceso por horarios | `app.core.time_access` |

### 3.3 Inteligencia de Amenazas y Detección

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **HIBP integration** | Have I Been Pwned — verificación de breaches de email y contraseñas | `app.core.hibp_service`, `app.domains.security.models.BreachCheckLog` |
| **Threat intel** | Evaluación de riesgo del cliente, fingerprinting, scoring | `app.core.threat_intel`, `app.middleware.threat_intel` |
| **Cloudflare Turnstile** | CAPTCHA invisible de Cloudflare | `app.core.turnstile`, `app.core.cloudflare` |
| **Login anomaly detection** | Detección de logins anómalos con z-score y velocidad imposible | `app.core.anomaly_detection` |
| **Session integrity** | Verificación de integridad de sesiones | `app.core.session_integrity` |

### 3.4 Gestión de Sesiones y Logs

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **Session management** | Sesiones con revocación remota, nonces, expiración | `app.domains.security.models.UserSession`, `app.domains.security.models.SessionNonce` |
| **Audit logs** | Logs de acceso a datos con filtros y panel admin | `app.middleware.audit_log`, `app.domains.security.models.DataAccessLog` |
| **Security audit middleware** | Middleware de logging de seguridad | `app.middleware.security_logging` |
| **ELK integration** | Logging en formato ECS para Elastic Stack | `app.core.elk_logger` |
| **Security notifications** | Notificaciones push/email de eventos de seguridad | `app.core.security_notifications`, `app.domains.security.models.PushSubscription` |

### 3.5 Protección de Datos

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **Field-level encryption** | Encriptación a nivel de campo para datos sensibles | `app.core.encryption`, `app.core.field_encryption`, `app.core.encrypted_types` |
| **PII masking** | Enmascaramiento de información personal identificable | `app.core.pii_masking` |
| **Data retention policies** | Políticas de retención y eliminación automática de datos | `app.core.data_deletion`, `app.domains.security.models.DataRetentionPolicy` |
| **Data access logs** | Registro de acceso a datos sensibles | `app.domains.security.models.DataAccessLog` |

### 3.6 Protección de Archivos y Transacciones

| Mecanismo | Descripción | Ubicación |
|-----------|-------------|-----------|
| **File scanning con ClamAV** | Escaneo antivirus de archivos subidos | `app.core.file_scanner`, servicio Docker `clamav` |
| **Chargeback protection** | Protección contra chargebacks | `app.core.chargeback_protection` |
| **Secret rotation** | Rotación automática de tokens y secretos | `app.core.security`, `app.domains.security.models.SecretRotationLog` |

### 3.7 Middlewares de Seguridad

Los siguientes middlewares están registrados en `app.main`:

```python
SecurityHeadersMiddleware      # Headers de seguridad (HSTS, CSP, X-Frame-Options)
SecurityAuditMiddleware        # Auditoría de eventos de seguridad
ThreatIntelMiddleware          # Inteligencia de amenazas en tiempo real
SubscriptionAuditMiddleware    # Auditoría de operaciones de suscripción
DataAccessAuditMiddleware      # Auditoría de acceso a datos
CacheControlMiddleware         # Control de caché sensible
PayloadLimitMiddleware         # Límite de tamaño de payloads
```

### 3.8 Métricas de Seguridad (Prometheus)

| Métrica | Descripción |
|---------|-------------|
| `SELLIA_LOGINS` | Contador de logins exitosos |
| `SELLIA_FAILED_LOGINS` | Contador de logins fallidos |
| `SELLIA_GEOFENCE_VIOLATIONS` | Violaciones de geofencing |
| `SELLIA_NEW_DEVICES` | Nuevos dispositivos detectados |
| `SELLIA_RATE_LIMIT_HITS` | Hits de rate limiting |
| `SELLIA_REQUEST_DURATION` | Histograma de duración de requests |
| `SELLIA_REQUESTS` | Contador de requests |
| `SELLIA_ACTIVE_SESSIONS` | Sesiones activas |

---

## 4. SISTEMA DE AGENTES IA

El sistema de agentes es el núcleo diferenciador de SellIA. Combina agentes funcionales (captador, cualificador, vendedor, post-venta) con voces expertas de más de 250 personalidades de marketing, ventas y negocios.

### 4.1 Arquitectura del Sistema de Agentes

```
┌─────────────────────────────────────────────────────────────┐
│                    SELLIA ORCHESTRATOR                       │
│              (Meta-Agente / Procesador de Intenciones)       │
│                                                              │
│  Recibe lenguaje natural → Clasifica intención → Enruta    │
│  a agente funcional o sugiere agentes expertos               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CAPTADOR   │    │ CUALIFICADOR │    │  VENDEDOR    │
│   (Lead Gen) │    │ (Qualification)│   │  (Closer)    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              SELLIA DIRECTOR (CEO Virtual)                   │
│                                                              │
│  - Refresca KPIs cada ciclo                                  │
│  - Evalúa objetivos (activos, en riesgo, fallidos)          │
│  - Detecta anomalías con BI                                 │
│  - Genera planes de acción para objetivos en riesgo         │
│  - Ejecuta acciones automáticas                             │
│  - Genera briefing diario para el dueño del negocio         │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Componentes Principales

#### 4.2.1 Orchestrator (`backend/app/domains/agents/orchestrator.py`)

Meta-agente que:
- Procesa comandos en lenguaje natural
- Clasifica intenciones del usuario
- Enruta a agentes funcionales o sugiere agentes expertos
- Soporta procesamiento síncrono (`process_intent`) y streaming (`process_intent_stream`)
- Ejecuta acciones reales del sistema vía `SellIAActionExecutor`

**Acciones soportadas:**
- `ASK_CLARIFICATION` — Preguntas de seguimiento
- `SUGGEST_AGENTS` — Sugerir 1-3 agentes relevantes
- `CREATE_CONVERSATION` — Crear conversación con un agente específico
- `GENERATE_CONTENT` — Generar contenido con un agente experto
- `NAVIGATE` — Navegar a secciones del dashboard

#### 4.2.2 Director (`backend/app/domains/agents/director.py`)

CEO virtual (`SellIADirector`) que:
- Se ejecuta cada 6 horas vía Celery Beat (`selia_director_daily`)
- Refresca todos los KPIs del negocio
- Evalúa objetivos y detecta los en riesgo o fallidos
- Genera planes de acción específicos para recuperar objetivos
- Ejecuta acciones automáticas cuando está configurado
- Genera un briefing diario y lo envía al dueño del negocio

#### 4.2.3 Playbooks (`backend/app/domains/agents/playbooks.py`)

Generador de **playbooks de ventas personalizados** que:
- Analiza el perfil del negocio
- Revisa el catálogo de productos/servicios
- Analiza el historial de deals/oportunidades
- Genera scripts de venta, manejo de objeciones y workflows
- Aplica metodologías de ventas expertas

#### 4.2.4 Context Builder (`backend/app/domains/agents/context_builder.py`)

Construye contexto enriquecido para conversaciones incluyendo:
- Historial de mensajes del cliente
- Perfil del negocio
- Catálogo relevante
- Pipeline y deals activos
- Objetivos y KPIs actuales

### 4.3 Sistema de Prompts

#### 4.3.1 Registro Central (`backend/app/domains/agents/prompts.py`)

Registro `AGENT_PROMPTS` que indexa todas las personalidades de agentes por `slug`.

#### 4.3.2 Compositor de Prompts (`backend/app/domains/agents/prompts/composer.py`)

Permite componer prompts funcionales con voces expertas:

```python
FUNCTIONAL_SLUGS = {"captador", "cualificador", "vendedor", "post-venta"}

def compose_system_prompt(base_slug: str, voice_slug: str = None, ...):
    # Combina el rol funcional con la filosofía del experto
```

#### 4.3.3 Las 43+ Categorías de Prompts

Las categorías cubren más de **250 personalidades expertas** organizadas por dominio:

**Leyendas del Marketing y Ventas:**
- Alex Hormozi, Gary Vaynerchuk, Grant Cardone, Jordan Belfort, Dan Kennedy, etc.

**Mujeres Líderes:**
- Sara Blakely, Sophia Amoruso, Marie Forleo, Brene Brown, etc.

**Especialistas TikTok:**
- Maestros de comunicación y ventas
- Especialistas de atención (hook creators)
- Nichos específicos (fitness, food, tech, travel, family)
- Servicios profesionales
- Tech, dinero y pasiones

**Profesiones y Oficios:**
- Legal, finanzas, contabilidad
- Tech, ingeniería, STEM
- Negocios, comercio, RRHH
- Agricultura y granjas
- Transporte y logística
- Hospitalidad y turismo
- Educación y capacitación
- Gobierno y sector público
- Investigación y ciencia
- Medios y comunicaciones
- Deportes y recreación
- Tecnologías emergentes
- Finanzas y fintech
- Artes y cultura
- Construcción y bienes raíces
- Energía y medio ambiente
- Manufactura e industrial
- Creatividad y estilo de vida
- Salud y especialistas científicos
- Nichos especializados

### 4.4 LLM Providers

**Archivo:** `backend/app/domains/agents/llm_provider.py`

Abstracción de proveedores de LLM que permite:
- OpenAI (GPT-4o, GPT-4, GPT-3.5)
- Anthropic (Claude)
- Ollama (modelos locales)
- Fallback entre proveedores

### 4.5 Sistema de Mejoramiento Automático

**Ubicación:** `backend/app/core/intelligence/`

Subsistema de ML que mejora continuamente la plataforma:

#### 4.5.1 ML Data Collector (`ml_data_collector.py`)

Recolecta datos de entrenamiento:
- Resultados de conversaciones
- Ratings de respuestas IA
- Accuracy de clasificación de intenciones
- Métricas de Prometheus
- Errores recientes

#### 4.5.2 ML Trainer (`ml_trainer.py`)

Entrena modelos de ML:
- `SimpleIntentClassifier` — Clasificador de intenciones (LogisticRegression + TF-IDF)
- `ResponseQualityPredictor` — Predictor de calidad de respuestas
- `LeadScorer` — Scoring de leads

#### 4.5.3 Improvement Generator (`improvement_generator.py`)

Genera mejoras automáticas del sistema:
- Análisis de health report
- Recomendaciones de optimización
- Creación de feature flags para mejoras
- Rollout progresivo de features

#### 4.5.4 System Analyzer (`system_analyzer.py`)

Analiza el estado del sistema:
- Genera `SystemHealthReport`
- Detecta cuellos de botella
- Identifica oportunidades de mejora

#### 4.5.5 Feature Flags (`feature_flags.py`)

Sistema de feature flags:
- Activación por plan de suscripción
- Rollout progresivo (porcentaje de usuarios)
- Canaries y A/B testing de features

---

## 5. AUTOMATIZACIONES

### 5.1 Motor de Workflows

**Ubicación:** `backend/app/domains/automations/`

Sistema completo de automatización con:

**Triggers:**
- Eventos de conversación
- Cambios de estado en deals
- Acciones del usuario
- Programaciones temporales
- Webhooks entrantes

**Actions:**
- Enviar mensaje
- Enviar email
- Asignar agente
- Mover deal de etapa
- Generar contenido
- Llamar webhook externo
- Crear tarea

### 5.2 Secuencias de Email

**Archivos:** `EmailSequence`, `SequenceStep`, `SequenceSubscription`

- Secuencias drip automatizadas
- Pasos con delays condicionales
- Tracking de aperturas y clicks
- Logs de envío (`SequenceEmailLog`)

### 5.3 A/B Testing

**Modelo:** `WorkflowVariant`

- Variantes de workflows para testing
- Distribución de tráfico entre variantes
- Métricas de conversión por variante
- `WorkflowABTestResult` para resultados

### 5.4 Chatbot Rules

**Modelo:** `ChatbotRule`

- Reglas basadas en condiciones
- Respuestas automáticas
- Escalamiento a humanos

### 5.5 Generación de Contenido Automatizada

**Modelos:** `GeneratedContent`, `ContentCalendar`

- Generación automática de copy, imágenes, videos, carruseles
- Calendario editorial con scheduling
- Análisis de performance de contenido

---

## 6. INTEGRACIONES

### 6.1 Generación de Contenido Multimodal

**Ubicación:** `backend/app/integrations/content_generation/`

Sistema de enrutamiento inteligente a 27+ proveedores de IA generativa:

| Proveedor | Tipo de Contenido | Archivo |
|-----------|-------------------|---------|
| **Midjourney** | Imágenes artísticas | `providers/midjourney.py` |
| **DALL-E (OpenAI)** | Imágenes | `providers/openai_image.py` |
| **Sora** | Video generativo | `providers/sora.py` |
| **Runway** | Video/edición | `providers/runway.py` |
| **ElevenLabs** | Audio/voz | `providers/elevenlabs.py` |
| **HeyGen** | Avatares/video | `providers/heygen.py` |
| **Kling** | Video | `providers/kling.py` |
| **Luma** | Video 3D | `providers/luma.py` |
| **Pika** | Video | `providers/pika.py` |
| **Seedance** | Video/danza | `providers/seedance.py` |
| **Leonardo** | Imágenes | `providers/leonardo.py` |
| **Ideogram** | Imágenes con texto | `providers/ideogram.py` |
| **Replicate** | Modelos diversos | `providers/replicate.py` |
| **FAL Aggregator** | Aggregator de modelos | `providers/fal_aggregator.py` |
| **Ollama** | Modelos locales | `providers/ollama.py` |
| **Kimi** | Generación de contenido | `providers/kimi.py` |
| **CopyAI** | Copy/marketing | `providers/copyai.py` |
| **Jasper** | Copy/marketing | `providers/jasper.py` |
| **Writesonic** | Copy/SEO | `providers/writesonic.py` |
| **AdCreative** | Creativos de ads | `providers/adcreative.py` |
| **Canva** | Diseño gráfico | `providers/canva.py` |
| **BeautifulAI** | Presentaciones | `providers/beautifulai.py` |
| **Gamma** | Presentaciones | `providers/gamma.py` |
| **CapCut** | Edición de video | `providers/capcut.py` |
| **OpusClip** | Clips de video | `providers/opusclip.py` |
| **Photoroom** | Edición de fotos | `providers/photoroom.py` |

**Arquitectura:**
- `base.py` — Clase base `BaseProvider` con interfaz uniforme
- `router.py` — Enrutador inteligente que selecciona el mejor proveedor según tipo de contenido, presupuesto y calidad requerida
- `budget.py` — Gestión de presupuesto por proveedor
- `cache.py` — Caché de contenido generado
- `plan_tools.py` — Herramientas de planificación de contenido
- `utils.py` — Utilidades compartidas

### 6.2 Conectores de Canales

Ver sección **2.8 channels** para el listado completo de 18 conectores.

---

## 7. FRONTEND

### 7.1 Arquitectura

**Tecnología:** Next.js 15 + React + TypeScript + Tailwind CSS

- **App Router** con React Server Components
- **Layouts anidados** (`dashboard/layout.tsx`)
- **Middleware** (`middleware.ts`) para protección de rutas
- **Hooks custom** para autenticación, voz, notificaciones push

### 7.2 Dashboard Principal

**Páginas del Dashboard** (`frontend/src/app/dashboard/`):

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/dashboard` | Home | Panel principal con métricas |
| `/dashboard/agentes` | Agentes | Configuración de agentes + `AutopilotVoiceConfig` |
| `/dashboard/analytics` | Analytics | Métricas y gráficos |
| `/dashboard/alertas` | Alertas | Gestión de alertas |
| `/dashboard/automatizaciones` | Automatizaciones | Lista de workflows |
| `/dashboard/automatizaciones/builder` | Builder | Constructor de workflows |
| `/dashboard/canales` | Canales | Conexiones de canales |
| `/dashboard/catalogo` | Catálogo | Productos y servicios |
| `/dashboard/catalogo/nuevo` | Nuevo Item | Crear item de catálogo |
| `/dashboard/conversaciones` | Conversaciones | Chat omnicanal |
| `/dashboard/connections` | Conexiones | Conexiones externas |
| `/dashboard/crm` | CRM | Pipeline y deals |
| `/dashboard/envios` | Envíos | Logística |
| `/dashboard/finanzas` | Finanzas | Facturación y pagos |
| `/dashboard/inteligencia` | Inteligencia | Panel de IA y ML |
| `/dashboard/negocios` | Negocios | Gestión de negocios |
| `/dashboard/negocios/nuevo` | Nuevo Negocio | Crear negocio |
| `/dashboard/objetivos` | Objetivos | OKRs y KPIs |
| `/dashboard/ordenes` | Órdenes | Pedidos |
| `/dashboard/planes` | Planes | Planes de suscripción |
| `/dashboard/recomendaciones` | Recomendaciones | Sugerencias de IA |
| `/dashboard/retencion` | Retención | Lealtad y referidos |
| `/dashboard/seguridad` | Seguridad | Panel de seguridad |
| `/dashboard/sequences` | Secuencias | Email sequences |
| `/dashboard/sessions` | Sesiones | Gestión de sesiones |
| `/dashboard/suscripcion` | Suscripción | Billing y facturación |
| `/dashboard/agenda` | Agenda | Citas y servicios |

### 7.3 Panel de Administración

**Rutas:** `frontend/src/app/dashboard/admin/`

| Ruta | Página | Descripción |
|------|--------|-------------|
| `/dashboard/admin/audit` | Audit | Logs de auditoría |
| `/dashboard/admin/feedback` | Feedback | Feedback de usuarios |
| `/dashboard/admin/finanzas` | Finanzas | Métricas financieras |
| `/dashboard/admin/metrics` | Métricas | Métricas del sistema |
| `/dashboard/admin/soporte` | Soporte | Tickets de soporte |

### 7.4 Panel de Agentes con Configuración de Voz

**Archivo clave:** `frontend/src/app/dashboard/agentes/AutopilotVoiceConfig.tsx`

Configuración de voz para el piloto automático:
- Selección de voz (ElevenLabs)
- Configuración de tono y velocidad
- Activación/desactivación de respuesta por voz

### 7.5 Páginas Públicas

| Ruta | Descripción |
|------|-------------|
| `/` | Landing page |
| `/login` | Inicio de sesión |
| `/register` | Registro |
| `/pitch` | Pitch de ventas |
| `/feedback` | Formulario de feedback |
| `/soporte` | Portal de soporte |

### 7.6 Componentes Reutilizables

**UI Components** (`frontend/src/components/ui/`):
`Avatar`, `Badge`, `Button`, `Card`, `Dialog`, `EmptyState`, `Input`, `Label`, `Select`, `Separator`, `Sheet`, `Skeleton`, `StatCard`, `Tabs`, `Textarea`, `Tooltip`

**Componentes de Negocio:**
- `SellIAAssistant` — Asistente flotante de IA
- `SecurityAlert` — Alertas de seguridad
- `Sidebar` / `Navbar` — Navegación
- `ABTestModal` — Modal de A/B testing
- `FeedbackCard` / `FeedbackForm` — Feedback
- `FAQAccordion` / `TicketChat` / `TicketForm` — Soporte

### 7.7 Librerías de Cliente

**Archivos en `frontend/src/lib/`:**
`agents`, `alerts`, `analytics`, `api`, `assistant`, `auth`, `automations`, `bi`, `business`, `catalog`, `channels`, `conversations`, `crm`, `finance`, `objectives`, `orders`, `retention`, `sequences`, `services`, `shipments`, `subscriptions`

---

## 8. INFRAESTRUCTURA Y DEVOPS

### 8.1 Docker + Docker Compose

**Archivo:** `docker-compose.yml`

**9 servicios orchestrados:**

| Servicio | Imagen | Puerto | Rol |
|----------|--------|--------|-----|
| `db` | postgres:16-alpine | 5432 | Base de datos PostgreSQL |
| `redis` | redis:7-alpine | 6379 | Caché y broker Celery |
| `backend` | Build local | 8000 | API FastAPI |
| `celery-worker` | Build local | — | Workers de Celery |
| `celery-beat` | Build local | — | Scheduler de tareas |
| `frontend` | Build local | 3000 | Next.js app |
| `clamav` | clamav/clamav:latest | 3310 | Antivirus |
| `db-backup` | Build local | — | Backups programados |
| `nginx` | nginx:alpine | 80/8080 | Reverse proxy |

### 8.2 Terraform (AWS)

**Ubicación:** `infra/terraform/`

**8 módulos:**

| Módulo | Recursos | Archivos |
|--------|----------|----------|
| `vpc` | VPC, subnets, NAT, IGW | `modules/vpc/` |
| `eks` | Cluster Kubernetes, node groups | `modules/eks/` |
| `rds` | PostgreSQL RDS, parametrización | `modules/rds/` |
| `redis` | ElastiCache Redis | `modules/redis/` |
| `alb` | Application Load Balancer | `modules/alb/` |
| `s3` | Buckets S3 | `modules/s3/` |
| `cloudfront` | CDN CloudFront | `modules/cloudfront/` |
| `iam` | Roles y políticas IAM | `modules/iam/` |

### 8.3 Helm Charts

**Ubicación:** `infra/helm/sellia/`

**Templates:**
- `backend-deployment.yaml`
- `backend-service.yaml`
- `frontend-deployment.yaml`
- `frontend-service.yaml`
- `nginx-deployment.yaml` + `nginx-configmap.yaml` + `nginx-service.yaml`
- `clamav-deployment.yaml` + `clamav-pvc.yaml` + `clamav-service.yaml`
- `ingress.yaml`
- `hpa.yaml` (Horizontal Pod Autoscaler)
- `pdb.yaml` (Pod Disruption Budget)
- `networkpolicy.yaml`
- `secrets.yaml`
- `serviceaccount.yaml`
- `namespace.yaml`

**Archivos de valores:**
- `values.yaml` — Valores por defecto
- `values-production.yaml` — Override para producción

**Monitoring:** `infra/helm/monitoring/prometheus-values.yaml`

### 8.4 Prometheus + Grafana

**Dashboards:** `infra/grafana/dashboards/`
- `performance-dashboard.json` — Métricas de performance
- `security-dashboard.json` — Métricas de seguridad

### 8.5 Seguridad en CI/CD

**OWASP ZAP + Semgrep + Trivy:**
- `.zap/rules.tsv` — Reglas custom de ZAP
- `.github/workflows/security-scan.yml` — Pipeline de scanning

### 8.6 GitHub Actions

**Workflows** (`.github/workflows/`):

| Workflow | Archivo | Descripción |
|----------|---------|-------------|
| CI | `ci.yml` | Tests unitarios, lint, type check |
| Build | `build.yml` | Build de imágenes Docker |
| Deploy | `deploy.yml` | Deploy a EKS |
| E2E | `e2e.yml` | Tests de Playwright |
| Security Scan | `security-scan.yml` | OWASP ZAP, Semgrep, Trivy |

### 8.7 Backups de Base de Datos

**Servicio:** `db-backup`
- Dockerfile: `db-backup/Dockerfile`
- Backups programados con encriptación
- Variable `BACKUP_ENCRYPTION_KEY`
- Volumen persistente `postgres_backups`

---

## 9. TAREAS Y WORKERS

### 9.1 Celery App

**Archivo:** `backend/app/tasks/celery_app.py`

Configuración:
- **Broker:** Redis
- **Backend:** Redis
- **Serializer:** JSON
- **Timezone:** America/Argentina/Buenos_Aires
- **Task time limit:** 5 minutos
- **Worker prefetch:** 1 tarea por worker

### 9.2 Tareas Programadas (Celery Beat)

**28 tareas periódicas configuradas:**

#### Workflows (9 tareas)
| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `check_pending_workflows` | 30 seg | Revisar workflows pendientes |
| `check_email_sequences` | 60 seg | Revisar secuencias de email |
| `check_human_handoffs` | 15 seg | Escalamiento a humanos |
| `check_deals_stalled` | 1 hora | Deals estancados |
| `check_hot_leads_no_deal` | 6 horas | Leads calientes sin deal |
| `check_abandoned_carts` | 1 día | Carritos abandonados |
| `check_no_reply_conversations` | 1 hora | Conversaciones sin respuesta |
| `check_upcoming_appointments` | 15 min | Citas próximas |
| `process_no_show_appointments` | 30 min | No-shows |
| `request_pending_confirmations` | 1 hora | Confirmaciones pendientes |

#### Generación de Contenido (4 tareas)
| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `auto_generate_catalog_content` | 24 horas | Generar contenido del catálogo |
| `schedule_content_posts` | 5 min | Publicar contenido programado |
| `analyze_content_performance` | 7 días | Analizar performance de contenido |
| `cleanup_old_generated_content` | 24 horas | Limpiar contenido viejo |

#### Suscripciones (8 tareas)
| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `check_expiring_subscriptions` | 6 horas | Suscripciones por vencer |
| `process_crypto_pending_payments` | 2 min | Pagos crypto pendientes |
| `cleanup_expired_crypto_payments` | 10 min | Limpiar pagos crypto expirados |
| `check_usage_alerts` | 5 min | Alertas de uso |
| `generate_recurring_invoices` | 24 horas | Facturas recurrentes |
| `send_transfer_reminders` | 6 horas | Recordatorios de transferencia |
| `expire_pending_transfers` | 6 horas | Expirar transferencias pendientes |
| `sync_mercadopago_preapprovals` | 6 horas | Sincronizar preapprovals de MP |

#### SellIA Virtual Company (4 tareas)
| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `selia_director_daily` | 24 horas | Ciclo diario del CEO virtual |
| `rfm_segmentation` | 24 horas | Segmentación RFM |
| `payment_reminder_check` | 1 hora | Recordatorios de pago |
| `bi_analytics_daily` | 24 horas | Analytics diario de BI |

#### Seguridad y Compliance (2 tareas)
| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `data_retention_cleanup` | 7 días | Limpieza de datos por retención |
| `rotate_webhook_tokens` | 90 días | Rotación de tokens de webhook |

### 9.3 Workers Especializados

**Archivos de tareas:**
- `workflow_tasks.py` — Ejecución de workflows, escalamiento, deals
- `content_tasks.py` — Generación de imágenes, copy, videos, carruseles, thumbnails
- `subscription_tasks.py` — Gestión de suscripciones, pagos, facturas
- `selia_tasks.py` — Tareas del CEO virtual, RFM, BI
- `security_tasks.py` — Limpieza de datos, rotación de secretos
- `intelligence_tasks.py` — Entrenamiento de ML, generación de mejoras
- `support_tasks.py` — Clasificación de tickets, respuestas automáticas, escalamiento

---

## 10. MODELOS DE BASE DE DATOS

### 10.1 Listado Completo por Dominio

#### users
- `User`

#### businesses
- `Business`
- `BusinessUserRole`

#### catalogs
- `CatalogItem`

#### channels
- `ChannelConnection`
- `Conversation`
- `Message`

#### crm
- `Pipeline`
- `Deal`
- `LeadScore`
- `LeadActivity`

#### orders
- `Order`
- `RevenueEvent`
- `PaymentIntegration`

#### agents
- `AgentPersonality`
- `AgentConfig`
- `AgentConversation`
- `AgentMessage`
- `SellIAConversation`

#### automations
- `Workflow`
- `WorkflowExecution`
- `WorkflowVariant`
- `EmailTemplate`
- `EmailSequence`
- `SequenceStep`
- `SequenceSubscription`
- `SequenceEmailLog`
- `ChatbotRule`
- `GeneratedContent`
- `ContentCalendar`

#### subscriptions
- `SubscriptionPlan`
- `Subscription`
- `UserAPIKey`
- `UsageTracking`
- `PaymentTransaction`
- `Invoice`
- `UsageAlert`
- `BankTransferPayment`
- `CancellationFeedback`

#### alerts
- `AlertRule`
- `Alert`
- `Recommendation`

#### analytics
- `FunnelMetric`
- `CohortMetric`
- `ChurnPrediction`
- `LtvPrediction`
- `InsightAlert`

#### bi
- `FunnelMetrics`
- `CohortMetrics`
- `ChurnPrediction`
- `LtvPrediction`
- `InsightAlert`

#### objectives
- `Department`
- `BusinessObjective`
- `KPI`
- `KeyResult`

#### retention
- `LoyaltyProgram`
- `ReferralProgram`
- `ReferralCode`
- `ReferralUse`
- `NpsCampaign`
- `NpsResponse`
- `CustomerSegment`

#### finance
- `SalesInvoice`
- `PaymentReminder`
- `AccountsReceivableSnapshot`
- `TaxConfig`

#### services
- `ServiceDelivery`
- `Appointment`

#### shipments
- `ShipmentConfig`
- `Shipment`
- `ShipmentTrackingEvent`

#### support
- `SupportTicket`
- `TicketMessage`
- `FAQ`
- `KnowledgeBaseArticle`

#### feedback
- `UserFeedback`
- `FeedbackVote`
- `FeedbackComment`
- `SystemImprovement`
- `FeatureFlag`
- `MLTrainingData`

#### security
- `UserLoginLog`
- `SecurityWebhook`
- `SecurityConfig`
- `PushSubscription`
- `UserSession`
- `TwoFABackupCode`
- `BreachCheckLog`
- `SubscriptionAccessLog`
- `ChargebackAlert`
- `EmailOTP`
- `WebAuthnCredential`
- `SecurityKey`
- `TrustedDevice`
- `SessionNonce`
- `IPAllowlist`
- `LoginAnomaly`
- `DataAccessLog`
- `RolePermission`
- `DataRetentionPolicy`
- `DataRetentionLog`
- `SecretRotationLog`

### 10.2 Resumen Estadístico

| Dominio | Tablas/Modelos |
|---------|---------------|
| security | 21 |
| automations | 11 |
| subscriptions | 9 |
| retention | 7 |
| agents | 5 |
| channels | 3 |
| crm | 4 |
| support | 4 |
| feedback | 6 |
| objectives | 4 |
| finance | 4 |
| services | 2 |
| shipments | 3 |
| alerts | 3 |
| analytics/bi | 5 |
| orders | 3 |
| catalogs | 1 |
| businesses | 2 |
| users | 1 |
| **TOTAL** | **~98+ modelos** |

---

## 11. NOTA IMPORTANTE SOBRE HISTORIAL

> **Aviso de Limitación de Contexto Histórico**
>
> Este documento fue generado a través de un análisis exhaustivo del **código fuente actual** del proyecto SellIA, incluyendo la estructura de archivos, modelos de base de datos, configuraciones de infraestructura, y todos los artefactos técnicos presentes en el repositorio.
>
> **Sin embargo, es importante aclarar lo siguiente:**
>
> 1. **No se tiene acceso al historial de conversaciones previas** que pudieron haber ocurrido durante el desarrollo de este proyecto. Los prompts textuales, decisiones de diseño discutidas verbalmente, iteraciones conceptuales, o instrucciones específicas dadas en conversaciones anteriores **no están disponibles** en el contexto de generación de este documento.
>
> 2. **No se tiene acceso a commits de Git** ni al historial de cambios del repositorio (a menos que se solicite explícitamente un análisis de `git log`). Por lo tanto, no se pueden documentar fechas exactas de implementación de cada feature, autores específicos de cada módulo, o la secuencia cronológica precisa de desarrollo.
>
> 3. **Este documento refleja el ESTADO ACTUAL del código** al momento de su generación (2026-05-14), no la evolución histórica paso a paso.
>
> 4. **Para completar esta sección** con el historial real de desarrollo, sería necesario:
>    - Acceder al historial de conversaciones previas (si existen logs)
>    - Ejecutar `git log --all --oneline --graph` para reconstruir la línea temporal
>    - Revisar issues, PRs, o documentos de planificación del proyecto
>
> **Recomendación:** Si se requiere un historial detallado de decisiones, fechas de implementación y evolución del proyecto, se sugiere complementar este documento con el análisis del historial de Git y cualquier documentación de proyecto previa que exista fuera del repositorio.

---

## APÉNDICE A: Estructura de Directorios del Proyecto

```
Agente IA - Vendedor Automático/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # Routers API v1
│   │   ├── core/                # Configuración, seguridad, utilidades core
│   │   │   └── intelligence/    # ML Trainer, Data Collector, Improvement Generator
│   │   ├── domains/             # 21 dominios DDD
│   │   │   ├── agents/
│   │   │   │   └── prompts/categories/  # 43+ categorías de prompts
│   │   │   ├── channels/
│   │   │   │   └── connectors/  # 18 conectores de canales
│   │   │   └── [otros dominios]
│   │   ├── integrations/
│   │   │   └── content_generation/
│   │   │       └── providers/   # 27 proveedores de IA generativa
│   │   ├── middleware/          # Middlewares de seguridad y auditoría
│   │   ├── tasks/               # Tareas Celery
│   │   └── workers/             # Workers especializados
│   ├── tests/                   # Tests unitarios y de integración
│   ├── alembic/                 # Migraciones de base de datos
│   ├── scripts/                 # Scripts de utilidad
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   └── dashboard/       # 25+ páginas del dashboard
│   │   ├── components/          # Componentes React
│   │   ├── hooks/               # Custom hooks
│   │   └── lib/                 # Clientes API
│   ├── e2e/                     # Tests Playwright
│   └── Dockerfile
├── infra/
│   ├── terraform/               # 8 módulos AWS
│   ├── helm/sellia/             # 14 templates Kubernetes
│   ├── grafana/                 # Dashboards
│   └── monitoring/              # Configuración de monitoreo
├── nginx/
│   └── nginx.conf               # Configuración de reverse proxy
├── docs/                        # 10 documentos técnicos
├── .github/workflows/           # 5 workflows de CI/CD
├── docker-compose.yml           # 9 servicios
└── .env / .env.example          # Variables de entorno
```

---

*Documento generado automáticamente. Última actualización: 2026-05-14*
