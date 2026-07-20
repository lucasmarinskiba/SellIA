#!/usr/bin/env python3
"""
Validate production environment configuration.
Checks all required environment variables are set.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Required environment variables for production
REQUIRED_VARS = {
    # Database
    "DATABASE_URL": "PostgreSQL connection string",
    "REDIS_URL": "Redis connection string",
    "DB_POOL_SIZE": "Database connection pool size",

    # Security
    "SECRET_KEY": "Django/FastAPI secret key",
    "JWT_SECRET": "JWT secret for auth tokens",
    "ENVIRONMENT": "Should be 'production'",

    # Frontend
    "FRONTEND_URL": "Frontend domain (https://selldia.app)",
    "BACKEND_URL": "Backend API domain (https://api.selldia.app)",
    "CORS_ORIGINS": "Allowed CORS origins",

    # Stripe Payment
    "STRIPE_API_KEY": "Stripe live API key (sk_live_...)",
    "STRIPE_WEBHOOK_SECRET": "Stripe webhook secret",
    "STRIPE_PUBLISHABLE_KEY": "Stripe publishable key (pk_live_...)",

    # Email
    "SENDGRID_API_KEY": "SendGrid API key",
    "SMTP_FROM_EMAIL": "Email sender address",

    # Monitoring
    "SENTRY_DSN": "Sentry error tracking DSN",
    "DATADOG_API_KEY": "Datadog monitoring API key",
    "LOG_LEVEL": "Log level (info, debug, warning, error)",

    # Security headers
    "SECURE_SSL_REDIRECT": "Force HTTPS redirect",
    "SESSION_COOKIE_SECURE": "Secure cookie flag",
    "SESSION_COOKIE_HTTPONLY": "HttpOnly cookie flag",
    "SESSION_COOKIE_SAMESITE": "SameSite cookie policy",

    # Rate limiting
    "RATE_LIMIT_ENABLED": "Enable rate limiting",
    "RATE_LIMIT_PER_MINUTE": "Requests per minute limit",
    "RATE_LIMIT_PER_HOUR": "Requests per hour limit",

    # Feature flags
    "ENABLE_COMPUTER_USE": "Enable computer use automation",
    "ENABLE_WEBHOOK_SIGNATURES": "Enable webhook signature verification",

    # Timeouts
    "API_TIMEOUT_SECONDS": "API request timeout",
    "WEBHOOK_TIMEOUT_SECONDS": "Webhook processing timeout",

    # Backups
    "BACKUP_ENABLED": "Enable automated backups",
    "BACKUP_RETENTION_DAYS": "Backup retention period",
}

OPTIONAL_VARS = {
    "AWS_ACCESS_KEY_ID": "AWS S3 file storage",
    "AWS_SECRET_ACCESS_KEY": "AWS S3 credentials",
    "AWS_STORAGE_BUCKET_NAME": "S3 bucket for assets",
    "GOOGLE_ANALYTICS_ID": "Google Analytics tracking",
}

def load_env_file(filepath: str) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def validate_variables(
    env_vars: dict, required: dict, optional: dict
) -> Tuple[List[str], List[str], List[str]]:
    """Validate environment variables."""
    missing = []
    warnings = []
    errors = []

    # Check required variables
    for var, description in required.items():
        if var not in os.environ and var not in env_vars:
            missing.append(f"  ✗ {var}: {description}")

    # Check optional variables
    for var, description in optional.items():
        if var not in os.environ and var not in env_vars:
            warnings.append(f"  ⚠ {var}: {description} (optional)")

    # Validate specific values
    env_value = env_vars.get("ENVIRONMENT") or os.environ.get("ENVIRONMENT", "")
    if env_value and env_value != "production":
        errors.append(f"  ✗ ENVIRONMENT should be 'production', got '{env_value}'")

    stripe_key = env_vars.get("STRIPE_API_KEY") or os.environ.get("STRIPE_API_KEY", "")
    if stripe_key and not stripe_key.startswith("sk_live_"):
        errors.append(f"  ✗ STRIPE_API_KEY should be live key (sk_live_...)")

    frontend_url = env_vars.get("FRONTEND_URL") or os.environ.get("FRONTEND_URL", "")
    if frontend_url and not frontend_url.startswith("https://"):
        errors.append(f"  ✗ FRONTEND_URL must use HTTPS")

    backend_url = env_vars.get("BACKEND_URL") or os.environ.get("BACKEND_URL", "")
    if backend_url and not backend_url.startswith("https://"):
        errors.append(f"  ✗ BACKEND_URL must use HTTPS")

    debug = env_vars.get("DEBUG") or os.environ.get("DEBUG", "false")
    if debug.lower() == "true":
        errors.append(f"  ✗ DEBUG should be 'false' in production")

    return missing, warnings, errors

def main():
    """Run validation."""
    print("\n" + "="*70)
    print("SellIA Production Environment Validation")
    print("="*70)

    # Load .env.production if it exists
    env_file = ".env.production"
    if os.path.exists(env_file):
        print(f"\n📖 Loading {env_file}...")
        env_vars = load_env_file(env_file)
        print(f"   Loaded {len(env_vars)} variables from file")
    else:
        print(f"\n⚠️  No {env_file} found, checking environment variables...")
        env_vars = {}

    # Add environment variables
    env_vars.update(os.environ)

    # Validate
    missing, warnings, errors = validate_variables(
        env_vars, REQUIRED_VARS, OPTIONAL_VARS
    )

    # Display results
    print("\n" + "-"*70)
    print("VALIDATION RESULTS")
    print("-"*70)

    if not missing and not warnings and not errors:
        print("\n✅ ALL CHECKS PASSED")
        print(f"\n   Total required variables: {len(REQUIRED_VARS)}")
        print(f"   Optional variables: {len(OPTIONAL_VARS)}")
        print(f"   Total configured: {len(env_vars)}")
        return 0

    if errors:
        print("\n🔴 ERRORS (Must fix before deployment)")
        for error in errors:
            print(error)

    if missing:
        print("\n🔴 MISSING REQUIRED VARIABLES")
        for var in missing:
            print(var)

    if warnings:
        print("\n🟡 WARNINGS (Optional)")
        for warning in warnings:
            print(warning)

    print("\n" + "="*70)
    if missing or errors:
        print("❌ Validation FAILED")
        print("\nNext steps:")
        print("1. Create .env.production with all required variables")
        print("2. Run: python3 scripts/generate-credentials.py")
        print("3. Fill in the missing values")
        print("4. Re-run this validation")
        return 1
    else:
        print("⚠️  Validation has warnings - please review")
        return 0

if __name__ == "__main__":
    sys.exit(main())
