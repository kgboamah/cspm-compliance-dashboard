"""
Remediation Guidance Mapping - EXPANDED
Location: backend/app/services/remediation_guidance.py

Comprehensive mapping of Prowler check IDs to actionable remediation steps
"""

REMEDIATION_GUIDE = {
    # ============================================
    # IAM SECURITY
    # ============================================
    "iam_root_mfa_enabled": {
        "title": "Root Account MFA Not Enabled",
        "severity": "CRITICAL",
        "description": "AWS root account does not have multi-factor authentication enabled",
        "impact": "Complete account takeover possible if credentials are compromised",
        "remediation_steps": [
            "Sign in to AWS Console as root user",
            "Navigate to IAM Dashboard → Security credentials",
            "Click 'Activate MFA' under Multi-factor authentication",
            "Follow the setup wizard to configure virtual or hardware MFA",
            "Store backup codes in a secure location"
        ],
        "aws_cli": "# Root MFA must be enabled via AWS Console\n# Go to: My Security Credentials → Multi-factor authentication (MFA)",
        "terraform": "# Not applicable - must be configured manually via Console",
        "prevention": "Enable MFA immediately upon account creation; use hardware MFA for production accounts"
    },
    
    "iam_root_hardware_mfa_enabled": {
        "title": "Root Account Hardware MFA Not Enabled",
        "severity": "CRITICAL",
        "description": "Root account uses virtual MFA instead of hardware MFA device",
        "impact": "Virtual MFA is less secure than hardware tokens; phishing attacks possible",
        "remediation_steps": [
            "Purchase a FIDO2 hardware security key (e.g., YubiKey)",
            "Sign in as root user",
            "Navigate to My Security Credentials → MFA",
            "Deactivate current virtual MFA",
            "Activate hardware MFA device",
            "Store the device in a secure physical location"
        ],
        "aws_cli": "# Root Hardware MFA must be enabled via AWS Console",
        "terraform": "# Not applicable - must be configured manually",
        "prevention": "Use hardware MFA for all production root accounts; maintain backup device"
    },
    
    "iam_user_mfa_enabled_console_access": {
        "title": "IAM User with Console Access Has No MFA",
        "severity": "HIGH",
        "description": "IAM user can access AWS Console without multi-factor authentication",
        "impact": "Account compromise from stolen credentials",
        "remediation_steps": [
            "Identify users without MFA using IAM credential report",
            "Require all console users to enable MFA",
            "Use IAM policy to deny actions when MFA is not present",
            "Consider AWS SSO with enforced MFA instead of IAM users"
        ],
        "aws_cli": """# Get credential report to identify users without MFA
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d > credential_report.csv

# Attach policy requiring MFA
aws iam put-user-policy --user-name {resource_id} --policy-name RequireMFA --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Deny",
    "NotAction": ["iam:CreateVirtualMFADevice","iam:EnableMFADevice"],
    "Resource": "*",
    "Condition": {"BoolIfExists": {"aws:MultiFactorAuthPresent": "false"}}
  }]
}'""",
        "terraform": """resource "aws_iam_user_policy" "require_mfa" {
  name = "RequireMFA"
  user = "{resource_id}"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Deny"
      NotAction = ["iam:*"]
      Resource = "*"
      Condition = {
        BoolIfExists = {"aws:MultiFactorAuthPresent" = "false"}
      }
    }]
  })
}""",
        "prevention": "Use AWS SSO with enforced MFA; eliminate long-lived IAM users"
    },

    "iam_password_policy_minimum_length_14": {
        "title": "IAM Password Policy Does Not Require 14+ Characters",
        "severity": "MEDIUM",
        "description": "Password policy allows passwords shorter than 14 characters",
        "impact": "Weak passwords vulnerable to brute force attacks",
        "remediation_steps": [
            "Update IAM password policy to require minimum 14 characters",
            "Enforce uppercase, lowercase, numbers, and symbols",
            "Set password expiration to 90 days",
            "Prevent password reuse (24 previous passwords)"
        ],
        "aws_cli": """aws iam update-account-password-policy \\
  --minimum-password-length 14 \\
  --require-symbols \\
  --require-numbers \\
  --require-uppercase-characters \\
  --require-lowercase-characters \\
  --max-password-age 90 \\
  --password-reuse-prevention 24""",
        "terraform": """resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 14
  require_lowercase_characters   = true
  require_uppercase_characters   = true
  require_numbers                = true
  require_symbols                = true
  max_password_age              = 90
  password_reuse_prevention     = 24
}""",
        "prevention": "Enforce strong password policy from day one; migrate to SSO"
    },

    # ============================================
    # CLOUDTRAIL & LOGGING
    # ============================================
    "cloudtrail_multi_region_enabled": {
        "title": "CloudTrail Not Enabled in All Regions",
        "severity": "HIGH",
        "description": "CloudTrail is not logging API activity across all AWS regions",
        "impact": "Blind spots in audit trail; cannot detect unauthorized activity in some regions",
        "remediation_steps": [
            "Create a new CloudTrail trail or update existing one",
            "Enable 'Apply trail to all regions'",
            "Enable log file validation",
            "Configure S3 bucket with proper access controls",
            "Enable CloudWatch Logs integration for real-time monitoring"
        ],
        "aws_cli": """aws cloudtrail create-trail \\
  --name organization-trail \\
  --s3-bucket-name cloudtrail-logs-bucket \\
  --is-multi-region-trail \\
  --enable-log-file-validation

aws cloudtrail start-logging --name organization-trail""",
        "terraform": """resource "aws_cloudtrail" "main" {
  name                          = "organization-trail"
  s3_bucket_name               = aws_s3_bucket.cloudtrail.id
  is_multi_region_trail        = true
  enable_log_file_validation   = true
  include_global_service_events = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}""",
        "prevention": "Enable organization-wide CloudTrail at account creation"
    },

    # ============================================
    # EC2 & NETWORKING
    # ============================================
    "ec2_ebs_default_encryption": {
        "title": "EBS Default Encryption Not Enabled",
        "severity": "HIGH",
        "description": "New EBS volumes are not encrypted by default",
        "impact": "Unencrypted data at rest; compliance violations (HIPAA, PCI-DSS)",
        "remediation_steps": [
            "Enable EBS encryption by default in each region",
            "Existing unencrypted volumes must be manually encrypted",
            "Create encrypted snapshots and restore as new encrypted volumes"
        ],
        "aws_cli": """# Enable default EBS encryption in current region
aws ec2 enable-ebs-encryption-by-default

# Verify
aws ec2 get-ebs-encryption-by-default""",
        "terraform": """resource "aws_ebs_encryption_by_default" "enabled" {
  enabled = true
}

resource "aws_ebs_default_kms_key" "default" {
  key_arn = aws_kms_key.ebs.arn
}""",
        "prevention": "Enable in all regions via AWS Config conformance pack"
    },

    "ec2_networkacl_allow_ingress_tcp_port_22": {
        "title": "Network ACL Allows SSH From Internet",
        "severity": "HIGH",
        "description": "Network ACL allows TCP port 22 (SSH) from 0.0.0.0/0",
        "impact": "Brute force attacks; unauthorized access attempts",
        "remediation_steps": [
            "Review Network ACL inbound rules",
            "Remove rules allowing 0.0.0.0/0 on port 22",
            "Add specific IP ranges for authorized SSH access",
            "Use AWS Systems Manager Session Manager instead of SSH"
        ],
        "aws_cli": """# List Network ACL rules
aws ec2 describe-network-acls --network-acl-ids {resource_id}

# Delete unrestricted SSH rule (replace RULE_NUMBER)
aws ec2 delete-network-acl-entry \\
  --network-acl-id {resource_id} \\
  --rule-number RULE_NUMBER \\
  --ingress""",
        "terraform": """resource "aws_network_acl_rule" "deny_ssh_from_internet" {
  network_acl_id = "{resource_id}"
  rule_number    = 100
  egress         = false
  protocol       = "tcp"
  rule_action    = "deny"
  cidr_block     = "0.0.0.0/0"
  from_port      = 22
  to_port        = 22
}""",
        "prevention": "Use security groups instead of NACLs for granular control; eliminate SSH access"
    },

    "ec2_securitygroup_default_restrict_traffic": {
        "title": "Default Security Group Allows Traffic",
        "severity": "MEDIUM",
        "description": "Default VPC security group has not been hardened",
        "impact": "Resources using default SG may have unintended exposure",
        "remediation_steps": [
            "Identify default security groups in all VPCs",
            "Remove all inbound and outbound rules",
            "Ensure no EC2 instances use the default security group",
            "Create purpose-specific security groups instead"
        ],
        "aws_cli": """# Find default security groups
aws ec2 describe-security-groups --filters Name=group-name,Values=default

# Remove all inbound rules from default SG
aws ec2 revoke-security-group-ingress \\
  --group-id {resource_id} \\
  --ip-permissions '[...]'

# Remove all outbound rules
aws ec2 revoke-security-group-egress \\
  --group-id {resource_id} \\
  --ip-permissions '[...]'""",
        "terraform": """# Harden default security group
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  
  # No ingress rules
  ingress = []
  
  # No egress rules
  egress = []
}""",
        "prevention": "Never use default security groups; create purpose-specific groups"
    },

    # ============================================
    # MONITORING & DETECTION
    # ============================================
    "guardduty_is_enabled": {
        "title": "GuardDuty Not Enabled",
        "severity": "HIGH",
        "description": "AWS GuardDuty threat detection is not enabled in this region",
        "impact": "Cannot detect malicious activity, compromised instances, or reconnaissance",
        "remediation_steps": [
            "Enable GuardDuty in all regions",
            "Configure GuardDuty to send findings to Security Hub",
            "Set up EventBridge rules to alert on high/critical findings",
            "Enable S3 Protection and EKS Protection features"
        ],
        "aws_cli": """# Enable GuardDuty
aws guardduty create-detector --enable

# Enable S3 Protection
aws guardduty update-detector \\
  --detector-id DETECTOR_ID \\
  --data-sources S3Logs={Enable=true}""",
        "terraform": """resource "aws_guardduty_detector" "main" {
  enable = true
  
  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
  }
}""",
        "prevention": "Enable GuardDuty organization-wide at account creation"
    },

    "config_recorder_all_regions_enabled": {
        "title": "AWS Config Not Enabled in All Regions",
        "severity": "MEDIUM",
        "description": "AWS Config is not recording resource configurations across all regions",
        "impact": "Cannot track configuration changes; compliance auditing gaps",
        "remediation_steps": [
            "Enable AWS Config in all regions",
            "Configure S3 bucket for configuration snapshots",
            "Enable recording of all resource types",
            "Set up Config Rules for automated compliance checks"
        ],
        "aws_cli": """# Create Config configuration recorder
aws configservice put-configuration-recorder \\
  --configuration-recorder name=default,roleARN=arn:aws:iam::ACCOUNT:role/config-role

# Create delivery channel
aws configservice put-delivery-channel \\
  --delivery-channel name=default,s3BucketName=config-bucket

# Start recording
aws configservice start-configuration-recorder --configuration-recorder-name default""",
        "terraform": """resource "aws_config_configuration_recorder" "main" {
  name     = "default"
  role_arn = aws_iam_role.config.arn
  
  recording_group {
    all_supported = true
    include_global_resource_types = true
  }
}

resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true
}""",
        "prevention": "Deploy AWS Config via CloudFormation StackSets organization-wide"
    },

    # ============================================
    # S3 SECURITY
    # ============================================
    "s3_bucket_public_access": {
        "title": "S3 Bucket Has Public Access",
        "severity": "CRITICAL",
        "description": "S3 bucket is publicly accessible, potentially exposing sensitive data",
        "impact": "Data breach; unauthorized access to confidential information",
        "remediation_steps": [
            "Review bucket ACLs and bucket policies",
            "Enable S3 Block Public Access",
            "Remove any 'AllUsers' or 'AuthenticatedUsers' grants",
            "Implement least-privilege bucket policies"
        ],
        "aws_cli": """# Block all public access
aws s3api put-public-access-block \\
  --bucket {resource_id} \\
  --public-access-block-configuration \\
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true""",
        "terraform": """resource "aws_s3_bucket_public_access_block" "example" {
  bucket = "{resource_id}"
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}""",
        "prevention": "Enable S3 Block Public Access at account level"
    }
}

def get_remediation(check_id: str, resource_id: str = None) -> dict:
    """
    Get remediation guidance for a specific check
    
    Args:
        check_id: Prowler check identifier
        resource_id: Optional resource identifier to customize commands
    
    Returns:
        Dictionary with remediation guidance
    """
    # Try exact match first
    guidance = REMEDIATION_GUIDE.get(check_id)
    
    if not guidance:
        # Try partial match
        for key, value in REMEDIATION_GUIDE.items():
            if key in check_id or check_id in key:
                guidance = value
                break
    
    if not guidance:
        # Return generic guidance
        return {
            "title": f"Security Finding: {check_id}",
            "severity": "UNKNOWN",
            "description": "Security issue detected by compliance scan",
            "impact": "This finding indicates a deviation from security best practices",
            "remediation_steps": [
                "Review the specific check documentation in Prowler",
                "Consult AWS Well-Architected Framework Security Pillar",
                "Apply principle of least privilege",
                "Enable logging and monitoring for this resource",
                "Implement defense-in-depth security controls"
            ],
            "aws_cli": f"# Remediation steps for {check_id}\n# Refer to AWS documentation for specific guidance",
            "terraform": f"# Terraform configuration for {check_id}\n# Refer to AWS provider documentation",
            "prevention": "Follow AWS security best practices; use AWS Config for continuous compliance"
        }
    
    # Customize with resource_id if provided
    if resource_id:
        customized = guidance.copy()
        for key in ['aws_cli', 'terraform']:
            if key in customized:
                customized[key] = customized[key].replace('{resource_id}', resource_id)
        return customized
    
    return guidance
