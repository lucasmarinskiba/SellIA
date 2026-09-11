# Automation Toggles Control System

Sistema de control granular para activar/desactivar automaciones, agentes y features per negocio.

## Overview

- **Models**: `AutomationToggle`, `ToggleAuditLog`
- **API**: 7 endpoints CRUD + dashboard
- **Middleware**: `toggle_enforcement_middleware` chequea antes de ejecutar
- **Frontend**: Tab en `/sellia-brain` con UI completa
- **Seed**: 12 toggles por defecto (4 agentes, 3 automations, 3 features, 2 integraciones)

## Quick Start

### Backend

1. **Crear migraciones**
   ```bash
   alembic upgrade head
   ```

2. **Seed toggles para negocio nuevo**
   ```bash
   POST /api/v1/automations/toggles/seed/{business_id}
   ```

3. **Listar toggles**
   ```bash
   GET /api/v1/automations/toggles/business/{business_id}
   ```

### Frontend

Navigate a `/sellia-brain` → Click tab "🎛️ Control Center"

Ver 12 toggles agrupados por categoría.

## API Endpoints

### CRUD

| Endpoint | Method | Descripción |
|----------|--------|-------------|
| `/toggles/business/{business_id}` | GET | Listar todos los toggles |
| `/toggles/business/{business_id}` | POST | Crear toggle manual (admin) |
| `/toggles/{toggle_id}` | GET | Obtener toggle específico |
| `/toggles/{toggle_id}` | PATCH | Cambiar ON/OFF o límite |
| `/toggles/{toggle_id}/audit` | GET | Historial de cambios |
| `/toggles/{toggle_id}/reset-usage` | POST | Reset contador mensual |
| `/toggles/dashboard/{business_id}` | GET | Stats consolidadas |
| `/toggles/seed/{business_id}` | POST | Seed 12 toggles por defecto |

### Example: Deshabilitar Feature

```bash
PATCH /api/v1/automations/toggles/{toggle_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "is_enabled": false
}
```

Response:
```json
{
  "id": "...",
  "business_id": "...",
  "toggle_key": "feature:computer_use",
  "is_enabled": false,
  "disabled_at": "2026-09-11T18:42:00Z",
  "monthly_limit": 100,
  "current_month_usage": 0
}
```

### Example: Cambiar Límite Mensual

```bash
PATCH /api/v1/automations/toggles/{toggle_id}
{
  "monthly_limit": 500
}
```

## Middleware Enforcement

Rutas protegidas:
- `/api/v1/computer_use` → feature:computer_use
- `/api/v1/sales_agents/lead_score` → agent:lead_scorer
- `/api/v1/sales_agents/negotiate` → agent:negotiation
- `/api/v1/email_sequences/send` → automation:email_sequences
- `/api/v1/fomo` → automation:fomo_campaigns
- `/api/v1/sms` → automation:sms_marketing

Comportamiento:
1. Request llega → middleware chequea si toggle está enabled
2. Si disabled → 403 "Feature deshabilitada"
3. Si alcanzó límite → 429 "Límite excedido"
4. Si OK → ejecuta endpoint
5. Si exitoso (status < 400) → incrementa `current_month_usage`

## Default Toggles (12)

### Agents (4)

| Key | Name | Limit |
|-----|------|-------|
| agent:lead_scorer | Lead Scorer IA | 1000/mes |
| agent:cold_email | Agente Cold Email | 500/mes |
| agent:negotiation | Agente Negociación | 200/mes |
| agent:competitor_intel | Inteligencia Competitiva | — |

### Automations (3)

| Key | Name | Limit |
|-----|------|-------|
| automation:email_sequences | Secuencias Email | — |
| automation:fomo_campaigns | Campañas FOMO | — |
| automation:sms_marketing | Marketing SMS | 5000/mes |

### Features (3)

| Key | Name | Limit |
|-----|------|-------|
| feature:dynamic_pricing | Precios Dinámicos | — |
| feature:predictive_analytics | Análisis Predictivo | — |
| feature:computer_use | Browser Automation | 100/mes |

### Integrations (2)

| Key | Name | Limit |
|-----|------|-------|
| integration:stripe | Stripe Payments | — |
| integration:meta_ads | Meta Ads Automation | — |

## Frontend Components

### ToggleSwitch
Individual toggle UI:
- ON/OFF button (visual switch)
- Usage progress bar (rojo/amarillo/verde)
- "Límite" button → inline form
- "📋" button → audit modal

### ControlCenter
Main dashboard:
- Sidebar: categorías con conteo
- Main: toggles por categoría
- Llama API al cambiar estado

### AuditPanel
Modal historial:
- Tabla con todos los cambios
- Quién, cuándo, qué cambió
- Timestamps en español (date-fns)

### ToggleAnalytics
Tab de analytics:
- 4 stat cards (total, enabled, disabled, usage)
- Tabla: categoría, total, enabled, %, usage
- Barras de progreso

## Testing

### Backend Tests

```bash
# Unit tests
pytest backend/tests/test_automation_toggles.py -v

# E2E tests
pytest backend/tests/test_automation_toggles_e2e.py -v
```

### Frontend Tests

```bash
# Component tests
npm test -- ToggleSwitch.test.tsx

# E2E (manual)
1. Go to /sellia-brain
2. Click Control Center tab
3. Toggle a feature ON/OFF
4. Click audit button → verify history
```

## Audit Log

Cada cambio genera entry:

```python
{
  "id": "...",
  "toggle_id": "...",
  "action": "disabled" | "enabled" | "limit_changed",
  "old_value": {"is_enabled": true, "monthly_limit": 1000},
  "new_value": {"is_enabled": false},
  "changed_by_email": "admin@example.com",
  "reason": "Cost control",
  "leads_affected": null,
  "estimated_impact_pct": null,
  "created_at": "2026-09-11T18:42:00Z"
}
```

## Integration with Onboarding

Cuando se crea negocio nuevo, se debe llamar:

```python
POST /api/v1/automations/toggles/seed/{business_id}
```

Esto crea los 12 toggles por defecto, todos enabled.

## Billing Integration

Toggles y límites se pueden mapear a planes:

- **Free**: solo 3 toggles (lead_scorer, email_sequences, sms)
- **Pro**: 8 toggles
- **Enterprise**: todos

Ver `backend/app/api/v1/automations.py:get_pricing_info` para detalles.

## Future Work

- [ ] Conditional toggles (ej: solo habilitar si conversion_rate > 5%)
- [ ] Auto-disable si error_rate > threshold
- [ ] Canary rollout: 5% → 25% → 50% → 100%
- [ ] Cost tracking: CT por toggle
- [ ] ROI calculator: revenue_generated / total_cost

## Support

Issues: check audit log first
- `/toggles/{toggle_id}/audit` → see history
- `/toggles/dashboard/{business_id}` → see stats

Debug middleware:
- Check if route is in `PROTECTED_ROUTES` map
- Check business_id extraction (query param o header X-Business-ID)
- Check if toggle enabled + within limit
