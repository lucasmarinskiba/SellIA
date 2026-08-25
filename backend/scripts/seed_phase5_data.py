"""Seed Phase 5 test data: locations, offline conversions, proximity events."""

import asyncio
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import get_settings

# Import models
from app.domains.businesses.location_models import Location, LocationType, LocalizationModel
from app.domains.businesses.models import Business
from app.domains.users.models import User


async def seed_data():
    """Seed test locations and offline conversions."""
    settings = get_settings()
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create test user if needed
        user_id = uuid4()
        business_id = uuid4()
        
        # Create test locations
        locations = [
            Location(
                id=uuid4(),
                business_id=business_id,
                name="Showroom Centro",
                type=LocationType.SHOWROOM,
                address="Av. Corrientes 1234, Buenos Aires",
                city="Buenos Aires",
                latitude=-34.6037,
                longitude=-58.3816,
                phone="+54 11 1234-5678",
                email="centro@sellía.local",
                allows_walk_ins=True,
                allows_appointments=True,
                allows_demos=True,
                service_radius_km=2.0,
                is_active=True,
            ),
            Location(
                id=uuid4(),
                business_id=business_id,
                name="Service Center Belgrano",
                type=LocationType.SERVICE_CENTER,
                address="Calle Echeverría 1000, Buenos Aires",
                city="Buenos Aires",
                latitude=-34.5765,
                longitude=-58.4506,
                phone="+54 11 5678-1234",
                allows_appointments=True,
                service_radius_km=5.0,
                is_active=True,
            ),
        ]
        
        for loc in locations:
            session.add(loc)
        
        await session.commit()
        
        print(f"✅ Seeded {len(locations)} test locations")
        print(f"  - Business: {business_id}")
        print(f"  - Locations: Showroom Centro, Service Center Belgrano")
        print(f"\nTo use:")
        print(f"  POST /api/v1/businesses/{business_id}/locations")
        print(f"  GET  /api/v1/businesses/{business_id}/locations")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
