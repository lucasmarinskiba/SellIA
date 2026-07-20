"""Computer Use — Markdown Export

Genera reportes en Markdown para documentación y sharing.
"""

from datetime import datetime
from typing import List, Dict, Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class MarkdownExportService:
    """Exporta sesiones de Computer Use a Markdown."""

    def export_session(
        self,
        session_data: Dict[str, Any],
        steps: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]],
    ) -> str:
        """Genera un reporte Markdown de la sesión."""
        lines = []

        # Header
        lines.append(f"# 🖥️ Reporte de Sesión — Caja de Cristal")
        lines.append("")
        lines.append(f"**Tarea:** {session_data.get('task_description', 'N/A')}")
        lines.append(f"**Estado:** {session_data.get('status', 'N/A')}")
        lines.append(f"**Pasos:** {session_data.get('total_steps', 0)}")
        lines.append(f"**Inicio:** {session_data.get('started_at', 'N/A')}")
        lines.append(f"**Fin:** {session_data.get('completed_at', 'N/A')}")
        lines.append("")

        # Summary
        result = session_data.get('result_data') or {}
        if result.get('summary'):
            lines.append("## 📋 Resumen")
            lines.append("")
            lines.append(result['summary'])
            lines.append("")

        # Steps
        lines.append("## 🔄 Acciones")
        lines.append("")

        for step in steps:
            step_num = step.get('step_number', 0)
            action_type = step.get('action_type', 'unknown')
            params = step.get('action_params') or {}
            reason = step.get('reason', '')
            result_text = step.get('execution_result', 'N/A')

            lines.append(f"### Paso #{step_num}: `{action_type}`")
            lines.append("")

            if reason:
                lines.append(f"> **Razón:** {reason}")
                lines.append("")

            if params:
                lines.append("**Parámetros:**")
                lines.append("```json")
                lines.append(str(params).replace("'", '\"'))
                lines.append("```")
                lines.append("")

            lines.append(f"**Resultado:** {result_text}")
            lines.append("")

            # Annotations for this step
            step_anns = [a for a in annotations if a.get('step_number') == step_num]
            if step_anns:
                lines.append("**Anotaciones:**")
                for ann in step_anns:
                    lines.append(f"- 💬 {ann.get('content', '')}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Footer
        lines.append(f"*Generado por SellIA Caja de Cristal — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def export_steps_table(self, steps: List[Dict[str, Any]]) -> str:
        """Genera una tabla Markdown de los pasos."""
        lines = []
        lines.append("| Paso | Acción | Parámetros | Resultado |")
        lines.append("|------|--------|------------|-----------|")

        for step in steps:
            params = str(step.get('action_params', {})).replace('|', '\\|')[:50]
            lines.append(
                f"| {step.get('step_number', 0)} | "
                f"`{step.get('action_type', 'unknown')}` | "
                f"{params} | "
                f"{step.get('execution_result', 'N/A')} |"
            )

        return "\n".join(lines)
