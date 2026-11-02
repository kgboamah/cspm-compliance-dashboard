"""
Generate Multiple Historical Scans with Recurring Findings
Location: backend/scripts/generate_historical_scans.py

Creates 5 scans per account over 2 weeks showing:
- Recurring findings (same issues appearing multiple times)
- Progressive remediation (some findings get fixed)
- Security drift (new findings appear)
- Realistic compliance trends
"""
import psycopg2
from psycopg2.extras import execute_values
import random
from datetime import datetime, timedelta
import uuid

# Database connection (DOCKER CONFIG)
DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'cspm_db',
    'user': 'cspm_user',
    'password': 'cspm_password'
}

# Account profiles with improvement trajectories
ACCOUNT_TRAJECTORIES = {
    'TechStart Inc': {
        'baseline_pass_rate': 0.30,
        'improvement_per_scan': 0.02,  # Slow improvement
        'description': 'Startup gradually addressing security gaps'
    },
    'MidSize Corp': {
        'baseline_pass_rate': 0.60,
        'improvement_per_scan': 0.03,  # Moderate improvement
        'description': 'SMB with active security program'
    },
    'GlobalTech Enterprise': {
        'baseline_pass_rate': 0.80,
        'improvement_per_scan': 0.01,  # Already good, minor improvements
        'description': 'Enterprise maintaining high compliance'
    },
    'SecureBank Financial': {
        'baseline_pass_rate': 0.85,
        'improvement_per_scan': 0.005,  # Very small improvements, already excellent
        'description': 'Financial services with mature security'
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


def get_accounts(conn):
    """Get the 4 new cloud accounts we created"""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, account_name 
        FROM cloud_accounts 
        WHERE account_name LIKE '%TechStart%' 
           OR account_name LIKE '%MidSize%'
           OR account_name LIKE '%GlobalTech%'
           OR account_name LIKE '%SecureBank%'
        ORDER BY account_name;
    """)
    accounts = cur.fetchall()
    cur.close()
    print(f"📋 Found {len(accounts)} accounts to generate historical scans for")
    return accounts


def get_technical_checks(conn):
    """Get all technical checks"""
    cur = conn.cursor()
    cur.execute("SELECT id, check_name FROM technical_checks ORDER BY id;")
    checks = cur.fetchall()
    cur.close()
    return checks


def delete_existing_scans(conn, account_id):
    """Delete existing scans and related data for an account"""
    cur = conn.cursor()
    
    # Get scan IDs
    cur.execute("SELECT id FROM assessment_scans WHERE account_id = %s;", (account_id,))
    scan_ids = [row[0] for row in cur.fetchall()]
    
    if scan_ids:
        # Delete compliance scores
        cur.execute("DELETE FROM compliance_scores WHERE account_id = %s;", (account_id,))
        
        # Delete scan findings (cascades via foreign key)
        for scan_id in scan_ids:
            cur.execute("DELETE FROM scan_findings WHERE scan_id = %s;", (scan_id,))
        
        # Delete scans
        cur.execute("DELETE FROM assessment_scans WHERE account_id = %s;", (account_id,))
        
        conn.commit()
        print(f"  🗑️  Deleted {len(scan_ids)} existing scans")
    
    cur.close()


def create_historical_scan(conn, account_id, scan_date, scan_number):
    """Create a historical scan"""
    cur = conn.cursor()
    
    scan_id = str(uuid.uuid4())
    started_at = scan_date
    completed_at = scan_date + timedelta(minutes=random.randint(15, 25))
    
    cur.execute("""
        INSERT INTO assessment_scans
        (id, account_id, scan_type, scan_status, started_at, completed_at, total_checks_run)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        scan_id,
        account_id,
        f'Scheduled Scan #{scan_number}',
        'Completed',
        started_at,
        completed_at,
        67
    ))
    
    scan_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    return scan_id


def generate_findings_with_recurrence(conn, account_id, scans_data, checks, base_pass_rate, improvement_rate):
    """
    Generate findings across multiple scans with:
    - Recurring findings (same resource_id fails multiple times)
    - Progressive fixes (some findings transition from Fail to Pass)
    - New findings (some appear in later scans)
    """
    
    # Track which checks fail for which resources across scans
    # Structure: {check_id: {resource_id: [scan1_status, scan2_status, ...]}}
    check_resource_history = {}
    
    num_scans = len(scans_data)
    
    # Initialize resource IDs for each check (consistent across scans)
    for check_id, check_name in checks:
        # Each check has 1-3 resources
        num_resources = random.randint(1, 3)
        check_resource_history[check_id] = {}
        
        for i in range(num_resources):
            resource_id = f"arn:aws::{check_id}:resource-{random.randint(1000, 9999)}"
            check_resource_history[check_id][resource_id] = []
    
    # Generate findings for each scan
    all_findings = []
    
    for scan_idx, (scan_id, scan_date) in enumerate(scans_data):
        # Calculate pass rate for this scan (improves over time)
        current_pass_rate = min(0.95, base_pass_rate + (improvement_rate * scan_idx))
        
        scan_findings = []
        
        for check_id, check_name in checks:
            resources = check_resource_history[check_id]
            
            for resource_id in resources.keys():
                # Determine status for this resource in this scan
                
                # If it failed before, there's a chance it gets fixed
                previous_statuses = check_resource_history[check_id][resource_id]
                
                if previous_statuses:
                    last_status = previous_statuses[-1]
                    
                    if last_status == 'Fail':
                        # 20% chance of remediation in next scan
                        if random.random() < 0.20:
                            status = 'Pass'
                        else:
                            status = 'Fail'  # Still failing (recurring)
                    else:
                        # Once fixed, stays fixed (95% of the time)
                        status = 'Pass' if random.random() < 0.95 else 'Fail'
                else:
                    # First scan - use base pass rate
                    status = 'Pass' if random.random() < current_pass_rate else 'Fail'
                
                # Record status
                check_resource_history[check_id][resource_id].append(status)
                
                # Generate finding
                risk_level = random.choice(['Critical', 'High', 'Medium', 'Low'])
                
                scan_findings.append((
                    scan_id,
                    check_id,
                    resource_id,
                    random.choice(['S3', 'EC2', 'IAM', 'RDS', 'Lambda', 'VPC']),
                    status,
                    risk_level,
                    None,
                    scan_date
                ))
        
        all_findings.extend(scan_findings)
        
        passed = sum(1 for f in scan_findings if f[4] == 'Pass')
        failed = sum(1 for f in scan_findings if f[4] == 'Fail')
        
        print(f"    Scan {scan_idx + 1}: {passed} Pass, {failed} Fail ({current_pass_rate*100:.1f}% target)")
    
    # Bulk insert all findings
    cur = conn.cursor()
    execute_values(
        cur,
        """
        INSERT INTO scan_findings 
        (scan_id, check_id, resource_id, resource_type, finding_status, risk_level, finding_details, discovered_at)
        VALUES %s
        """,
        all_findings
    )
    conn.commit()
    cur.close()
    
    return all_findings


def calculate_compliance_scores(conn, scan_id, account_id, scan_date):
    """Calculate compliance scores for a scan"""
    cur = conn.cursor()
    
    # Get all frameworks
    cur.execute("SELECT id, framework_name FROM compliance_frameworks;")
    frameworks = cur.fetchall()
    
    # Count findings
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE finding_status = 'Pass') as passed,
            COUNT(*) FILTER (WHERE finding_status = 'Fail') as failed,
            COUNT(*) FILTER (WHERE finding_status = 'Fail' AND risk_level = 'Critical') as critical,
            COUNT(*) FILTER (WHERE finding_status = 'Fail' AND risk_level = 'High') as high,
            COUNT(*) FILTER (WHERE finding_status = 'Fail' AND risk_level = 'Medium') as medium,
            COUNT(*) FILTER (WHERE finding_status = 'Fail' AND risk_level = 'Low') as low
        FROM scan_findings
        WHERE scan_id = %s;
    """, (scan_id,))
    
    result = cur.fetchone()
    passed, failed, critical, high, medium, low = result
    
    total = passed + failed
    overall_score = (passed / total * 100) if total > 0 else 0
    
    # Create scores for each framework
    for framework_id, framework_name in frameworks:
        framework_variation = random.uniform(0.90, 1.10)
        framework_score = min(100, max(0, overall_score * framework_variation))
        
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
            critical,
            high,
            medium,
            low,
            scan_date
        ))
    
    conn.commit()
    cur.close()


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 Historical Scans & Recurring Findings Generator")
    print("="*70 + "\n")
    
    conn = connect_db()
    accounts = get_accounts(conn)
    checks = get_technical_checks(conn)
    
    if not accounts:
        print("❌ No accounts found! Run generate_realistic_compliance_data.py first.")
        return
    
    print(f"\n{'='*70}")
    print("📋 Generating 5 Historical Scans Per Account")
    print(f"{'='*70}\n")
    
    now = datetime.utcnow()
    
    for account_id, account_name in accounts:
        # Extract base name (remove "- AWS Account")
        base_name = account_name.replace(' - AWS Account', '')
        
        if base_name not in ACCOUNT_TRAJECTORIES:
            print(f"⚠️  Skipping {account_name} - no trajectory defined")
            continue
        
        trajectory = ACCOUNT_TRAJECTORIES[base_name]
        
        print(f"\n{'─'*70}")
        print(f"🏢 {account_name}")
        print(f"   {trajectory['description']}")
        print(f"   Baseline: {trajectory['baseline_pass_rate']*100:.0f}%, Improvement: +{trajectory['improvement_per_scan']*100:.1f}% per scan")
        print(f"{'─'*70}\n")
        
        # Delete existing scans
        delete_existing_scans(conn, account_id)
        
        # Create 5 scans over 14 days
        scans_data = []
        for i in range(5):
            days_ago = 14 - (i * 3)  # Scans at day 14, 11, 8, 5, 2 ago
            scan_date = now - timedelta(days=days_ago, hours=random.randint(8, 18))
            scan_id = create_historical_scan(conn, account_id, scan_date, i + 1)
            scans_data.append((scan_id, scan_date))
            print(f"  ✅ Created scan #{i+1} on {scan_date.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"\n  📊 Generating findings with recurring patterns...")
        
        # Generate findings with recurrence
        generate_findings_with_recurrence(
            conn,
            account_id,
            scans_data,
            checks,
            trajectory['baseline_pass_rate'],
            trajectory['improvement_per_scan']
        )
        
        # Calculate compliance scores for each scan
        print(f"\n  📈 Calculating compliance scores...")
        for scan_id, scan_date in scans_data:
            calculate_compliance_scores(conn, scan_id, account_id, scan_date)
        
        print(f"\n✅ {account_name} complete!\n")
    
    conn.close()
    
    print("\n" + "="*70)
    print("🎉 SUCCESS! Historical scan data generated!")
    print("="*70 + "\n")
    print("📊 Summary:")
    print("  - 5 scans per account over 14 days")
    print("  - Recurring findings tracked across scans")
    print("  - Progressive compliance improvements")
    print("  - 20% remediation rate per scan for failed controls")
    print("  - Ready for Trends and Recurring Findings pages!")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
