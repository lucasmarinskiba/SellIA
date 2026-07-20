"""Cryptocurrency Payment Integration (USDT TRC-20 / BEP-20)

Provides helpers to generate crypto payment instructions and verify
USDT transactions on Tron (TRC-20) and Binance Smart Chain (BEP-20).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USDT_CONTRACT_ADDRESSES = {
    "trc20": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "bep20": "0x55d398326f99059fF775485246999027B3197955",
}

TRONSCAN_API_BASE = "https://apilist.tronscanapi.com"
BSCSCAN_API_BASE = "https://api.bscscan.com/api"

PAYMENT_EXPIRATION_MINUTES = 60


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_usdt_contract_address(network: str) -> str:
    """Return the official USDT contract address for the given network."""
    normalized = _normalize_network(network)
    address = USDT_CONTRACT_ADDRESSES.get(normalized)
    if not address:
        raise ValueError(f"Red no soportada: {network}. Use 'trc20' o 'bep20'.")
    return address


def generate_crypto_payment(
    plan_slug: str,
    price_usd: float,
    user_id: str,
    subscription_id: str,
    network: str,
) -> dict[str, Any]:
    """Generate payment instructions for a USDT crypto payment.

    Returns the creator's wallet address together with a unique transaction
    identifier so the payment can be tracked later.
    """
    normalized = _normalize_network(network)
    wallet_address = _get_creator_address(normalized)
    payment_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PAYMENT_EXPIRATION_MINUTES)

    return {
        "transaction_id": payment_id,
        "wallet_address": wallet_address,
        "amount_usdt": float(price_usd),
        "network": normalized,
        "plan_slug": plan_slug,
        "user_id": user_id,
        "subscription_id": subscription_id,
        "expires_at": expires_at,
        "status": "pending",
        "memo": payment_id,  # Unique ID used to correlate the payment
    }


async def check_crypto_payment_status(tx_hash: str, network: str) -> dict[str, Any]:
    """Check the on-chain status of a USDT transfer.

    * TRC-20 -> TronScan API
    * BEP-20 -> BscScan API
    """
    normalized = _normalize_network(network)

    if normalized == "trc20":
        return await _check_trc20_status(tx_hash)
    if normalized == "bep20":
        return await _check_bep20_status(tx_hash)

    raise ValueError(f"Red no soportada: {network}")


async def verify_crypto_payment(
    tx_hash: str,
    expected_amount: float,
    wallet_address: str,
    network: str,
) -> dict[str, Any]:
    """Verify that a crypto payment matches the expected amount and recipient.

    Returns a dictionary with:
        - verified: bool
        - tx_hash: str
        - amount_received: float | None
        - from_address: str | None
        - to_address: str | None
        - confirmations: int
        - status: str
        - error: str | None
    """
    normalized = _normalize_network(network)
    expected_amount = float(expected_amount)

    # Fetch raw transaction / transfer info
    if normalized == "trc20":
        raw = await _fetch_trc20_tx(tx_hash)
    elif normalized == "bep20":
        raw = await _fetch_bep20_tx(tx_hash, wallet_address)
    else:
        return _verification_error("Red no soportada", tx_hash)

    # Parse common fields
    transfer = raw.get("transfer", {})
    status = raw.get("status", "unknown")
    confirmations = raw.get("confirmations", 0)

    to_address = transfer.get("to_address", "")
    from_address = transfer.get("from_address", "")
    amount_received = transfer.get("amount", 0.0)

    # Compare recipient (case-insensitive for EVM chains)
    recipient_ok = _addresses_equal(to_address, wallet_address, normalized)

    # Compare amount with a small tolerance for floating point / decimals
    amount_ok = abs(amount_received - expected_amount) < 1e-6

    verified = recipient_ok and amount_ok and status in ("confirmed", "success")

    return {
        "verified": verified,
        "tx_hash": tx_hash,
        "amount_received": amount_received,
        "from_address": from_address,
        "to_address": to_address,
        "confirmations": confirmations,
        "status": status,
        "error": None if verified else _build_error_message(recipient_ok, amount_ok, status),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_network(network: str) -> str:
    """Normalize network identifier to lower-case canonical form."""
    return network.strip().lower()


def _get_creator_address(network: str) -> str:
    """Return the configured creator address for the requested network."""
    if network == "trc20":
        addr = settings.CREATOR_USDT_TRC20_ADDRESS
    elif network == "bep20":
        addr = settings.CREATOR_USDT_BEP20_ADDRESS
    else:
        raise ValueError(f"Red no soportada: {network}")

    if not addr:
        raise ValueError(
            f"CREATOR_USDT_{network.upper()}_ADDRESS no está configurado en settings"
        )
    return addr


def _addresses_equal(a: str, b: str, network: str) -> bool:
    """Case-insensitive address comparison (EVM chains are case-insensitive)."""
    if network == "bep20":
        return a.lower() == b.lower()
    # Tron addresses are mixed-case but should be compared case-insensitively
    # for basic verification (checksum is optional here).
    return a.lower() == b.lower()


def _verification_error(error: str, tx_hash: str) -> dict[str, Any]:
    return {
        "verified": False,
        "tx_hash": tx_hash,
        "amount_received": None,
        "from_address": None,
        "to_address": None,
        "confirmations": 0,
        "status": "error",
        "error": error,
    }


def _build_error_message(recipient_ok: bool, amount_ok: bool, status: str) -> str:
    parts: list[str] = []
    if not recipient_ok:
        parts.append("el destinatario no coincide")
    if not amount_ok:
        parts.append("el monto no coincide")
    if status not in ("confirmed", "success"):
        parts.append(f"estado de transacción: {status}")
    return "; ".join(parts) or "verificación fallida"


# ---------------------------------------------------------------------------
# TRC-20 (TronScan)
# ---------------------------------------------------------------------------


async def _check_trc20_status(tx_hash: str) -> dict[str, Any]:
    """Query TronScan for a transaction status."""
    url = f"{TRONSCAN_API_BASE}/api/transaction-info"
    params: dict[str, str] = {"hash": tx_hash}
    headers: dict[str, str] = {}
    if settings.TRONGRID_API_KEY:
        headers["TRON-PRO-API-KEY"] = settings.TRONGRID_API_KEY

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            return {
                "tx_hash": tx_hash,
                "status": "error",
                "confirmations": 0,
                "error": f"TronScan HTTP error: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            return {
                "tx_hash": tx_hash,
                "status": "error",
                "confirmations": 0,
                "error": f"TronScan request error: {exc}",
            }

    # TronScan returns e.g. {"confirmed": true, "contractType": 1, ...}
    confirmed = data.get("confirmed", False)
    success = data.get("contractRet") == "SUCCESS" or data.get("contractRet") is None

    # Attempt to extract USDT transfer details
    trc20_transfers = data.get("trc20TransferInfo", [])
    usdt_transfer = None
    for t in trc20_transfers:
        if t.get("symbol", "").upper() == "USDT" or t.get("name", "").upper() == "TETHER USD":
            usdt_transfer = t
            break

    # Fallback: if no explicit USDT transfer, try tokenTransferInfo
    if not usdt_transfer:
        token_info = data.get("tokenTransferInfo", {})
        if token_info and token_info.get("tokenName", "").upper() == "TETHER USD":
            usdt_transfer = token_info

    result: dict[str, Any] = {
        "tx_hash": tx_hash,
        "status": "confirmed" if confirmed and success else "pending",
        "confirmations": 1 if confirmed else 0,
        "block": data.get("block"),
        "timestamp": data.get("timestamp"),
        "error": None,
    }

    if usdt_transfer:
        # Amounts on TronScan are usually returned with the token's decimals already applied
        amount_str = usdt_transfer.get("amount_str") or usdt_transfer.get("amount")
        try:
            amount = float(amount_str) if amount_str is not None else 0.0
        except (ValueError, TypeError):
            amount = 0.0

        result.update({
            "amount": amount,
            "from_address": usdt_transfer.get("from_address") or usdt_transfer.get("fromAddr"),
            "to_address": usdt_transfer.get("to_address") or usdt_transfer.get("toAddr"),
            "token_name": usdt_transfer.get("name") or usdt_transfer.get("tokenName"),
            "token_symbol": usdt_transfer.get("symbol") or usdt_transfer.get("tokenSymbol"),
        })

    return result


async def _fetch_trc20_tx(tx_hash: str) -> dict[str, Any]:
    """Fetch and normalize a TRC-20 transaction for verification."""
    status_info = await _check_trc20_status(tx_hash)

    transfer = {}
    if status_info.get("from_address") and status_info.get("to_address"):
        transfer = {
            "from_address": status_info["from_address"],
            "to_address": status_info["to_address"],
            "amount": status_info.get("amount", 0.0),
        }

    return {
        "status": status_info.get("status"),
        "confirmations": status_info.get("confirmations", 0),
        "transfer": transfer,
        "raw": status_info,
    }


# ---------------------------------------------------------------------------
# BEP-20 (BscScan)
# ---------------------------------------------------------------------------


async def _check_bep20_status(tx_hash: str) -> dict[str, Any]:
    """Query BscScan for a BEP-20 token transfer status.

    BscScan does not provide a direct 'tx by hash' endpoint for token transfers
    in the free tier, so we rely on the general transaction endpoint and the
    token transaction list filtered by wallet.
    """
    # 1. General transaction info
    tx_url = BSCSCAN_API_BASE
    tx_params: dict[str, str] = {
        "module": "transaction",
        "action": "gettxreceiptstatus",
        "txhash": tx_hash,
        "apikey": settings.BSCSCAN_API_KEY or "",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            tx_resp = await client.get(tx_url, params=tx_params)
            tx_resp.raise_for_status()
            tx_data = tx_resp.json()
        except httpx.HTTPStatusError as exc:
            return {
                "tx_hash": tx_hash,
                "status": "error",
                "confirmations": 0,
                "error": f"BscScan HTTP error: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            return {
                "tx_hash": tx_hash,
                "status": "error",
                "confirmations": 0,
                "error": f"BscScan request error: {exc}",
            }

    receipt_status = tx_data.get("result", {}).get("status", "")
    tx_status = "success" if receipt_status == "1" else "pending" if receipt_status == "" else "failed"

    return {
        "tx_hash": tx_hash,
        "status": tx_status,
        "confirmations": 0,  # Will be enriched by verify if needed
        "error": None,
        "raw": tx_data,
    }


async def _fetch_bep20_tx(tx_hash: str, wallet_address: str) -> dict[str, Any]:
    """Fetch BEP-20 token transfer details from BscScan and normalize them."""
    url = BSCSCAN_API_BASE
    params: dict[str, str] = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDT_CONTRACT_ADDRESSES["bep20"],
        "address": wallet_address,
        "page": "1",
        "offset": "10",
        "sort": "desc",
        "apikey": settings.BSCSCAN_API_KEY or "",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            return {
                "status": "error",
                "confirmations": 0,
                "transfer": {},
                "error": f"BscScan HTTP error: {exc.response.status_code}",
            }
        except httpx.RequestError as exc:
            return {
                "status": "error",
                "confirmations": 0,
                "transfer": {},
                "error": f"BscScan request error: {exc}",
            }

    if data.get("status") != "1" or not data.get("result"):
        return {
            "status": "not_found",
            "confirmations": 0,
            "transfer": {},
            "error": data.get("message", "Transacción no encontrada en BscScan"),
        }

    # Find the matching transaction hash
    transfer = {}
    for tx in data["result"]:
        if tx.get("hash", "").lower() == tx_hash.lower():
            # BscScan returns value with 18 decimals for USDT on BSC
            value_str = tx.get("value", "0")
            decimals = int(tx.get("tokenDecimal", "6"))
            try:
                amount = float(value_str) / (10 ** decimals)
            except (ValueError, TypeError):
                amount = 0.0

            transfer = {
                "from_address": tx.get("from"),
                "to_address": tx.get("to"),
                "amount": amount,
            }
            confirmations = int(tx.get("confirmations", "0"))
            return {
                "status": "confirmed" if confirmations >= 1 else "pending",
                "confirmations": confirmations,
                "transfer": transfer,
                "error": None,
                "raw": tx,
            }

    return {
        "status": "not_found",
        "confirmations": 0,
        "transfer": {},
        "error": "Hash no encontrado en las últimas transacciones del wallet",
    }
