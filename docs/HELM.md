# Helm Charts — Kubernetes Deployment

Chart de Helm para desplegar SellIA en cualquier cluster Kubernetes.

## Dependencias

| Chart | Versión | Propósito |
|-------|---------|-----------|
| postgresql | 13.2.0 | Base de datos (opcional, modo dev) |
| redis | 18.6.0 | Cache y rate limiting (opcional, modo dev) |

## Instalación

```bash
# Añadir repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm dependency update infra/helm/sellia

# Instalar en namespace sellia
helm upgrade --install sellia infra/helm/sellia \
  --namespace sellia --create-namespace \
  --values infra/helm/sellia/values.yaml \
  --set secrets.secretKey="$(openssl rand -hex 32)" \
  --set secrets.databaseUrl="postgresql://..." \
  --set secrets.redisUrl="redis://..."

# Production overrides
helm upgrade --install sellia infra/helm/sellia \
  --namespace sellia \
  --values infra/helm/sellia/values.yaml \
  --values infra/helm/sellia/values-production.yaml
```

## Valores de producción (`values-production.yaml`)

```yaml
backend:
  replicaCount: 3
  autoscaling:
    minReplicas: 3
    maxReplicas: 20
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi

frontend:
  replicaCount: 3
  autoscaling:
    minReplicas: 3
    maxReplicas: 20

postgresql:
  enabled: false  # Usar RDS externo

redis:
  enabled: false  # Usar ElastiCache externo

ingress:
  hosts:
    - host: app.sellia.com
```

## Seguridad

- **Pod Security Standards**: Namespace en modo `restricted`
- **Network Policies**: Solo tráfico permitido entre componentes
- **Security Context**: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`
- **Pod Disruption Budgets**: Garantiza disponibilidad durante upgrades
- **HPA**: Escalado automático basado en CPU/memoria

## Actualización

```bash
# Rollout restart
kubectl rollout restart deployment/sellia-backend -n sellia

# Verificar estado
kubectl get pods -n sellia
kubectl get hpa -n sellia
kubectl get networkpolicy -n sellia
```
