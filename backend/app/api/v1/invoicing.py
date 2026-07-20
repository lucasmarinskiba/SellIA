"""
Invoicing — Generación de facturas PDF, historial, email automático.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

router = APIRouter(prefix="/api/v1/invoicing", tags=["invoicing"])
logger = logging.getLogger(__name__)

# Mock invoice DB
_INVOICES_DB: Dict[str, Any] = {}


class InvoiceLineItem(BaseModel):
    """Item en factura."""
    product_name: str
    qty: int
    unit_price: float
    total: float


class Invoice(BaseModel):
    """Factura."""
    id: str
    invoice_number: str  # INV-2026-0001
    order_id: str
    business_name: str
    business_tax_id: str
    customer_name: str
    customer_email: str
    items: List[InvoiceLineItem]
    subtotal: float
    tax_pct: float
    tax_amount: float
    total: float
    issued_at: datetime
    due_date: datetime
    status: str  # draft, issued, paid


@router.post("/invoices", tags=["create"])
async def create_invoice(
    order_id: str,
    customer_name: str,
    customer_email: str,
    items: List[Dict[str, Any]],
    subtotal: float,
    tax_pct: float = 0.0,
):
    """
    Crea factura automáticamente cuando pago confirmado.

    Calcula tax, genera número secuencial, envía email.
    """

    try:
        # TODO: Obtener datos del negocio desde config
        business_name = "Mi Negocio"
        business_tax_id = "CIF-123456"

        # Calcular montos
        tax_amount = subtotal * (tax_pct / 100)
        total = subtotal + tax_amount

        # Generar número de factura (TODO: incrementar desde última)
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y')}-0001"
        invoice_id = f"inv_{order_id}"

        # Crear factura
        invoice = {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "order_id": order_id,
            "business_name": business_name,
            "business_tax_id": business_tax_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "items": items,
            "subtotal": round(subtotal, 2),
            "tax_pct": tax_pct,
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2),
            "issued_at": datetime.utcnow().isoformat(),
            "due_date": datetime.utcnow().isoformat(),  # TODO: +30 días si crédito
            "status": "issued",
        }

        _INVOICES_DB[invoice_id] = invoice

        logger.info(f"Factura creada: {invoice_number} para {customer_name}")

        # TODO: Generar PDF (pdfkit/weasyprint)
        # pdf_bytes = generate_pdf_from_template(invoice)
        # save_to_s3(f"invoices/{invoice_number}.pdf", pdf_bytes)

        # TODO: Enviar email
        # send_email(
        #     to=customer_email,
        #     subject=f"Tu factura {invoice_number}",
        #     body=f"Adjunta tu factura. Total: ${total}",
        #     attachment=("invoice.pdf", pdf_bytes)
        # )

        return {
            "status": "created",
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "pdf_url": f"/invoices/{invoice_id}.pdf",  # TODO: real URL
            "total": total,
        }

    except Exception as e:
        logger.error(f"Error creando factura: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/{invoice_id}", tags=["retrieve"])
async def get_invoice(invoice_id: str):
    """Obtener detalles factura."""

    if invoice_id not in _INVOICES_DB:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return _INVOICES_DB[invoice_id]


@router.post("/invoices/{invoice_id}/email", tags=["send"])
async def send_invoice_email(invoice_id: str):
    """Reenviar factura por email."""

    if invoice_id not in _INVOICES_DB:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = _INVOICES_DB[invoice_id]

    logger.info(f"Reenviando factura {invoice['invoice_number']} a {invoice['customer_email']}")

    # TODO: send_email con PDF adjunto

    return {
        "status": "sent",
        "invoice_number": invoice["invoice_number"],
        "sent_to": invoice["customer_email"]
    }


@router.get("/invoices/orders/{order_id}", tags=["lookup"])
async def get_invoices_for_order(order_id: str):
    """Obtener todas las facturas de una orden."""

    invoices = [inv for inv in _INVOICES_DB.values() if inv["order_id"] == order_id]

    return {"total": len(invoices), "invoices": invoices}
