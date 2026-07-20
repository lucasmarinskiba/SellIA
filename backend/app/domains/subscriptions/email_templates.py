"""
Plantillas de email para suscripciones y pagos.

Cada función retorna (subject, html_body, text_body).
"""

from app.core.email_service import base_email_template


def transfer_order_created(order_number: str, plan_name: str, amount: float, currency: str, alias: str, cbu: str | None, holder: str, expires_at: str) -> tuple[str, str, str]:
    subject = f"Orden de pago #{order_number} — SellIA"

    cbu_html = f"""
        <div class="box-row"><span>CBU</span><span>{cbu}</span></div>
    """ if cbu else ""

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Recibimos tu solicitud para el plan <strong>{plan_name}</strong>. Acá están los datos para realizar la transferencia bancaria:</p>

        <div class="box">
            <div class="box-row"><span>N° de orden</span><span><code>{order_number}</code></span></div>
            <div class="box-row"><span>Plan</span><span>{plan_name}</span></div>
            <div class="box-row"><span>Monto</span><span>{amount:,.2f} {currency}</span></div>
            <div class="box-row"><span>Titular</span><span>{holder}</span></div>
            <div class="box-row"><span>Alias</span><span><code>{alias}</code></span></div>
            {cbu_html}
            <div class="box-row"><span>Válido hasta</span><span>{expires_at}</span></div>
        </div>

        <p>Una vez realizada la transferencia, volvé a la plataforma y confirmá el pago. Tenés 48 horas para completarla.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Ir a mis planes</a></p>
    """)

    text = f"""Orden de pago #{order_number} — SellIA

Plan: {plan_name}
Monto: {amount:,.2f} {currency}
Titular: {holder}
Alias: {alias}
CBU: {cbu or '—'}
Válido hasta: {expires_at}

Una vez realizada la transferencia, volvé a la plataforma y confirmá el pago.
https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def transfer_reminder(order_number: str, plan_name: str, amount: float, currency: str, hours_left: int) -> tuple[str, str, str]:
    subject = f"Recordatorio: tu orden #{order_number} expira en {hours_left}h"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Tu orden de pago para el plan <strong>{plan_name}</strong> está por vencer.</p>

        <div class="box">
            <div class="box-row"><span>N° de orden</span><span>{order_number}</span></div>
            <div class="box-row"><span>Monto</span><span>{amount:,.2f} {currency}</span></div>
            <div class="box-row"><span>Tiempo restante</span><span style="color:#ef4444;">{hours_left} horas</span></div>
        </div>

        <p>Si ya realizaste la transferencia, no olvides confirmarla desde la plataforma.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Confirmar pago</a></p>
    """)

    text = f"""Recordatorio: tu orden #{order_number} expira en {hours_left}h

Plan: {plan_name}
Monto: {amount:,.2f} {currency}

Si ya realizaste la transferencia, confirmala desde:
https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def transfer_expired(order_number: str, plan_name: str) -> tuple[str, str, str]:
    subject = f"Orden #{order_number} expirada"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Tu orden de pago <strong>#{order_number}</strong> para el plan <strong>{plan_name}</strong> expiró.</p>
        <p>Si aún querés suscribirte, podés generar una nueva orden desde la plataforma.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Generar nueva orden</a></p>
    """)

    text = f"""Orden #{order_number} expirada

Tu orden de pago para el plan {plan_name} expiró.
Si aún querés suscribirte, generá una nueva orden:
https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def transfer_confirmed(order_number: str, plan_name: str) -> tuple[str, str, str]:
    subject = f"Comprobante recibido — Orden #{order_number}"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Recibimos la confirmación de tu transferencia para la orden <strong>#{order_number}</strong>.</p>
        <p>Estamos verificando el pago. Te avisaremos en cuanto esté aprobado (generalmente en 24-48h hábiles).</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Ver estado</a></p>
    """)

    text = f"""Comprobante recibido — Orden #{order_number}

Estamos verificando tu pago. Te avisaremos en cuanto esté aprobado.
https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def transfer_approved(order_number: str, plan_name: str, period_end: str) -> tuple[str, str, str]:
    subject = f"¡Pago aprobado! Plan {plan_name} activado"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>¡Excelente noticia! Tu transferencia <strong>#{order_number}</strong> fue aprobada.</p>
        <p>Tu plan <strong>{plan_name}</strong> ya está activo.</p>

        <div class="box">
            <div class="box-row"><span>Plan activo</span><span>{plan_name}</span></div>
            <div class="box-row"><span>Próxima facturación</span><span>{period_end}</span></div>
        </div>

        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard" class="cta">Ir al dashboard</a></p>
    """)

    text = f"""¡Pago aprobado! Plan {plan_name} activado

Tu transferencia #{order_number} fue aprobada.
Próxima facturación: {period_end}

https://app.sellia.com/dashboard
"""
    return subject, html, text


def transfer_rejected(order_number: str, plan_name: str, reason: str | None = None) -> tuple[str, str, str]:
    subject = f"Transferencia rechazada — Orden #{order_number}"

    reason_html = f"<p><strong>Motivo:</strong> {reason}</p>" if reason else ""

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Tu transferencia <strong>#{order_number}</strong> para el plan <strong>{plan_name}</strong> no pudo ser verificada.</p>
        {reason_html}
        <p>Si creés que fue un error, contactanos respondiendo a este email o generá una nueva orden.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Generar nueva orden</a></p>
    """)

    text = f"""Transferencia rechazada — Orden #{order_number}

Tu transferencia para el plan {plan_name} no pudo ser verificada.
{reason or ''}

https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def subscription_cancelled(plan_name: str, period_end: str) -> tuple[str, str, str]:
    subject = "Tu suscripción fue cancelada"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Tu suscripción al plan <strong>{plan_name}</strong> fue cancelada.</p>
        <p>Vas a seguir teniendo acceso hasta el <strong>{period_end}</strong>.</p>
        <p>Si querés reactivarla en cualquier momento, podés hacerlo desde la plataforma.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/planes" class="cta">Ver planes</a></p>
    """)

    text = f"""Tu suscripción fue cancelada

Tu suscripción al plan {plan_name} fue cancelada.
Vas a seguir teniendo acceso hasta el {period_end}.

https://app.sellia.com/dashboard/planes
"""
    return subject, html, text


def preapproval_payment_failed(plan_name: str, next_retry: str | None = None) -> tuple[str, str, str]:
    subject = f"Problema con el cobro de {plan_name}"

    retry_html = f"<p>El próximo intento de cobro será el <strong>{next_retry}</strong>.</p>" if next_retry else ""

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>No pudimos procesar el cobro automático de tu suscripción al plan <strong>{plan_name}</strong>.</p>
        <p>Esto puede deberse a una tarjeta vencida, fondos insuficientes o un problema temporal con el banco.</p>
        {retry_html}
        <p>Si el problema persiste, tu suscripción podría pausarse. Actualizá tus datos de pago para evitar interrupciones.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/suscripcion" class="cta">Actualizar datos de pago</a></p>
    """)

    text = f"""Problema con el cobro de {plan_name}

No pudimos procesar el cobro automático de tu suscripción.
{next_retry and f'Próximo intento: {next_retry}' or ''}

Actualizá tus datos de pago:
https://app.sellia.com/dashboard/suscripcion
"""
    return subject, html, text


def preapproval_activated(plan_name: str, amount: float, currency: str, next_payment: str) -> tuple[str, str, str]:
    subject = f"Cobro automático activado — {plan_name}"

    html = base_email_template(f"""
        <p>Hola,</p>
        <p>Activaste el cobro automático para el plan <strong>{plan_name}</strong>.</p>

        <div class="box">
            <div class="box-row"><span>Plan</span><span>{plan_name}</span></div>
            <div class="box-row"><span>Monto mensual</span><span>{amount:,.2f} {currency}</span></div>
            <div class="box-row"><span>Próximo cobro</span><span>{next_payment}</span></div>
        </div>

        <p>Podés cancelar la renovación automática en cualquier momento desde tu cuenta.</p>
        <p style="margin-top:20px;"><a href="https://app.sellia.com/dashboard/suscripcion" class="cta">Gestionar suscripción</a></p>
    """)

    text = f"""Cobro automático activado — {plan_name}

Plan: {plan_name}
Monto mensual: {amount:,.2f} {currency}
Próximo cobro: {next_payment}

https://app.sellia.com/dashboard/suscripcion
"""
    return subject, html, text
