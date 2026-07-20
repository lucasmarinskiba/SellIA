"""
Endpoint seguro para subida de archivos con escaneo antivirus.
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from fastapi_limiter.depends import RateLimiter

from app.core.file_scanner import file_scanner, ScanResult
from app.core.deps import get_current_active_user
from app.domains.users.models import User

router = APIRouter()

# Directorio de uploads (debe ser un volumen persistente en producción)
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    summary="Subir archivo de forma segura",
    description="Sube un archivo que será escaneado por antivirus ClamAV antes de ser aceptado.",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    Endpoint seguro para subida de archivos.
    
    Validaciones:
    - Extensión en whitelist
    - MIME type verificado
    - Firma de archivo (magic bytes) validada
    - Escaneo antivirus con ClamAV
    - Rate limiting: 10 archivos/minuto
    """
    # Escaneo de seguridad
    scan_result = await file_scanner.scan_upload(file)

    if not scan_result.clean:
        # Loguear intento de subida maliciosa
        from app.middleware.security_logging import security_logger
        import json
        security_logger.warning(json.dumps({
            "event": "MALICIOUS_UPLOAD_BLOCKED",
            "user_id": str(current_user.id),
            "filename": file.filename,
            "ip": getattr(request.state, "client_ip", "unknown"),
            "reason": scan_result.message,
            "details": scan_result.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Archivo rechazado por seguridad",
                "reason": scan_result.message,
                "details": scan_result.details,
            },
        )

    # Calcular hash para trazabilidad
    content = await file.read()
    file_hash = file_scanner.calculate_sha256(content)
    await file.seek(0)

    # Generar nombre único y seguro
    safe_ext = Path(file.filename or "").suffix.lower()
    if safe_ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".txt", ".csv", ".xlsx", ".docx"}:
        safe_ext = ".bin"

    unique_name = f"{uuid.uuid4().hex}_{file_hash[:16]}{safe_ext}"
    file_path = UPLOAD_DIR / unique_name

    # Guardar archivo
    with open(file_path, "wb") as f:
        f.write(content)

    # Loguear subida exitosa
    from app.middleware.security_logging import security_logger
    import json
    security_logger.info(json.dumps({
        "event": "FILE_UPLOAD_SUCCESS",
        "user_id": str(current_user.id),
        "filename": file.filename,
        "stored_as": unique_name,
        "sha256": file_hash,
        "size": len(content),
        "ip": getattr(request.state, "client_ip", "unknown"),
        "scan_result": scan_result.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False))

    return {
        "success": True,
        "filename": file.filename,
        "stored_as": unique_name,
        "sha256": file_hash,
        "size": len(content),
        "scan_result": scan_result.message,
        "download_url": f"/api/v1/upload/download/{unique_name}",
    }


@router.get("/upload/download/{filename}")
async def download_file(filename: str, current_user: User = Depends(get_current_active_user)):
    """
    Descarga un archivo previamente subido.
    Valida que el nombre no contenga path traversal.
    """
    # Prevenir path traversal
    safe_name = Path(filename).name
    if safe_name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    file_path = UPLOAD_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/octet-stream",
    )
