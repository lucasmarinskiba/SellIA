"""
Sistema de escaneo de archivos subidos por usuarios.
Integra ClamAV para detección de malware y validaciones de seguridad adicionales.
"""

import io
import os
import hashlib
import mimetypes
from pathlib import Path
from typing import BinaryIO

try:
    import clamd
    CLAMD_AVAILABLE = True
except ImportError:
    clamd = None  # type: ignore
    CLAMD_AVAILABLE = False

from fastapi import UploadFile, HTTPException, status

# Configuración
CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", "3310"))
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10_485_760"))  # 10 MB por defecto

# Tipos MIME y extensiones permitidas (whitelist estricta)
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
}

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".pdf", ".txt", ".csv", ".xlsx", ".docx",
}

# Firmas mágicas de archivos peligrosos (bloqueo estricto)
DANGEROUS_SIGNATURES = [
    b"MZ",  # Windows executable
    b"\x7fELF",  # Linux executable
    b"PK\x03\x04",  # ZIP (podría contener malware)
    b"<?php",  # PHP
    b"#!/bin/bash",  # Shell script
    b"#!/usr/bin/env python",  # Python script
    b"<script",  # HTML/JS
    b"<%@",  # JSP
    b"<jsp:",  # JSP
]

# Extensiones peligrosas (bloqueo inmediato)
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".sh", ".php", ".jsp", ".asp", ".aspx",
    ".py", ".rb", ".pl", ".jar", ".war", ".ear", ".zip", ".rar", ".7z",
    ".tar", ".gz", ".bz2", ".xz", ".iso", ".img", ".msi", ".deb", ".rpm",
    ".apk", ".ipa", ".dmg", ".pkg", ".app", ".scr", ".pif", ".com",
    ".vbs", ".js", ".jse", ".wsf", ".wsh", ".hta", ".cpl", ".inf",
}


class ScanResult:
    def __init__(self, clean: bool, message: str, details: dict | None = None):
        self.clean = clean
        self.message = message
        self.details = details or {}


class FileScanner:
    """Escáner de archivos con ClamAV y validaciones de seguridad."""

    def __init__(self):
        self._clamd = None

    def _get_clamd(self) -> "clamd.ClamdNetworkSocket | None" if CLAMD_AVAILABLE else "None":
        """Obtiene o crea la conexión a ClamAV."""
        if self._clamd is None:
            if not CLAMD_AVAILABLE:
                import logging
                logging.getLogger("security").warning("ClamAV no disponible: módulo clamd no instalado")
                self._clamd = None
            else:
                try:
                    self._clamd = clamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
                    self._clamd.ping()
                except Exception as e:
                    # Si ClamAV no está disponible, loguear warning pero no fallar
                    import logging
                    logging.getLogger("security").warning(f"ClamAV no disponible: {e}")
                    self._clamd = None
        return self._clamd

    def _get_file_signature(self, content: bytes) -> bytes:
        """Obtiene los primeros bytes del archivo para análisis de firma."""
        return content[:64]

    def _has_dangerous_signature(self, content: bytes) -> tuple[bool, str]:
        """Verifica si el contenido tiene firmas de archivos peligrosos."""
        sig = self._get_file_signature(content)
        for dangerous in DANGEROUS_SIGNATURES:
            if dangerous in sig:
                return True, f"Firma peligrosa detectada: {dangerous[:20]}"
        return False, ""

    def _validate_extension(self, filename: str) -> tuple[bool, str]:
        """Valida que la extensión del archivo esté en la whitelist."""
        ext = Path(filename).suffix.lower()
        if ext in DANGEROUS_EXTENSIONS:
            return False, f"Extensión bloqueada por seguridad: {ext}"
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Extensión no permitida: {ext}. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
        return True, ""

    def _validate_mime_type(self, content_type: str | None, filename: str) -> tuple[bool, str]:
        """Valida que el MIME type esté permitido."""
        if not content_type:
            return False, "Content-Type no proporcionado"

        # Normalizar MIME type
        main_type = content_type.split(";")[0].strip().lower()

        if main_type not in ALLOWED_MIME_TYPES:
            # Fallback: intentar adivinar por extensión
            guessed, _ = mimetypes.guess_type(filename)
            if guessed and guessed in ALLOWED_MIME_TYPES:
                return True, ""
            return False, f"Tipo de archivo no permitido: {main_type}"

        return True, ""

    def _validate_content_mismatch(self, content: bytes, declared_mime: str, filename: str) -> tuple[bool, str]:
        """Valida que el contenido real coincida con el MIME declarado (magic bytes)."""
        try:
            import magic
            detected = magic.from_buffer(content, mime=True)
            if detected and detected not in ALLOWED_MIME_TYPES:
                # Verificar si el tipo detectado es consistente con la extensión
                guessed, _ = mimetypes.guess_type(filename)
                if detected != guessed:
                    return False, f"Tipo de archivo real ({detected}) no coincide con el declarado ({declared_mime})"
        except ImportError:
            pass  # python-magic no disponible, saltar validación
        return True, ""

    def _scan_with_clamav(self, content: bytes) -> ScanResult:
        """Escanea el contenido con ClamAV."""
        cd = self._get_clamd()
        if cd is None:
            # Si ClamAV no está disponible, rechazar el archivo en producción
            env = os.getenv("ENVIRONMENT", "development")
            if env == "production":
                return ScanResult(
                    clean=False,
                    message="Servicio de antivirus no disponible. Subida de archivos bloqueada temporalmente.",
                )
            # En desarrollo, permitir con warning
            return ScanResult(
                clean=True,
                message="Escaneo omitido (ClamAV no disponible en desarrollo)",
                details={"skipped": True, "reason": "ClamAV no disponible"},
            )

        try:
            result = cd.scan_stream(io.BytesIO(content))
            if result and "stream" in result:
                scan_result = result["stream"]
                if scan_result[0] == "FOUND":
                    return ScanResult(
                        clean=False,
                        message=f"MALWARE DETECTADO: {scan_result[1]}",
                        details={"virus": scan_result[1], "scanner": "ClamAV"},
                    )
                elif scan_result[0] == "ERROR":
                    return ScanResult(
                        clean=False,
                        message=f"Error en escaneo: {scan_result[1]}",
                        details={"error": scan_result[1]},
                    )

            return ScanResult(
                clean=True,
                message="Archivo limpio (ClamAV)",
                details={"scanner": "ClamAV", "status": "OK"},
            )
        except Exception as e:
            return ScanResult(
                clean=False,
                message=f"Error al escanear con ClamAV: {str(e)}",
                details={"error": str(e)},
            )

    async def scan_upload(self, file: UploadFile) -> ScanResult:
        """
        Escanea un archivo subido por un usuario.
        Realiza validaciones de extensión, MIME, firmas y escaneo antivirus.
        """
        # Validar tamaño
        content = await file.read()
        await file.seek(0)

        if len(content) > MAX_FILE_SIZE:
            return ScanResult(
                clean=False,
                message=f"Archivo demasiado grande: {len(content)} bytes. Máximo: {MAX_FILE_SIZE} bytes",
                details={"max_size": MAX_FILE_SIZE, "file_size": len(content)},
            )

        # Validar extensión
        valid, msg = self._validate_extension(file.filename or "")
        if not valid:
            return ScanResult(clean=False, message=msg)

        # Validar MIME type
        valid, msg = self._validate_mime_type(file.content_type, file.filename or "")
        if not valid:
            return ScanResult(clean=False, message=msg)

        # Validar firma peligrosa
        dangerous, msg = self._has_dangerous_signature(content)
        if dangerous:
            return ScanResult(clean=False, message=msg, details={"signature_match": True})

        # Validar contenido vs MIME declarado
        valid, msg = self._validate_content_mismatch(
            content, file.content_type or "", file.filename or ""
        )
        if not valid:
            return ScanResult(clean=False, message=msg)

        # Escaneo con ClamAV
        scan_result = self._scan_with_clamav(content)
        return scan_result

    def calculate_sha256(self, content: bytes) -> str:
        """Calcula hash SHA-256 del archivo para trazabilidad."""
        return hashlib.sha256(content).hexdigest()


# Instancia global
file_scanner = FileScanner()
