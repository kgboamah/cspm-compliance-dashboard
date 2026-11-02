-- Migration: Create audit_logs table
-- Location: Save as backend/migrations/005_create_audit_logs.sql

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    event_description TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);

-- Comments
COMMENT ON TABLE audit_logs IS 'Security audit trail for all user actions';
COMMENT ON COLUMN audit_logs.event_type IS 'Type of event: login, logout, mfa_enabled, password_changed, etc.';
COMMENT ON COLUMN audit_logs.event_category IS 'Category: authentication, account, security, admin';
COMMENT ON COLUMN audit_logs.status IS 'Event status: success, failure, warning';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional event-specific data in JSON format';
