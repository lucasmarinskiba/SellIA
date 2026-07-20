#!/usr/bin/env python3
"""
Generate secure credentials for production deployment.
Outputs random secrets suitable for .env.production
"""

import secrets
import string
import json
from datetime import datetime
from pathlib import Path

def generate_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def generate_secret_key(length: int = 64) -> str:
    """Generate a secret key for Django/FastAPI."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def generate_jwt_secret(length: int = 48) -> str:
    """Generate a JWT secret."""
    return secrets.token_urlsafe(length)

def generate_api_key() -> str:
    """Generate an API key."""
    return secrets.token_hex(32)

def main():
    """Generate and display credentials."""
    credentials = {
        "generated_at": datetime.utcnow().isoformat(),
        "database": {
            "DB_PASSWORD": generate_password(32),
            "DB_USER": "selliauser",
            "DB_NAME": "selliadb",
        },
        "redis": {
            "REDIS_PASSWORD": generate_password(32),
            "REDIS_CACHE_PASSWORD": generate_password(32),
        },
        "security": {
            "SECRET_KEY": generate_secret_key(64),
            "JWT_SECRET": generate_jwt_secret(48),
            "API_KEY": generate_api_key(),
        },
        "instructions": {
            "STRIPE_API_KEY": "Get from: https://dashboard.stripe.com/apikeys (Live mode)",
            "STRIPE_WEBHOOK_SECRET": "Get from: https://dashboard.stripe.com/webhooks",
            "SENDGRID_API_KEY": "Get from: https://app.sendgrid.com/settings/api_keys",
            "SENTRY_DSN": "Get from: https://sentry.io/settings/organization/projects/",
            "DATADOG_API_KEY": "Get from: https://app.datadoghq.com/organization/settings/api-keys",
        }
    }

    # Display results
    print("\n" + "="*70)
    print("SellIA Production Credentials Generator")
    print("="*70)

    print("\n📋 DATABASE CREDENTIALS")
    print("-" * 70)
    print(f"DB_USER={credentials['database']['DB_USER']}")
    print(f"DB_NAME={credentials['database']['DB_NAME']}")
    print(f"DB_PASSWORD={credentials['database']['DB_PASSWORD']}")

    print("\n🔑 REDIS CREDENTIALS")
    print("-" * 70)
    print(f"REDIS_PASSWORD={credentials['redis']['REDIS_PASSWORD']}")
    print(f"REDIS_CACHE_PASSWORD={credentials['redis']['REDIS_CACHE_PASSWORD']}")

    print("\n🔐 SECURITY KEYS")
    print("-" * 70)
    print(f"SECRET_KEY={credentials['security']['SECRET_KEY']}")
    print(f"JWT_SECRET={credentials['security']['JWT_SECRET']}")
    print(f"API_KEY={credentials['security']['API_KEY']}")

    print("\n📌 MANUAL ACTIONS REQUIRED")
    print("-" * 70)
    for key, instruction in credentials['instructions'].items():
        print(f"\n{key}:")
        print(f"  {instruction}")

    # Save to file
    output_file = Path(__file__).parent.parent / "credentials.json"
    with open(output_file, "w") as f:
        json.dump(credentials, f, indent=2)

    print(f"\n✅ Credentials saved to: {output_file}")
    print("⚠️  IMPORTANT: Keep this file secure! Add to .gitignore")
    print("⚠️  Copy values from this output to your .env.production")
    print("⚠️  Do NOT commit .env.production to git")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
