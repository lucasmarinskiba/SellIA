# SellIA Vercel Integration

Conecta frontend Next.js con backend FastAPI.

---

## Estructura

```
frontend/
├── src/lib/sellia-api.ts          ✅ Cliente HTTP para backend
├── src/hooks/useSellIA.ts         ✅ Custom React hooks
├── src/app/                       📱 Pages (existentes)
└── package.json
```

---

## Configuración

### 1. Environment Variables

**`.env.local` (desarrollo local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

**Vercel (production):**
```bash
NEXT_PUBLIC_API_URL=https://api.sellia.io
NEXT_PUBLIC_ENVIRONMENT=production
```

### 2. Backend Requerido

Backend FastAPI debe estar corriendo:
```bash
# Local
uvicorn app.sellbot:app --reload

# Production
# Fly.io, Heroku, AWS, etc.
```

---

## Uso

### Hooks Disponibles

**Leads:**
```typescript
import { useLeads, useLead } from "@/hooks/useSellIA";

// List leads
const { leads, loading, error } = useLeads({ status: "engaged" });

// Get single lead
const { lead, loading, error } = useLead(42);
```

**Analytics:**
```typescript
import { 
  useAnalyticsFunnel,
  useAnalyticsEmail,
  useAnalyticsLeadHealth,
  useAnalyticsSummary 
} from "@/hooks/useSellIA";

const { funnel } = useAnalyticsFunnel();
const { metrics } = useAnalyticsEmail();
const { health } = useAnalyticsLeadHealth();
const { summary } = useAnalyticsSummary();
```

**Workflows:**
```typescript
import { useWorkflows } from "@/hooks/useSellIA";

const { workflows } = useWorkflows("active");
```

**Queue:**
```typescript
import { useQueueStats } from "@/hooks/useSellIA";

// Poll every 5 seconds
const { stats } = useQueueStats(5000);
```

### Componentes Sugeridos

**Dashboard de Leads (enganchados):**
```tsx
import { useAnalyticsLeadHealth } from "@/hooks/useSellIA";

export default function HotLeads() {
  const { health, loading } = useAnalyticsLeadHealth();

  if (loading) return <div>Cargando...</div>;

  return (
    <div>
      <h2>Leads Calientes ({health?.hot?.count || 0})</h2>
      {health?.hot?.leads?.map((lead) => (
        <div key={lead.id}>
          <p>{lead.name} - {lead.company}</p>
          <p>Score: {lead.score}</p>
          <p>Contactado hace: {lead.days_since_contact} días</p>
        </div>
      ))}
    </div>
  );
}
```

**Email Metrics:**
```tsx
import { useAnalyticsEmail } from "@/hooks/useSellIA";

export default function EmailMetrics() {
  const { metrics, loading } = useAnalyticsEmail();

  if (loading) return <div>Cargando...</div>;

  return (
    <div>
      <p>Entregados: {metrics?.delivery_rate}%</p>
      <p>Abiertos: {metrics?.open_rate}%</p>
      <p>Clicks: {metrics?.click_rate}%</p>
    </div>
  );
}
```

**Queue Monitor (Real-time):**
```tsx
import { useQueueStats } from "@/hooks/useSellIA";

export default function QueueMonitor() {
  const { stats } = useQueueStats(2000);  // Poll every 2s

  return (
    <div>
      <p>En cola: {stats?.queued || 0}</p>
      <p>Procesando: {stats?.processing || 0}</p>
      <p>Fallidas: {stats?.failed || 0}</p>
    </div>
  );
}
```

---

## Deployment

### Vercel

1. **Setup remoto:**
```bash
cd frontend
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://api.sellia.io
vercel env add NEXT_PUBLIC_ENVIRONMENT
# Enter: production
```

2. **Deploy:**
```bash
vercel deploy --prod
```

### Backend (Fly.io)

1. **Setup Fly:**
```bash
cd backend
fly launch
fly env set SENDGRID_API_KEY=sg_...
fly env set DATABASE_URL=postgresql://...
fly env set REDIS_URL=redis://...
```

2. **Deploy:**
```bash
fly deploy
```

### CORS

Backend debe permitir Vercel:
```python
# backend/app/sellbot.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sellia-brain.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Endpoints Integrados

**Base:** `NEXT_PUBLIC_API_URL/api/v1`

```
GET  /leads                  (list)
POST /leads                  (create)
GET  /leads/{id}             (get)
PUT  /leads/{id}             (update)

GET  /workflows              (list)
POST /workflows/{id}/enroll-lead

GET  /analytics/funnel       (sales funnel)
GET  /analytics/email-metrics
GET  /analytics/lead-sources
GET  /analytics/lead-health
GET  /analytics/summary      (dashboard completo)

GET  /queue/stats            (queue monitoring)
GET  /queue/peek

GET  /progression/{id}/workflow-executions
```

---

## Troubleshooting

### API No responde
```bash
# 1. Verificar backend
curl http://localhost:8000/api/ping
# Expected: {"status": "ok", "service": "SellIA Sellbot"}

# 2. Verificar CORS
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS http://localhost:8000/api/ping -v

# 3. Verificar env var
echo $NEXT_PUBLIC_API_URL
```

### Hooks devuelven error
```typescript
// Agregar error handler
const { leads, error } = useLeads();
if (error) {
  console.error("API Error:", error);
}
```

### CORS bloqueado en prod
Agregar headers en vercel.json:
```json
{
  "headers": [
    {
      "source": "/api/:path*",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ]
}
```

---

## Componentes Faltantes (TODO)

Importar `sellia-api.ts` y hooks en:
- `app/dashboard/crecimiento/page.tsx` → useAnalyticsFunnel + useLeads
- `app/dashboard/metricas/page.tsx` → useAnalyticsSummary + charts
- `app/dashboard/pipeline/page.tsx` → useLeads + status filters
- `app/dashboard/escuadrones/[squadId]/page.tsx` → useQueueStats + executions

---

## Ejemplo Completo

**`src/app/dashboard/panel-sellia/page.tsx`:**
```tsx
'use client';

import {
  useAnalyticsSummary,
  useQueueStats,
  useAnalyticsLeadHealth,
} from '@/hooks/useSellIA';

export default function SellIAPanel() {
  const { summary, loading: summaryLoading } = useAnalyticsSummary();
  const { stats } = useQueueStats(5000);
  const { health } = useAnalyticsLeadHealth();

  if (summaryLoading) return <div>Cargando SellIA...</div>;

  const funnel = summary?.funnel || {};
  const emailMetrics = summary?.email_metrics || {};

  return (
    <div className="space-y-8">
      <h1>Panel SellIA - Datos en Vivo</h1>

      {/* Funnel */}
      <section>
        <h2>Embudo de Ventas</h2>
        <p>Nuevos: {funnel.new}</p>
        <p>Contactados: {funnel.contacted}</p>
        <p>Enganchados: {funnel.engaged}</p>
        <p>Calificados: {funnel.qualified}</p>
        <p>Ganados: {funnel.won}</p>
      </section>

      {/* Email Metrics */}
      <section>
        <h2>Email Performance</h2>
        <p>Enviados: {emailMetrics.total_sent}</p>
        <p>Tasa apertura: {emailMetrics.open_rate}%</p>
        <p>Tasa click: {emailMetrics.click_rate}%</p>
      </section>

      {/* Queue */}
      <section>
        <h2>Queue en Tiempo Real</h2>
        <p>En cola: {stats?.queued || 0}</p>
        <p>Procesando: {stats?.processing || 0}</p>
        <p>Fallidas: {stats?.failed || 0}</p>
      </section>

      {/* Hot Leads */}
      <section>
        <h2>Leads Calientes ({health?.hot?.count || 0})</h2>
        {health?.hot?.leads?.map((lead: any) => (
          <div key={lead.id} className="border p-4">
            <p>
              <strong>{lead.name}</strong> - {lead.company}
            </p>
            <p>Score: {lead.score} | Contactado: {lead.days_since_contact}d</p>
          </div>
        ))}
      </section>
    </div>
  );
}
```

---

✅ **Frontend + Backend integrados**
✅ **Hooks listos para usar**
✅ **Variables de env configuradas**
✅ **CORS habilitado**

Deployment: Vercel (frontend) + Fly.io (backend)
