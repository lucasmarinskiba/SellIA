"""Computer Use — Screenshot Comparator

Compara screenshots entre pasos para detectar cambios significativos
en la página. Útil para detectar cuando una acción no tuvo efecto o
para monitorear cambios de estado.
"""

import io
from typing import Optional, Tuple
from dataclasses import dataclass

from PIL import Image, ImageChops
import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ComparisonResult:
    """Resultado de comparación de screenshots."""
    changed: bool
    similarity: float  # 0.0 to 1.0
    diff_pixels: int
    total_pixels: int
    diff_percentage: float
    diff_image: Optional[bytes] = None  # Highlighted diff image


class ScreenshotComparator:
    """Comparador de screenshots con múltiples algoritmos."""

    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold  # Minimum similarity to consider "same"

    def compare(
        self,
        screenshot_a: bytes,
        screenshot_b: bytes,
        generate_diff_image: bool = False,
    ) -> ComparisonResult:
        """Compara dos screenshots."""
        try:
            img_a = Image.open(io.BytesIO(screenshot_a)).convert("RGB")
            img_b = Image.open(io.BytesIO(screenshot_b)).convert("RGB")

            # Resize to same dimensions
            target_size = (min(img_a.width, img_b.width), min(img_a.height, img_b.height))
            if target_size[0] < 1 or target_size[1] < 1:
                return ComparisonResult(
                    changed=True, similarity=0.0, diff_pixels=0, total_pixels=1, diff_percentage=100.0
                )

            img_a = img_a.resize(target_size, Image.Resampling.LANCZOS)
            img_b = img_b.resize(target_size, Image.Resampling.LANCZOS)

            # Pixel-by-pixel comparison
            diff = ImageChops.difference(img_a, img_b)
            diff_array = np.array(diff)

            # Calculate difference
            total_pixels = target_size[0] * target_size[1]
            # A pixel is different if any channel differs by more than 10
            diff_pixels = int(np.sum(np.any(diff_array > 10, axis=2)))
            diff_percentage = (diff_pixels / total_pixels) * 100 if total_pixels > 0 else 0
            similarity = 1.0 - (diff_pixels / total_pixels) if total_pixels > 0 else 0

            changed = similarity < self.threshold

            # Generate diff image
            diff_image_bytes = None
            if generate_diff_image and changed:
                diff_highlight = self._generate_diff_highlight(img_a, img_b, diff)
                buf = io.BytesIO()
                diff_highlight.save(buf, format="PNG")
                diff_image_bytes = buf.getvalue()

            return ComparisonResult(
                changed=changed,
                similarity=round(similarity, 4),
                diff_pixels=diff_pixels,
                total_pixels=total_pixels,
                diff_percentage=round(diff_percentage, 2),
                diff_image=diff_image_bytes,
            )

        except Exception as e:
            logger.warning(f"Screenshot comparison failed: {e}")
            return ComparisonResult(
                changed=True, similarity=0.0, diff_pixels=0, total_pixels=1, diff_percentage=100.0
            )

    def _generate_diff_highlight(
        self,
        img_a: Image.Image,
        img_b: Image.Image,
        diff: Image.Image,
    ) -> Image.Image:
        """Genera una imagen resaltando las diferencias en rojo."""
        # Create a blended image with differences highlighted
        result = img_b.copy()
        result_array = np.array(result)
        diff_array = np.array(diff)

        # Highlight differences in red
        mask = np.any(diff_array > 10, axis=2)
        result_array[mask] = [255, 0, 0]  # Red

        return Image.fromarray(result_array)

    def compare_ssim(
        self,
        screenshot_a: bytes,
        screenshot_b: bytes,
    ) -> float:
        """Compara screenshots usando SSIM (Structural Similarity Index).
        
        Requiere scikit-image. Si no está disponible, fallback a pixel diff.
        """
        try:
            from skimage.metrics import structural_similarity as ssim

            img_a = Image.open(io.BytesIO(screenshot_a)).convert("L")  # Grayscale
            img_b = Image.open(io.BytesIO(screenshot_b)).convert("L")

            target_size = (min(img_a.width, img_b.width), min(img_a.height, img_b.height))
            img_a = img_a.resize(target_size, Image.Resampling.LANCZOS)
            img_b = img_b.resize(target_size, Image.Resampling.LANCZOS)

            arr_a = np.array(img_a)
            arr_b = np.array(img_b)

            score, _ = ssim(arr_a, arr_b, full=True)
            return float(score)

        except ImportError:
            logger.debug("scikit-image not available, using pixel comparison")
            result = self.compare(screenshot_a, screenshot_b)
            return result.similarity
        except Exception as e:
            logger.warning(f"SSIM comparison failed: {e}")
            return 0.0

    def detect_stale_state(
        self,
        screenshots: list[bytes],
        window_size: int = 3,
    ) -> list[int]:
        """Detecta pasos donde la página no cambió (stale state).
        
        Retorna lista de índices de pasos donde no hubo cambio.
        """
        if len(screenshots) < 2:
            return []

        stale_indices = []
        for i in range(1, len(screenshots)):
            result = self.compare(screenshots[i - 1], screenshots[i])
            if not result.changed:
                stale_indices.append(i)

        return stale_indices
