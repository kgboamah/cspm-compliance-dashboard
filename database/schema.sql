-- CSPM Compliance Dashboard Database Schema
-- PostgreSQL 15

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: Cloud Accounts
CREATE TABLE cloud_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_name VARCHAR(255) NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL CHECK (cloud_provider IN ('AWS', 'Azure', 'GCP')),
    account_id VARCHAR(225) NOT NULL UNIQUE,
    credentials JSONB DEFAULT '{}'::jsonb NOT NULL,
    regions JSONB DEFAULT '[]'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_scanned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Compliance Frameworks
CREATE TABLE compliance_frameworks (
    id SERIAL PRIMARY KEY,
    framework_name VARCHAR(100) NOT NULL,
    framework_version VARCHAR(50) NOT NULL,
    total_controls INTEGER,
    description TEXT,
    UNIQUE(framework_name, framework_version)
);

-- Table 3: Framework Controls
CREATE TABLE framework_controls (
    id SERIAL PRIMARY KEY,
    framework_id INTEGER NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    control_id VARCHAR(50) NOT NULL,
    control_title VARCHAR(255) NOT NULL,
    control_description TEXT,
    control_category VARCHAR(100),
    severity VARCHAR(20) CHECK (severity IN ('Critical', 'High', 'Medium', 'Low')),
    UNIQUE(framework_id, control_id)
);

CREATE INDEX idx_framework_controls_framework_id ON framework_controls(framework_id);
CREATE INDEX idx_framework_controls_severity ON framework_controls(severity);

-- Table 4: Technical Checks
CREATE TABLE technical_checks (
    id SERIAL PRIMARY KEY,
    check_name VARCHAR(255) NOT NULL UNIQUE,
    check_description TEXT,
    cloud_provider VARCHAR(50) NOT NULL,
    cloud_service VARCHAR(100) NOT NULL,
    check_query JSONB,
    remediation_guidance TEXT,
    remediation_links TEXT[]
);

CREATE INDEX idx_technical_checks_cloud_provider ON technical_checks(cloud_provider);
CREATE INDEX idx_technical_checks_cloud_service ON technical_checks(cloud_service);

-- Table 5: Control-Check Mappings
CREATE TABLE control_check_mappings (
    id SERIAL PRIMARY KEY,
    control_id INTEGER NOT NULL REFERENCES framework_controls(id) ON DELETE CASCADE,
    check_id INTEGER NOT NULL REFERENCES technical_checks(id) ON DELETE CASCADE,
    UNIQUE(control_id, check_id)
);

CREATE INDEX idx_ccm_control_id ON control_check_mappings(control_id);
CREATE INDEX idx_ccm_check_id ON control_check_mappings(check_id);

-- Table 6: Assessment Scans
CREATE TABLE assessment_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES cloud_accounts(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL CHECK (scan_type IN ('Full', 'Incremental', 'Targeted')),
    scan_status VARCHAR(50) NOT NULL CHECK (scan_status IN ('Running', 'Completed', 'Failed', 'Cancelled')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_checks_run INTEGER DEFAULT 0,
    error_log TEXT
);

CREATE INDEX idx_assessment_scans_account_id ON assessment_scans(account_id);
CREATE INDEX idx_assessment_scans_status ON assessment_scans(scan_status);
CREATE INDEX idx_assessment_scans_started_at ON assessment_scans(started_at DESC);

-- Table 7: Scan Findings
CREATE TABLE scan_findings (
    id SERIAL PRIMARY KEY,
    scan_id UUID NOT NULL REFERENCES assessment_scans(id) ON DELETE CASCADE,
    check_id INTEGER NOT NULL REFERENCES technical_checks(id) ON DELETE CASCADE,
    resource_id VARCHAR(500) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    finding_status VARCHAR(20) NOT NULL CHECK (finding_status IN ('Pass', 'Fail', 'Error', 'N/A')),
    finding_details JSONB,
    risk_level VARCHAR(20) CHECK (risk_level IN ('Critical', 'High', 'Medium', 'Low', 'Info')),
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scan_findings_scan_id ON scan_findings(scan_id);
CREATE INDEX idx_scan_findings_check_id ON scan_findings(check_id);
CREATE INDEX idx_scan_findings_status ON scan_findings(finding_status);
CREATE INDEX idx_scan_findings_risk_level ON scan_findings(risk_level);
CREATE INDEX idx_scan_findings_resource_id ON scan_findings(resource_id);

-- Table 8: Compliance Scores
CREATE TABLE compliance_scores (
    id SERIAL PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES cloud_accounts(id) ON DELETE CASCADE,
    framework_id INTEGER NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    scan_id UUID NOT NULL REFERENCES assessment_scans(id) ON DELETE CASCADE,
    overall_score DECIMAL(5, 2) NOT NULL,
    controls_passed INTEGER DEFAULT 0,
    controls_failed INTEGER DEFAULT 0,
    controls_not_applicable INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    high_findings INTEGER DEFAULT 0,
    medium_findings INTEGER DEFAULT 0,
    low_findings INTEGER DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, framework_id, scan_id)
);

CREATE INDEX idx_compliance_scores_account_id ON compliance_scores(account_id);
CREATE INDEX idx_compliance_scores_framework_id ON compliance_scores(framework_id);
CREATE INDEX idx_compliance_scores_scan_id ON compliance_scores(scan_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to cloud_accounts
CREATE TRIGGER update_cloud_accounts_updated_at BEFORE UPDATE ON cloud_accounts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();