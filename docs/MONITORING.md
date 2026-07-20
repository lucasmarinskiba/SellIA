# Prometheus + Grafana — Monitoreo

Stack de observabilidad completo para SellIA.

## Arquitectura

```
┌─────────────────────────────────────────────┐
│              Grafana (UI)                    │
│         grafana.sellia.example.com           │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│           Prometheus Server                  │
│    • Scraping cada 15s                      │
│    • Retención 30d / 50GB                  │
│    • Alertmanager integrado                │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼────┐  ┌──▼────┐
│Backend│  │ Node  │  │ Kube  │
│Metrics│  │Export │  │State  │
└───────┘  └───────┘  └───────┘
```

## Métricas exponidas

### Métricas automáticas (Instrumentator)
- `http_requests_total` — Requests por método/status
- `http_request_duration_seconds` — Latencia por endpoint
- `http_request_size_bytes` — Tamaño de requests
- `http_response_size_bytes` — Tamaño de responses

### Métricas custom de negocio
| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `sellia_logins_total{status}` | Counter | Logins exitosos/fallidos |
| `sellia_failed_logins_total{ip}` | Counter | Logins fallidos por IP |
| `sellia_geofence_violations_total` | Counter | Violaciones de geofencing |
| `sellia_new_devices_total` | Counter | Nuevos dispositivos |
| `sellia_rate_limit_hits_total{endpoint}` | Counter | Hits de rate limiting |
| `sellia_active_sessions` | Gauge | Sesiones activas |
| `sellia_request_duration_seconds{path}` | Histogram | Latencia por path |
| `sellia_requests_total{status,path}` | Counter | Requests por status/path |

## Instalación

```bash
# Añadir repo de Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Instalar kube-prometheus-stack
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values infra/helm/monitoring/prometheus-values.yaml \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}" \
  --set alertmanager.config.global.slack_configs[0].api_url="${SLACK_WEBHOOK_URL}"

# Port-forward a Grafana
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```

## Dashboards

- **SellIA Security** (`infra/grafana/dashboards/security-dashboard.json`)
  - Logins 24h, failed logins, geofence violations, new devices
  - Login rate, rate limit hits, top IPs sospechosas

- **SellIA Performance** (`infra/grafana/dashboards/performance-dashboard.json`)
  - CPU/Memory por pod, P99 latency, error rate 5xx
  - Request rate by status, latency percentiles

## Alertas configuradas

| Alerta | Condición | Canal |
|--------|-----------|-------|
| High Error Rate | 5xx > 5% | PagerDuty + Slack |
| High Latency | p99 > 500ms | Slack |
| Geofence Spike | > 5 violations/1h | Slack |
| Failed Login Spike | > 50 failed/1h | Slack |
| Pod CrashLoop | cualquier pod | PagerDuty |

## Scraping de app metrics

El backend expone métricas en `/metrics` (puerto 9090). Prometheus las descubre automáticamente via `pod` role con el label `app.kubernetes.io/component: backend`.
