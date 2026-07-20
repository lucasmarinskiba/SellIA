"""Smoke test REAL de Computer Use — sin DB ni API key.

Ejercita BrowserService (Playwright headless) end-to-end: start → navigate →
screenshot (PNG real a disco) → scroll → click → type → stop. Prueba que el
loop de acciones del agente funciona contra un navegador real.

Uso:
    cd backend && python scripts/cu_smoke.py
Requiere: python -m playwright install chromium
"""

import asyncio
import pathlib
import sys

from app.domains.computer_use.browser_service import BrowserService


async def main() -> int:
    b = BrowserService()
    try:
        print("[1] start headless…")
        await b.start(headless=True)

        print("[2] navigate https://example.com …")
        nav = await b.navigate("https://example.com")
        print("    ->", nav)

        print("[3] screenshot…")
        png = await b.screenshot()
        out = pathlib.Path(__file__).parent / "cu_smoke.png"
        out.write_bytes(png)
        print(f"    PNG real: {len(png)} bytes -> {out}")

        print("[4] scroll down…")
        await b.scroll("down", 200)

        print("[5] click (100,100)…")
        await b.click(100, 100)

        print("[6] type texto…")
        await b.type("hola sellia")

        print("[7] press_key Escape…")
        await b.press_key("Escape")

        print("[8] stop…")
        await b.stop()

        ok = len(png) > 1000
        print("SMOKE OK" if ok else "SMOKE FAIL (screenshot vacío)")
        return 0 if ok else 1
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE FAIL: {type(exc).__name__}: {exc}")
        try:
            await b.stop()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
