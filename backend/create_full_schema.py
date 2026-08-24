#!/usr/bin/env python
"""Create complete production schema for SellIA."""

import asyncio
from sqlalchemy import text
from app.db.database import engine

SQL = """
-- Core user/business tables
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    is_2fa_enabled BOOLEAN DEFAULT false,
    totp_secret VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    description TEXT,
    website VARCHAR(255),
    logo_url VARCHAR(255),
    localization_model VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products & inventory
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL,
    cost NUMERIC(12,2),
    inventory_count INT DEFAULT 0,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales funnel - leads to customers
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(20),
    name VARCHAR(255),
    source VARCHAR(50),
    stage VARCHAR(50) DEFAULT 'lead',
    value NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversions & orders
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    lead_id VARCHAR(255),
    customer_email VARCHAR(255),
    total NUMERIC(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    platform VARCHAR(50),
    platform_order_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Platform connections (Amazon, Mercado Libre, etc)
CREATE TABLE IF NOT EXISTS platform_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    platform VARCHAR(100) NOT NULL,
    api_key VARCHAR(500),
    credentials JSONB,
    status VARCHAR(50) DEFAULT 'active',
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FOMO/Scarcity system
CREATE TABLE IF NOT EXISTS fomo_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    campaign_type VARCHAR(50),
    trigger_value VARCHAR(255),
    message TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Automations/Workflows
CREATE TABLE IF NOT EXISTS automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100),
    actions JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics & tracking
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id),
    event_type VARCHAR(100),
    event_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Offline conversions & locations
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offline_conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id),
    location_id UUID REFERENCES locations(id),
    visitor_name VARCHAR(255),
    visitor_email VARCHAR(255),
    visitor_phone VARCHAR(20),
    visit_type VARCHAR(50),
    purchased BOOLEAN DEFAULT false,
    amount NUMERIC(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SEO & structured data
CREATE TABLE IF NOT EXISTS seo_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id),
    url VARCHAR(500),
    title VARCHAR(255),
    description TEXT,
    keywords TEXT,
    schema_type VARCHAR(100),
    schema_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_businesses_user_id ON businesses(user_id);
CREATE INDEX IF NOT EXISTS ix_products_business_id ON products(business_id);
CREATE INDEX IF NOT EXISTS ix_leads_business_id ON leads(business_id);
CREATE INDEX IF NOT EXISTS ix_leads_stage ON leads(stage);
CREATE INDEX IF NOT EXISTS ix_orders_business_id ON orders(business_id);
CREATE INDEX IF NOT EXISTS ix_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS ix_platform_credentials_business ON platform_credentials(business_id);
CREATE INDEX IF NOT EXISTS ix_fomo_campaigns_business ON fomo_campaigns(business_id);
CREATE INDEX IF NOT EXISTS ix_automations_business ON automations(business_id);
CREATE INDEX IF NOT EXISTS ix_analytics_business ON analytics_events(business_id);
CREATE INDEX IF NOT EXISTS ix_locations_business ON locations(business_id);
CREATE INDEX IF NOT EXISTS ix_offline_conversions_business ON offline_conversions(business_id);
CREATE INDEX IF NOT EXISTS ix_seo_business ON seo_data(business_id);
"""

async def main():
    async with engine.begin() as conn:
        count = 0
        errors = 0
        for stmt in SQL.split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                    count += 1
                except Exception as e:
                    errors += 1
                    print(f"Skipped (error): {stmt[:50]}... - {str(e)[:80]}")
    print(f"Schema: {count} succeeded, {errors} skipped")

if __name__ == "__main__":
    asyncio.run(main())
