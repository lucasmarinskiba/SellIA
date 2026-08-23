-- Minimal schema for users + businesses to unblock signup/auth
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    is_superuser BOOLEAN DEFAULT false,
    is_2fa_enabled BOOLEAN DEFAULT false,
    country_code VARCHAR(2) DEFAULT 'AR',
    preferred_currency VARCHAR(3) DEFAULT 'ARS',
    timezone VARCHAR(50) DEFAULT 'America/Argentina/Buenos_Aires',
    billing_address JSONB DEFAULT '{}',
    payment_methods JSONB DEFAULT '[]',
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
    locations JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_businesses_user_id ON businesses(user_id);
