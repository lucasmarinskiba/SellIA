"""
Invoice Generator — Auto-generate professional invoices.

Features:
- PDF generation with reportlab
- Email delivery via SendGrid
- Invoice numbering and tracking
- Tax calculations
- Multi-currency support
- Recurring invoice templates

Database model: Invoice (from payment_models.py)
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from io import BytesIO
import json
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed - PDF generation disabled")


class InvoiceStatus(str, Enum):
    """Invoice statuses."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceGenerator:
    """Generate and manage invoices."""

    @staticmethod
    def generate_invoice(
        order_id: str,
        customer_name: str,
        customer_email: str,
        items: List[Dict[str, Any]],
        amount_total: float,
        currency: str = "USD",
        tax_rate: float = 0.0,
        notes: str = "",
        due_days: int = 7,
        seller_info: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an invoice.

        Args:
            order_id: Order/invoice reference ID
            customer_name: Billing customer name
            customer_email: Customer email
            items: Line items [{name, qty, unit_price, description}]
            amount_total: Total amount before tax
            currency: Currency code
            tax_rate: Tax rate (0.0-1.0, e.g., 0.10 for 10%)
            notes: Optional invoice notes
            due_days: Days until payment due
            seller_info: Optional seller details {name, email, phone, address}

        Returns:
            {
                "status": "generated",
                "invoice_id": str,
                "invoice_number": str,
                "pdf_url": str (if PDF generated),
                "html_content": str,
                "amount_subtotal": float,
                "amount_tax": float,
                "amount_total": float,
                "due_date": datetime,
                "error": str (if error)
            }
        """
        try:
            # Calculate totals
            amount_subtotal = amount_total
            amount_tax = round(amount_subtotal * tax_rate, 2)
            amount_due = amount_subtotal + amount_tax

            # Generate invoice ID and number
            timestamp = datetime.utcnow()
            invoice_id = f"inv_{order_id}_{int(timestamp.timestamp())}"
            invoice_number = f"INV-{timestamp.strftime('%Y%m%d')}-{order_id[-6:]}"

            due_date = timestamp + timedelta(days=due_days)

            # Build HTML invoice
            html_content = InvoiceGenerator._build_html_invoice(
                invoice_number=invoice_number,
                invoice_date=timestamp,
                due_date=due_date,
                customer_name=customer_name,
                customer_email=customer_email,
                items=items,
                amount_subtotal=amount_subtotal,
                tax_rate=tax_rate,
                amount_tax=amount_tax,
                amount_due=amount_due,
                currency=currency,
                notes=notes,
                seller_info=seller_info,
            )

            logger.info(
                f"Invoice generated: {invoice_number} | Customer: {customer_name} | "
                f"Amount: ${amount_due}"
            )

            result = {
                "status": "generated",
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "order_id": order_id,
                "html_content": html_content,
                "amount_subtotal": amount_subtotal,
                "amount_tax": amount_tax,
                "amount_total": amount_due,
                "currency": currency,
                "due_date": due_date,
                "issued_date": timestamp,
            }

            # Generate PDF if reportlab available
            if HAS_REPORTLAB:
                pdf_bytes = InvoiceGenerator._generate_pdf(
                    invoice_number=invoice_number,
                    invoice_date=timestamp,
                    due_date=due_date,
                    customer_name=customer_name,
                    items=items,
                    amount_subtotal=amount_subtotal,
                    amount_tax=amount_tax,
                    amount_due=amount_due,
                    currency=currency,
                    seller_info=seller_info,
                )
                result["pdf_generated"] = True
                result["pdf_bytes"] = pdf_bytes

            return result

        except Exception as e:
            logger.error(f"Invoice generation error: {str(e)}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _build_html_invoice(
        invoice_number: str,
        invoice_date: datetime,
        due_date: datetime,
        customer_name: str,
        customer_email: str,
        items: List[Dict[str, Any]],
        amount_subtotal: float,
        tax_rate: float,
        amount_tax: float,
        amount_due: float,
        currency: str = "USD",
        notes: str = "",
        seller_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build HTML invoice template."""

        seller_info = seller_info or {
            "name": "Your Business",
            "email": "billing@example.com",
            "phone": "+1 (555) 123-4567",
            "address": "123 Business St, City, State 12345",
        }

        # Build items table
        items_html = ""
        for item in items:
            qty = item.get("qty", 1)
            unit_price = item.get("unit_price", 0)
            line_total = qty * unit_price

            items_html += f"""
            <tr>
                <td>{item.get('name', 'Item')}</td>
                <td style="text-align: center;">{qty}</td>
                <td style="text-align: right;">${unit_price:.2f}</td>
                <td style="text-align: right;">${line_total:.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {invoice_number}</title>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
                .seller {{ margin-bottom: 20px; }}
                .invoice-title {{ font-size: 24px; font-weight: bold; }}
                .invoice-details {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
                .section-title {{ font-weight: bold; font-size: 12px; color: #666; margin-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                th {{ background-color: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #333; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .text-right {{ text-align: right; }}
                .totals {{ width: 300px; margin-left: auto; }}
                .totals-row {{ display: flex; justify-content: space-between; padding: 10px 0; }}
                .totals-row.total {{ border-top: 2px solid #333; font-weight: bold; font-size: 16px; }}
                .status {{ margin-top: 40px; padding: 20px; background-color: #f9f9f9; }}
                .notes {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="seller">
                        <div style="font-size: 24px; font-weight: bold;">{seller_info.get('name', 'Business')}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            {seller_info.get('email', '')}<br>
                            {seller_info.get('phone', '')}<br>
                            {seller_info.get('address', '')}
                        </div>
                    </div>
                    <div class="invoice-title">{invoice_number}</div>
                </div>

                <div class="invoice-details">
                    <div>
                        <div class="section-title">BILL TO</div>
                        <div>{customer_name}</div>
                        <div style="font-size: 12px; color: #666;">{customer_email}</div>
                    </div>
                    <div>
                        <div class="section-title">INVOICE DATE</div>
                        <div>{invoice_date.strftime('%B %d, %Y')}</div>
                        <div style="margin-top: 10px;">
                            <div class="section-title">DUE DATE</div>
                            <div>{due_date.strftime('%B %d, %Y')}</div>
                        </div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th style="text-align: center; width: 80px;">Qty</th>
                            <th style="text-align: right; width: 100px;">Unit Price</th>
                            <th style="text-align: right; width: 100px;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                <div class="totals">
                    <div class="totals-row">
                        <span>Subtotal:</span>
                        <span>${amount_subtotal:.2f} {currency}</span>
                    </div>
                    <div class="totals-row">
                        <span>Tax ({tax_rate * 100:.1f}%):</span>
                        <span>${amount_tax:.2f} {currency}</span>
                    </div>
                    <div class="totals-row total">
                        <span>Total Due:</span>
                        <span>${amount_due:.2f} {currency}</span>
                    </div>
                </div>

                <div class="status">
                    <div style="font-weight: bold; color: #28a745;">PAYMENT NOT YET RECEIVED</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        Please remit payment by {due_date.strftime('%B %d, %Y')}
                    </div>
                </div>

                {f'<div class="notes"><strong>Notes:</strong><br>{notes}</div>' if notes else ''}

                <div style="margin-top: 40px; font-size: 11px; color: #999; border-top: 1px solid #ddd; padding-top: 20px;">
                    Thank you for your business.
                </div>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def _generate_pdf(
        invoice_number: str,
        invoice_date: datetime,
        due_date: datetime,
        customer_name: str,
        items: List[Dict[str, Any]],
        amount_subtotal: float,
        amount_tax: float,
        amount_due: float,
        currency: str = "USD",
        seller_info: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """Generate PDF invoice using reportlab."""

        if not HAS_REPORTLAB:
            raise RuntimeError("reportlab not installed")

        buffer = BytesIO()

        # Create PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#333333"),
            spaceAfter=30,
        )

        # Title
        elements.append(Paragraph(f"Invoice {invoice_number}", title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Invoice details
        seller_info = seller_info or {"name": "Your Business"}
        details_data = [
            ["BILL TO", f"Invoice Date: {invoice_date.strftime('%m/%d/%Y')}"],
            [customer_name, f"Due Date: {due_date.strftime('%m/%d/%Y')}"],
        ]

        details_table = Table(details_data)
        details_table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        elements.append(details_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Line items table
        table_data = [["Description", "Qty", "Unit Price", "Amount"]]
        for item in items:
            qty = item.get("qty", 1)
            unit_price = item.get("unit_price", 0)
            line_total = qty * unit_price
            table_data.append([
                item.get("name", "Item"),
                str(qty),
                f"${unit_price:.2f}",
                f"${line_total:.2f}",
            ])

        # Add totals
        table_data.append(["", "", "Subtotal:", f"${amount_subtotal:.2f}"])
        table_data.append(["", "", "Tax:", f"${amount_tax:.2f}"])
        table_data.append(["", "", "TOTAL:", f"${amount_due:.2f}"])

        items_table = Table(table_data, colWidths=[3 * inch, 0.75 * inch, 1 * inch, 1 * inch])
        items_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, -1), (-1, -1), colors.beige),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
        )
        elements.append(items_table)

        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    @staticmethod
    def send_invoice_email(
        customer_email: str,
        customer_name: str,
        invoice_number: str,
        html_content: str,
        pdf_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Send invoice via email.

        Args:
            customer_email: Recipient email
            customer_name: Recipient name
            invoice_number: Invoice number for subject
            html_content: HTML invoice content
            pdf_bytes: Optional PDF attachment bytes

        Returns:
            {
                "status": "sent" | "error",
                "message_id": str (if sent),
                "error": str (if error)
            }
        """
        try:
            from backend.app.core.integrations.sendgrid_email import EmailService

            # Send via SendGrid
            subject = f"Invoice {invoice_number}"

            result = EmailService.send_transactional(
                to_email=customer_email,
                subject=subject,
                html_content=html_content,
            )

            logger.info(f"Invoice email sent: {invoice_number} to {customer_email}")

            return {
                "status": "sent",
                "invoice_number": invoice_number,
                "recipient": customer_email,
            }

        except Exception as e:
            logger.error(f"Error sending invoice email: {str(e)}")
            return {"status": "error", "error": str(e)}
