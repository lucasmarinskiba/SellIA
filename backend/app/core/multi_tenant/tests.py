"""
Multi-tenant system tests: 400+ lines.
Unit tests for all components: tenant, isolation, API keys, billing, audit.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.database import Base
from app.domains.users.models import User
from .models import Tenant, TenantMember, TenantAPIKey, TenantBilling, AuditLog
from .tenant_manager import TenantService, TenantTier, TIER_LIMITS
from .tenant_isolation import TenantIsolation, TenantContext
from .api_key_management import APIKeyService
from .billing_integration import BillingService
from .audit_logging import AuditService, AuditAction, AuditStatus
from .tenant_migration import MigrationService

# Test fixtures
@pytest.fixture
async def test_db():
    """In-memory SQLite DB for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    return user


# Tenant Manager Tests
@pytest.mark.asyncio
async def test_create_tenant(test_db: AsyncSession, test_user: User):
    """Test tenant creation."""
    service = TenantService(test_db)

    tenant = await service.create_tenant(
        name="Test Organization",
        owner_id=str(test_user.id),
        tier=TenantTier.STARTER,
    )

    assert tenant is not None
    assert tenant.name == "Test Organization"
    assert tenant.owner_id == test_user.id
    assert tenant.tier == TenantTier.STARTER
    assert tenant.is_active == True

    # Check billing was created
    assert len(tenant.billing) == 1
    assert tenant.billing[0].base_tier_cost == TIER_LIMITS[TenantTier.STARTER]["monthly_cost"]


@pytest.mark.asyncio
async def test_get_tenant(test_db: AsyncSession, test_user: User):
    """Test retrieving tenant."""
    service = TenantService(test_db)

    tenant1 = await service.create_tenant(
        name="Tenant 1",
        owner_id=str(test_user.id),
    )

    tenant2 = await service.get_tenant(str(tenant1.id))
    assert tenant2 is not None
    assert tenant2.id == tenant1.id
    assert tenant2.name == "Tenant 1"


@pytest.mark.asyncio
async def test_list_user_tenants(test_db: AsyncSession, test_user: User):
    """Test listing user's tenants."""
    service = TenantService(test_db)

    tenant1 = await service.create_tenant("Tenant 1", str(test_user.id))
    tenant2 = await service.create_tenant("Tenant 2", str(test_user.id))

    tenants = await service.list_user_tenants(str(test_user.id))

    assert len(tenants) == 2
    tenant_ids = {str(t.id) for t in tenants}
    assert str(tenant1.id) in tenant_ids
    assert str(tenant2.id) in tenant_ids


@pytest.mark.asyncio
async def test_upgrade_tier(test_db: AsyncSession, test_user: User):
    """Test tenant tier upgrade."""
    service = TenantService(test_db)

    tenant = await service.create_tenant(
        "Test Tenant",
        str(test_user.id),
        tier=TenantTier.STARTER,
    )

    assert tenant.tier == TenantTier.STARTER
    assert tenant.max_users == TIER_LIMITS[TenantTier.STARTER]["max_users"]

    upgraded = await service.upgrade_tier(str(tenant.id), TenantTier.PRO)

    assert upgraded.tier == TenantTier.PRO
    assert upgraded.max_users == TIER_LIMITS[TenantTier.PRO]["max_users"]
    assert upgraded.max_monthly_api_calls == TIER_LIMITS[TenantTier.PRO]["max_monthly_api_calls"]


@pytest.mark.asyncio
async def test_suspend_resume_tenant(test_db: AsyncSession, test_user: User):
    """Test tenant suspension and resumption."""
    service = TenantService(test_db)

    tenant = await service.create_tenant("Test Tenant", str(test_user.id))
    assert tenant.is_paused == False

    suspended = await service.suspend_tenant(str(tenant.id), "Payment failed")
    assert suspended.is_paused == True
    assert suspended.suspended_reason == "Payment failed"

    resumed = await service.resume_tenant(str(tenant.id))
    assert resumed.is_paused == False
    assert resumed.suspended_reason is None


# Tenant Isolation Tests
@pytest.mark.asyncio
async def test_validate_tenant_access(test_db: AsyncSession, test_user: User):
    """Test tenant access validation."""
    service = TenantService(test_db)
    isolation = TenantIsolation(test_db)

    tenant = await service.create_tenant("Test Tenant", str(test_user.id))

    context = await isolation.validate_tenant_access(
        str(tenant.id),
        str(test_user.id),
    )

    assert context.tenant_id == str(tenant.id)
    assert context.user_id == str(test_user.id)
    assert context.role == "owner"


@pytest.mark.asyncio
async def test_unauthorized_tenant_access(test_db: AsyncSession, test_user: User):
    """Test access denied for non-member."""
    from app.core.exceptions import AppException

    service = TenantService(test_db)
    isolation = TenantIsolation(test_db)

    tenant = await service.create_tenant("Test Tenant", str(test_user.id))

    # Create another user
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        full_name="Other User",
        hashed_password="hashed",
        is_active=True,
    )
    test_db.add(other_user)
    await test_db.commit()

    # Try to access with non-member user
    with pytest.raises(AppException) as exc_info:
        await isolation.validate_tenant_access(
            str(tenant.id),
            str(other_user.id),
        )

    assert exc_info.value.status_code == 403


# API Key Tests
@pytest.mark.asyncio
async def test_create_api_key(test_db: AsyncSession, test_user: User):
    """Test API key creation."""
    service_tenant = TenantService(test_db)
    service_key = APIKeyService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    api_key, plaintext = await service_key.create_api_key(
        tenant_id=str(tenant.id),
        name="Test Key",
        created_by=str(test_user.id),
        scopes=["read", "write"],
    )

    assert api_key is not None
    assert plaintext is not None
    assert api_key.name == "Test Key"
    assert api_key.key_hash != plaintext  # Should be hashed
    assert api_key.key_prefix in plaintext


@pytest.mark.asyncio
async def test_validate_api_key(test_db: AsyncSession, test_user: User):
    """Test API key validation."""
    service_tenant = TenantService(test_db)
    service_key = APIKeyService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    api_key, plaintext = await service_key.create_api_key(
        tenant_id=str(tenant.id),
        name="Test Key",
        created_by=str(test_user.id),
    )

    # Validate with correct key
    validated = await service_key.validate_api_key(plaintext)
    assert validated is not None
    assert validated.id == api_key.id

    # Validate with wrong key
    invalid = await service_key.validate_api_key("sk_invalid_key")
    assert invalid is None


@pytest.mark.asyncio
async def test_rotate_api_key(test_db: AsyncSession, test_user: User):
    """Test API key rotation."""
    service_tenant = TenantService(test_db)
    service_key = APIKeyService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    old_key, _ = await service_key.create_api_key(
        tenant_id=str(tenant.id),
        name="Test Key",
        created_by=str(test_user.id),
    )

    new_key, new_plaintext = await service_key.rotate_api_key(str(old_key.id))

    # Old key should be revoked
    refreshed_old = await service_key.get_api_key(str(old_key.id))
    assert refreshed_old.is_revoked == True

    # New key should be active
    assert new_key.is_revoked == False

    # New key should validate
    validated = await service_key.validate_api_key(new_plaintext)
    assert validated is not None


@pytest.mark.asyncio
async def test_api_key_limit(test_db: AsyncSession, test_user: User):
    """Test API key creation limit."""
    from app.core.exceptions import AppException

    service_tenant = TenantService(test_db)
    service_key = APIKeyService(test_db)

    tenant = await service_tenant.create_tenant(
        "Test Tenant",
        str(test_user.id),
        tier=TenantTier.STARTER,  # Max 3 keys
    )

    # Create max keys
    for i in range(TIER_LIMITS[TenantTier.STARTER]["max_api_keys"]):
        await service_key.create_api_key(
            tenant_id=str(tenant.id),
            name=f"Key {i}",
            created_by=str(test_user.id),
        )

    # Try to exceed limit
    with pytest.raises(AppException) as exc_info:
        await service_key.create_api_key(
            tenant_id=str(tenant.id),
            name="Extra Key",
            created_by=str(test_user.id),
        )

    assert exc_info.value.status_code == 429


# Billing Tests
@pytest.mark.asyncio
async def test_record_api_call(test_db: AsyncSession, test_user: User):
    """Test API call usage tracking."""
    service_tenant = TenantService(test_db)
    service_billing = BillingService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    # Record calls
    for _ in range(100):
        await service_billing.record_api_call(str(tenant.id))

    # Verify recorded
    stats = await service_billing.get_usage_stats(str(tenant.id))
    assert stats["api_calls_used"] == 100


@pytest.mark.asyncio
async def test_billing_cycle_calculation(test_db: AsyncSession, test_user: User):
    """Test billing cost calculation."""
    service_tenant = TenantService(test_db)
    service_billing = BillingService(test_db)

    tenant = await service_tenant.create_tenant(
        "Test Tenant",
        str(test_user.id),
        tier=TenantTier.STARTER,
    )

    # Record usage
    for _ in range(1000):
        await service_billing.record_api_call(str(tenant.id))

    # Calculate costs
    costs = await service_billing.calculate_billing_cycle(str(tenant.id))

    assert costs["base_cost"] == TIER_LIMITS[TenantTier.STARTER]["monthly_cost"]
    assert costs["total_cost"] > costs["base_cost"]  # Should have overage


# Audit Tests
@pytest.mark.asyncio
async def test_audit_logging(test_db: AsyncSession, test_user: User):
    """Test audit log creation."""
    service_tenant = TenantService(test_db)
    service_audit = AuditService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    log = await service_audit.log_action(
        tenant_id=str(tenant.id),
        action=AuditAction.USER_LOGIN,
        resource_type="user",
        change_type="read",
        user_id=str(test_user.id),
        user_email=test_user.email,
        ip_address="192.168.1.1",
        status=AuditStatus.SUCCESS,
    )

    assert log is not None
    assert log.action == AuditAction.USER_LOGIN
    assert log.status == AuditStatus.SUCCESS


@pytest.mark.asyncio
async def test_list_audit_logs(test_db: AsyncSession, test_user: User):
    """Test querying audit logs."""
    service_tenant = TenantService(test_db)
    service_audit = AuditService(test_db)

    tenant = await service_tenant.create_tenant("Test Tenant", str(test_user.id))

    # Create multiple logs
    for i in range(5):
        await service_audit.log_action(
            tenant_id=str(tenant.id),
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            change_type="read",
            user_id=str(test_user.id),
        )

    # Query logs
    logs, count = await service_audit.list_tenant_audit_logs(str(tenant.id))

    assert count == 5
    assert len(logs) == 5


# Migration Tests
@pytest.mark.asyncio
async def test_migrate_user_to_tenant(test_db: AsyncSession, test_user: User):
    """Test user migration."""
    service = MigrationService(test_db)

    tenant = await service.migrate_user_to_tenant(
        str(test_user.id),
        tenant_name="My Workspace",
    )

    assert tenant is not None
    assert tenant.name == "My Workspace"
    assert tenant.owner_id == test_user.id


@pytest.mark.asyncio
async def test_validate_migration(test_db: AsyncSession, test_user: User):
    """Test migration validation."""
    service = MigrationService(test_db)

    tenant = await service.migrate_user_to_tenant(str(test_user.id))

    validation = await service.validate_migration(
        str(tenant.id),
        str(test_user.id),
    )

    assert validation["tenant_exists"] == True
    assert validation["user_is_owner"] == True
    assert validation["billing_exists"] == True
    assert validation["is_valid"] == True
