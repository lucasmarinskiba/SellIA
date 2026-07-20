-- Migration: Create sellia_conversations table for SellIA Assistant persistent history
-- Run this against your PostgreSQL database

CREATE TABLE IF NOT EXISTS sellia_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    messages JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sellia_conversations_user_id ON sellia_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_sellia_conversations_active ON sellia_conversations(is_active);
