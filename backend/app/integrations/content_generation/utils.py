"""Utilities for content generation: compression, hashing, download."""

import io
import hashlib
import base64
from typing import Optional
from pathlib import Path

import aiohttp
from PIL import Image


def hash_prompt(prompt: str) -> str:
    """Genera hash corto de un prompt."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def compress_image(
    image_bytes: bytes,
    target_format: str = "JPEG",
    quality: int = 85,
    max_dimension: int = 2048,
) -> bytes:
    """
    Comprime una imagen para reducir costos de storage y transferencia.

    Args:
        image_bytes: Bytes de la imagen original
        target_format: Formato de salida (JPEG, PNG, WEBP)
        quality: Calidad JPEG/WEBP (1-100)
        max_dimension: Dimensión máxima (redimensiona si es mayor)

    Returns:
        bytes de la imagen comprimida
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Redimensionar si excede dimensión máxima
    width, height = img.size
    if width > max_dimension or height > max_dimension:
        ratio = min(max_dimension / width, max_dimension / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Convertir a RGB si es necesario (para JPEG)
    if target_format.upper() in ("JPEG", "WEBP") and img.mode in ("RGBA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1])
        img = background

    output = io.BytesIO()
    img.save(output, format=target_format, quality=quality, optimize=True)
    return output.getvalue()


def get_image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    """Obtiene dimensiones de una imagen sin cargarla completa."""
    img = Image.open(io.BytesIO(image_bytes))
    return img.size


def get_image_size_kb(image_bytes: bytes) -> float:
    """Obtiene tamaño en KB."""
    return len(image_bytes) / 1024


async def download_url(url: str, timeout: int = 60) -> Optional[bytes]:
    """Descarga contenido de una URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    return await resp.read()
                return None
    except Exception:
        return None


def bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Convierte bytes a data URL."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def estimate_storage_cost_kb(size_kb: float, db_cost_per_gb: float = 0.023) -> float:
    """
    Estima costo mensual de storage.
    AWS S3 standard: ~$0.023/GB/mes
    """
    gb = size_kb / (1024 * 1024)
    return gb * db_cost_per_gb


def smart_quality_for_size(size_kb: float) -> int:
    """
    Selecciona calidad de compresión según tamaño original.
    Imágenes grandes -> más compresión.
    """
    if size_kb > 2000:
        return 70
    elif size_kb > 1000:
        return 80
    elif size_kb > 500:
        return 85
    return 90


def sanitize_filename(name: str) -> str:
    """Sanitiza nombre de archivo."""
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, '_')
    return name.strip()[:100]
