"""
Métricas Prometheus para SellIA.
Este módulo expone métricas custom de negocio y seguridad.
Se importa desde main.py para instrumentación automática y desde
auth.py para métricas de login.
"""

from prometheus_client import Counter, Histogram, Gauge

# Métricas de autenticación
SELLIA_LOGINS = Counter(
    "sellia_logins_total",
    "Total de logins",
    ["status"]
)

SELLIA_FAILED_LOGINS = Counter(
    "sellia_failed_logins_total",
    "Total de logins fallidos",
    ["ip"]
)

SELLIA_GEOFENCE_VIOLATIONS = Counter(
    "sellia_geofence_violations_total",
    "Violaciones de geofencing"
)

SELLIA_NEW_DEVICES = Counter(
    "sellia_new_devices_total",
    "Nuevos dispositivos detectados"
)

SELLIA_RATE_LIMIT_HITS = Counter(
    "sellia_rate_limit_hits_total",
    "Hits de rate limiting",
    ["endpoint"]
)

# Métricas de rendimiento
SELLIA_REQUEST_DURATION = Histogram(
    "sellia_request_duration_seconds",
    "Duración de requests",
    ["path"]
)

SELLIA_REQUESTS = Counter(
    "sellia_requests_total",
    "Total de requests",
    ["status", "path"]
)

# Métricas de sesiones
SELLIA_ACTIVE_SESSIONS = Gauge(
    "sellia_active_sessions",
    "Sesiones activas"
)

# Métricas de Computer Use Agents
COMPUTER_USE_SESSIONS_CREATED = Counter(
    "computer_use_sessions_created_total",
    "Total de sesiones de Computer Use creadas",
    ["provider"],
)

COMPUTER_USE_SESSIONS_COMPLETED = Counter(
    "computer_use_sessions_completed_total",
    "Total de sesiones de Computer Use completadas",
    ["provider"],
)

COMPUTER_USE_SESSIONS_FAILED = Counter(
    "computer_use_sessions_failed_total",
    "Total de sesiones de Computer Use fallidas",
    ["provider", "reason"],
)

COMPUTER_USE_SESSIONS_STOPPED = Counter(
    "computer_use_sessions_stopped_total",
    "Total de sesiones de Computer Use detenidas por el usuario",
)

COMPUTER_USE_STEPS_TOTAL = Counter(
    "computer_use_steps_total",
    "Total de pasos ejecutados en Computer Use",
    ["action_type"],
)

COMPUTER_USE_STEP_DURATION = Histogram(
    "computer_use_step_duration_seconds",
    "Duración de cada paso (screenshot + LLM + ejecución)",
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 60.0],
)

COMPUTER_USE_SESSION_DURATION = Histogram(
    "computer_use_session_duration_seconds",
    "Duración total de sesiones de Computer Use",
    buckets=[10.0, 30.0, 60.0, 120.0, 180.0, 300.0, 600.0],
)

COMPUTER_USE_ACTIVE_SESSIONS = Gauge(
    "computer_use_active_sessions",
    "Sesiones de Computer Use activas en este momento",
)
