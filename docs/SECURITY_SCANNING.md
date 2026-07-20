# OWASP ZAP — Escaneo de Vulnerabilidades

Pipeline de seguridad automatizado con múltiples herramientas.

## Herramientas

| Herramienta | Tipo | Alcance |
|-------------|------|---------|
| **Semgrep** | SAST | Código fuente (OWASP Top 10, CWE Top 25) |
| **Trivy** | SCA | Dependencias (CVEs en Python/Node) |
| **OWASP ZAP** | DAST | Aplicación en ejecución |

## Workflow `.github/workflows/security-scan.yml`

### Triggers
- **Push/PR** a `main` o `develop`
- **Schedule** diario a las 3 AM UTC
- **Manual** (`workflow_dispatch`)

### Jobs

#### 1. Semgrep SAST
```bash
semgrep --config=p/owasp-top-ten \
        --config=p/cwe-top-25 \
        --config=p/security-audit \
        backend/ frontend/src/
```
- Falla si hay findings de severidad `ERROR`
- Reporte en `semgrep-results.json`

#### 2. Trivy Dependency Scan
```bash
trivy fs backend/requirements.txt   # Python deps
trivy fs frontend/package.json      # Node deps
```
- Solo CVEs `CRITICAL` y `HIGH`
- Reportes SARIF subidos a GitHub Security tab

#### 3. OWASP ZAP Baseline Scan
- Escaneo pasivo + spider básico
- Corre en cada PR/push
- Target: `http://localhost:3000` (app en Docker Compose)
- No falla el build (report only)

#### 4. OWASP ZAP Full Scan
- Escaneo activo completo (todos los métodos HTTP)
- Solo en schedule y manual
- Puede tardar 30-60 minutos

## Configuración ZAP

Archivo `.zap/rules.tsv`:
- Desactiva findings informativos de headers de seguridad (ya los manejamos en código)
- Reduce ruido en CI

## Ver resultados

1. **GitHub Actions artifacts**: Descargar reportes HTML/JSON
2. **GitHub Security tab**: Trivy SARIF integrado
3. **ZAP Reports**: `report_*.html` con detalle de vulnerabilidades

## Integración con CI/CD

```yaml
# En .github/workflows/ci.yml
jobs:
  test:
    # ...

  security:
    uses: ./.github/workflows/security-scan.yml
    secrets: inherit
```

## Recomendaciones

- **ZAP Baseline** en cada PR (rápido, no bloqueante)
- **ZAP Full** semanalmente (profundo, revisión manual)
- **Trivy** en cada cambio de dependencias
- **Semgrep** en cada push (bloqueante para findings críticos)
