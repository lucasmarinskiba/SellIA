-- ─── Row-Level Security policies · multi-tenant isolation ───
-- Runs once on Postgres init. Idempotent.

-- Enable RLS on all tenant-scoped tables
ALTER TABLE IF EXISTS deals          ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS contacts       ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS conversations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS messages       ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS channels       ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs     ENABLE ROW LEVEL SECURITY;

-- Policy: tenant_id must match session-bound app.tenant_id
DROP POLICY IF EXISTS tenant_isolation ON deals;
CREATE POLICY tenant_isolation ON deals
    USING (tenant_id::text = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS tenant_isolation ON contacts;
CREATE POLICY tenant_isolation ON contacts
    USING (tenant_id::text = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS tenant_isolation ON conversations;
CREATE POLICY tenant_isolation ON conversations
    USING (tenant_id::text = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS tenant_isolation ON messages;
CREATE POLICY tenant_isolation ON messages
    USING (tenant_id::text = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS tenant_isolation ON channels;
CREATE POLICY tenant_isolation ON channels
    USING (tenant_id::text = current_setting('app.tenant_id', true));

DROP POLICY IF EXISTS tenant_isolation ON audit_logs;
CREATE POLICY tenant_isolation ON audit_logs
    USING (tenant_id::text = current_setting('app.tenant_id', true));
