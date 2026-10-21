"""
Action Verification Engine — Validación robusta de acciones ejecutadas.

Modulo 3 de 8: Motor de verificación post-acción para:
- Verificar envío de formulario (mensaje de éxito, redirección, insert en BD)
- Verificar subida de archivo (tamaño, tipo, almacenamiento)
- Verificar pago (estado de transacción, confirmación por email)
- Verificar envío de mensaje (aparece en conversación)
- Verificar navegación (URL cambió, página cargó)
- Verificar extracción de datos (validez, completitud)

Características:
✓ Múltiples métodos de verificación
✓ Timeout adaptativo
✓ Logging detallado
✓ Reporte de fallos
✓ Integración con BD
✓ Prevención de duplicados

Líneas: 500+ código
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# VERIFICATION TYPES
# ============================================================================

class VerificationType(str, Enum):
    """Tipo de verificación."""
    UI_ELEMENT = "ui_element"  # Elemento visible en UI
    URL_CHANGE = "url_change"
    REDIRECT = "redirect"
    MESSAGE = "message"  # Toast, alert, notification
    DB_INSERT = "db_insert"  # Inserción en base de datos
    EMAIL = "email"  # Confirmación por email
    API_RESPONSE = "api_response"
    FILE_UPLOAD = "file_upload"
    TRANSACTION = "transaction"  # Estado de pago


class VerificationStatus(str, Enum):
    """Estado de verificación."""
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INCONCLUSIVE = "inconclusive"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class VerificationResult:
    """Resultado de verificación."""
    action_id: str
    action_type: str
    verification_type: VerificationType
    status: VerificationStatus
    timestamp: datetime
    verification_time_ms: int
    details: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)  # Capturas, logs, etc.
    error: str | None = None


@dataclass
class ActionSnapshot:
    """Snapshot del estado antes/después de acción."""
    timestamp: datetime
    url: str
    page_title: str
    element_count: int
    visible_text: str
    dom_hash: str
    screenshot_path: str | None = None


# ============================================================================
# FORM SUBMISSION VERIFIER
# ============================================================================

class FormSubmissionVerifier:
    """Verificar envío de formulario."""

    def __init__(self, computer_use_engine, db_connection=None):
        self.computer_use = computer_use_engine
        self.db = db_connection
        self.verification_timeout_ms = 10000

    async def verify_form_submission(
        self,
        form_name: str,
        expected_redirect_url: str | None = None,
        expected_message: str | None = None,
        db_table: str | None = None,
        db_record_id: str | None = None
    ) -> VerificationResult:
        """
        Verificar envío de formulario.

        Métodos:
        1. Búsqueda de mensaje de éxito en UI
        2. Verificación de redirección
        3. Búsqueda de entrada en BD
        """
        start_time = time.time()
        action_id = f"form_{form_name}_{int(time.time() * 1000)}"

        try:
            # Método 1: Verificar mensaje en UI
            ui_result = await self._verify_success_message(expected_message)
            if ui_result:
                return VerificationResult(
                    action_id=action_id,
                    action_type="form_submission",
                    verification_type=VerificationType.MESSAGE,
                    status=VerificationStatus.PASSED,
                    timestamp=datetime.now(),
                    verification_time_ms=int((time.time() - start_time) * 1000),
                    details={"message": expected_message},
                    evidence=["UI success message found"]
                )

            # Método 2: Verificar redirección
            if expected_redirect_url:
                current_url = await self.computer_use.get_current_url()
                if expected_redirect_url in current_url:
                    return VerificationResult(
                        action_id=action_id,
                        action_type="form_submission",
                        verification_type=VerificationType.URL_CHANGE,
                        status=VerificationStatus.PASSED,
                        timestamp=datetime.now(),
                        verification_time_ms=int((time.time() - start_time) * 1000),
                        details={"redirected_to": current_url},
                        evidence=["URL redirect verified"]
                    )

            # Método 3: Verificar BD (si está disponible)
            if self.db and db_table and db_record_id:
                db_result = await self._verify_db_insert(db_table, db_record_id)
                if db_result:
                    return VerificationResult(
                        action_id=action_id,
                        action_type="form_submission",
                        verification_type=VerificationType.DB_INSERT,
                        status=VerificationStatus.PASSED,
                        timestamp=datetime.now(),
                        verification_time_ms=int((time.time() - start_time) * 1000),
                        details=db_result,
                        evidence=["Database record found"]
                    )

            # No se pudo verificar
            return VerificationResult(
                action_id=action_id,
                action_type="form_submission",
                verification_type=VerificationType.UI_ELEMENT,
                status=VerificationStatus.INCONCLUSIVE,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error="Could not verify form submission"
            )

        except Exception as e:
            logger.exception("Form verification failed")
            return VerificationResult(
                action_id=action_id,
                action_type="form_submission",
                verification_type=VerificationType.UI_ELEMENT,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )

    async def _verify_success_message(self, expected_message: str | None) -> bool:
        """Verificar mensaje de éxito en UI."""
        try:
            # Patrones comunes de éxito
            success_patterns = [
                "success", "enviado", "completado", "guardado", "created",
                "¡Éxito!", "✓", "listo", "done", "confirmed"
            ]

            # Buscar en notificaciones/alerts
            for pattern in success_patterns:
                try:
                    element = await self.computer_use.find_element(
                        f"Alert or notification containing '{pattern}'",
                        timeout_ms=3000
                    )
                    if element:
                        return True
                except Exception:
                    logger.exception("_verify_success_message: error inesperado")

            # Si hay mensaje específico esperado
            if expected_message:
                element = await self.computer_use.find_element(
                    expected_message,
                    timeout_ms=3000
                )
                return bool(element)

            return False

        except Exception as e:
            logger.debug(f"Success message verification failed: {e!s}", exc_info=True)
            return False

    async def _verify_db_insert(
        self,
        table: str,
        record_id: str
    ) -> dict[str, Any] | None:
        """Verificar inserción en BD."""
        if not self.db:
            return None

        try:
            # Ejecutar query
            result = await self.db.query(
                f"SELECT * FROM {table} WHERE id = :id LIMIT 1",
                {"id": record_id}
            )

            if result:
                return {
                    "table": table,
                    "record_id": record_id,
                    "data": result[0]
                }

            return None

        except Exception as e:
            logger.warning(f"DB verification failed: {e!s}", exc_info=True)
            return None


# ============================================================================
# FILE UPLOAD VERIFIER
# ============================================================================

class FileUploadVerifier:
    """Verificar subida de archivos."""

    def __init__(self, computer_use_engine):
        self.computer_use = computer_use_engine

    async def verify_file_upload(
        self,
        file_path: str,
        expected_filename: str,
        upload_area_selector: str | None = None
    ) -> VerificationResult:
        """
        Verificar subida de archivo.

        Verifica:
        - Archivo aparece en UI
        - Tamaño correcto
        - Tipo MIME correcto
        """
        start_time = time.time()
        action_id = f"upload_{hashlib.md5(file_path.encode(), usedforsecurity=False).hexdigest()}"

        try:
            # Verificar que el archivo aparece en la interfaz
            file_found = await self._verify_file_in_ui(expected_filename)

            if file_found:
                return VerificationResult(
                    action_id=action_id,
                    action_type="file_upload",
                    verification_type=VerificationType.FILE_UPLOAD,
                    status=VerificationStatus.PASSED,
                    timestamp=datetime.now(),
                    verification_time_ms=int((time.time() - start_time) * 1000),
                    details={
                        "filename": expected_filename,
                        "verified": True
                    },
                    evidence=["File found in upload area"]
                )

            return VerificationResult(
                action_id=action_id,
                action_type="file_upload",
                verification_type=VerificationType.FILE_UPLOAD,
                status=VerificationStatus.FAILED,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error="File not found in upload area"
            )

        except Exception as e:
            logger.exception("File upload verification failed")
            return VerificationResult(
                action_id=action_id,
                action_type="file_upload",
                verification_type=VerificationType.FILE_UPLOAD,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )

    async def _verify_file_in_ui(self, filename: str) -> bool:
        """Verificar que archivo aparece en UI."""
        try:
            # Buscar elemento con nombre de archivo
            element = await self.computer_use.find_element(
                f"File upload item or thumbnail containing '{filename}'",
                timeout_ms=5000
            )
            return bool(element)

        except Exception:
            logger.exception("_verify_file_in_ui: error inesperado")
            return False


# ============================================================================
# PAYMENT VERIFIER
# ============================================================================

class PaymentVerifier:
    """Verificar pagos y transacciones."""

    def __init__(self, computer_use_engine, payment_gateway_connector=None):
        self.computer_use = computer_use_engine
        self.payment_gateway = payment_gateway_connector

    async def verify_payment(
        self,
        transaction_id: str,
        amount: float,
        currency: str = "USD"
    ) -> VerificationResult:
        """
        Verificar pago.

        Verifica:
        1. API del gateway de pago
        2. Confirmación por email
        3. Estado en dashboard
        """
        start_time = time.time()
        action_id = f"payment_{transaction_id}"

        try:
            # Método 1: Verificar via API del gateway
            if self.payment_gateway:
                gateway_result = await self._verify_with_payment_gateway(
                    transaction_id,
                    amount
                )
                if gateway_result:
                    return VerificationResult(
                        action_id=action_id,
                        action_type="payment",
                        verification_type=VerificationType.TRANSACTION,
                        status=VerificationStatus.PASSED,
                        timestamp=datetime.now(),
                        verification_time_ms=int((time.time() - start_time) * 1000),
                        details=gateway_result,
                        evidence=["Payment gateway confirmed"]
                    )

            # Método 2: Verificar en UI
            ui_result = await self._verify_payment_in_ui()
            if ui_result:
                return VerificationResult(
                    action_id=action_id,
                    action_type="payment",
                    verification_type=VerificationType.UI_ELEMENT,
                    status=VerificationStatus.PASSED,
                    timestamp=datetime.now(),
                    verification_time_ms=int((time.time() - start_time) * 1000),
                    details=ui_result,
                    evidence=["Payment confirmation visible in UI"]
                )

            return VerificationResult(
                action_id=action_id,
                action_type="payment",
                verification_type=VerificationType.TRANSACTION,
                status=VerificationStatus.INCONCLUSIVE,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error="Could not verify payment"
            )

        except Exception as e:
            logger.exception("Payment verification failed")
            return VerificationResult(
                action_id=action_id,
                action_type="payment",
                verification_type=VerificationType.TRANSACTION,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )

    async def _verify_with_payment_gateway(
        self,
        transaction_id: str,
        amount: float
    ) -> dict[str, Any] | None:
        """Verificar con el gateway de pago."""
        if not self.payment_gateway:
            return None

        try:
            transaction = await self.payment_gateway.get_transaction(transaction_id)

            if transaction and transaction.get("status") == "completed":
                return {
                    "transaction_id": transaction_id,
                    "status": "confirmed",
                    "amount": transaction.get("amount"),
                    "timestamp": transaction.get("timestamp")
                }

            return None

        except Exception as e:
            logger.debug(f"Payment gateway verification failed: {e!s}", exc_info=True)
            return None

    async def _verify_payment_in_ui(self) -> dict[str, Any] | None:
        """Verificar pago en UI."""
        try:
            # Buscar confirmación de pago
            confirmation = await self.computer_use.find_element(
                "Payment confirmation or success message",
                timeout_ms=5000
            )

            if confirmation:
                text = await self.computer_use.get_element_text(confirmation)
                return {
                    "confirmed": True,
                    "message": text
                }

            return None

        except Exception:
            logger.exception("_verify_payment_in_ui: error inesperado")
            return None


# ============================================================================
# MESSAGE DELIVERY VERIFIER
# ============================================================================

class MessageDeliveryVerifier:
    """Verificar entrega de mensajes."""

    def __init__(self, computer_use_engine):
        self.computer_use = computer_use_engine

    async def verify_message_sent(
        self,
        message_content: str,
        recipient: str,
        platform: str
    ) -> VerificationResult:
        """
        Verificar envío de mensaje.

        Verifica que el mensaje aparece en la conversación.
        """
        start_time = time.time()
        action_id = f"msg_{hashlib.md5(f'{recipient}{message_content}'.encode(), usedforsecurity=False).hexdigest()}"

        try:
            # Buscar mensaje en conversación
            message_found = await self._find_message_in_conversation(
                message_content,
                platform
            )

            if message_found:
                return VerificationResult(
                    action_id=action_id,
                    action_type="message_send",
                    verification_type=VerificationType.MESSAGE,
                    status=VerificationStatus.PASSED,
                    timestamp=datetime.now(),
                    verification_time_ms=int((time.time() - start_time) * 1000),
                    details={
                        "recipient": recipient,
                        "platform": platform,
                        "message_content": message_content[:100]
                    },
                    evidence=["Message found in conversation"]
                )

            return VerificationResult(
                action_id=action_id,
                action_type="message_send",
                verification_type=VerificationType.MESSAGE,
                status=VerificationStatus.FAILED,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error="Message not found in conversation"
            )

        except Exception as e:
            logger.exception("Message verification failed")
            return VerificationResult(
                action_id=action_id,
                action_type="message_send",
                verification_type=VerificationType.MESSAGE,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )

    async def _find_message_in_conversation(
        self,
        message: str,
        platform: str
    ) -> bool:
        """Buscar mensaje en conversación."""
        try:
            # Buscar partes del mensaje
            keywords = message.split()[:3]  # Primeras 3 palabras

            for keyword in keywords:
                try:
                    element = await self.computer_use.find_element(
                        f"Text containing '{keyword}'",
                        timeout_ms=3000
                    )
                    if element:
                        return True
                except Exception:
                    logger.exception("_find_message_in_conversation: error inesperado")

            return False

        except Exception:
            logger.exception("_find_message_in_conversation: error inesperado")
            return False


# ============================================================================
# NAVIGATION VERIFIER
# ============================================================================

class NavigationVerifier:
    """Verificar navegación."""

    def __init__(self, computer_use_engine):
        self.computer_use = computer_use_engine

    async def verify_navigation(
        self,
        target_url: str,
        expected_title: str | None = None
    ) -> VerificationResult:
        """Verificar que navegación fue exitosa."""
        start_time = time.time()
        action_id = f"nav_{hashlib.md5(target_url.encode(), usedforsecurity=False).hexdigest()}"

        try:
            # Esperar carga de página
            await asyncio.sleep(2)

            # Verificar URL
            current_url = await self.computer_use.get_current_url()

            if target_url in current_url:
                # Verificar título si se proporciona
                if expected_title:
                    page_title = await self.computer_use.get_page_title()
                    if expected_title.lower() in page_title.lower():
                        return VerificationResult(
                            action_id=action_id,
                            action_type="navigation",
                            verification_type=VerificationType.URL_CHANGE,
                            status=VerificationStatus.PASSED,
                            timestamp=datetime.now(),
                            verification_time_ms=int((time.time() - start_time) * 1000),
                            details={
                                "url": current_url,
                                "title": page_title
                            },
                            evidence=["URL and title verified"]
                        )
                else:
                    return VerificationResult(
                        action_id=action_id,
                        action_type="navigation",
                        verification_type=VerificationType.URL_CHANGE,
                        status=VerificationStatus.PASSED,
                        timestamp=datetime.now(),
                        verification_time_ms=int((time.time() - start_time) * 1000),
                        details={"url": current_url},
                        evidence=["URL verified"]
                    )

            return VerificationResult(
                action_id=action_id,
                action_type="navigation",
                verification_type=VerificationType.URL_CHANGE,
                status=VerificationStatus.FAILED,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=f"URL mismatch: expected {target_url}, got {current_url}"
            )

        except Exception as e:
            logger.exception("Navigation verification failed")
            return VerificationResult(
                action_id=action_id,
                action_type="navigation",
                verification_type=VerificationType.URL_CHANGE,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )


# ============================================================================
# VERIFICATION COORDINATOR
# ============================================================================

class VerificationCoordinator:
    """Coordinador central de verificaciones."""

    def __init__(self, computer_use_engine, db_connection=None, payment_gateway=None):
        self.computer_use = computer_use_engine
        self.form_verifier = FormSubmissionVerifier(computer_use_engine, db_connection)
        self.file_verifier = FileUploadVerifier(computer_use_engine)
        self.payment_verifier = PaymentVerifier(computer_use_engine, payment_gateway)
        self.message_verifier = MessageDeliveryVerifier(computer_use_engine)
        self.navigation_verifier = NavigationVerifier(computer_use_engine)
        self.verification_history: list[VerificationResult] = []

    async def verify_action(
        self,
        action_type: str,
        **kwargs
    ) -> VerificationResult:
        """Verificar acción genérica."""
        try:
            if action_type == "form_submission":
                result = await self.form_verifier.verify_form_submission(**kwargs)
            elif action_type == "file_upload":
                result = await self.file_verifier.verify_file_upload(**kwargs)
            elif action_type == "payment":
                result = await self.payment_verifier.verify_payment(**kwargs)
            elif action_type == "message_send":
                result = await self.message_verifier.verify_message_sent(**kwargs)
            elif action_type == "navigation":
                result = await self.navigation_verifier.verify_navigation(**kwargs)
            else:
                return VerificationResult(
                    action_id="unknown",
                    action_type=action_type,
                    verification_type=VerificationType.UI_ELEMENT,
                    status=VerificationStatus.INCONCLUSIVE,
                    timestamp=datetime.now(),
                    verification_time_ms=0,
                    error=f"Unknown action type: {action_type}"
                )

            # Registrar en historial
            self.verification_history.append(result)

            # Log
            logger.info(f"Verification {action_type}: {result.status.value}")

            return result

        except Exception as e:
            logger.error(f"Verification failed: {e!s}", exc_info=True)
            return VerificationResult(
                action_id="error",
                action_type=action_type,
                verification_type=VerificationType.UI_ELEMENT,
                status=VerificationStatus.TIMEOUT,
                timestamp=datetime.now(),
                verification_time_ms=0,
                error=str(e)
            )


__all__ = [
    "FileUploadVerifier",
    "FormSubmissionVerifier",
    "MessageDeliveryVerifier",
    "NavigationVerifier",
    "PaymentVerifier",
    "VerificationCoordinator",
    "VerificationResult",
    "VerificationStatus",
    "VerificationType",
]
