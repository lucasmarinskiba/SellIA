# Agente IA - Vendedor Automático

Sistema integral de agentes de IA que automatiza todo el ciclo de ventas: desde la captación de clientes hasta la concretación de la venta, incluyendo logística de entrega.

## Stack Tecnológico

- **Backend**: Python + FastAPI + SQLAlchemy (async)
- **Frontend**: Next.js 15 + Tailwind CSS
- **Base de Datos**: PostgreSQL 16
- **Cache/Colas**: Redis + Celery
- **Agentes IA**: OpenAI / LangGraph
- **Contenedores**: Docker + Docker Compose
- **Infraestructura**: Terraform + Helm + Kubernetes (EKS)
- **Observabilidad**: Prometheus + Grafana
- **Seguridad**: OWASP ZAP + Semgrep + Trivy

## Requisitos

- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Node.js 20+ (solo si quieres correr el frontend fuera de Docker)
- Python 3.12+ (solo si quieres correr el backend fuera de Docker)

## Inicio Rápido

### 1. Clonar y entrar al proyecto

```bash
cd "Agente IA - Vendedor Automático"
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales (OpenAI, WhatsApp, etc.)
```

### 3. Levantar con Docker Compose

```bash
docker-compose up --build -d
```

Esto levanta:
- PostgreSQL en `localhost:5432`
- Redis en `localhost:6379`
- Backend en `http://localhost:8000`
- Frontend en `http://localhost:3000`

### 4. Crear las tablas de la base de datos

```bash
docker-compose exec backend python init_db.py
```

### 5. Acceder a la aplicación

- **Frontend**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs

## Funcionalidades actuales

### Autenticación y Seguridad
- [x] Registro e inicio de sesión con JWT + httpOnly cookies
- [x] 2FA TOTP con códigos de backup (8 códigos SHA-256)
- [x] Rate limiting por endpoint con Redis
- [x] Geofencing con detección de ubicación anómala
- [x] Detección de nuevos dispositivos con notificaciones
- [x] HIBP integration (breaches de email y contraseñas)
- [x] Cloudflare Turnstile CAPTCHA
- [x] Bloqueo de países y threat intel
- [x] Session management con revocación remota
- [x] Audit logs con filtros y panel admin
- [x] ELK integration (ECS logging)

### Negocio
- [x] Creación de negocios por tipo (servicios, bienes, digitales, mixto)
- [x] Configuración por defecto según tipo de negocio
- [x] Gestión de catálogo (productos, servicios, digitales)
- [x] Panel de control con métricas
- [x] Estructura lista para integraciones con canales

### Infraestructura y DevOps
- [x] Terraform (AWS: VPC, EKS, RDS, ElastiCache, ALB, S3, CloudFront)
- [x] Helm Charts (Kubernetes deployment)
- [x] Prometheus + Grafana (métricas y dashboards)
- [x] OWASP ZAP + Semgrep + Trivy (security scanning CI/CD)
- [x] GitHub Actions (CI/CD multi-stage)
- [x] Playwright E2E tests

## Tipos de Negocio

### Servicios
- Modalidad: home office, presencial, híbrido
- Zonas de cobertura
- Disponibilidad horaria
- Duración de turnos

### Bienes / Productos
- Métodos de entrega: envío, retiro en local, punto de encuentro
- Integraciones con correos: Andreani, DHL, Mercado Envíos, OCA, Correo Argentino
- Calculadora de envíos

### Productos Digitales
- Entrega automática post-pago
- Links expirables
- Protección contra descargas masivas

## Próximas Fases

- **Fase 2**: Canales de comunicación (WhatsApp, Email, Instagram)
- **Fase 3**: Agentes IA con LangGraph (captación, cualificación, cierre)
- **Fase 4**: Integraciones con marketplaces (MercadoLibre, Amazon, Beacons)
- **Fase 5**: Logística completa y tracking de envíos
- **Fase 6**: Analytics, billing y multi-tenant (SaaS)

## Estructura del Proyecto

```
.
├── backend/
│   ├── app/
│   │   ├── core/          # Config, DB, seguridad
│   │   ├── api/v1/        # Routers FastAPI
│   │   └── domains/       # Módulos por dominio
│   ├── init_db.py         # Script para crear tablas
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/           # App Router Next.js
│       ├── components/    # Componentes reutilizables
│       ├── lib/           # API clients
│       └── hooks/         # Custom hooks
├── docker-compose.yml
└── .env.example
```

## Desarrollo local (sin Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
python init_db.py  # necesitas PostgreSQL corriendo
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Licencia

Proyecto privado - Uso personal y comercial bajo desarrollo.
