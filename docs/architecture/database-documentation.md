-- Comments for documentation
COMMENT ON TABLE cloud_accounts IS 'Stores AWS/Azure/GCP account credentials and metadata';
COMMENT ON TABLE compliance_frameworks IS 'Stores compliance framework definitions (ISO 27001, NIST CSF, PCI-DSS)';
COMMENT ON TABLE framework_controls IS 'Individual controls within each compliance framework';
COMMENT ON TABLE technical_checks IS 'Automated security checks that can be executed';
COMMENT ON TABLE control_check_mappings IS 'Maps compliance controls to technical checks (many-to-many)';
COMMENT ON TABLE assessment_scans IS 'Records of compliance scan executions';
COMMENT ON TABLE scan_findings IS 'Individual check results from scans';
COMMENT ON TABLE compliance_scores IS 'Aggregated compliance scores per framework per scan';
