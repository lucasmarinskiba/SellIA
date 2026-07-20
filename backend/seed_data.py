"""
Seed script for SellIA - Generate realistic test data.

Usage:
    docker compose exec backend python seed_data.py
    
Or locally (with DB accessible):
    cd backend && python seed_data.py
"""

import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
# Import all models so SQLAlchemy registers them before queries
from app.domains.users.models import User
from app.domains.businesses.models import Business, BusinessType, DEFAULT_CONFIGS
from app.domains.catalogs.models import CatalogItem, CatalogItemType
from app.domains.channels.models import (
    ChannelConnection, ChannelPlatform, ChannelStatus,
    Conversation, ConversationStatus, Message, MessageDirection, MessageStatus,
)
from app.domains.security.models import (
    UserLoginLog, SecurityConfig, SecurityWebhook,
    UserSession, PushSubscription, TwoFABackupCode, BreachCheckLog,
)
from app.domains.subscriptions.models import Subscription, SubscriptionPlan
from app.domains.orders.models import Order
from app.domains.crm.models import Pipeline, Deal
from app.domains.agents.models import AgentPersonality, AgentConfig


# ============ SEED DATA ============

import secrets as _secrets

def _gen_password():
    return _secrets.token_urlsafe(16)

USERS = [
    {
        "email": "demo@selia.com",
        "password": _gen_password(),
        "full_name": "Usuario Demo",
        "is_superuser": False,
        "failed_login_attempts": 0,
    },
    {
        "email": "maria@latienda.com",
        "password": _gen_password(),
        "full_name": "María González",
        "is_superuser": False,
        "failed_login_attempts": 2,
        "locked_until": None,
    },
    {
        "email": "carlos@techservice.ar",
        "password": _gen_password(),
        "full_name": "Carlos Rodríguez",
        "is_superuser": False,
        "failed_login_attempts": 0,
    },
    {
        "email": "admin@selia.com",
        "password": _gen_password(),
        "full_name": "Administrador SellIA",
        "is_superuser": True,
        "failed_login_attempts": 0,
    },
]

BUSINESSES = [
    {
        "user_email": "maria@latienda.com",
        "name": "La Tienda de María",
        "type": BusinessType.GOODS,
        "description": "Venta de productos artesanales y decoración para el hogar. Envíos a todo el país.",
    },
    {
        "user_email": "maria@latienda.com",
        "name": "María Digital",
        "type": BusinessType.DIGITAL,
        "description": "Cursos online de decoración y manualidades.",
    },
    {
        "user_email": "carlos@techservice.ar",
        "name": "TechService Carlos",
        "type": BusinessType.SERVICES,
        "description": "Reparación de computadoras, notebooks y servicios de redes. Atención a domicilio en CABA.",
    },
    {
        "user_email": "demo@selia.com",
        "name": "Demo Business",
        "type": BusinessType.MIXED,
        "description": "Negocio de prueba para demostraciones.",
    },
]

CATALOG_ITEMS = [
    # La Tienda de María
    {"business_name": "La Tienda de María", "type": CatalogItemType.GOOD, "name": "Velas aromáticas pack x3", "price": 4500.00, "stock": 25, "tags": ["hogar", "aromaterapia"]},
    {"business_name": "La Tienda de María", "type": CatalogItemType.GOOD, "name": "Maceta cerámica artesanal", "price": 8900.00, "stock": 12, "tags": ["jardín", "decoración"]},
    {"business_name": "La Tienda de María", "type": CatalogItemType.GOOD, "name": "Almohadón tejido a mano", "price": 12000.00, "stock": 8, "tags": ["textil", "dormitorio"]},
    {"business_name": "La Tienda de María", "type": CatalogItemType.GOOD, "name": "Lámpara de sal del Himalaya", "price": 15000.00, "stock": 5, "tags": ["iluminación", "bienestar"]},
    # María Digital
    {"business_name": "María Digital", "type": CatalogItemType.DIGITAL, "name": "Curso: Decora tu hogar en 7 días", "price": 25000.00, "stock": None, "tags": ["curso", "decoración"]},
    {"business_name": "María Digital", "type": CatalogItemType.DIGITAL, "name": "Ebook: 50 manualidades fáciles", "price": 3500.00, "stock": None, "tags": ["ebook", "manualidades"]},
    # TechService Carlos
    {"business_name": "TechService Carlos", "type": CatalogItemType.SERVICE, "name": "Diagnóstico y reparación de PC", "price": 15000.00, "stock": None, "tags": ["reparación", "computadoras"]},
    {"business_name": "TechService Carlos", "type": CatalogItemType.SERVICE, "name": "Instalación de red WiFi empresarial", "price": 45000.00, "stock": None, "tags": ["redes", "wifi"]},
    {"business_name": "TechService Carlos", "type": CatalogItemType.SERVICE, "name": "Mantenimiento mensual de equipos", "price": 28000.00, "stock": None, "tags": ["mantenimiento", "soporte"]},
]

CHANNELS = [
    {"business_name": "La Tienda de María", "platform": ChannelPlatform.WHATSAPP, "name": "WhatsApp Ventas"},
    {"business_name": "La Tienda de María", "platform": ChannelPlatform.INSTAGRAM, "name": "Instagram DM"},
    {"business_name": "TechService Carlos", "platform": ChannelPlatform.WHATSAPP, "name": "WhatsApp Soporte"},
    {"business_name": "TechService Carlos", "platform": ChannelPlatform.EMAIL, "name": "Email Corporativo"},
    {"business_name": "Demo Business", "platform": ChannelPlatform.WEBCHAT, "name": "Chat Web"},
]

CONVERSATIONS = [
    {"business_name": "La Tienda de María", "platform": ChannelPlatform.WHATSAPP, "lead_name": "Juan Pérez", "lead_phone": "+5491167890123", "messages": [
        ("inbound", "Hola, ¿tienen stock de las velas aromáticas?"),
        ("outbound", "¡Hola Juan! Sí, tenemos stock. ¿Te gustaría que te reserve un pack?"),
        ("inbound", "Sí por favor, ¿hacen envíos a Córdoba?"),
        ("outbound", "Claro, enviamos a todo el país por Andreani. El costo es $3.500."),
    ]},
    {"business_name": "La Tienda de María", "platform": ChannelPlatform.INSTAGRAM, "lead_name": "Ana López", "lead_phone": None, "messages": [
        ("inbound", "Me encantan las macetas! Tienen en color terracota?"),
        ("outbound", "Hola Ana! Sí, tenemos terracota, blanco y verde musgo. ¿Cuál preferís?"),
        ("inbound", "Terracota! Quiero 2"),
    ]},
    {"business_name": "TechService Carlos", "platform": ChannelPlatform.WHATSAPP, "lead_name": "Empresa ABC", "lead_phone": "+5491145678901", "messages": [
        ("inbound", "Necesitamos instalar WiFi en nuestra oficina de 200m2"),
        ("outbound", "Buen día! Podemos hacer una visita técnica sin cargo. ¿Qué día les queda cómodo?"),
        ("inbound", "El jueves a las 10hs?"),
        ("outbound", "Perfecto, queda agendado. Les envío confirmación por mail."),
    ]},
    {"business_name": "Demo Business", "platform": ChannelPlatform.WEBCHAT, "lead_name": "Visitante Web", "lead_phone": None, "messages": [
        ("inbound", "Hola, quiero saber más sobre sus servicios"),
        ("outbound", "¡Hola! Soy el agente IA de SellIA. ¿En qué puedo ayudarte hoy?"),
        ("inbound", "¿Tienen plan gratuito?"),
        ("outbound", "Sí, nuestro plan Free incluye 1 agente, 1 canal y 50 conversaciones. ¿Te gustaría probarlo?"),
    ]},
]

LOGIN_LOGS = [
    # demo user - logins normales
    {"email": "demo@selia.com", "ip": "190.191.100.50", "country": "AR", "city": "Buenos Aires", "lat": -34.60, "lon": -58.38, "success": True},
    {"email": "demo@selia.com", "ip": "190.191.100.50", "country": "AR", "city": "Buenos Aires", "lat": -34.60, "lon": -58.38, "success": True},
    # maria - failed attempts
    {"email": "maria@latienda.com", "ip": "201.235.78.12", "country": "AR", "city": "Córdoba", "lat": -31.42, "lon": -64.18, "success": False},
    {"email": "maria@latienda.com", "ip": "201.235.78.12", "country": "AR", "city": "Córdoba", "lat": -31.42, "lon": -64.18, "success": False},
    {"email": "maria@latienda.com", "ip": "201.235.78.12", "country": "AR", "city": "Córdoba", "lat": -31.42, "lon": -64.18, "success": True},
    # carlos - login from different location (geofence demo)
    {"email": "carlos@techservice.ar", "ip": "190.191.100.50", "country": "AR", "city": "Buenos Aires", "lat": -34.60, "lon": -58.38, "success": True},
    {"email": "carlos@techservice.ar", "ip": "186.22.45.100", "country": "CL", "city": "Santiago", "lat": -33.45, "lon": -70.67, "success": True},  # Should trigger geofence
    # admin logins
    {"email": "admin@selia.com", "ip": "172.20.0.1", "country": None, "city": None, "lat": None, "lon": None, "success": True},
]

SECURITY_WEBHOOKS = [
    {"name": "Slack Security Alerts", "url": "SLACK_WEBHOOK_URL_HERE", "platform": "slack", "events": "login,failed_login,new_device,malware,brute_force,geofence,breach"},
    {"name": "Discord Monitoring", "url": "https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz", "platform": "discord", "events": "login,failed_login,new_device,geofence"},
]


async def seed_users(db: AsyncSession) -> dict:
    """Create or get users. Returns email -> user dict."""
    users = {}
    for u_data in USERS:
        result = await db.execute(select(User).where(User.email == u_data["email"]))
        existing = result.scalar_one_or_none()
        if existing:
            users[u_data["email"]] = existing
            print(f"  User exists: {u_data['email']}")
            continue
        
        user = User(
            email=u_data["email"],
            hashed_password=get_password_hash(u_data["password"]),
            full_name=u_data["full_name"],
            is_active=True,
            is_superuser=u_data.get("is_superuser", False),
            failed_login_attempts=u_data.get("failed_login_attempts", 0),
            locked_until=u_data.get("locked_until"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        users[u_data["email"]] = user
        print(f"  Created user: {u_data['email']}")
    return users


async def seed_businesses(db: AsyncSession, users: dict) -> dict:
    """Create businesses. Returns name -> business dict."""
    businesses = {}
    for b_data in BUSINESSES:
        result = await db.execute(select(Business).where(Business.name == b_data["name"]))
        existing = result.scalar_one_or_none()
        if existing:
            businesses[b_data["name"]] = existing
            print(f"  Business exists: {b_data['name']}")
            continue
        
        user = users[b_data["user_email"]]
        business = Business(
            user_id=user.id,
            name=b_data["name"],
            type=b_data["type"],
            description=b_data["description"],
            config=DEFAULT_CONFIGS.get(b_data["type"], {}),
        )
        db.add(business)
        await db.commit()
        await db.refresh(business)
        businesses[b_data["name"]] = business
        print(f"  Created business: {b_data['name']}")
    return businesses


async def seed_catalog(db: AsyncSession, businesses: dict):
    """Create catalog items."""
    for item_data in CATALOG_ITEMS:
        business = businesses[item_data["business_name"]]
        result = await db.execute(
            select(CatalogItem).where(
                CatalogItem.business_id == business.id,
                CatalogItem.name == item_data["name"],
            )
        )
        if result.scalar_one_or_none():
            print(f"  Catalog item exists: {item_data['name']}")
            continue
        
        item = CatalogItem(
            business_id=business.id,
            type=item_data["type"],
            name=item_data["name"],
            description=f"Producto de alta calidad: {item_data['name']}",
            price=Decimal(str(item_data["price"])),
            stock=item_data["stock"],
            tags=item_data["tags"],
        )
        db.add(item)
        await db.commit()
        print(f"  Created catalog item: {item_data['name']}")


async def seed_channels(db: AsyncSession, businesses: dict) -> dict:
    """Create channels and conversations with messages."""
    channels_map = {}  # (business_name, platform) -> channel
    
    for ch_data in CHANNELS:
        business = businesses[ch_data["business_name"]]
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business.id,
                ChannelConnection.platform == ch_data["platform"],
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            channels_map[(ch_data["business_name"], ch_data["platform"])] = existing
            print(f"  Channel exists: {ch_data['name']}")
            continue
        
        channel = ChannelConnection(
            business_id=business.id,
            platform=ch_data["platform"],
            name=ch_data["name"],
            status=ChannelStatus.CONNECTED,
            credentials={"demo": True},
        )
        db.add(channel)
        await db.commit()
        await db.refresh(channel)
        channels_map[(ch_data["business_name"], ch_data["platform"])] = channel
        print(f"  Created channel: {ch_data['name']}")
    
    return channels_map


async def seed_conversations(db: AsyncSession, businesses: dict, channels_map: dict):
    """Create conversations with messages."""
    for conv_data in CONVERSATIONS:
        business = businesses[conv_data["business_name"]]
        channel = channels_map.get((conv_data["business_name"], conv_data["platform"]))
        
        conv = Conversation(
            business_id=business.id,
            channel_connection_id=channel.id if channel else None,
            external_id=f"demo_{uuid.uuid4().hex[:8]}",
            lead_name=conv_data["lead_name"],
            lead_phone=conv_data.get("lead_phone"),
            status=ConversationStatus.ACTIVE,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        
        for direction, content in conv_data["messages"]:
            msg = Message(
                conversation_id=conv.id,
                direction=direction,
                content=content,
                status=MessageStatus.READ if direction == "outbound" else MessageStatus.DELIVERED,
            )
            db.add(msg)
        
        conv.last_message_at = datetime.now(timezone.utc)
        await db.commit()
        print(f"  Created conversation with {len(conv_data['messages'])} messages: {conv_data['lead_name']}")


async def seed_login_logs(db: AsyncSession, users: dict):
    """Create login logs for audit panel."""
    base_time = datetime.now(timezone.utc) - timedelta(days=1)
    
    for log_data in LOGIN_LOGS:
        user = users[log_data["email"]]
        log = UserLoginLog(
            user_id=user.id,
            ip_address=log_data["ip"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            device_fingerprint=f"fp_{uuid.uuid4().hex[:16]}",
            country=log_data["country"],
            city=log_data["city"],
            latitude=log_data.get("lat"),
            longitude=log_data.get("lon"),
            success=log_data["success"],
            created_at=base_time + timedelta(minutes=hash(log_data['email']) % 120),
        )
        db.add(log)
    
    await db.commit()
    print(f"  Created {len(LOGIN_LOGS)} login logs")


async def seed_sessions(db: AsyncSession, users: dict):
    """Create some active and expired sessions."""
    from app.core.security import create_access_token
    import hashlib
    
    for email in ["demo@selia.com", "maria@latienda.com", "carlos@techservice.ar"]:
        user = users[email]
        token = create_access_token(data={"sub": str(user.id)})
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
        
        session = UserSession(
            user_id=user.id,
            session_token=token_hash,
            device_name="Chrome on Windows",
            device_fingerprint=f"fp_{uuid.uuid4().hex[:16]}",
            ip_address="190.191.100.50",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            country="AR",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_revoked=False,
        )
        db.add(session)
    
    # Expired session
    user = users["demo@selia.com"]
    expired = UserSession(
        user_id=user.id,
        session_token="expired_" + uuid.uuid4().hex[:32],
        device_name="Safari on iPhone",
        ip_address="201.235.78.12",
        country="AR",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        is_revoked=False,
    )
    db.add(expired)
    
    await db.commit()
    print(f"  Created 4 sessions (3 active, 1 expired)")


async def seed_security_config(db: AsyncSession):
    """Ensure security config exists with demo settings."""
    result = await db.execute(select(SecurityConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SecurityConfig(
            blocked_countries="CN,RU,KP,IR",
            require_turnstile=False,
            require_2fa_for_admins=False,
            alert_on_new_device=True,
            alert_on_failed_login=True,
            alert_on_malware=True,
            max_distance_km=500.0,
            alert_on_geofence=True,
            hibp_api_key=None,
            alert_on_breach=False,
        )
        db.add(config)
        await db.commit()
        print("  Created security config")
    else:
        print("  Security config exists")


async def seed_webhooks(db: AsyncSession):
    """Create security webhooks."""
    result = await db.execute(select(SecurityWebhook))
    existing = result.scalars().all()
    if existing:
        print(f"  {len(existing)} webhooks exist, skipping")
        return
    
    for wh_data in SECURITY_WEBHOOKS:
        webhook = SecurityWebhook(
            name=wh_data["name"],
            url=wh_data["url"],
            platform=wh_data["platform"],
            events=wh_data["events"],
            is_active=True,
        )
        db.add(webhook)
    
    await db.commit()
    print(f"  Created {len(SECURITY_WEBHOOKS)} security webhooks")


async def seed_2fa_backup_codes(db: AsyncSession, users: dict):
    """Create some backup codes for demo user (already used some)."""
    import hashlib
    import secrets
    
    user = users.get("demo@selia.com")
    if not user:
        return
    
    # Enable 2FA on demo user
    import pyotp
    user.totp_secret = pyotp.random_base32()
    user.is_2fa_enabled = True
    await db.commit()
    
    # Create 8 backup codes, mark 2 as used
    codes = [secrets.token_hex(4).upper() for _ in range(8)]
    for i, code in enumerate(codes):
        bc = TwoFABackupCode(
            user_id=user.id,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            is_used=(i < 2),
            used_at=datetime.now(timezone.utc) - timedelta(days=i) if i < 2 else None,
        )
        db.add(bc)
    
    await db.commit()
    print(f"  Enabled 2FA for demo@selia.com with {len(codes)} backup codes (2 used)")


async def seed_breach_checks(db: AsyncSession, users: dict):
    """Create sample breach check logs."""
    user = users.get("maria@latienda.com")
    if not user:
        return
    
    result = await db.execute(select(BreachCheckLog).where(BreachCheckLog.user_id == user.id))
    if result.scalar_one_or_none():
        print("  Breach checks exist for maria, skipping")
        return
    
    log = BreachCheckLog(
        user_id=user.id,
        email=user.email,
        breaches_found=0,
        breach_names="",
    )
    db.add(log)
    await db.commit()
    print("  Created breach check log for maria (clean)")


async def main():
    print("=" * 50)
    print("SellIA Seed Data")
    print("=" * 50)
    print("\n⚠️  SEED PASSWORDS (auto-generated, copy them now):")
    for u_data in USERS:
        print(f"    {u_data['email']}: {u_data['password']}")
    print()
    
    async with AsyncSessionLocal() as db:
        print("\n1. Seeding users...")
        users = await seed_users(db)
        
        print("\n2. Seeding security config...")
        await seed_security_config(db)
        
        print("\n3. Seeding businesses...")
        businesses = await seed_businesses(db, users)
        
        print("\n4. Seeding catalog items...")
        await seed_catalog(db, businesses)
        
        print("\n5. Seeding channels...")
        channels_map = await seed_channels(db, businesses)
        
        print("\n6. Seeding conversations...")
        await seed_conversations(db, businesses, channels_map)
        
        print("\n7. Seeding login logs (audit)...")
        await seed_login_logs(db, users)
        
        print("\n8. Seeding sessions...")
        await seed_sessions(db, users)
        
        print("\n9. Seeding webhooks...")
        await seed_webhooks(db)
        
        print("\n10. Seeding 2FA backup codes...")
        await seed_2fa_backup_codes(db, users)
        
        print("\n11. Seeding breach checks...")
        await seed_breach_checks(db, users)
    
    print("\n" + "=" * 50)
    print("Seed complete!")
    print("=" * 50)
    print("\nDemo accounts:")
    print("  demo@selia.com / DemoPassword123! (2FA enabled, 6 backup codes left)")
    print("  maria@latienda.com / MariaPass123! (2 failed login attempts)")
    print("  carlos@techservice.ar / CarlosPass123! (geofence violation: BA -> Santiago)")
    print("  admin@selia.com / AdminSecure123! (superuser)")


if __name__ == "__main__":
    asyncio.run(main())
