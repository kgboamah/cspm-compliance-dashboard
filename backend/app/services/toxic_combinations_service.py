"""
Toxic Combinations Detection Service - MASSIVELY EXPANDED
Location: backend/app/services/toxic_combinations_service.py
Total Patterns: 30+ attack scenarios
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

class ToxicCombinationsService:
    """Service to detect dangerous combinations of security findings"""
    
    RISK_PATTERNS = [
        # TIER 1: CRITICAL - IMMEDIATE ACCOUNT TAKEOVER PATHS (Risk 90-98)
        {
            "id": "ROOT_ACCOUNT_EXPOSED",
            "name": "Root Account Active + No Hardware MFA",
            "severity": "CRITICAL",
            "risk_score": 98,
            "description": "Active root account without hardware MFA is the ultimate target for account takeover",
            "attack_path": [
                "Attacker phishes root account credentials",
                "Bypasses virtual MFA through device compromise",
                "Gains complete AWS account control",
                "Creates backdoor admin users, disables security controls"
            ],
            "required_findings": [
                {"check_pattern": ".*root.*hardware.*mfa.*", "min_severity": "Critical"},
                {"check_pattern": ".*root.*mfa.*enabled.*", "min_severity": "High"}
            ],
            "mitigation_priority": "IMMEDIATE - 12 hour SLA"
        },
        
        {
            "id": "DATA_EXFIL_PUBLIC_EC2_S3",
            "name": "Public EC2 with S3 Full Access",
            "severity": "CRITICAL",
            "risk_score": 95,
            "description": "Publicly accessible EC2 instance with IAM role granting full S3 access creates direct data exfiltration path",
            "attack_path": [
                "Attacker gains access to public EC2 instance via RCE",
                "Exploits IAM role credentials from instance metadata service",
                "Downloads entire S3 buckets containing PII/IP",
                "Exfiltrates terabytes of data without detection"
            ],
            "required_findings": [
                {"check_pattern": ".*ec2.*public.*|.*networkacl.*", "min_severity": "High"},
                {"check_pattern": ".*s3.*|.*iam.*role.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "IMMEDIATE - 24 hour SLA"
        },

        {
            "id": "LAMBDA_PRIVILEGE_ESCALATION",
            "name": "Lambda + IAM Privilege Escalation",
            "severity": "CRITICAL",
            "risk_score": 94,
            "description": "Lambda function with overpermissive IAM role can be exploited to escalate privileges across AWS services",
            "attack_path": [
                "Attacker invokes public/accessible Lambda function",
                "Lambda role has permissions to create IAM users, EC2 instances, or assume other roles",
                "Attacker creates new admin user or role",
                "Lateral movement to any AWS service in the account"
            ],
            "required_findings": [
                {"check_pattern": ".*lambda.*", "min_severity": "Medium"},
                {"check_pattern": ".*iam.*policy.*|.*iam.*role.*", "min_severity": "High"}
            ],
            "mitigation_priority": "IMMEDIATE - 12 hour SLA"
        },

        {
            "id": "UNRESTRICTED_CREDENTIALS_NO_ROTATION",
            "name": "Long-Lived Credentials Without Rotation",
            "severity": "CRITICAL",
            "risk_score": 93,
            "description": "Access keys that never rotate + no monitoring = undetected credential compromise for months",
            "attack_path": [
                "Attacker obtains old/leaked access keys",
                "Uses keys to access AWS services",
                "Keys have been valid for years (no rotation policy)",
                "Attacker maintains persistent access indefinitely"
            ],
            "required_findings": [
                {"check_pattern": ".*access.*key.*rotation.*|.*credential.*age.*", "min_severity": "High"},
                {"check_pattern": ".*iam.*user.*|.*access.*key.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "IMMEDIATE - 24 hour SLA"
        },

        # TIER 2: HIGH SEVERITY - MAJOR BREACH PATHS (Risk 85-89)
        {
            "id": "RDP_EXPOSED_NO_THREAT_DETECTION",
            "name": "RDP Exposed + No Threat Detection",
            "severity": "CRITICAL",
            "risk_score": 91,
            "description": "Remote Desktop Protocol exposed to internet without GuardDuty or threat detection",
            "attack_path": [
                "Attacker scans for open RDP ports (3389) on internet",
                "Launches automated brute force attack against Windows instances",
                "No GuardDuty alerts on suspicious login attempts",
                "Gains access to production Windows servers with admin access"
            ],
            "required_findings": [
                {"check_pattern": ".*3389.*|.*rdp.*", "min_severity": "High"},
                {"check_pattern": ".*guardduty.*enabled.*", "min_severity": "High"}
            ],
            "mitigation_priority": "IMMEDIATE - 24 hour SLA"
        },

        {
            "id": "DATA_LEAK_CLOUDTRAIL_S3",
            "name": "S3 Data Events Not Logged",
            "severity": "CRITICAL",
            "risk_score": 88,
            "description": "S3 bucket access not logged by CloudTrail prevents detection of data exfiltration",
            "attack_path": [
                "Attacker gains access to S3 bucket (bucket policy, compromised credentials)",
                "Downloads sensitive customer data or intellectual property",
                "No CloudTrail S3 data events logged",
                "Data breach discovered weeks later through external sources"
            ],
            "required_findings": [
                {"check_pattern": ".*cloudtrail.*s3.*dataevents.*", "min_severity": "High"},
                {"check_pattern": ".*s3.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "IMMEDIATE - 48 hour SLA"
        },

        {
            "id": "SSH_BRUTEFORCE_NO_MFA",
            "name": "Internet SSH Access + No MFA",
            "severity": "CRITICAL",
            "risk_score": 90,
            "description": "SSH accessible from internet combined with IAM users lacking MFA enables credential-based attacks",
            "attack_path": [
                "Attacker scans for SSH ports open to internet (port 22)",
                "Brute forces or uses leaked credentials",
                "Gains console access without MFA challenge",
                "Establishes persistence in production environment via reverse shell"
            ],
            "required_findings": [
                {"check_pattern": ".*networkacl.*ssh.*22.*", "min_severity": "High"},
                {"check_pattern": ".*iam.*mfa.*", "min_severity": "High"}
            ],
            "mitigation_priority": "IMMEDIATE - 48 hour SLA"
        },

        {
            "id": "NO_LOGGING_ADMIN_ACCESS",
            "name": "Admin Privileges Without Audit Trail",
            "severity": "HIGH",
            "risk_score": 85,
            "description": "Administrative access without CloudTrail logging prevents detection of malicious activity",
            "attack_path": [
                "Attacker compromises admin credentials",
                "Performs malicious actions (data deletion, resource creation, IAM changes)",
                "No audit trail exists to detect or investigate activities",
                "Attack goes unnoticed until damage is discovered"
            ],
            "required_findings": [
                {"check_pattern": ".*cloudtrail.*enabled.*", "min_severity": "High"},
                {"check_pattern": ".*iam.*root.*|.*admin.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        # TIER 3: HIGH - INFRASTRUCTURE EXPLOITATION (Risk 80-84)
        {
            "id": "UNENCRYPTED_STORAGE_BACKUP",
            "name": "Unencrypted Storage Without Backup",
            "severity": "HIGH",
            "risk_score": 82,
            "description": "Critical data stored unencrypted with no backup strategy creates ransomware vulnerability",
            "attack_path": [
                "Attacker gains access to unencrypted EBS volumes or S3 buckets",
                "Exfiltrates sensitive data (customer info, source code, trade secrets)",
                "Deploys ransomware to encrypt remaining data",
                "No backups exist for recovery - organization forced to pay ransom"
            ],
            "required_findings": [
                {"check_pattern": ".*ebs.*encryption.*|.*athena.*encryption.*|.*glue.*encryption.*", "min_severity": "Medium"},
                {"check_pattern": ".*backup.*vault.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 1 week SLA"
        },

        {
            "id": "EXPOSED_DATABASES_NO_AUTH",
            "name": "Publicly Accessible Database Without Authentication",
            "severity": "HIGH",
            "risk_score": 83,
            "description": "Database accessible from internet with weak or missing authentication",
            "attack_path": [
                "Attacker scans for open database ports (3306, 5432, 27017, etc.)",
                "Connects without credentials or with default credentials",
                "Dumps entire database containing customer PII",
                "Sells or leaks data on dark web marketplaces"
            ],
            "required_findings": [
                {"check_pattern": ".*rds.*|.*database.*|.*dynamodb.*", "min_severity": "High"},
                {"check_pattern": ".*securitygroup.*|.*networkacl.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 24 hour SLA"
        },

        {
            "id": "SECRETS_IN_CODE_NO_ROTATION",
            "name": "Hardcoded Secrets + No Rotation",
            "severity": "HIGH",
            "risk_score": 81,
            "description": "Database passwords, API keys, or AWS credentials hardcoded in application with no rotation",
            "attack_path": [
                "Attacker obtains application code through GitHub leak, container image, or backup",
                "Extracts hardcoded AWS credentials, DB passwords, or API keys",
                "Credentials never rotated, providing indefinite access",
                "Attacker accesses production databases and AWS services"
            ],
            "required_findings": [
                {"check_pattern": ".*secret.*|.*credential.*", "min_severity": "High"},
                {"check_pattern": ".*rotation.*|.*key.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 24 hour SLA"
        },

        {
            "id": "CONFIG_DRIFT_NO_DETECTION",
            "name": "No AWS Config + No Change Monitoring",
            "severity": "HIGH",
            "risk_score": 76,
            "description": "Lack of configuration tracking combined with no CloudWatch alarms prevents detection of unauthorized changes",
            "attack_path": [
                "Attacker gains limited AWS access (compromised IAM user)",
                "Makes subtle infrastructure changes (opens security groups, creates IAM policies)",
                "No configuration monitoring detects changes",
                "Attacker creates backdoors that persist undetected for months"
            ],
            "required_findings": [
                {"check_pattern": ".*config.*recorder.*enabled.*", "min_severity": "Medium"},
                {"check_pattern": ".*cloudwatch.*alarm.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 1 week SLA"
        },

        {
            "id": "WEAK_PASSWORD_NO_ROTATION",
            "name": "Weak Password Policy + No Rotation",
            "severity": "HIGH",
            "risk_score": 78,
            "description": "Weak password requirements combined with no expiration policy enables long-term credential compromise",
            "attack_path": [
                "Attacker obtains weak user password through brute force (8 chars, no uppercase required)",
                "Password never expires, allowing indefinite access",
                "Compromised account goes undetected for months or years",
                "Attacker maintains persistent backdoor access and escalates privileges"
            ],
            "required_findings": [
                {"check_pattern": ".*password.*policy.*length.*", "min_severity": "Medium"},
                {"check_pattern": ".*password.*expires.*90.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 1 week SLA"
        },

        # TIER 4: CRITICAL CONTROL GAPS (Risk 75-79)
        {
            "id": "PRIVILEGE_ESCALATION_ASSUME_ROLE",
            "name": "AssumeRole Permission Without Restrictions",
            "severity": "HIGH",
            "risk_score": 79,
            "description": "IAM users can assume privileged roles without conditions or MFA requirements",
            "attack_path": [
                "Attacker compromises standard IAM user",
                "Uses 'sts:AssumeRole' permission to assume admin role",
                "No MFA or conditions required for assumption",
                "Gains elevated privileges without additional authentication"
            ],
            "required_findings": [
                {"check_pattern": ".*assume.*role.*|.*sts.*", "min_severity": "High"},
                {"check_pattern": ".*iam.*policy.*", "min_severity": "High"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        {
            "id": "NO_MONITORING_HIGH_RISK",
            "name": "High-Risk Resources Without Monitoring",
            "severity": "HIGH",
            "risk_score": 80,
            "description": "Critical resources lack GuardDuty or real-time monitoring",
            "attack_path": [
                "Attacker compromises production resource (EC2, Lambda, RDS)",
                "Performs reconnaissance activities undetected",
                "Escalates privileges and moves laterally across infrastructure",
                "Maintains persistence without triggering any security alerts"
            ],
            "required_findings": [
                {"check_pattern": ".*guardduty.*enabled.*", "min_severity": "High"},
                {"check_pattern": ".*ec2.*|.*lambda.*|.*rds.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        {
            "id": "CROSS_ACCOUNT_TRUST_MISCONFIGURATION",
            "name": "Overpermissive Cross-Account Trust",
            "severity": "HIGH",
            "risk_score": 77,
            "description": "Cross-account IAM roles with overly permissive trust relationships enable lateral movement",
            "attack_path": [
                "Attacker compromises principal in trusted account",
                "Uses trust relationship to assume role in target account",
                "No external ID or additional conditions prevent abuse",
                "Gains access to sensitive resources in connected accounts"
            ],
            "required_findings": [
                {"check_pattern": ".*trust.*|.*cross.*account.*", "min_severity": "High"},
                {"check_pattern": ".*iam.*role.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        # TIER 5: PERSISTENCE & LATERAL MOVEMENT (Risk 72-74)
        {
            "id": "INSTANCE_PROFILE_OVERPERMISSION",
            "name": "EC2 Instance Profile with Admin Permissions",
            "severity": "HIGH",
            "risk_score": 74,
            "description": "EC2 instances with IAM profiles granting admin or overly broad permissions",
            "attack_path": [
                "Attacker compromises EC2 instance via SSH, RCE, or SSRF",
                "Queries instance metadata service for IAM credentials",
                "Uses credentials to access any AWS service in the account",
                "Escalates attack to data exfiltration or infrastructure destruction"
            ],
            "required_findings": [
                {"check_pattern": ".*ec2.*instance.*|.*instance.*profile.*", "min_severity": "Medium"},
                {"check_pattern": ".*iam.*policy.*admin.*", "min_severity": "High"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        {
            "id": "WILDCARD_PRINCIPAL_TRUST",
            "name": "Resource Policy with Wildcard Principal",
            "severity": "HIGH",
            "risk_score": 72,
            "description": "S3, SQS, SNS, or other resources trusting '*' (any) principal",
            "attack_path": [
                "Attacker from any AWS account or internet can access resource",
                "Reads sensitive data from S3 buckets, SQS messages, or SNS topics",
                "Potential for data exfiltration, privilege escalation, or DoS attacks",
                "No authentication required"
            ],
            "required_findings": [
                {"check_pattern": ".*principal.*|.*policy.*", "min_severity": "High"},
                {"check_pattern": ".*s3.*|.*sqs.*|.*sns.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 48 hour SLA"
        },

        {
            "id": "VPC_FLOW_LOGS_DISABLED",
            "name": "VPC Flow Logs Disabled + No Network Monitoring",
            "severity": "HIGH",
            "risk_score": 73,
            "description": "Network traffic not logged, preventing detection of lateral movement and data exfiltration",
            "attack_path": [
                "Attacker compromises instance in VPC",
                "Exfiltrates data to external IP without detection",
                "No network flow logs to audit traffic patterns",
                "Attacker escapes undetected with sensitive data"
            ],
            "required_findings": [
                {"check_pattern": ".*vpc.*flow.*log.*", "min_severity": "High"},
                {"check_pattern": ".*vpc.*|.*network.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 72 hour SLA"
        },

        # TIER 6: COMPLIANCE & REGULATORY (Risk 70-71)
        {
            "id": "ENCRYPTION_KEY_NO_ROTATION",
            "name": "KMS Keys Without Rotation Policy",
            "severity": "MEDIUM",
            "risk_score": 71,
            "description": "Master encryption keys never rotated increases blast radius if key is compromised",
            "attack_path": [
                "Attacker obtains or tricks attacker to use KMS key (through phishing or code leak)",
                "Decrypts all historical data encrypted with that key",
                "Years of encrypted data becomes readable",
                "Potential HIPAA, PCI, or GDPR violation"
            ],
            "required_findings": [
                {"check_pattern": ".*kms.*|.*encryption.*key.*", "min_severity": "High"},
                {"check_pattern": ".*rotation.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "HIGH - 1 week SLA"
        },

        {
            "id": "LOG_DELETION_NO_PROTECTION",
            "name": "CloudTrail Logs Deletable Without Protection",
            "severity": "MEDIUM",
            "risk_score": 70,
            "description": "CloudTrail logs can be deleted by attacker covering tracks of malicious activity",
            "attack_path": [
                "Attacker gains AWS credentials with S3 delete permissions",
                "Deletes CloudTrail logs from S3 bucket",
                "Covers tracks of data exfiltration, privilege escalation, or backdoor installation",
                "Forensic investigation impossible"
            ],
            "required_findings": [
                {"check_pattern": ".*cloudtrail.*", "min_severity": "High"},
                {"check_pattern": ".*s3.*bucket.*lock.*|.*mfa.*delete.*", "min_severity": "High"}
            ],
            "mitigation_priority": "HIGH - 1 week SLA"
        },

        # TIER 7: AUTOMATION & DETECTION GAPS (Risk 68-69)
        {
            "id": "NO_WAF_UNPROTECTED_ALB",
            "name": "Public ALB Without WAF Protection",
            "severity": "MEDIUM",
            "risk_score": 69,
            "description": "Internet-facing load balancer exposed to web attacks without WAF",
            "attack_path": [
                "Attacker scans ALB for web vulnerabilities (SQL injection, XSS, etc.)",
                "Exploits vulnerability in application",
                "No WAF to block or rate-limit malicious requests",
                "Gains access to application backend and database"
            ],
            "required_findings": [
                {"check_pattern": ".*alb.*|.*elb.*|.*load.*balancer.*", "min_severity": "Medium"},
                {"check_pattern": ".*waf.*", "min_severity": "High"}
            ],
            "mitigation_priority": "MEDIUM - 1 week SLA"
        },

        {
            "id": "SECRETS_MANAGER_NO_ROTATION",
            "name": "Secrets Manager Enabled But No Rotation",
            "severity": "MEDIUM",
            "risk_score": 68,
            "description": "Secrets stored but never rotated creates long-term exposure if compromised",
            "attack_path": [
                "Attacker obtains secret (via code repository, backup, or credentials leak)",
                "Secret stored in AWS Secrets Manager but rotation disabled",
                "Attacker maintains access indefinitely",
                "Secret not detected as compromised until much later"
            ],
            "required_findings": [
                {"check_pattern": ".*secrets.*manager.*", "min_severity": "Medium"},
                {"check_pattern": ".*rotation.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "MEDIUM - 2 weeks SLA"
        },

        # TIER 8: SUPPLY CHAIN & DEPENDENCIES (Risk 65-67)
        {
            "id": "ECR_VULNERABILITY_NO_SCANNING",
            "name": "ECR Images Without Vulnerability Scanning",
            "severity": "MEDIUM",
            "risk_score": 67,
            "description": "Container images deployed without vulnerability scanning creates deployment of known exploits",
            "attack_path": [
                "Developer pushes container image with outdated vulnerable libraries",
                "No ECR image scanning detects CVEs",
                "Image deployed to production ECS/EKS",
                "Attacker exploits known vulnerability in container"
            ],
            "required_findings": [
                {"check_pattern": ".*ecr.*|.*container.*registry.*", "min_severity": "Medium"},
                {"check_pattern": ".*vulnerability.*scan.*|.*image.*scan.*", "min_severity": "High"}
            ],
            "mitigation_priority": "MEDIUM - 1 week SLA"
        },

        {
            "id": "LAMBDA_EXTERNAL_LIBRARIES",
            "name": "Lambda with Unvetted External Dependencies",
            "severity": "MEDIUM",
            "risk_score": 66,
            "description": "Lambda functions importing third-party libraries without vetting could contain malware or backdoors",
            "attack_path": [
                "Developer uses npm package with supply chain compromise",
                "Package contains malware or backdoor code",
                "Lambda function executes malicious code",
                "Attacker steals credentials, exfiltrates data, or modifies behavior"
            ],
            "required_findings": [
                {"check_pattern": ".*lambda.*", "min_severity": "Medium"},
                {"check_pattern": ".*dependency.*|.*libraries.*", "min_severity": "Medium"}
            ],
            "mitigation_priority": "MEDIUM - 2 weeks SLA"
        },

        {
            "id": "SERVERLESS_NO_TIMEOUT",
            "name": "Lambda Without Appropriate Timeout Settings",
            "severity": "MEDIUM",
            "risk_score": 65,
            "description": "Lambda functions with excessive timeout (15 min max allowed) could enable resource exhaustion DoS",
            "attack_path": [
                "Attacker invokes Lambda function with specially crafted input",
                "Lambda enters infinite loop or heavy processing",
                "Runs until timeout, consuming compute resources",
                "Repeated invocations cause account-level resource exhaustion"
            ],
            "required_findings": [
                {"check_pattern": ".*lambda.*timeout.*", "min_severity": "Medium"},
                {"check_pattern": ".*lambda.*", "min_severity": "Low"}
            ],
            "mitigation_priority": "MEDIUM - 2 weeks SLA"
        }
    ]
    
    @staticmethod
    def detect_toxic_combinations(scan_id: str, db: Session) -> List[Dict]:
        """Detect toxic combinations for a given scan"""
        
        findings_query = text("""
            SELECT 
                sf.id as finding_id,
                tc.check_name,
                sf.risk_level,
                sf.resource_id,
                sf.resource_type,
                sf.finding_details
            FROM scan_findings sf
            JOIN technical_checks tc ON tc.id = sf.check_id
            WHERE sf.scan_id = :scan_id
            AND sf.finding_status = 'Fail'
        """)
        
        findings = db.execute(findings_query, {"scan_id": scan_id}).fetchall()
        
        if not findings:
            return []
        
        findings_list = []
        for f in findings:
            findings_list.append({
                "finding_id": f.finding_id,
                "check_name": f.check_name or "",
                "severity": f.risk_level,
                "resource_id": f.resource_id,
                "resource_type": f.resource_type,
                "finding_details": f.finding_details or {}
            })
        
        detected_combinations = []
        
        for pattern in ToxicCombinationsService.RISK_PATTERNS:
            matched_findings = ToxicCombinationsService._match_pattern(pattern, findings_list)
            
            if matched_findings:
                detected_combinations.append({
                    "combination_id": pattern["id"],
                    "name": pattern["name"],
                    "severity": pattern["severity"],
                    "risk_score": pattern["risk_score"],
                    "description": pattern["description"],
                    "attack_path": pattern["attack_path"],
                    "mitigation_priority": pattern["mitigation_priority"],
                    "matched_findings": matched_findings,
                    "finding_count": len(matched_findings),
                    "detected_at": datetime.utcnow().isoformat()
                })
        
        detected_combinations.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return detected_combinations
    
    @staticmethod
    def _match_pattern(pattern: Dict, findings: List[Dict]) -> Optional[List[Dict]]:
        """Check if a risk pattern matches the given findings"""
        matched_findings = []
        
        for required in pattern["required_findings"]:
            check_pattern = required["check_pattern"]
            min_severity = required["min_severity"]
            
            found = False
            for finding in findings:
                if re.search(check_pattern, finding["check_name"], re.IGNORECASE):
                    if ToxicCombinationsService._severity_meets_minimum(
                        finding["severity"], min_severity
                    ):
                        matched_findings.append({
                            "finding_id": finding["finding_id"],
                            "check_name": finding["check_name"],
                            "severity": finding["severity"],
                            "resource_id": finding["resource_id"],
                            "resource_type": finding["resource_type"]
                        })
                        found = True
                        break
            
            if not found:
                return None
        
        return matched_findings if matched_findings else None
    
    @staticmethod
    def _severity_meets_minimum(actual: str, minimum: str) -> bool:
        """Check if actual severity meets minimum requirement"""
        severity_levels = {
            "Critical": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Info": 1
        }
        
        return severity_levels.get(actual, 0) >= severity_levels.get(minimum, 0)
    
    @staticmethod
    def get_risk_summary(scan_id: str, db: Session) -> Dict:
        """Get summary statistics for toxic combinations"""
        combinations = ToxicCombinationsService.detect_toxic_combinations(scan_id, db)
        
        return {
            "total_combinations": len(combinations),
            "critical_combinations": len([c for c in combinations if c["severity"] == "CRITICAL"]),
            "high_combinations": len([c for c in combinations if c["severity"] == "HIGH"]),
            "medium_combinations": len([c for c in combinations if c["severity"] == "MEDIUM"]),
            "average_risk_score": sum(c["risk_score"] for c in combinations) / len(combinations) if combinations else 0,
            "highest_risk_score": max((c["risk_score"] for c in combinations), default=0),
            "requires_immediate_action": len([c for c in combinations if "IMMEDIATE" in c["mitigation_priority"]])
        }
