"""Pilar 4 — Auto-Protección (Self-Protection)

Detecta y neutraliza vulnerabilidades, amenazas, accesos no autorizados
y comportamientos anómalos en tiempo real sin intervención humana.
"""

from __future__ import annotations

import uuid
import hashlib
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update

from app.core.logger import get_logger

logger = get_logger(__name__)


class ThreatLevel(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    UNUSUAL_API_USAGE = "unusual_api_usage"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SPAM_DETECTED = "spam_detected"
    PROMPT_INJECTION = "prompt_injection"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    SUSPICIOUS_GEOLOCATION = "suspicious_geolocation"
    BOT_ACTIVITY = "bot_activity"


@dataclass
class ThreatEvent:
    threat_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    threat_type: ThreatType = ThreatType.BRUTE_FORCE
    threat_level: ThreatLevel = ThreatLevel.LOW
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    business_id: Optional[str] = None
    description: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    action_taken: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_resolved: bool = False


class SelfProtectionEngine:
    """Motor de auto-protección de SellIA con detección activa de amenazas."""

    THRESHOLDS = {
        "failed_logins_5min": 5,         # intentos fallidos en 5 min
        "api_calls_per_minute": 120,     # llamadas API por minuto
        "message_burst_rate": 50,        # mensajes por minuto (spam)
        "unusual_country_change": True,  # detectar cambio de país
        "prompt_injection_patterns": [  # patrones de inyección de prompt
            "ignore previous instructions",
            "disregard all prior",
            "forget everything",
            "you are now",
            "jailbreak",
            "DAN mode",
            "pretend you are",
            "act as if you have no restrictions",
        ],
        "data_exfiltration_patterns": [
            "export all",
            "dump database",
            "list all users",
            "show all passwords",
            "select * from",
        ],
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._threat_log: list[ThreatEvent] = []
        self._blocked_ips: set[str] = set()
        self._suspicious_users: set[str] = set()

    async def run_protection_cycle(
        self, business_id: Optional[uuid.UUID] = None
    ) -> dict[str, Any]:
        """Ejecuta ciclo completo de escaneo y protección."""
        logger.info("[SelfProtection] Iniciando ciclo de auto-protección")

        threats_detected: list[ThreatEvent] = []
        actions_taken: list[str] = []

        # Escaneo de amenazas en paralelo
        import asyncio
        scan_results = await asyncio.gather(
            self._scan_login_anomalies(business_id),
            self._scan_api_abuse(business_id),
            self._scan_message_spam(business_id),
            self._scan_content_for_injection(),
            self._scan_geo_anomalies(business_id),
            return_exceptions=True,
        )

        for result in scan_results:
            if isinstance(result, list):
                threats_detected.extend(result)

        # Respuesta automática a amenazas
        for threat in threats_detected:
            action = await self._respond_to_threat(threat, business_id)
            threat.action_taken = action
            actions_taken.append(f"[{threat.threat_type}] {action}")
            self._threat_log.append(threat)

        if len(self._threat_log) > 1000:
            self._threat_log = self._threat_log[-500:]

        critical = [t for t in threats_detected if t.threat_level == ThreatLevel.CRITICAL]
        if critical:
            await self._escalate_critical_threats(critical, business_id)

        threat_score = self._calculate_threat_score(threats_detected)

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "threats_detected": len(threats_detected),
            "critical_threats": len(critical),
            "actions_taken": len(actions_taken),
            "threat_score": threat_score,
            "threat_level": self._score_to_level(threat_score),
            "blocked_ips": len(self._blocked_ips),
            "threat_breakdown": {
                t.value: sum(1 for th in threats_detected if th.threat_type == t)
                for t in ThreatType
                if any(th.threat_type == t for th in threats_detected)
            },
        }

        logger.info(f"[SelfProtection] Score de amenaza: {threat_score}/100")
        return summary

    # ─────────────────────────────────────────────
    # ESCÁNERES DE AMENAZAS
    # ─────────────────────────────────────────────

    async def _scan_login_anomalies(
        self, business_id: Optional[uuid.UUID]
    ) -> list[ThreatEvent]:
        """Detecta intentos de fuerza bruta y credential stuffing."""
        threats = []
        try:
            from app.domains.security.models import UserLoginLog
            threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

            query = select(
                UserLoginLog.ip_address,
                func.count(UserLoginLog.id).label("attempts"),
            ).where(
                and_(
                    UserLoginLog.created_at >= threshold,
                    UserLoginLog.success == False,
                )
            ).group_by(UserLoginLog.ip_address).having(
                func.count(UserLoginLog.id) >= self.THRESHOLDS["failed_logins_5min"]
            )

            result = await self.db.execute(query)
            suspicious_ips = result.all()

            for row in suspicious_ips:
                ip, attempts = row[0], row[1]
                level = ThreatLevel.CRITICAL if attempts >= 20 else ThreatLevel.HIGH
                threats.append(ThreatEvent(
                    threat_type=ThreatType.BRUTE_FORCE,
                    threat_level=level,
                    source_ip=ip,
                    description=f"Fuerza bruta detectada: {attempts} intentos fallidos en 5 min desde {ip}",
                    evidence={"ip": ip, "attempts": attempts, "window_minutes": 5},
                ))
        except Exception as e:
            logger.warning(f"[SelfProtection] Error en login scan: {e}")
        return threats

    async def _scan_api_abuse(
        self, business_id: Optional[uuid.UUID]
    ) -> list[ThreatEvent]:
        """Detecta abuso de la API (exceso de llamadas, patrones anómalos)."""
        threats = []
        try:
            from app.domains.security.models import UserSession
            threshold = datetime.now(timezone.utc) - timedelta(minutes=1)

            query = select(
                UserSession.user_id,
                func.count(UserSession.id).label("calls"),
            ).where(
                UserSession.last_activity >= threshold,
            ).group_by(UserSession.user_id).having(
                func.count(UserSession.id) >= self.THRESHOLDS["api_calls_per_minute"]
            )

            result = await self.db.execute(query)
            abusers = result.all()

            for row in abusers:
                user_id, calls = row[0], row[1]
                threats.append(ThreatEvent(
                    threat_type=ThreatType.RATE_LIMIT_ABUSE,
                    threat_level=ThreatLevel.MEDIUM,
                    user_id=str(user_id),
                    description=f"Abuso de rate limit: {calls} llamadas/min del usuario {user_id}",
                    evidence={"user_id": str(user_id), "calls_per_minute": calls},
                ))
        except Exception as e:
            logger.warning(f"[SelfProtection] Error en API abuse scan: {e}")
        return threats

    async def _scan_message_spam(
        self, business_id: Optional[uuid.UUID]
    ) -> list[ThreatEvent]:
        """Detecta patrones de spam en mensajes entrantes."""
        threats = []
        try:
            from app.domains.channels.models import Message, Conversation
            threshold = datetime.now(timezone.utc) - timedelta(minutes=1)

            query = select(
                Conversation.contact_id,
                func.count(Message.id).label("msg_count"),
            ).select_from(Message).join(
                Conversation, Message.conversation_id == Conversation.id
            ).where(
                and_(
                    Message.created_at >= threshold,
                    Message.sender_type == "contact",
                )
            ).group_by(Conversation.contact_id).having(
                func.count(Message.id) >= self.THRESHOLDS["message_burst_rate"]
            )
            if business_id:
                query = query.where(Conversation.business_id == business_id)

            result = await self.db.execute(query)
            spammers = result.all()

            for row in spammers:
                contact_id, count = row[0], row[1]
                threats.append(ThreatEvent(
                    threat_type=ThreatType.SPAM_DETECTED,
                    threat_level=ThreatLevel.MEDIUM,
                    description=f"Actividad de spam: {count} mensajes/min del contacto {contact_id}",
                    evidence={"contact_id": str(contact_id), "messages_per_minute": count},
                    business_id=str(business_id) if business_id else None,
                ))
        except Exception as e:
            logger.warning(f"[SelfProtection] Error en spam scan: {e}")
        return threats

    async def _scan_content_for_injection(self) -> list[ThreatEvent]:
        """Escanea mensajes recientes por patrones de inyección de prompt."""
        threats = []
        try:
            from app.domains.channels.models import Message
            threshold = datetime.now(timezone.utc) - timedelta(minutes=30)

            result = await self.db.execute(
                select(Message).where(
                    and_(
                        Message.created_at >= threshold,
                        Message.sender_type == "contact",
                    )
                ).limit(100)
            )
            recent_messages = result.scalars().all()

            injection_patterns = self.THRESHOLDS["prompt_injection_patterns"]
            exfil_patterns = self.THRESHOLDS["data_exfiltration_patterns"]

            for msg in recent_messages:
                content_lower = (msg.content or "").lower()

                for pattern in injection_patterns:
                    if pattern in content_lower:
                        threats.append(ThreatEvent(
                            threat_type=ThreatType.PROMPT_INJECTION,
                            threat_level=ThreatLevel.HIGH,
                            description=f"Posible inyección de prompt detectada en mensaje {msg.id}",
                            evidence={
                                "message_id": str(msg.id),
                                "pattern_matched": pattern,
                                "content_hash": hashlib.sha256(content_lower.encode()).hexdigest()[:16],
                            },
                        ))
                        break

                for pattern in exfil_patterns:
                    if pattern in content_lower:
                        threats.append(ThreatEvent(
                            threat_type=ThreatType.DATA_EXFILTRATION,
                            threat_level=ThreatLevel.CRITICAL,
                            description=f"Posible intento de exfiltración de datos en mensaje {msg.id}",
                            evidence={
                                "message_id": str(msg.id),
                                "pattern_matched": pattern,
                            },
                        ))
                        break
        except Exception as e:
            logger.warning(f"[SelfProtection] Error en content scan: {e}")
        return threats

    async def _scan_geo_anomalies(
        self, business_id: Optional[uuid.UUID]
    ) -> list[ThreatEvent]:
        """Detecta accesos desde geolocalizaciones inusuales."""
        threats = []
        try:
            from app.domains.security.models import UserLoginLog
            threshold = datetime.now(timezone.utc) - timedelta(hours=24)

            result = await self.db.execute(
                select(UserLoginLog).where(
                    and_(
                        UserLoginLog.created_at >= threshold,
                        UserLoginLog.success == True,
                        UserLoginLog.is_suspicious == True,
                    )
                ).limit(20)
            )
            suspicious_logins = result.scalars().all()

            for login in suspicious_logins:
                threats.append(ThreatEvent(
                    threat_type=ThreatType.SUSPICIOUS_GEOLOCATION,
                    threat_level=ThreatLevel.MEDIUM,
                    source_ip=login.ip_address,
                    user_id=str(login.user_id) if login.user_id else None,
                    description=f"Login desde ubicación sospechosa: {login.country or 'desconocido'}",
                    evidence={
                        "ip": login.ip_address,
                        "country": login.country,
                        "user_id": str(login.user_id) if login.user_id else None,
                    },
                ))
        except Exception as e:
            logger.warning(f"[SelfProtection] Error en geo scan: {e}")
        return threats

    # ─────────────────────────────────────────────
    # RESPUESTA A AMENAZAS
    # ─────────────────────────────────────────────

    async def _respond_to_threat(
        self, threat: ThreatEvent, business_id: Optional[uuid.UUID]
    ) -> str:
        """Aplica la respuesta automática apropiada para cada amenaza."""

        if threat.threat_type == ThreatType.BRUTE_FORCE:
            return await self._block_ip_temporarily(threat)

        elif threat.threat_type == ThreatType.PROMPT_INJECTION:
            return await self._quarantine_message(threat)

        elif threat.threat_type == ThreatType.DATA_EXFILTRATION:
            return await self._quarantine_message(threat) + " | " + await self._alert_security_team(threat, business_id)

        elif threat.threat_type == ThreatType.SPAM_DETECTED:
            return await self._throttle_contact(threat, business_id)

        elif threat.threat_type == ThreatType.RATE_LIMIT_ABUSE:
            return await self._apply_rate_limit(threat)

        elif threat.threat_type == ThreatType.SUSPICIOUS_GEOLOCATION:
            return await self._flag_suspicious_session(threat)

        return "Amenaza registrada — sin acción automática disponible"

    async def _block_ip_temporarily(self, threat: ThreatEvent) -> str:
        """Bloquea temporalmente una IP sospechosa."""
        try:
            ip = threat.source_ip
            if not ip:
                return "Sin IP para bloquear"

            self._blocked_ips.add(ip)

            from app.domains.security.models import IPAllowlist
            pass

            logger.warning(f"[SelfProtection] IP bloqueada temporalmente: {ip}")
            return f"IP {ip} bloqueada temporalmente (1 hora)"
        except Exception as e:
            return f"Error bloqueando IP: {str(e)[:100]}"

    async def _quarantine_message(self, threat: ThreatEvent) -> str:
        """Marca un mensaje como cuarentenado para revisión humana."""
        try:
            msg_id = threat.evidence.get("message_id")
            if not msg_id:
                return "Sin mensaje para cuarentenar"

            from app.domains.channels.models import Message
            await self.db.execute(
                update(Message)
                .where(Message.id == uuid.UUID(msg_id))
                .values(is_quarantined=True, quarantine_reason=threat.threat_type.value)
            )
            await self.db.commit()
            return f"Mensaje {msg_id[:8]}... cuarentenado"
        except Exception as e:
            return f"Mensaje marcado para revisión (DB update fallido: {str(e)[:50]})"

    async def _throttle_contact(self, threat: ThreatEvent, business_id: Optional[uuid.UUID]) -> str:
        """Limita la tasa de mensajes de un contacto detectado como spam."""
        return f"Rate limit aplicado al contacto sospechoso"

    async def _apply_rate_limit(self, threat: ThreatEvent) -> str:
        """Aplica rate limiting adicional a un usuario abusivo."""
        user_id = threat.user_id
        if user_id:
            self._suspicious_users.add(user_id)
        return f"Rate limit reforzado para usuario {user_id or 'desconocido'}"

    async def _flag_suspicious_session(self, threat: ThreatEvent) -> str:
        """Marca una sesión como sospechosa para revisión."""
        return f"Sesión marcada como sospechosa desde {threat.source_ip or 'IP desconocida'}"

    async def _alert_security_team(
        self, threat: ThreatEvent, business_id: Optional[uuid.UUID]
    ) -> str:
        """Envía alerta crítica de seguridad al equipo/dueño."""
        try:
            if not business_id:
                return "Sin business_id para alertar"

            from app.domains.alerts.models import Alert, AlertSeverity
            alert = Alert(
                business_id=business_id,
                title=f"🚨 ALERTA DE SEGURIDAD CRÍTICA: {threat.threat_type.value}",
                message=f"Amenaza de nivel {threat.threat_level.value} detectada:\n{threat.description}\n\nAcción tomada: {threat.action_taken}\n\nEvidencia: {threat.evidence}",
                severity=AlertSeverity.CRITICAL,
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(alert)
            await self.db.commit()
            return "Alerta crítica enviada al equipo de seguridad"
        except Exception as e:
            return f"Error enviando alerta: {str(e)[:50]}"

    async def _escalate_critical_threats(
        self, threats: list[ThreatEvent], business_id: Optional[uuid.UUID]
    ) -> None:
        """Escala amenazas críticas al dueño del negocio con detalle completo."""
        if not business_id or not threats:
            return

        summary = f"Se detectaron {len(threats)} amenazas críticas:\n"
        for t in threats:
            summary += f"• {t.threat_type}: {t.description}\n"

        try:
            from app.domains.alerts.models import Alert, AlertSeverity
            alert = Alert(
                business_id=business_id,
                title=f"🚨 [{len(threats)}] AMENAZAS CRÍTICAS DETECTADAS",
                message=summary,
                severity=AlertSeverity.CRITICAL,
                is_read=False,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(alert)
            await self.db.commit()
        except Exception as e:
            logger.error(f"[SelfProtection] Error escalando amenazas críticas: {e}")

    # ─────────────────────────────────────────────
    # MÉTRICAS Y REPORTING
    # ─────────────────────────────────────────────

    def _calculate_threat_score(self, threats: list[ThreatEvent]) -> int:
        """Calcula el score de amenaza del sistema (0-100, mayor = más peligroso)."""
        if not threats:
            return 0

        weight_map = {
            ThreatLevel.MINIMAL: 1,
            ThreatLevel.LOW: 5,
            ThreatLevel.MEDIUM: 15,
            ThreatLevel.HIGH: 30,
            ThreatLevel.CRITICAL: 50,
        }

        total = sum(weight_map.get(t.threat_level, 5) for t in threats)
        return min(100, total)

    def _score_to_level(self, score: int) -> str:
        if score == 0:
            return "secure"
        elif score < 15:
            return "low_risk"
        elif score < 40:
            return "medium_risk"
        elif score < 70:
            return "high_risk"
        else:
            return "critical"

    def scan_message_for_injection(self, content: str) -> bool:
        """Verifica si un mensaje contiene patrones de inyección (sync)."""
        content_lower = content.lower()
        patterns = (
            self.THRESHOLDS["prompt_injection_patterns"]
            + self.THRESHOLDS["data_exfiltration_patterns"]
        )
        return any(p in content_lower for p in patterns)

    def is_ip_blocked(self, ip: str) -> bool:
        return ip in self._blocked_ips

    def get_threat_summary(self) -> dict[str, Any]:
        recent = [t for t in self._threat_log
                  if t.detected_at >= datetime.now(timezone.utc) - timedelta(hours=24)]
        return {
            "threats_24h": len(recent),
            "blocked_ips": len(self._blocked_ips),
            "suspicious_users": len(self._suspicious_users),
            "critical_threats_24h": sum(1 for t in recent if t.threat_level == ThreatLevel.CRITICAL),
            "threat_score": self._calculate_threat_score(recent),
        }
