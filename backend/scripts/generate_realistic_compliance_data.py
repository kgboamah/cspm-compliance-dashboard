"""
Generate Realistic Compliance Data for CSPM Dashboard
Location: backend/scripts/generate_realistic_compliance_data.py

Creates 4 customer profiles with realistic compliance scores:
- Startup: ~30% compliance
- SMB: ~60% compliance  
- Enterprise: ~80% compliance
- Financial Services: ~85% compliance
"""
import psycopg2
from psycopg2.extras import execute_values
import random
from datetime import datetime, timedelta
import uuid

# Database connection (DOCKER CONFIG)
DB_CONFIG = {
    'host': 'postgres',  # Docker service name, NOT localhost!
    'port': 5432,
    'database': 'cspm_db',
    'user': 'cspm_user',
    'password': 'cspm_password'
}

# Customer profiles with realistic compliance levels
CUSTOMER_PROFILES = {
    'startup': {
        'name': 'TechStart Inc',
        'pass_rate': 0.30,  # 30% compliance
        'description': 'Early-stage startup, limited security resources'
    },
    'smb': {
        'name': 'MidSize Corp',
        'pass_rate': 0.60,  # 60% compliance
        'description': 'Growing SMB with dedicated IT team'
    },
    'enterprise': {
        'name': 'GlobalTech Enterprise',
        'pass_rate': 0.80,  # 80% compliance
        'description': 'Large enterprise with mature security program'
    },
    'financial': {
        'name': 'SecureBank Financial',
        'pass_rate': 0.85,  # 85% compliance
        'description': 'Financial services with strict compliance requirements'
    }
}


def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


def get_existing_checks(conn):
    """Get all technical checks from database"""
    cur = conn.cursor()
    cur.execute("SELECT id, check_name FROM technical_checks ORDER BY id;")
    checks = cur.fetchall()
    cur.close()
    print(f"📋 Found {len(checks)} technical checks")
    return checks


def create_cloud_account(conn, profile_name, profile_data):
    """Create a cloud account for the customer profile"""
    cur = conn.cursor()
    
    # Generate UUIDs and AWS account ID
    cloud_account_uuid = str(uuid.uuid4())  # This is the primary key 'id'
    aws_account_number = f"{random.randint(100000000000, 999999999999)}"  # This is 'account_id'
    
    cur.execute("""
        INSERT INTO cloud_accounts 
        (id, account_name, cloud_provider, account_id, regions, is_active, credentials, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        cloud_account_uuid,
        f"{profile_data['name']} - AWS Account",
        'AWS',
        aws_account_number,
        '["us-east-1", "us-west-2"]',  # Default regions as JSONB
        True,
        '{}',  # Empty credentials JSONB
        datetime.utcnow()
    ))
    
    returned_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    print(f"✅ Created cloud account: {profile_data['name']} (ID: {returned_id})")
    return returned_id


def create_assessment_scan(conn, account_id, profile_name):
    """Create an assessment scan for the account"""
    cur = conn.cursor()
    
    scan_id = str(uuid.uuid4())
    completed_at = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
    started_at = completed_at - timedelta(minutes=random.randint(10, 30))
    
    cur.execute("""
        INSERT INTO assessment_scans
        (id, account_id, scan_type, scan_status, started_at, completed_at, total_checks_run)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        scan_id,
        account_id,
        'Full Compliance Scan',
        'Completed',
        started_at,
        completed_at,
        67  # Number of technical checks we have
    ))
    
    scan_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    print(f"✅ Created assessment scan for {profile_name}: {scan_id}")
    return scan_id


def generate_scan_findings(conn, scan_id, checks, pass_rate):
    """Generate realistic scan findings based on pass rate"""
    cur = conn.cursor()
    
    findings = []
    
    for check_id, check_name in checks:
        # Determine if this check passes based on pass_rate
        passes = random.random() < pass_rate
        
        finding_status = 'Pass' if passes else 'Fail'
        
        # Randomize risk level for each finding
        risk_level = random.choice(['Critical', 'High', 'Medium', 'Low'])
        
        # Create finding
        findings.append((
            scan_id,
            check_id,
            f"resource-{check_id}-{random.randint(1000, 9999)}",  # resource_id
            random.choice(['S3', 'EC2', 'IAM', 'RDS', 'Lambda', 'VPC']),  # resource_type
            finding_status,
            risk_level,
            None,  # finding_details (can be JSON)
            datetime.utcnow()
        ))
    
    # Bulk insert findings
    execute_values(
        cur,
        """
        INSERT INTO scan_findings 
        (scan_id, check_id, resource_id, resource_type, finding_status, risk_level, finding_details, discovered_at)
        VALUES %s
        """,
        findings
    )
    
    conn.commit()
    cur.close()
    
    passed = sum(1 for f in findings if f[4] == 'Pass')
    failed = sum(1 for f in findings if f[4] == 'Fail')
    
    print(f"✅ Generated {len(findings)} findings: {passed} Pass, {failed} Fail ({pass_rate*100:.0f}% compliance)")
    
    return passed, failed


def calculate_compliance_scores(conn, scan_id, account_id, passed, failed):
    """Calculate compliance scores for all frameworks"""
    cur = conn.cursor()
    
    # Get all frameworks
    cur.execute("SELECT id, framework_name FROM compliance_frameworks;")
    frameworks = cur.fetchall()
    
    total_checks = passed + failed
    overall_score = (passed / total_checks * 100) if total_checks > 0 else 0
    
    # Count findings by severity
    cur.execute("""
        SELECT risk_level, COUNT(*)
        FROM scan_findings
        WHERE scan_id = %s AND finding_status = 'Fail'
        GROUP BY risk_level;
    """, (scan_id,))
    
    severity_counts = {row[0]: row[1] for row in cur.fetchall()}
    
    critical_findings = severity_counts.get('Critical', 0)
    high_findings = severity_counts.get('High', 0)
    medium_findings = severity_counts.get('Medium', 0)
    low_findings = severity_counts.get('Low', 0)
    
    # Create compliance scores for each framework
    for framework_id, framework_name in frameworks:
        # Slightly vary scores by framework (±5%)
        framework_variation = random.uniform(0.90, 1.10)
        framework_score = min(100, max(0, overall_score * framework_variation))
        
        # Distribute pass/fail across frameworks
        framework_passed = int(passed * random.uniform(0.8, 1.2))
        framework_failed = int(failed * random.uniform(0.8, 1.2))
        framework_not_applicable = random.randint(0, 10)
        
        cur.execute("""
            INSERT INTO compliance_scores
            (account_id, framework_id, scan_id, overall_score, 
             controls_passed, controls_failed, controls_not_applicable,
             critical_findings, high_findings, medium_findings, low_findings,
             calculated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            account_id,
            framework_id,
            scan_id,
            round(framework_score, 2),
            framework_passed,
            framework_failed,
            framework_not_applicable,
            critical_findings,
            high_findings,
            medium_findings,
            low_findings,
            datetime.utcnow()
        ))
        
        print(f"  📊 {framework_name}: {framework_score:.1f}% (Passed: {framework_passed}, Failed: {framework_failed})")
    
    conn.commit()
    cur.close()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 CSPM Compliance Data Generator")
    print("="*70 + "\n")
    
    # Connect to database
    conn = connect_db()
    
    # Get existing technical checks
    checks = get_existing_checks(conn)
    
    if not checks:
        print("❌ No technical checks found! Please run scans first to populate checks.")
        return
    
    print(f"\n{'='*70}")
    print("📋 Generating Data for 4 Customer Profiles")
    print(f"{'='*70}\n")
    
    # Generate data for each customer profile
    for profile_name, profile_data in CUSTOMER_PROFILES.items():
        print(f"\n{'─'*70}")
        print(f"🏢 Creating: {profile_data['name']} ({profile_name.upper()})")
        print(f"   Target Compliance: {profile_data['pass_rate']*100:.0f}%")
        print(f"   {profile_data['description']}")
        print(f"{'─'*70}\n")
        
        # Create cloud account
        account_id = create_cloud_account(conn, profile_name, profile_data)
        
        # Create assessment scan
        scan_id = create_assessment_scan(conn, account_id, profile_data['name'])
        
        # Generate findings
        passed, failed = generate_scan_findings(
            conn, 
            scan_id, 
            checks, 
            profile_data['pass_rate']
        )
        
        # Calculate compliance scores
        calculate_compliance_scores(conn, scan_id, account_id, passed, failed)
        
        print(f"\n✅ {profile_data['name']} data generation complete!\n")
    
    conn.close()
    
    print("\n" + "="*70)
    print("🎉 SUCCESS! All customer profiles created with realistic data!")
    print("="*70 + "\n")
    print("📊 Summary:")
    print("  - 4 customer profiles created")
    print("  - Compliance scores range from 30% to 85%")
    print("  - Realistic pass/fail distributions")
    print("  - Ready for dashboard demonstration!")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
