#!/usr/bin/env python3
"""Validate env vars are set before deploy. Exit 1 if missing critical."""
import os
import sys


REQUIRED = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL", "JWT_SECRET"]
RECOMMENDED = ["ANTHROPIC_API_KEY", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "SENTRY_DSN"]
PROD_REQUIRED = ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "SENTRY_DSN"]


def main() -> int:
    env = os.getenv("ENV", "dev")
    missing_req = [k for k in REQUIRED if not os.getenv(k)]
    missing_rec = [k for k in RECOMMENDED if not os.getenv(k)]

    print(f"Validating env for ENV={env}")

    if missing_req:
        print(f"\n❌ MISSING REQUIRED: {', '.join(missing_req)}", file=sys.stderr)
        return 1

    if env == "prod":
        missing_prod = [k for k in PROD_REQUIRED if not os.getenv(k)]
        if missing_prod:
            print(f"\n❌ MISSING PROD-CRITICAL: {', '.join(missing_prod)}", file=sys.stderr)
            return 1

    if missing_rec:
        print(f"\n⚠  Recommended (non-fatal): {', '.join(missing_rec)}", file=sys.stderr)

    # Check secret strength
    for k in ("SECRET_KEY", "JWT_SECRET"):
        v = os.getenv(k, "")
        if len(v) < 32:
            print(f"\n❌ {k} too short ({len(v)} chars) · min 32", file=sys.stderr)
            return 1

    print("\n✓ env OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
