#!/usr/bin/env python3
"""
SellIA — Generador de Secretos para Producción

Uso:
    python scripts/generate-production-secrets.py

Este script genera claves criptográficas seguras y muestra un .env listo para
copiar. NUNCA guarda archivos automáticamente para evitar sobreescribir
configuraciones existentes.
"""

import secrets
import base64


def generate_hex(length: int = 32) -> str:
    return secrets.token_hex(length)


def generate_urlsafe(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_base64(length: int = 32) -> str:
    return base64.b64encode(secrets.token_bytes(length)).decode()


def main():
    print("=" * 70)
    print("🔐  SellIA — Secretos de Producción")
    print("=" * 70)
    print()
    print("Copiá el siguiente bloque en tu archivo .env (reemplazá los valores")
    print("existentes). NUNCA commitees este archivo.")
    print()
    print("-" * 70)
    print()

    print("# ─── Base de datos ───")
    print(f"DB_PASSWORD={generate_urlsafe(32)}")
    print()

    print("# ─── JWT / Seguridad ───")
    print(f"SECRET_KEY={generate_hex(32)}")
    print(f"FERNET_SECRET={generate_base64(32)}")
    print()

    print("# ─── Backup ───")
    print(f"BACKUP_ENCRYPTION_KEY={generate_urlsafe(40)}")
    print()

    print("# ─── VAPID (Web Push) ───")
    print("# Generá las claves con: openssl ecparam -genkey -name prime256v1 -noout -out vapid_private.pem")
    print("# Luego: openssl ec -in vapid_private.pem -pubout -out vapid_public.pem")
    print("# Y codificá a base64: base64 vapid_private.pem")
    print(f"VAPID_PRIVATE_KEY={generate_base64(32)}")
    print(f"VAPID_PUBLIC_KEY={generate_base64(32)}")
    print()

    print("# ─── Cloudflare Turnstile ───")
    print("# Crear en: https://dash.cloudflare.com/?to=/:account/turnstile")
    print("TURNSTILE_SECRET_KEY=0x0000000000000000000000000000000000000000")
    print("NEXT_PUBLIC_TURNSTILE_SITE_KEY=1x00000000000000000000AA")
    print()

    print("# ─── MercadoPago / Stripe ───")
    print("MERCADOPAGO_ACCESS_TOKEN=")
    print("STRIPE_SECRET_KEY=")
    print()

    print("-" * 70)
    print()
    print("✅  Instrucciones adicionales:")
    print("   1. Copiá el bloque de arriba en tu .env")
    print("   2. Ejecutá: docker compose down && docker compose up -d")
    print("   3. Verificá que los backups funcionen: docker logs ia_vendedor_db_backup")
    print("   4. Para producción, usá docker-compose.prod.yml")
    print()


if __name__ == "__main__":
    main()
