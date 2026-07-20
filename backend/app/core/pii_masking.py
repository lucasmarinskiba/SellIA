"""PII Masking utilities for API responses.

Prevents accidental exposure of sensitive personal data in JSON responses.
"""

import re
from typing import Any


def mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***" if local else "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return phone
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "***"
    visible = digits[-4:]
    return phone[: -len(visible)] + "****" if len(phone) > len(visible) else "****"


def mask_name(name: str | None) -> str | None:
    if not name:
        return name
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0] + "***" if len(parts[0]) > 1 else "***"
    # First name initial + ***, last name initial + ***
    first = parts[0][0] + "***" if len(parts[0]) > 1 else "***"
    last = parts[-1][0] + "***" if len(parts[-1]) > 1 else "***"
    return f"{first} {last}"


def mask_tax_id(tax_id: str | None) -> str | None:
    if not tax_id:
        return tax_id
    if len(tax_id) <= 4:
        return "***"
    return tax_id[:2] + "***" + tax_id[-2:]


def mask_dict_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask PII fields in a dict (for JSON responses)."""
    if not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        lower_key = key.lower()
        if lower_key in ("email", "customer_email", "referrer_email"):
            result[key] = mask_email(value)
        elif lower_key in ("phone", "customer_phone", "referrer_phone"):
            result[key] = mask_phone(value)
        elif lower_key in ("name", "customer_name", "full_name", "referrer_name"):
            result[key] = mask_name(value)
        elif lower_key in ("tax_id", "tax_id_number", "cuit", "cuil", "dni"):
            result[key] = mask_tax_id(value)
        elif isinstance(value, dict):
            result[key] = mask_dict_pii(value)
        elif isinstance(value, list):
            result[key] = [
                mask_dict_pii(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
