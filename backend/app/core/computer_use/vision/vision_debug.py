"""Vision Debug — Annotate & Visualize Vision Understanding

Responsibilities:
- Annotate screenshots with detected elements
- Show what CU sees vs what should see
- Log visual decisions for debugging
- Generate visual reports

Debug toolkit for vision-based automation.
"""

import logging
import base64
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionDebugAnnotator:
    """Anota screenshots con elementos detectados."""

    @staticmethod
    def annotate_with_buttons(
        screenshot_bytes: bytes,
        buttons: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> bytes:
        """Anota screenshot mostrando botones detectados.

        Args:
            screenshot_bytes: Imagen original
            buttons: Lista de botones detectados
            output_path: Ruta para guardar imagen anotada

        Returns:
            Imagen con anotaciones
        """
        try:
            from PIL import Image, ImageDraw
            import io

            image = Image.open(io.BytesIO(screenshot_bytes))
            draw = ImageDraw.Draw(image, 'RGBA')

            for btn in buttons:
                x = btn.get("x", 0)
                y = btn.get("y", 0)
                width = btn.get("width", 50)
                height = btn.get("height", 30)

                # Dibujar rectángulo alrededor del botón
                draw.rectangle(
                    [x, y, x + width, y + height],
                    outline='red',
                    width=3
                )

                # Dibujar label
                label = btn.get("label", "")
                try:
                    draw.text((x + 5, y + 5), label, fill='red')
                except Exception:
                    pass

            if output_path:
                image.save(output_path)
                logger.info(f"Annotated screenshot saved: {output_path}")

            # Retornar como bytes
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Annotation failed: {e}")
            return screenshot_bytes

    @staticmethod
    def annotate_with_form_fields(
        screenshot_bytes: bytes,
        fields: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> bytes:
        """Anota campos de formulario."""
        try:
            from PIL import Image, ImageDraw
            import io

            image = Image.open(io.BytesIO(screenshot_bytes))
            draw = ImageDraw.Draw(image, 'RGBA')

            for field in fields:
                x = field.get("x", 0)
                y = field.get("y", 0)
                width = field.get("width", 100)
                height = field.get("height", 30)
                label = field.get("label", "")
                field_type = field.get("type", "")

                # Color según tipo
                color_map = {
                    "input": "blue",
                    "select": "green",
                    "textarea": "orange",
                    "checkbox": "purple",
                }
                color = color_map.get(field_type, "gray")

                # Dibujar rectángulo
                draw.rectangle(
                    [x, y, x + width, y + height],
                    outline=color,
                    width=2
                )

                # Dibujar label con tipo
                label_text = f"{label} ({field_type})"
                try:
                    draw.text((x + 5, y - 15), label_text, fill=color)
                except Exception:
                    pass

            if output_path:
                image.save(output_path)
                logger.info(f"Annotated screenshot saved: {output_path}")

            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Form annotation failed: {e}")
            return screenshot_bytes

    @staticmethod
    def annotate_with_all_elements(
        screenshot_bytes: bytes,
        analysis: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """Anota con TODOS los elementos detectados."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io

            image = Image.open(io.BytesIO(screenshot_bytes))
            draw = ImageDraw.Draw(image, 'RGBA')

            # Botones (rojo)
            for btn in analysis.get("buttons", []):
                VisionDebugAnnotator._draw_box(draw, btn, "red", "B")

            # Campos (azul)
            for field in analysis.get("form_fields", []):
                VisionDebugAnnotator._draw_box(draw, field, "blue", "F")

            # Texto (verde)
            for text in analysis.get("all_text", [])[:10]:  # Max 10 texts
                VisionDebugAnnotator._draw_box(draw, text, "green", "T")

            if output_path:
                image.save(output_path)
                logger.info(f"Annotated screenshot saved: {output_path}")

            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"All-elements annotation failed: {e}")
            return screenshot_bytes

    @staticmethod
    def _draw_box(draw, element, color, label_prefix):
        """Dibuja un box alrededor de elemento."""
        x = element.get("x", 0)
        y = element.get("y", 0)
        width = element.get("width", 50)
        height = element.get("height", 30)

        draw.rectangle(
            [x, y, x + width, y + height],
            outline=color,
            width=2
        )

        # Pequeño label en corner
        try:
            draw.text((x + 2, y + 2), label_prefix, fill=color)
        except Exception:
            pass

    @staticmethod
    def create_comparison_image(
        before_bytes: bytes,
        after_bytes: bytes,
        output_path: Optional[str] = None
    ) -> bytes:
        """Crea imagen comparativa before/after."""
        try:
            from PIL import Image
            import io

            before_img = Image.open(io.BytesIO(before_bytes))
            after_img = Image.open(io.BytesIO(after_bytes))

            # Asegurar mismo tamaño
            size = before_img.size
            after_img = after_img.resize(size)

            # Crear imagen side-by-side
            comparison = Image.new(
                'RGB',
                (size[0] * 2 + 20, size[1] + 40),
                color='white'
            )

            # Pegar imágenes
            comparison.paste(before_img, (10, 30))
            comparison.paste(after_img, (size[0] + 10, 30))

            # Agregar labels
            try:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(comparison)
                draw.text((20, 10), "BEFORE", fill='black')
                draw.text((size[0] + 20, 10), "AFTER", fill='black')
            except Exception:
                pass

            if output_path:
                comparison.save(output_path)
                logger.info(f"Comparison image saved: {output_path}")

            output = io.BytesIO()
            comparison.save(output, format="PNG")
            return output.getvalue()

        except Exception as e:
            logger.error(f"Comparison creation failed: {e}")
            return before_bytes


class VisionDebugLogger:
    """Log detallado de decisiones visuales."""

    def __init__(self, session_id: str, output_dir: Optional[str] = None):
        self.session_id = session_id
        self.output_dir = Path(output_dir or f"./vision_debug/{session_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "vision_debug.jsonl"
        self.step_counter = 0

    def log_analysis(
        self,
        step: int,
        screenshot_path: Optional[str],
        analysis: Dict[str, Any],
        action_taken: Optional[str] = None
    ) -> None:
        """Registra análisis de screenshot."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "session_id": self.session_id,
            "screenshot_path": screenshot_path,
            "analysis": {
                "page_type": analysis.get("page_type"),
                "buttons_found": len(analysis.get("buttons", [])),
                "fields_found": len(analysis.get("form_fields", [])),
                "text_regions": len(analysis.get("all_text", [])),
                "confidence": analysis.get("confidence_score"),
            },
            "action_taken": action_taken,
        }

        self._write_log_entry(entry)

    def log_element_search(
        self,
        step: int,
        search_query: str,
        found_element: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0
    ) -> None:
        """Registra búsqueda de elemento."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "session_id": self.session_id,
            "event_type": "element_search",
            "query": search_query,
            "found": found_element is not None,
            "element": found_element,
            "confidence": confidence,
        }

        self._write_log_entry(entry)

    def log_action_execution(
        self,
        step: int,
        action: str,
        target: Optional[str],
        result: str,
        error: Optional[str] = None
    ) -> None:
        """Registra ejecución de acción."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "session_id": self.session_id,
            "event_type": "action_execution",
            "action": action,
            "target": target,
            "result": result,
            "error": error,
        }

        self._write_log_entry(entry)

    def log_confirmation(
        self,
        step: int,
        action: str,
        confirmation_result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registra confirmación de acción."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "session_id": self.session_id,
            "event_type": "confirmation",
            "action": action,
            "result": confirmation_result,
            "details": details,
        }

        self._write_log_entry(entry)

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Escribe entrada en log."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")

    def generate_report(self) -> str:
        """Genera reporte de debug."""
        lines = [
            f"Vision Debug Report",
            f"Session: {self.session_id}",
            f"Debug Dir: {self.output_dir}",
            f"",
        ]

        # Leer y resumir logs
        if self.log_file.exists():
            entries = []
            with open(self.log_file) as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

            lines.append(f"Total Events: {len(entries)}")

            # Agrupar por tipo
            by_type = {}
            for entry in entries:
                event_type = entry.get("event_type", "unknown")
                if event_type not in by_type:
                    by_type[event_type] = 0
                by_type[event_type] += 1

            lines.append(f"\nEvents by Type:")
            for event_type, count in by_type.items():
                lines.append(f"  {event_type}: {count}")

            # Último estado
            if entries:
                last = entries[-1]
                lines.append(f"\nLast Event:")
                lines.append(f"  Time: {last.get('timestamp')}")
                lines.append(f"  Type: {last.get('event_type')}")
                if 'action' in last:
                    lines.append(f"  Action: {last.get('action')}")
                if 'result' in last:
                    lines.append(f"  Result: {last.get('result')}")

        return "\n".join(lines)

    def save_report(self, output_file: Optional[str] = None) -> str:
        """Guarda reporte a archivo."""
        report = self.generate_report()

        path = Path(output_file or self.output_dir / "report.txt")
        path.write_text(report)

        logger.info(f"Report saved: {path}")
        return str(path)


class VisionComparator:
    """Compara análisis para debuggear diferencias."""

    @staticmethod
    def compare_analyses(
        analysis1: Dict[str, Any],
        analysis2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compara dos análisis."""
        return {
            "page_type_changed": (
                analysis1.get("page_type") != analysis2.get("page_type")
            ),
            "buttons_diff": (
                len(analysis2.get("buttons", [])) - len(analysis1.get("buttons", []))
            ),
            "fields_diff": (
                len(analysis2.get("form_fields", [])) - len(analysis1.get("form_fields", []))
            ),
            "text_regions_diff": (
                len(analysis2.get("all_text", [])) - len(analysis1.get("all_text", []))
            ),
            "confidence_diff": (
                analysis2.get("confidence_score", 0) - analysis1.get("confidence_score", 0)
            ),
        }

    @staticmethod
    def print_comparison(comparison: Dict[str, Any]) -> str:
        """Retorna comparación en formato legible."""
        lines = ["ANALYSIS COMPARISON:"]

        if comparison.get("page_type_changed"):
            lines.append("  Page type: CHANGED")

        buttons_diff = comparison.get("buttons_diff", 0)
        if buttons_diff != 0:
            lines.append(f"  Buttons: {buttons_diff:+d}")

        fields_diff = comparison.get("fields_diff", 0)
        if fields_diff != 0:
            lines.append(f"  Form fields: {fields_diff:+d}")

        text_diff = comparison.get("text_regions_diff", 0)
        if text_diff != 0:
            lines.append(f"  Text regions: {text_diff:+d}")

        conf_diff = comparison.get("confidence_diff", 0)
        if abs(conf_diff) > 0.01:
            lines.append(f"  Confidence: {conf_diff:+.2%}")

        return "\n".join(lines)
