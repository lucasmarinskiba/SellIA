# Caja de Cristal — Computer Use Features

Documentación completa de todas las funcionalidades del sistema Computer Use de SellIA.

## Índice

1. [Core Features](#core-features)
2. [Infraestructura & Monitoreo](#infraestructura--monitoreo)
3. [Export & Reporting](#export--reporting)
4. [Multi-Navegador](#multi-navegador)
5. [Seguridad & Validación](#seguridad--validación)
6. [Automatización Avanzada](#automatización-avanzada)
7. [Colaboración](#colaboración)
8. [Inteligencia](#inteligencia)
9. [Mobile & Emulación](#mobile--emulación)
10. [Debugging](#debugging)
11. [Atajos de Teclado](#atajos-de-teclado)
12. [API Reference](#api-reference)

---

## Core Features

### Sesiones de Automatización Visual
- El agente de IA controla un navegador headless vía Playwright
- Screenshots en tiempo real enviados por WebSocket (Redis Pub/Sub para multi-worker)
- Loop de percepción-acción: screenshot → análisis LLM → ejecución → broadcast
- Estados: `pending` → `running` → `paused` → `completed`/`failed`/`stopped`
- Rate limit: máximo 3 sesiones concurrentes por usuario

### Providers de Visión (con Fallback Automático)
- **Anthropic Native** — Computer Use API beta (`computer_20241022` tool)
- **OpenAI GPT-4o** — Vision con JSON parsing
- **Ollama Local** — llava, bakllava, moondream (gratis/privado)
- **Fallback chain**: Anthropic → OpenAI → Ollama (auto-detecta disponibilidad)

---

## Infraestructura & Monitoreo

### Grafana Dashboard
Ubicación: `infra/grafana/dashboards/computer-use-dashboard.json`

Paneles incluidos:
- **Sesiones Activas** — Gauge en tiempo real
- **Rate de Sesiones (5m)** — Creadas, completadas, fallidas por provider
- **Uso por Provider** — Donut chart
- **Acciones por Tipo** — Barras apiladas de clicks, types, scrolls, etc.
- **Duración de Pasos (p50/p95/p99)** — Percentiles con leyenda
- **Duración de Sesiones (p95)** — Histograma de tiempos completos
- **Sesiones Detenidas vs Fallidas** — Comparación temporal
- **Top 10 Razones de Falla** — Tabla ordenada

Para Docker Compose:
```bash
docker-compose up -d grafana prometheus
```
Grafana: http://localhost:3000 (admin/admin)
Prometheus: http://localhost:9090

### Métricas Prometheus
| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `computer_use_sessions_created_total` | Counter | Sesiones creadas (por provider) |
| `computer_use_sessions_completed_total` | Counter | Sesiones completadas |
| `computer_use_sessions_failed_total` | Counter | Sesiones fallidas (por provider, razón) |
| `computer_use_sessions_stopped_total` | Counter | Sesiones detenidas por usuario |
| `computer_use_steps_total` | Counter | Pasos ejecutados (por action_type) |
| `computer_use_step_duration_seconds` | Histogram | Duración de cada paso |
| `computer_use_session_duration_seconds` | Histogram | Duración de sesiones completas |
| `computer_use_active_sessions` | Gauge | Sesiones activas actualmente |

---

## Export & Reporting

### PDF Export
Endpoint: `POST /api/v1/computer-use/sessions/{id}/export`

- Renderiza HTML con CSS profesional (headers degradados, badges de estado)
- Incluye timeline de acciones con screenshots embebidos en base64
- Muestra anotaciones de cada paso
- Generado con Playwright (`page.pdf()`) — no requiere librerías extra

### CSV Export
- Tabla de pasos con: step_number, action_type, params, reason, result, execution_ms

### JSON Export
- Estructura completa: session + steps + annotations

### Session Replay
Endpoint: `GET /api/v1/computer-use/sessions/{id}/replay`

- Reproduce paso a paso cualquier sesión pasada
- Controles: play/pause, velocidad (0.5x, 1x, 2x, 4x)
- Navegación con flechas del teclado
- Marcadores de anotaciones sobre el screenshot
- Panel lateral con detalle de cada acción

---

## Multi-Navegador

### Browser Pool Manager
- Pool de instancias reutilizables (máx. 6 por defecto)
- Soporta **Chromium**, **Firefox**, **WebKit**
- Reutilización inteligente: instancias del mismo tipo se reciclan
- Estrategias de adquisición: round-robin, random, least-used
- Cleanup automático entre sesiones (cookies, localStorage)

### Selección por Sesión
```json
POST /api/v1/computer-use/sessions
{
  "task_description": "...",
  "browser_type": "firefox"  // chromium | firefox | webkit
}
```

### Grid de Sesiones Activas
- Visualización en tarjetas con indicador de navegador (🌐🦊🧭)
- Estado en tiempo real con polling cada 5 segundos
- Click para conectarse a cualquier sesión activa

---

## Seguridad & Validación

### Action Validator
Valida cada acción antes de ejecutar:
- **Navigate**: bloquea `javascript:`, `data:`, `file://`, dominios en blacklist
- **Click**: coordenadas dentro de rangos razonables (0-4096)
- **Type**: límite de 10,000 chars, detección de datos sensibles (tarjetas, SSN)
- **Scroll**: direcciones válidas, montos máximos
- **Wait**: máximo 60 segundos

### Retry Handler
- Reintentos con backoff exponencial + jitter
- Circuit Breaker por provider (5 fallos → open, 30s recovery)
- Callback `on_retry` para notificaciones

### CAPTCHA Detector
- Detección de elementos: `#recaptcha`, `.h-captcha`, `#turnstile`, iframes
- Keywords: "I'm not a robot", "security check", "challenge"
- Pausa automática de la sesión + notificación vía webhook
- Mensaje contextual según nivel de confianza

### Proxy Manager
- Soporta HTTP, HTTPS, SOCKS5
- Rotación: round-robin, random, least-used
- Health checks vía `httpbin.org/ip`
- Estadísticas de uso y salud

### Credential Manager
- Credenciales encriptadas por dominio
- Auto-login detectando formularios
- Selectores CSS configurables por sitio
- Campos extra (2FA, tokens, etc.)

---

## Automatización Avanzada

### Plantillas
- Guardar tareas frecuentes como plantillas reutilizables
- Tags y búsqueda
- Contador de uso
- Uso con un click: aplica task + URL inicial

### Tareas Programadas (Cron)
- Expresiones cron estándar
- Timezone configurable
- Tracking de ejecuciones: success/fail count
- Última sesión ejecutada referenciada

### Batch Jobs
- Misma tarea ejecutada en múltiples URLs
- Concurrencia configurable (default: 3)
- Tracking de progreso: completed/failed/total

### Browser Profiles
- Viewport personalizado (mobile, desktop, tablet)
- User-Agent, locale, timezone
- Cookies y localStorage pre-cargados
- Geolocalización simulada
- Perfil default automático

### Session Cloning
- Duplicar cualquier sesión como punto de partida
- Preserva task, URL, browser type, perfil
- Ideal para iterar sobre la misma tarea

### Smart Wait
- Espera por elemento visible/oculto/enabled
- Espera por navegación o URL específica
- Espera por texto en la página
- Espera por estabilidad del DOM
- Espera por request de red o mensaje de consola

---

## Colaboración

### Compartir Sesiones
- Enlace con token único y expiración
- Permisos: `view` | `comment` | `control`
- Compartir por email o user_id
- Sin necesidad de autenticación (acceso vía token)

### Anotaciones
- Comentarios en screenshots específicos (por step)
- Coordenadas x/y opcionales (marcador visual)
- Colores personalizables
- Visibles en replay y PDF export

### Bookmarks
- Marcar pasos importantes con etiqueta
- Navegación rápida entre bookmarks
- Colores personalizables

### Webhooks
- Eventos: `session.completed`, `session.failed`, `session.captcha_detected`, `batch.completed`
- Firma HMAC-SHA256 para verificación
- Retry con backoff exponencial
- Tracking de delivery y fallos

---

## Inteligencia

### OCR Service
- Extrae texto de screenshots (easyocr / pytesseract)
- Regiones con coordenadas para click preciso
- Búsqueda de texto específico en imagen
- Detección de campos de formulario visuales

### DOM Inspector
- Extracción de elementos interactivos con coordenadas
- Árbol de accesibilidad simplificado
- Estado de formularios (values, checked)
- Búsqueda de elementos por texto

### Screenshot Comparator
- Detección de stale states (página sin cambios)
- Similaridad con SSIM (si scikit-image disponible)
- Imagen de diff resaltada en rojo
- Alerta automática en sesión

### Performance Budget
- Alertas por duración de sesión, pasos, retries, stale states
- Niveles: info / warning / critical
- Recomendaciones automáticas
- Summary al finalizar sesión

### AI Suggestions
- Sugiere acciones basadas en sesiones similares previas
- Embeddings de tareas para similitud
- Sugerencias de recuperación tras errores
- Basado en historial de éxitos

---

## Mobile & Emulación

### Presets de Dispositivos
- iPhone 14, iPhone 14 Pro Max
- iPad Pro 12.9
- Google Pixel 7
- Samsung Galaxy S23
- Desktop HD (1920x1080)
- Desktop 4K (3840x2160)

Endpoint: `GET /api/v1/computer-use/mobile-presets`

---

## Debugging

### Browser Logger
- Captura logs de consola del navegador
- Captura errores JS (`pageerror`)
- Monitorea network requests/responses
- Filtra errores y requests fallidos
- Exporta logs serializables

### Console/Network Viewer (Frontend)
- Tab de console con niveles coloreados
- Tab de network con method, status, duration
- Actualización en tiempo real

---

## Import/Export de Configuración

### Export
Endpoint: `POST /api/v1/computer-use/config/export`

Exporta: templates, profiles, proxies (sin passwords), webhooks (sin secrets)

### Import
Endpoint: `POST /api/v1/computer-use/config/import`

Importa toda la configuración de un JSON.

---

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `P` | Pausar sesión |
| `R` | Reanudar sesión |
| `Shift + S` | Detener sesión |
| `Shift + F` | Pantalla completa |
| `Shift + H` | Abrir historial |
| `Shift + M` | Abrir chat |
| `← →` | Navegar replay |
| `Espacio` | Play/Pause replay |
| `Esc` | Cerrar replay |

---

## API Reference

### Endpoints Extendidos

```
# Templates
POST   /api/v1/computer-use/templates
GET    /api/v1/computer-use/templates
POST   /api/v1/computer-use/templates/{id}/use

# Scheduled Tasks
POST   /api/v1/computer-use/scheduled-tasks
GET    /api/v1/computer-use/scheduled-tasks

# Annotations
POST   /api/v1/computer-use/sessions/{id}/annotations
GET    /api/v1/computer-use/sessions/{id}/annotations

# Bookmarks
POST   /api/v1/computer-use/sessions/{id}/bookmarks
GET    /api/v1/computer-use/sessions/{id}/bookmarks

# Browser Profiles
POST   /api/v1/computer-use/browser-profiles
GET    /api/v1/computer-use/browser-profiles

# Proxy Configs
POST   /api/v1/computer-use/proxy-configs
GET    /api/v1/computer-use/proxy-configs

# Session Sharing
POST   /api/v1/computer-use/sessions/{id}/shares
GET    /api/v1/computer-use/sessions/{id}/shares
GET    /api/v1/computer-use/shared-sessions/{token}

# Batch Jobs
POST   /api/v1/computer-use/batch-jobs
GET    /api/v1/computer-use/batch-jobs

# Tags
POST   /api/v1/computer-use/sessions/{id}/tags
GET    /api/v1/computer-use/sessions/{id}/tags
GET    /api/v1/computer-use/tags/search?tag={tag}

# Clone
POST   /api/v1/computer-use/sessions/{id}/clone

# Mobile Presets
GET    /api/v1/computer-use/mobile-presets

# Config Import/Export
POST   /api/v1/computer-use/config/export
POST   /api/v1/computer-use/config/import

# Webhooks
POST   /api/v1/computer-use/webhooks
GET    /api/v1/computer-use/webhooks

# Export & Replay
POST   /api/v1/computer-use/sessions/{id}/export     # pdf | csv | json
GET    /api/v1/computer-use/sessions/{id}/replay

# Analytics
GET    /api/v1/computer-use/analytics/summary
GET    /api/v1/computer-use/active-sessions
GET    /api/v1/computer-use/browser-pool/stats
```

---

## Inicialización

```bash
# Crear tablas extendidas
python -m backend.scripts.init_computer_use_extended

# Iniciar con monitoreo
docker-compose up -d backend frontend grafana prometheus
```

---

## Archivos Creados

### Backend (Nuevos)
- `services/pdf_service.py` — Export PDF/CSV/JSON
- `services/browser_pool.py` — Pool multi-navegador
- `services/action_validator.py` — Validación de acciones
- `services/retry_handler.py` — Retry + Circuit Breaker
- `services/captcha_detector.py` — Detección CAPTCHA
- `services/proxy_manager.py` — Gestión de proxies
- `services/webhook_service.py` — Webhooks con HMAC
- `services/screenshot_compare.py` — Comparación de screenshots
- `services/credential_manager.py` — Auto-login
- `services/ocr_service.py` — OCR en screenshots
- `services/dom_inspector.py` — Inspector DOM
- `services/performance_budget.py` — Alertas de performance
- `services/mobile_presets.py` — Presets de dispositivos
- `services/smart_wait.py` — Esperas inteligentes
- `services/browser_logger.py` — Logs de navegador
- `services/ai_suggestions.py` — Sugerencias basadas en historial
- `session_manager_v2.py` — Session manager mejorado
- `models_extended.py` — Modelos extendidos
- `schemas_extended.py` — Schemas extendidos
- `api/v1/computer_use_extended.py` — API extendida

### Frontend (Nuevos)
- `ComputerUseReplay.tsx` — Reproductor de sesiones
- `ComputerUseExportButton.tsx` — Botón exportar PDF/CSV/JSON
- `ComputerUseBatchPanel.tsx` — Panel de batch jobs
- `ComputerUseAnnotationsOverlay.tsx` — Anotaciones en screenshots
- `ComputerUseTemplatesPanel.tsx` — Panel de plantillas
- `ComputerUseActiveGrid.tsx` — Grid de sesiones activas
- `ComputerUseMobilePresets.tsx` — Selector de dispositivos
- `ComputerUseConsoleViewer.tsx` — Viewer de console/network
- `ComputerUseBookmarks.tsx` — Marcadores de pasos
- `useComputerUseKeyboardShortcuts.ts` — Hook de atajos

### Infra (Nuevos/Actualizados)
- `infra/grafana/dashboards/computer-use-dashboard.json` — Dashboard
- `infra/monitoring/prometheus/prometheus.yml` — Config Prometheus
- `infra/monitoring/grafana/provisioning/` — Provisionamiento Grafana
- `docker-compose.yml` — Grafana + Prometheus services
- `infra/helm/monitoring/prometheus-values.yaml` — Dashboard en Helm

### Tests
- `tests/computer_use/test_services.py` — Tests de servicios
- `tests/computer_use/test_extended_api.py` — Tests de API extendida

### Docs
- `docs/COMPUTER_USE_FEATURES.md` — Documentación completa
