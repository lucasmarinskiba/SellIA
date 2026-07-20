"""Computer Use — Autopilot / Supervised execution policy.

Clasifica cada acción por riesgo y decide si ejecutarla, pedir
confirmación o bloquearla, según el modo de la sesión:

- ``supervised``: las acciones de riesgo (publicar, enviar, comprar, gastar
  dinero, cambios irreversibles) pausan la sesión y piden confirmación
  humana antes de ejecutarse.
- ``autopilot``: el agente ejecuta acciones de riesgo medio de forma
  autónoma (registradas para auditoría), pero las acciones críticas
  (pagos, credenciales, descargas) siempre se bloquean.

No reemplaza al ``ActionValidator`` (seguridad dura); añade una capa de
gobernanza de negocio sobre acciones que SON técnicamente válidas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class AutopilotMode(str, Enum):
    SUPERVISED = "supervised"
    AUTOPILOT = "autopilot"


class RiskLevel(str, Enum):
    SAFE = "safe"        # navegar, screenshot, scroll, leer
    MEDIUM = "medium"    # escribir, click en botones, programar
    HIGH = "high"        # publicar, enviar, postear contenido público
    CRITICAL = "critical"  # pagar, gastar ads, descargar, credenciales


@dataclass(frozen=True)
class PolicyDecision:
    allow: bool                 # ejecutar ya
    require_confirmation: bool  # pausar y pedir OK humano
    risk: RiskLevel
    reason: str


# Palabras que delatan intención de alto riesgo en el "reason" / params del LLM.
_HIGH_RISK_WORDS = re.compile(
    r"\b(publr?icar|publish|post(ear|ar)?|enviar|send|share|compartir|"
    r"submit|confirmar|aceptar (terminos|términos)|delete|eliminar|borrar)\b",
    re.IGNORECASE,
)
_CRITICAL_WORDS = re.compile(
    r"\b(pagar|pay|checkout|comprar|purchase|buy|tarjeta|card|cvv|"
    r"descargar|download|aumentar presupuesto|increase budget|"
    r"password|contrase[nñ]a|credit)\b",
    re.IGNORECASE,
)

# Texto que, escrito en un input, sugiere envío/publicación de contenido.
_PUBLISH_SELECTOR = re.compile(
    r"(submit|publish|post|send|share|buy|checkout|pay|confirm|"
    r"publicar|enviar|comprar|pagar|confirmar)",
    re.IGNORECASE,
)


def classify_action_risk(action_type: str, params: Dict[str, Any], reason: str = "") -> RiskLevel:
    """Clasifica el nivel de riesgo de una acción de Computer Use."""
    params = params or {}
    blob = f"{reason} {params.get('text', '')} {params.get('selector', '')} {params.get('value', '')}"

    if _CRITICAL_WORDS.search(blob):
        return RiskLevel.CRITICAL

    if action_type in ("done", "error", "screenshot", "scroll", "wait",
                       "wait_for_selector", "navigate"):
        # navigate a esquemas peligrosos lo bloquea ActionValidator; aquí es safe.
        return RiskLevel.SAFE

    if action_type in ("click", "double_click", "right_click", "click_selector",
                       "click_text", "press_key"):
        target = f"{params.get('selector', '')} {params.get('text', '')} {params.get('key', '')}"
        if _PUBLISH_SELECTOR.search(target) or _HIGH_RISK_WORDS.search(blob):
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    if action_type in ("type", "fill"):
        if _HIGH_RISK_WORDS.search(blob) or _PUBLISH_SELECTOR.search(params.get("selector", "")):
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    # Acción desconocida → tratar como media por precaución.
    return RiskLevel.MEDIUM


class AutopilotPolicy:
    """Decide la ejecución de una acción según el modo de la sesión."""

    def __init__(self, mode: AutopilotMode | str = AutopilotMode.SUPERVISED):
        self.mode = AutopilotMode(mode) if not isinstance(mode, AutopilotMode) else mode

    def evaluate(self, action_type: str, params: Dict[str, Any], reason: str = "") -> PolicyDecision:
        risk = classify_action_risk(action_type, params, reason)

        # Críticas: nunca automáticas. Gastan dinero, exponen credenciales o
        # son irreversibles → siempre requieren confirmación humana explícita
        # (en ambos modos).
        if risk == RiskLevel.CRITICAL:
            return PolicyDecision(
                allow=False,
                require_confirmation=True,
                risk=risk,
                reason="Acción crítica (pago/credenciales/descarga): requiere confirmación humana.",
            )

        if risk == RiskLevel.HIGH:
            if self.mode == AutopilotMode.SUPERVISED:
                return PolicyDecision(
                    allow=False,
                    require_confirmation=True,
                    risk=risk,
                    reason="Acción de alto impacto (publicar/enviar): confirma antes de ejecutar.",
                )
            # Autopilot: permitido pero auditado.
            return PolicyDecision(
                allow=True,
                require_confirmation=False,
                risk=risk,
                reason="Acción de alto impacto ejecutada en piloto automático (auditada).",
            )

        # MEDIUM / SAFE → ejecutar.
        return PolicyDecision(
            allow=True,
            require_confirmation=False,
            risk=risk,
            reason="Acción de riesgo bajo/medio: ejecución directa.",
        )
