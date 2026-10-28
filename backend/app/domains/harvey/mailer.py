"""Email transport for Harvey: SMTP out, IMAP in, through the business's own mailbox.

A business connects its mailbox once as an EMAIL channel (``channel_connections``
credentials: smtp_host/smtp_port/smtp_user/smtp_password/from_address, optionally
imap_host/imap_port/imap_user/imap_password). Harvey sends and reads through that
mailbox, never through a shared SellIA sender: the reputation, the replies and the
legal responsibility stay with the business that owns the list.

Network calls are isolated in ``send`` and ``fetch_new`` so tests can replace them.
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import re
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from uuid import UUID

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.channels.models import (
    ChannelConnection,
    ChannelPlatform,
    ChannelStatus,
)

logger = get_logger(__name__)

MAX_BODY_CHARS = 5000
IMAP_TIMEOUT = 30
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@dataclass
class EmailAccount:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_address: str
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str


@dataclass
class InboundEmail:
    uid: int
    message_id: str
    in_reply_to: str
    references: list[str]
    from_email: str
    from_name: str
    subject: str
    body: str
    is_auto: bool = False
    is_bounce: bool = False
    bounced_recipients: list[str] = field(default_factory=list)


# ── account ───────────────────────────────────────────────────────────────
def derive_imap_host(smtp_host: str) -> str:
    host = (smtp_host or "").strip().lower()
    if host in ("smtp.office365.com", "smtp-mail.outlook.com"):
        return "outlook.office365.com"
    if host.startswith("smtp."):
        return "imap." + host[len("smtp."):]
    return host


def account_from_credentials(creds: dict) -> EmailAccount | None:
    """None when the channel has no usable SMTP login (nothing can be sent or read)."""
    user = str(creds.get("smtp_user") or "").strip()
    password = str(creds.get("smtp_password") or "")
    if not user or not password:
        return None
    smtp_host = str(creds.get("smtp_host") or "smtp.gmail.com").strip()
    return EmailAccount(
        smtp_host=smtp_host,
        smtp_port=int(creds.get("smtp_port") or 587),
        smtp_user=user,
        smtp_password=password,
        from_address=str(creds.get("from_address") or user).strip(),
        imap_host=str(creds.get("imap_host") or derive_imap_host(smtp_host)).strip(),
        imap_port=int(creds.get("imap_port") or 993),
        imap_user=str(creds.get("imap_user") or user).strip(),
        imap_password=str(creds.get("imap_password") or password),
    )


async def get_email_account(db: AsyncSession, business_id: UUID) -> EmailAccount | None:
    """The business's own active EMAIL channel, or None if it has not connected one."""
    channels = (
        await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business_id,
                ChannelConnection.platform == ChannelPlatform.EMAIL,
                ChannelConnection.is_active.is_(True),
                # Only a mailbox whose owner confirmed it (code, or "Probar") may send in their name.
                ChannelConnection.status == ChannelStatus.CONNECTED,
            )
        )
    ).scalars()
    for channel in channels:
        account = account_from_credentials(channel.credentials or {})
        if account is not None:
            return account
    return None


@dataclass
class LoginCheck:
    ok: bool
    kind: str = ""  # auth | connect | other (the first thing that failed)
    host: str = ""


def _imap_login_sync(account: EmailAccount) -> LoginCheck:
    try:
        conn = imaplib.IMAP4_SSL(account.imap_host, account.imap_port, timeout=IMAP_TIMEOUT)
    except (TimeoutError, OSError):
        return LoginCheck(False, "connect", account.imap_host)
    try:
        conn.login(account.imap_user, account.imap_password)
    except imaplib.IMAP4.error:
        return LoginCheck(False, "auth", account.imap_host)
    except (TimeoutError, OSError):
        return LoginCheck(False, "connect", account.imap_host)
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    return LoginCheck(True)


async def check_login(account: EmailAccount) -> LoginCheck:
    """Log in to both servers (send and read) without sending anything. Never raises."""
    implicit_tls = account.smtp_port == 465
    smtp = aiosmtplib.SMTP(hostname=account.smtp_host, port=account.smtp_port, use_tls=implicit_tls, timeout=20)
    try:
        await smtp.connect(start_tls=not implicit_tls)
        await smtp.login(account.smtp_user, account.smtp_password)
    except aiosmtplib.SMTPAuthenticationError:
        return LoginCheck(False, "auth", account.smtp_host)
    except (OSError, asyncio.TimeoutError, aiosmtplib.SMTPConnectError, aiosmtplib.SMTPServerDisconnected):
        return LoginCheck(False, "connect", account.smtp_host)
    except aiosmtplib.SMTPException:
        return LoginCheck(False, "other", account.smtp_host)
    finally:
        try:
            await smtp.quit()
        except Exception:
            pass
    return await asyncio.to_thread(_imap_login_sync, account)


# ── outbound ──────────────────────────────────────────────────────────────
def build_message(
    account: EmailAccount,
    *,
    to_email: str,
    subject: str,
    body: str,
    sender_name: str = "",
    in_reply_to: str = "",
    references: list[str] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, account.from_address)) if sender_name else account.from_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=False)
    domain = account.from_address.rpartition("@")[2] or None
    msg["Message-ID"] = make_msgid(domain=domain)
    if in_reply_to:
        chain = list(references or [])
        if in_reply_to not in chain:
            chain.append(in_reply_to)
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = " ".join(chain)
    # Mailbox providers expect a way out that is not a link; the body also carries the opt-out line.
    msg["List-Unsubscribe"] = f"<mailto:{account.from_address}?subject=baja>"
    msg.set_content(body)
    return msg


async def send(account: EmailAccount, msg: EmailMessage) -> None:
    """Raises on any SMTP failure; the caller decides whether to retry."""
    implicit_tls = account.smtp_port == 465
    await aiosmtplib.send(
        msg,
        hostname=account.smtp_host,
        port=account.smtp_port,
        use_tls=implicit_tls,
        start_tls=not implicit_tls,
        username=account.smtp_user,
        password=account.smtp_password,
        timeout=30,
    )


# ── inbound ───────────────────────────────────────────────────────────────
_QUOTE_MARKERS = re.compile(
    r"^(>|On .{5,200} wrote:|El .{5,200} escribi[óo]:|-{2,}\s*(Original Message|Mensaje original)|"
    r"De:\s.+|From:\s.+)",
    re.IGNORECASE,
)
_AUTO_SUBJECT = re.compile(
    r"^\s*(auto(matic)?[- ]?reply|respuesta autom[áa]tica|out of office|fuera de (la )?oficina|"
    r"autorespuesta|undeliverable|delivery status)",
    re.IGNORECASE,
)


def strip_quoted(text: str) -> str:
    """The new part of a reply: everything above the first quoted-history marker."""
    kept: list[str] = []
    for line in (text or "").replace("\r\n", "\n").split("\n"):
        if _QUOTE_MARKERS.match(line.strip()):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text)


def _body_text(msg: EmailMessage) -> str:
    part = msg.get_body(preferencelist=("plain",))
    if part is not None:
        return part.get_content()
    part = msg.get_body(preferencelist=("html",))
    return _html_to_text(part.get_content()) if part is not None else ""


def _ids(value: str) -> list[str]:
    return re.findall(r"<[^<>\s]+>", value or "")


def _bounced_recipients(msg: EmailMessage) -> list[str]:
    found: list[str] = []
    header = str(msg.get("X-Failed-Recipients") or "")
    found += [parseaddr(p)[1].lower() for p in header.split(",") if "@" in p]
    for part in msg.walk():
        if part.get_content_type() == "message/delivery-status":
            for block in part.get_payload():
                final = str(block.get("Final-Recipient") or "")
                if ";" in final:
                    found.append(final.split(";", 1)[1].strip().lower())
    return list(dict.fromkeys(a for a in found if "@" in a))


def parse_inbound(uid: int, raw: bytes) -> InboundEmail:
    msg = email.message_from_bytes(raw, policy=policy.default)
    from_name, from_email = parseaddr(str(msg.get("From") or ""))
    from_email = from_email.strip().lower()
    local = from_email.partition("@")[0]
    is_bounce = (
        local in ("mailer-daemon", "postmaster")
        or msg.get_content_type() == "multipart/report"
        or "delivery-status" in str(msg.get("Content-Type") or "").lower()
    )
    auto_submitted = str(msg.get("Auto-Submitted") or "no").strip().lower()
    precedence = str(msg.get("Precedence") or "").strip().lower()
    subject = str(msg.get("Subject") or "").strip()
    is_auto = (
        auto_submitted != "no"
        or precedence in ("bulk", "junk", "list", "auto_reply")
        or bool(msg.get("X-Autoreply") or msg.get("X-Autorespond"))
        or bool(_AUTO_SUBJECT.match(subject))
    )
    try:
        body = strip_quoted(_body_text(msg))[:MAX_BODY_CHARS]
    except (KeyError, LookupError, ValueError):
        body = ""
    return InboundEmail(
        uid=uid,
        message_id=(_ids(str(msg.get("Message-ID") or "")) or [""])[0],
        in_reply_to=(_ids(str(msg.get("In-Reply-To") or "")) or [""])[0],
        references=_ids(str(msg.get("References") or "")),
        from_email=from_email,
        from_name=from_name,
        subject=subject,
        body=body,
        is_auto=is_auto,
        is_bounce=is_bounce,
        bounced_recipients=_bounced_recipients(msg) if is_bounce else [],
    )


def _imap_date(when: datetime) -> str:
    # Not strftime: %b follows the machine's locale and IMAP only accepts English month names.
    return f"{when.day:02d}-{_MONTHS[when.month - 1]}-{when.year}"


def _fetch_sync(account: EmailAccount, since_uid: int, since_date: datetime, limit: int) -> list[InboundEmail]:
    client = imaplib.IMAP4_SSL(account.imap_host, account.imap_port, timeout=IMAP_TIMEOUT)
    try:
        client.login(account.imap_user, account.imap_password)
        client.select("INBOX", readonly=True)  # reading never changes the owner's read/unread flags
        if since_uid > 0:
            status, data = client.uid("SEARCH", None, f"UID {since_uid + 1}:*")
        else:
            status, data = client.uid("SEARCH", None, "SINCE", _imap_date(since_date))
        if status != "OK":
            raise imaplib.IMAP4.error(f"IMAP search failed: {status}")
        # "N:*" always returns the newest message even when N is past it, so drop what we have seen.
        uids = sorted(int(u) for u in (data[0] or b"").split() if int(u) > since_uid)[:limit]
        out: list[InboundEmail] = []
        for uid in uids:
            status, parts = client.uid("FETCH", str(uid), "(BODY.PEEK[])")
            if status != "OK" or not parts or not isinstance(parts[0], tuple):
                out.append(InboundEmail(uid, "", "", [], "", "", "", "", is_auto=True))
                continue
            out.append(parse_inbound(uid, parts[0][1]))
        return out
    finally:
        try:
            client.logout()
        except (imaplib.IMAP4.error, OSError):
            pass


async def fetch_new(
    account: EmailAccount, since_uid: int, since_date: datetime, limit: int = 100
) -> list[InboundEmail]:
    """New inbox messages after ``since_uid`` (or since ``since_date`` on a first sync), oldest first."""
    return await asyncio.to_thread(_fetch_sync, account, since_uid, since_date, limit)
