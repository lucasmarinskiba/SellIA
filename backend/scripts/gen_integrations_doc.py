"""Generate docs/INTEGRACIONES.md from the integrations registry.

Run: python backend/scripts/gen_integrations_doc.py

The document is generated rather than written by hand so it cannot drift from
the code that actually reads the variables. Re-run it after touching
app/domains/integrations/registry.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.domains.integrations.registry import INTEGRATIONS  # noqa: E402

OUT = BACKEND.parent / "docs" / "INTEGRACIONES.md"

HEADER = """# Integraciones externas

Qué API le falta a cada herramienta para funcionar completa, cuánto cuesta y qué
variable de entorno hay que cargar en Railway (Variables → New Variable) o en el
gestor de secretos que se use.

**Generado desde `backend/app/domains/integrations/registry.py`** — no editar a
mano: correr `python backend/scripts/gen_integrations_doc.py`.

El estado real de esta instalación (qué está cargado y qué falta) se consulta en
vivo con `GET /api/v1/integrations/status`, que lee el entorno de verdad. Este
documento describe el catálogo; ese endpoint describe el deploy.

## Regla que sigue el producto

Sin la API, ninguna pantalla inventa el número: dice que no puede medirlo. Estas
claves reemplazan ese mensaje por datos reales, no arreglan un dato falso.

"""


def priority_label(priority: int) -> str:
    return {1: "🔴 Primero", 2: "🟡 Después", 3: "⚪ Cuando haga falta"}.get(priority, "")


def main() -> None:
    by_tool: dict[str, list] = {}
    for integration in INTEGRATIONS:
        by_tool.setdefault(integration.tool, []).append(integration)

    lines = [HEADER]

    lines.append("## Resumen por prioridad\n")
    lines.append("| Prioridad | Integración | Herramienta | Costo | Variables |")
    lines.append("| --- | --- | --- | --- | --- |")
    for integration in sorted(INTEGRATIONS, key=lambda i: (i.priority, i.tool)):
        env = "`" + "`, `".join(integration.required_env) + "`"
        lines.append(
            f"| {priority_label(integration.priority)} | {integration.name} "
            f"| {integration.tool} | {integration.cost} | {env} |"
        )
    lines.append("")

    for tool, entries in by_tool.items():
        lines.append(f"## {tool}\n")
        for integration in sorted(entries, key=lambda i: i.priority):
            lines.append(f"### {integration.name}")
            lines.append("")
            lines.append(f"- **Proveedor:** {integration.provider}")
            lines.append(f"- **Costo:** {integration.cost}")
            lines.append(f"- **Prioridad:** {priority_label(integration.priority)}")
            lines.append(
                "- **Variables requeridas:** " + ", ".join(f"`{e}`" for e in integration.required_env)
            )
            if integration.optional_env:
                lines.append(
                    "- **Opcionales:** " + ", ".join(f"`{e}`" for e in integration.optional_env)
                )
            if integration.docs_url:
                lines.append(f"- **Cómo obtenerla:** {integration.docs_url}")
            lines.append(f"- **Qué desbloquea:** {integration.unlocks}")
            lines.append(f"- **Qué hace hoy sin esto:** {integration.today_instead}")
            lines.append("")

    lines.append("## Cómo cargarlas en Railway\n")
    lines.append("```bash")
    lines.append("# Una por una, desde la raíz del repo (railway link ya hecho):")
    lines.append('railway variables --set "GOOGLE_PAGESPEED_API_KEY=tu-clave"')
    lines.append("")
    lines.append("# Verificar qué quedó cargado (nombres, no valores):")
    lines.append("railway variables")
    lines.append("```")
    lines.append("")
    lines.append(
        "Railway reinicia el servicio al cambiar una variable. Después de cargarlas, "
        "`GET /api/v1/integrations/status` debería mostrarlas como `configured: true`.\n"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"escrito: {OUT} ({len(INTEGRATIONS)} integraciones)")


if __name__ == "__main__":
    main()
