#!/usr/bin/env python
"""
Verify Railway environment configuration.

Checks if all required variables are set.

Usage:
  python verify_railway_config.py
"""

import os
import sys
import logging
from typing import Dict, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def check_env_vars() -> Tuple[bool, Dict[str, str]]:
    """Check all required and recommended env vars"""

    # Critical (must have)
    critical = {
        'DATABASE_URL': 'PostgreSQL connection string',
        'REDIS_URL': 'Redis cache URL',
        'SECRET_KEY': 'JWT signing key (strong random)',
        'ANTHROPIC_API_KEY': 'Claude API key',
        'ENVIRONMENT': 'Deployment environment (production)',
    }

    # Recommended (should have)
    recommended = {
        'FRONTEND_URL': 'Frontend URL for CORS',
        'TURNSTILE_SECRET_KEY': 'Cloudflare Turnstile secret',
        'MERCADOPAGO_ACCESS_TOKEN': 'MercadoPago API token',
    }

    # Optional (nice to have)
    optional = {
        'OPENAI_API_KEY': 'OpenAI API key (fallback)',
        'WEBAUTHN_RP_ID': 'WebAuthn relying party ID',
        'WEBAUTHN_RP_ORIGIN': 'WebAuthn origin',
    }

    missing_critical = {}
    missing_recommended = {}
    present = {}

    # Check critical
    logger.info("\n" + "=" * 70)
    logger.info("CRITICAL VARIABLES (MUST HAVE)")
    logger.info("=" * 70)
    for key, desc in critical.items():
        value = os.getenv(key)
        if value:
            # Don't log the actual secret
            if len(value) > 50:
                display = value[:20] + "..." + value[-10:]
            else:
                display = value
            logger.info(f"✓ {key:<30} {desc}")
            logger.info(f"  Value: {display}")
            present[key] = value
        else:
            logger.error(f"✗ {key:<30} {desc} [MISSING]")
            missing_critical[key] = desc

    # Check recommended
    logger.info("\n" + "=" * 70)
    logger.info("RECOMMENDED VARIABLES (SHOULD HAVE)")
    logger.info("=" * 70)
    for key, desc in recommended.items():
        value = os.getenv(key)
        if value:
            if len(value) > 50:
                display = value[:20] + "..." + value[-10:]
            else:
                display = value
            logger.info(f"✓ {key:<30} {desc}")
            logger.info(f"  Value: {display}")
            present[key] = value
        else:
            logger.warning(f"⚠ {key:<30} {desc} [not set]")

    # Check optional
    logger.info("\n" + "=" * 70)
    logger.info("OPTIONAL VARIABLES (NICE TO HAVE)")
    logger.info("=" * 70)
    for key, desc in optional.items():
        value = os.getenv(key)
        if value:
            logger.info(f"✓ {key:<30} {desc}")
            present[key] = value
        else:
            logger.info(f"  {key:<30} {desc} [not set]")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    total_vars = len(critical) + len(recommended) + len(optional)
    logger.info(f"Critical:     {len(critical) - len(missing_critical)}/{len(critical)}")
    logger.info(f"Recommended:  {len(recommended) - len([k for k in recommended if not os.getenv(k)])}/{len(recommended)}")
    logger.info(f"Optional:     {len([k for k in optional if os.getenv(k)])}/{len(optional)}")
    logger.info(f"Total:        {len(present)}/{total_vars}")

    if missing_critical:
        logger.error(f"\n❌ CRITICAL VARIABLES MISSING: {len(missing_critical)}")
        for key, desc in missing_critical.items():
            logger.error(f"   - {key}: {desc}")
        return False, present
    else:
        logger.info("\n✅ All critical variables set!")
        return True, present


def verify_database_connection(db_url: str) -> bool:
    """Test PostgreSQL connection"""
    logger.info("\n" + "=" * 70)
    logger.info("DATABASE CONNECTION TEST")
    logger.info("=" * 70)

    try:
        import asyncio
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        async def test():
            engine = create_async_engine(db_url, echo=False)
            try:
                async with engine.connect() as conn:
                    result = await conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    logger.info(f"✓ PostgreSQL connected: {version}")
                    return True
            finally:
                await engine.dispose()

        return asyncio.run(test())
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def main():
    """Main verification"""
    logger.info("\n🔍 Railway Configuration Verification\n")

    success, present = check_env_vars()

    # Test DB connection if credentials available
    if 'DATABASE_URL' in present:
        db_ok = verify_database_connection(present['DATABASE_URL'])
        if not db_ok:
            success = False

    # Final verdict
    logger.info("\n" + "=" * 70)
    if success:
        logger.info("✅ CONFIGURATION OK - Ready for deployment")
        logger.info("=" * 70)
        logger.info("\nNext steps:")
        logger.info("  1. Run migrations: python run_migrations.py")
        logger.info("  2. Test memory: python test_multi_user_memory.py")
        logger.info("  3. Deploy to Vercel")
        sys.exit(0)
    else:
        logger.error("❌ CONFIGURATION INCOMPLETE - See errors above")
        logger.error("=" * 70)
        logger.error("\nMissing critical variables. Add them in:")
        logger.error("  Railway Dashboard → Settings → Variables")
        sys.exit(1)


if __name__ == "__main__":
    main()
