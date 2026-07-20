"""Computer Use — PDF Export Service

Genera reportes PDF de sesiones de Computer Use con screenshots,
log de acciones, y resumen ejecutivo. Usa Playwright para renderizar
HTML a PDF (ya instalado) sin librerías adicionales.
"""

import os
import base64
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class PDFExportService:
    """Servicio para exportar sesiones de Computer Use a PDF."""

    def __init__(self):
        self.storage_dir = os.path.join(os.getcwd(), "storage", "exports")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _build_html(
        self,
        session_data: dict,
        steps: list[dict],
        annotations: list[dict],
        include_screenshots: bool = True,
    ) -> str:
        """Construye el HTML del reporte."""
        session = session_data
        created_at = session.get("created_at", "N/A")
        if isinstance(created_at, datetime):
            created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")

        completed_at = session.get("completed_at")
        if isinstance(completed_at, datetime):
            completed_at = completed_at.strftime("%Y-%m-%d %H:%M:%S")
        elif completed_at is None:
            completed_at = "En progreso"

        # Header
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="es">',
            "<head>",
            '<meta charset="UTF-8">',
            '<style>',
            self._get_css(),
            "</style>",
            "</head>",
            "<body>",
            '<div class="header">',
            '<h1>🖥️ Reporte de Sesión — Caja de Cristal</h1>',
            f'<p class="meta">Tarea: <strong>{session.get("task_description", "N/A")}</strong></p>',
            f'<p class="meta">Estado: <span class="badge badge-{session.get("status", "unknown")}">{session.get("status", "N/A")}</span></p>',
            f'<p class="meta">Inicio: {created_at} | Fin: {completed_at} | Pasos: {session.get("total_steps", 0)}</p>',
            "</div>",
        ]

        # Summary section
        result_data = session.get("result_data") or {}
        html_parts.extend([
            '<div class="section">',
            "<h2>📋 Resumen Ejecutivo</h2>",
            f'<p>{result_data.get("summary", "No hay resumen disponible.")}</p>',
            "</div>",
        ])

        # Steps timeline
        html_parts.extend([
            '<div class="section">',
            "<h2>🔄 Timeline de Acciones</h2>",
            '<div class="timeline">',
        ])

        for step in steps:
            step_num = step.get("step_number", 0)
            action_type = step.get("action_type", "unknown")
            params = step.get("action_params") or {}
            reason = step.get("reason") or ""
            result = step.get("execution_result") or "N/A"
            exec_ms = step.get("execution_ms")

            # Action params string
            params_str = json.dumps(params, ensure_ascii=False) if params else "{}"
            if len(params_str) > 200:
                params_str = params_str[:200] + "..."

            step_annotations = [a for a in annotations if a.get("step_number") == step_num]
            annotations_html = ""
            if step_annotations:
                annotations_html = '<div class="annotations">' + "".join(
                    f'<span class="annotation" style="background:{a.get("color", "#f59e0b")}">💬 {a.get("content", "")}</span>'
                    for a in step_annotations
                ) + "</div>"

            screenshot_html = ""
            if include_screenshots and step.get("screenshot_path"):
                screenshot_path = os.path.join(
                    os.getcwd(), "storage", "screenshots",
                    str(session.get("id")), f"step_{step_num}.jpg"
                )
                if os.path.exists(screenshot_path):
                    with open(screenshot_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                    screenshot_html = f'<img src="data:image/jpeg;base64,{img_b64}" class="screenshot" />'

            html_parts.append(f"""
                <div class="step">
                    <div class="step-header">
                        <span class="step-num">#{step_num}</span>
                        <span class="badge badge-action">{action_type}</span>
                        {f'<span class="exec-time">{exec_ms}ms</span>' if exec_ms else ''}
                    </div>
                    <div class="step-body">
                        <p><strong>Razón:</strong> {reason or 'Sin razón documentada'}</p>
                        <p><strong>Parámetros:</strong> <code>{params_str}</code></p>
                        <p><strong>Resultado:</strong> {result}</p>
                        {annotations_html}
                        {screenshot_html}
                    </div>
                </div>
            """)

        html_parts.extend([
            "</div>",  # timeline
            "</div>",  # section
            '<div class="footer">',
            f'<p>Generado por SellIA Caja de Cristal — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_parts)

    def _get_css(self) -> str:
        return """
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8fafc; color: #1e293b; }
            .header { background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }
            .header h1 { margin: 0 0 12px 0; font-size: 28px; }
            .meta { margin: 6px 0; opacity: 0.9; font-size: 14px; }
            .section { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .section h2 { margin: 0 0 16px 0; color: #1e40af; font-size: 20px; }
            .timeline { display: flex; flex-direction: column; gap: 16px; }
            .step { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
            .step-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
            .step-num { background: #3b82f6; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
            .badge { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
            .badge-running { background: #dbeafe; color: #1e40af; }
            .badge-completed { background: #dcfce7; color: #166534; }
            .badge-failed { background: #fee2e2; color: #991b1b; }
            .badge-stopped { background: #fef3c7; color: #92400e; }
            .badge-action { background: #ede9fe; color: #5b21b6; }
            .exec-time { color: #64748b; font-size: 12px; }
            .step-body p { margin: 6px 0; font-size: 14px; }
            .step-body code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
            .screenshot { max-width: 100%; border-radius: 8px; margin-top: 12px; border: 1px solid #e2e8f0; }
            .annotations { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
            .annotation { padding: 4px 10px; border-radius: 6px; color: white; font-size: 12px; }
            .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 40px; padding: 20px; }
        """

    async def export_session(
        self,
        session_id: UUID,
        session_data: dict,
        steps: list[dict],
        annotations: list[dict],
        include_screenshots: bool = True,
    ) -> str:
        """Genera un PDF y devuelve la ruta al archivo."""
        html_content = self._build_html(session_data, steps, annotations, include_screenshots)

        output_path = os.path.join(self.storage_dir, f"session_{session_id}.pdf")

        # Use Playwright to render HTML to PDF
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.pdf(
                path=output_path,
                format="A4",
                margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"},
                print_background=True,
            )
            await browser.close()

        logger.info(f"PDF exported: {output_path}")
        return output_path

    async def export_csv(self, steps: list[dict]) -> str:
        """Exporta los pasos a CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["step_number", "action_type", "action_params", "reason", "execution_result", "execution_ms"])

        for step in steps:
            writer.writerow([
                step.get("step_number", ""),
                step.get("action_type", ""),
                json.dumps(step.get("action_params") or {}, ensure_ascii=False),
                step.get("reason", ""),
                step.get("execution_result", ""),
                step.get("execution_ms", ""),
            ])

        output_path = os.path.join(self.storage_dir, f"steps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            f.write(output.getvalue())

        return output_path

    async def export_json(self, session_data: dict, steps: list[dict], annotations: list[dict]) -> str:
        """Exporta la sesión completa a JSON."""
        export_data = {
            "session": session_data,
            "steps": steps,
            "annotations": annotations,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

        output_path = os.path.join(self.storage_dir, f"session_{session_data.get('id')}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        return output_path
