"""Wire format of the SellIA -> feedIA webhook (feedIA: src/server/selliaRoutes.ts, POST /api/sellia/webhook).

feedIA verifies ``HMAC-SHA256(secret, JSON.stringify({eventType, event}))`` where ``event`` is the PARSED body, so the
string signed here has to be byte-identical to what JavaScript would print for that same object. That holds as long
as the event only carries strings and integers (a Python ``49.0`` prints as ``49.0`` but JS parses and prints ``49``),
so amounts and dates are sent as strings; ``canonical_json`` refuses anything else instead of signing something
feedIA would reject.
"""

import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

ACCOUNT_ID = re.compile(r"^[\w-]{1,64}$")  # same rule feedIA applies (it is used as a file name there)
PSEUDONYM_DOMAIN = "customers.sellia.invalid"


def _check(value: Any, path: str = "event") -> None:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{path}: only strings and integers are allowed")
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(f"{path}: keys must be strings")
            _check(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _check(v, f"{path}[{i}]")
    elif not isinstance(value, (str, int)):
        raise ValueError(f"{path}: {type(value).__name__} is not allowed (send it as a string)")


def canonical_json(event_type: str, event: dict[str, Any]) -> str:
    """What ``JSON.stringify({ eventType, event })`` prints in feedIA."""
    _check(event)
    return json.dumps({"eventType": event_type, "event": event}, separators=(",", ":"), ensure_ascii=False)


def sign_event(event_type: str, event: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), canonical_json(event_type, event).encode("utf-8"), hashlib.sha256).hexdigest()


def pseudonymous_email(business_id: Any, email: str | None, key: str) -> str:
    """A stable, email-shaped id for a customer. feedIA only needs to tell customers apart (new vs returning), not to
    reach them, so the real address never leaves SellIA. Per business: the same person is unlinkable across businesses."""
    clean = (email or "").strip().lower()
    if not clean:
        return ""
    digest = hmac.new(key.encode("utf-8"), f"{business_id}:{clean}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{digest}@{PSEUDONYM_DOMAIN}"


def _iso(moment: datetime | None) -> str:
    if moment is None:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def sale_event(*, order_id: Any, total: Any, when: datetime | None, business_id: Any, email: str | None, key: str) -> dict[str, str]:
    amount = Decimal(str(total or 0)).quantize(Decimal("0.01"))
    return {
        "orderId": str(order_id),
        "totalAmount": f"{amount:.2f}",
        "timestamp": _iso(when),
        "customerEmail": pseudonymous_email(business_id, email, key),
        "sourcePostId": "",
    }


def refund_event(*, order_id: Any) -> dict[str, str]:
    return {"orderId": str(order_id)}
