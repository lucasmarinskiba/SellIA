"""aiosmtplib 3.0.1 -> 5.1.3: what goes on the SMTP wire.

5.1.1 and 5.1.3 fixed SMTP command injection (GHSA-v3q9-hj7j-63hq): addresses with control characters, whitespace
or angle brackets are refused before anything is written. Every sender in the app (core/notifications/email_service,
core/security_notifications, channels/connectors/email, harvey/mailer) hands aiosmtplib a message object and lets it
read the From/To headers, so the envelope must come out as bare addresses; and an address that tries to smuggle in an
extra command must be refused, not sent. A tiny in-process SMTP server records the conversation (no network).
"""

import asyncio
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import aiosmtplib
import pytest


class _FakeSMTP:
    """Just enough SMTP to accept a message; records every command line it receives."""

    def __init__(self):
        self.commands: list[str] = []
        self.messages: list[str] = []
        self._server = None
        self.port = 0

    async def __aenter__(self):
        self._server = await asyncio.start_server(self._client, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_exc):
        self._server.close()
        await self._server.wait_closed()

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        async def reply(text: str):
            writer.write(text.encode() + b"\r\n")
            await writer.drain()

        await reply("220 fake ESMTP")
        while line := await reader.readline():
            text = line.decode().rstrip("\r\n")
            self.commands.append(text)
            verb = text.split(" ", 1)[0].upper()
            if verb == "EHLO" or verb == "HELO":
                await reply("250 fake")
            elif verb == "DATA":
                await reply("354 go ahead")
                body = []
                while (chunk := (await reader.readline()).decode().rstrip("\r\n")) != ".":
                    body.append(chunk)
                self.messages.append("\n".join(body))
                await reply("250 queued")
            elif verb == "QUIT":
                await reply("221 bye")
                break
            else:  # MAIL / RCPT / RSET / NOOP
                await reply("250 ok")
        writer.close()

    def envelope(self) -> tuple[list[str], list[str]]:
        mail = [c for c in self.commands if c.upper().startswith("MAIL FROM")]
        rcpt = [c for c in self.commands if c.upper().startswith("RCPT TO")]
        return mail, rcpt


async def _send(server: _FakeSMTP, msg, **kwargs):
    return await aiosmtplib.send(msg, hostname="127.0.0.1", port=server.port, start_tls=False, timeout=10, **kwargs)


async def test_email_message_with_display_name_goes_out_with_bare_addresses():
    """harvey/mailer.py builds From with formataddr((name, address))."""
    msg = EmailMessage()
    msg["From"] = formataddr(("Ana Pérez", "ana@negocio.com"))
    msg["To"] = "cliente@example.com"
    msg["Subject"] = "Hola"
    msg.set_content("cuerpo")
    async with _FakeSMTP() as server:
        await _send(server, msg)
    mail, rcpt = server.envelope()
    assert mail == ["MAIL FROM:<ana@negocio.com>"] or mail[0].startswith("MAIL FROM:<ana@negocio.com>")
    assert rcpt == ["RCPT TO:<cliente@example.com>"]


async def test_mime_message_with_a_name_in_from_like_the_notification_senders():
    msg = MIMEMultipart("alternative")
    msg["From"] = "SellIA Alertas <alertas@sellia.example>"
    msg["To"] = "dueno@example.com"
    msg["Subject"] = "[ALERTA SEGURIDAD] test"
    msg.attach(MIMEText("texto", "plain", "utf-8"))
    async with _FakeSMTP() as server:
        await _send(server, msg)
    mail, rcpt = server.envelope()
    assert mail[0].startswith("MAIL FROM:<alertas@sellia.example>")
    assert len(rcpt) == 1 and rcpt[0].startswith("RCPT TO:<")


async def test_smtp_context_manager_and_send_message_like_core_email_service():
    msg = MIMEMultipart()
    msg["From"] = "Tienda <tienda@example.com>"
    msg["To"] = "a@example.com, b@example.com"
    msg["Subject"] = "Pedido"
    msg.attach(MIMEText("hola", "plain"))
    async with _FakeSMTP() as server:
        async with aiosmtplib.SMTP(hostname="127.0.0.1", port=server.port, start_tls=False, timeout=10) as smtp:
            await smtp.send_message(msg)
    mail, rcpt = server.envelope()
    assert mail[0].startswith("MAIL FROM:<tienda@example.com>")
    assert sorted(r.split("<", 1)[1].split(">", 1)[0] for r in rcpt) == ["a@example.com", "b@example.com"]


@pytest.mark.parametrize("recipient", [
    "victim@example.com\r\nRCPT TO:<evil@example.org>",   # CR/LF command injection (5.1.1)
    "victim@example.com\nDATA",
    "user@example.com> AUTH=<attacker@example.org",         # ESMTP parameter smuggling (5.1.3)
    "a b@example.com",
])
async def test_an_address_that_tries_to_inject_smtp_commands_is_refused_before_sending(recipient):
    msg = EmailMessage()
    msg["From"] = "ana@negocio.com"
    msg["To"] = "cliente@example.com"
    msg.set_content("x")
    async with _FakeSMTP() as server:
        with pytest.raises(ValueError):
            await _send(server, msg, recipients=[recipient])
    assert not any("evil" in c or "attacker" in c or c.upper().startswith("DATA") for c in server.commands)
    assert server.envelope()[1] == []
