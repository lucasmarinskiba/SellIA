# ELK Stack Integration - Guía de Monitoreo de Seguridad

SellIA puede exportar todos los eventos de seguridad (logins, dispositivos nuevos, violaciones de geofencing, breaches detectados) a **Elasticsearch** para análisis avanzado, dashboards y alertas.

## Arquitectura

```
SellIA Backend
       │
       ├──► Filebeat (lector de archivos)
       │       │
       │       ▼
       │   Logstash (parseo/filtrado)
       │       │
       │       ▼
       └──► Elasticsearch (almacenamiento)
               │
               ▼
           Kibana (visualización)
```

O directamente:

```
SellIA Backend ──► Elasticsearch (HTTP API)
```

---

## Modo 1: Filebeat (Recomendado)

### Ventajas
- ✅ No dependencia de red en cada evento
- ✅ Buffer local si Elasticsearch está caído
- ✅ Formato JSON Lines estándar
- ✅ Fácil de escalar

### Configuración

#### 1. Habilitar escritura a archivo

```bash
# .env
ELK_ENABLED=true
ELK_USE_FILEBEAT=true
ELK_LOG_PATH=/var/log/sellia/security.json
```

#### 2. Configurar Filebeat

Crear `/etc/filebeat/modules.d/sellia.yml`:

```yaml
- module: sellia
  enabled: true
  var.paths:
    - /var/log/sellia/security.json

filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/sellia/security.json
  json.keys_under_root: true
  json.add_error_key: true
  json.message_key: message
  fields:
    service: sellia
    environment: production
  fields_under_root: true

output.elasticsearch:
  hosts: ["https://your-cluster.cloud.es.io:9243"]
  api_key: "your-api-key"
  index: "sellia-security-logs-%{+yyyy.MM.dd}"

setup.ilm.enabled: true
setup.ilm.rollover_alias: "sellia-security-logs"
setup.ilm.pattern: "{now/d}-000001"
```

#### 3. Iniciar Filebeat

```bash
sudo systemctl enable filebeat
sudo systemctl start filebeat
sudo filebeat test output
```

---

## Modo 2: Direct Push

### Ventajas
- ✅ Sin infraestructura adicional (sin Filebeat)
- ✅ Logs inmediatos en Elasticsearch
- ⚠️ Si Elasticsearch está caído, se pierden los logs

### Configuración

```bash
# .env
ELK_ENABLED=true
ELK_USE_FILEBEAT=false
ELK_HOST=https://your-cluster.cloud.es.io:9243
ELK_INDEX=sellia-security-logs
ELK_API_KEY=your-api-key
```

---

## Elastic Cloud (SaaS)

### 1. Crear deployment

1. Ir a [Elastic Cloud](https://cloud.elastic.co/)
2. Crear nuevo deployment
3. Elegir región más cercana (ej: `aws-sa-east-1` para Brasil/Argentina)
4. Guardar credenciales de `elastic` user

### 2. Crear API Key

```bash
# En Kibana Dev Tools
POST /_security/api_key
{
  "name": "sellia-security-logs",
  "role_descriptors": {
    "sellia_writer": {
      "cluster": ["monitor"],
      "index": [
        {
          "names": ["sellia-security-logs*"],
          "privileges": ["create_index", "index", "create"]
        }
      ]
    }
  }
}
```

El resultado incluye `encoded` que va en `ELK_API_KEY`.

### 3. Configurar Kibana Index Pattern

1. Ir a Kibana → Stack Management → Index Patterns
2. Crear pattern: `sellia-security-logs-*`
3. Time field: `@timestamp`

---

## Dashboards Pre-construidos

### Dashboard 1: Login Overview

Visualizaciones:
- **Métrica**: Total logins (24h)
- **Métrica**: Intentos fallidos (24h)
- **Gráfico de barras**: Logins por hora
- **Mapa**: Logins por país (usando `source.geo.country_iso_code`)
- **Tabla**: Top usuarios con más logins

### Dashboard 2: Security Threats

Visualizaciones:
- **Métrica**: Nuevos dispositivos detectados
- **Métrica**: Violaciones de geofencing
- **Gráfico de líneas**: Intentos fallidos vs exitosos
- **Tabla**: IPs con más intentos fallidos
- **Alerta**: Trigger si failed_logins > 10 en 5 minutos

### Dashboard 3: Breach Monitoring

Visualizaciones:
- **Métrica**: Emails comprometidos detectados
- **Tabla**: Usuarios con breaches
- **Gráfico de barras**: Breaches por nombre

---

## Campos Indexados

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `@timestamp` | date | ISO 8601 UTC |
| `event.type[]` | keyword | `login`, `failed_login`, `new_device`, `geofence_violation`, `breach_detected` |
| `event.outcome` | keyword | `success`, `failure`, `unknown` |
| `message` | text | Descripción legible |
| `source.ip` | ip | IP del cliente |
| `source.geo.country_iso_code` | keyword | Código ISO del país |
| `user.id` | keyword | UUID de usuario |
| `user.email` | keyword | Email |
| `sellia.distance_km` | float | Distancia de geofencing |
| `sellia.device_info` | text | User-Agent |
| `sellia.breach_count` | integer | Cantidad de breaches |
| `sellia.breach_names[]` | keyword | Nombres de breaches |

---

## Watcher / Alertas

### Alerta: Múltiples logins fallidos

```json
POST _watcher/watch/sellia-brute-force
{
  "trigger": { "schedule": { "interval": "5m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["sellia-security-logs-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "term": { "event.type": "failed_login" } },
                { "range": { "@timestamp": { "gte": "now-5m" } }}
              ]
            }
          },
          "aggs": {
            "by_ip": {
              "terms": { "field": "source.ip", "size": 10, "min_doc_count": 5 }
            }
          }
        }
      }
    }
  },
  "condition": {
    "script": "ctx.payload.aggregations.by_ip.buckets.size() > 0"
  },
  "actions": {
    "send_email": {
      "email": {
        "to": ["security@tusitio.com"],
        "subject": "🚨 Posible ataque de fuerza bruta detectado",
        "body": "IPs sospechosas: {{#ctx.payload.aggregations.by_ip.buckets}}\n- {{key}}: {{doc_count}} intentos{{/ctx.payload.aggregations.by_ip.buckets}}"
      }
    }
  }
}
```

### Alerta: Login desde país bloqueado

```json
POST _watcher/watch/sellia-blocked-country
{
  "trigger": { "schedule": { "interval": "1m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["sellia-security-logs-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "terms": { "source.geo.country_iso_code": ["CN", "RU", "KP", "IR"] } },
                { "range": { "@timestamp": { "gte": "now-1m" } }}
              ]
            }
          }
        }
      }
    }
  },
  "condition": { "compare": { "ctx.payload.hits.total": { "gt": 0 } } },
  "actions": {
    "slack": {
      "webhook": {
        "method": "POST",
        "url": "https://hooks.slack.com/services/...",
        "body": "{\"text\":\"⚠️ Login desde país bloqueado: {{ctx.payload.hits.hits.0._source.source.geo.country_iso_code}} - {{ctx.payload.hits.hits.0._source.user.email}}\"}"
      }
    }
  }
}
```

---

## Troubleshooting

### Filebeat no envía logs

```bash
# Verificar logs de Filebeat
sudo journalctl -u filebeat -f

# Test de conectividad
sudo filebeat test output

# Verificar permisos del archivo JSON
ls -la /var/log/sellia/security.json
sudo chmod 644 /var/log/sellia/security.json
```

### Direct push devuelve 401

```bash
# Verificar API key
curl -X GET "$ELK_HOST/_cluster/health" \
  -H "Authorization: ApiKey $ELK_API_KEY"

# Si falla, regenerar API key en Kibana
```

### Elasticsearch index no se crea

```bash
# Crear manualmente
PUT /sellia-security-logs-2024.01.01
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  },
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "mapping": { "type": "keyword" }
        }
      }
    ]
  }
}
```

---

## Referencias

- [Filebeat Reference](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
- [Elasticsearch Ingest APIs](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html)
- [Elastic Cloud](https://www.elastic.co/cloud/)
- [ECS Fields](https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html)
