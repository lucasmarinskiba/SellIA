from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings
from sqlalchemy.pool import NullPool

settings = get_settings()

# Build connect_args for SSL in production
connect_args = {}
if settings.ENVIRONMENT == "production" and settings.DB_SSL_MODE not in ("disable", "allow"):
    import ssl
    ssl_context = ssl.create_default_context()
    if settings.DB_SSL_MODE in ("verify-ca", "verify-full") and settings.DB_SSL_CA:
        ssl_context.load_verify_locations(settings.DB_SSL_CA)
    elif settings.DB_SSL_MODE in ("verify-ca", "verify-full"):
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        # require / prefer — verify server cert but don't require CA file
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

if settings.ENVIRONMENT == "testing":
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        connect_args=connect_args,
        # Pool tuning for production load
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 min
        pool_pre_ping=True,  # Verify connection health before use
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
