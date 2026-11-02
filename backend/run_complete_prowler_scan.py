"""
Complete Prowler Integration Test
This will run a full Prowler scan and populate the database with findings
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_complete_prowler_scan():
    """Run a complete end-to-end Prowler scan"""
    
    print("=" * 70)
    print("COMPLETE PROWLER SCAN TEST")
    print("=" * 70)
    
    # Step 1: Get or create cloud account
    print("\n1. Setting up cloud account...")
    
    # Check existing accounts
    response = requests.get(f"{BASE_URL}/api/cloud-accounts")
    if response.status_code == 200:
        accounts = response.json()
        if accounts:
            account = accounts[0]
            account_id = account['id']
            print(f"✓ Using existing account: {account['account_name']} ({account_id})")
        else:
            print("✗ No cloud accounts found. Please create one first.")
            print("\nTo create an account, use:")
            print("  POST /api/cloud-accounts")
            return
    else:
        print(f"✗ Failed to get accounts: {response.status_code}")
        return
    
    # Step 2: Start Prowler scan
    print(f"\n2. Starting Prowler scan for account {account_id}...")
    
    response = requests.post(
        f"{BASE_URL}/api/scans/start",
        json={"account_id": account_id}
    )
    
    if response.status_code != 200:
        print(f"✗ Failed to start scan: {response.text}")
        return
    
    data = response.json()
    scan_id = data['scan_id']
    print(f"✓ Scan started: {scan_id}")
    print(f"  Status: {data['status']}")
    
    # Step 3: Monitor scan progress
    print(f"\n3. Monitoring scan progress...")
    print("   This may take 5-15 minutes depending on AWS resources...")
    
    max_wait = 20 * 60  # 20 minutes
    check_interval = 30  # Check every 30 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        time.sleep(check_interval)
        elapsed += check_interval
        
        response = requests.get(f"{BASE_URL}/api/scans/{scan_id}")
        if response.status_code != 200:
            print(f"✗ Failed to check status: {response.status_code}")
            continue
        
        scan_data = response.json()
        status = scan_data.get('scan_status', 'Unknown')
        
        print(f"   [{elapsed//60}m {elapsed%60}s] Status: {status}")
        
        if status == "Completed":
            print(f"\n✓ Scan completed successfully!")
            print(f"  Total checks run: {scan_data.get('total_checks_run', 0)}")
            print(f"  Passed: {scan_data.get('passed_checks', 0)}")
            print(f"  Failed: {scan_data.get('failed_checks', 0)}")
            break
        elif status == "Failed":
            print(f"\n✗ Scan failed!")
            return
        elif status == "Running":
            continue
        else:
            print(f"   Unknown status: {status}")
    
    if elapsed >= max_wait:
        print(f"\n⚠ Scan timeout after {max_wait//60} minutes")
        print("  Check scan status manually")
        return
    
    # Step 4: Verify findings in database
    print(f"\n4. Verifying scan findings in database...")
    
    import subprocess
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgres",
        "psql", "-U", "cspm_user", "-d", "cspm_dashboard",
        "-c", f"SELECT COUNT(*) FROM scan_findings WHERE scan_id = '{scan_id}';"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        output = result.stdout
        # Parse the count from output
        lines = [l.strip() for l in output.split('\n') if l.strip() and l.strip().isdigit()]
        if lines:
            finding_count = int(lines[0])
            print(f"✓ Found {finding_count} scan findings in database")
        else:
            print("⚠ Could not parse finding count")
    else:
        print("⚠ Could not verify findings in database")
    
    # Step 5: Calculate compliance scores
    print(f"\n5. Calculating compliance scores...")
    
    response = requests.post(f"{BASE_URL}/api/scores/{scan_id}/calculate")
    
    if response.status_code != 200:
        print(f"✗ Failed to calculate scores: {response.text}")
        return
    
    score_data = response.json()
    print(f"✓ Calculated scores for {len(score_data['scores'])} frameworks")
    
    # Display scores
    print("\n6. Compliance Scores Summary:")
    print("-" * 70)
    
    for score in score_data['scores']:
        print(f"\n  📊 {score['framework']}")
        print(f"     Overall Score: {score['overall_score']}%")
        print(f"     Passed: {score['controls_passed']}/{score['total_controls']}")
        print(f"     Failed: {score['controls_failed']}")
        print(f"     N/A: {score['controls_not_applicable']}")
        
        if score['controls_failed'] > 0:
            findings = []
            if score.get('critical_findings', 0) > 0:
                findings.append(f"Critical: {score['critical_findings']}")
            if score.get('high_findings', 0) > 0:
                findings.append(f"High: {score['high_findings']}")
            if score.get('medium_findings', 0) > 0:
                findings.append(f"Medium: {score['medium_findings']}")
            if score.get('low_findings', 0) > 0:
                findings.append(f"Low: {score['low_findings']}")
            
            if findings:
                print(f"     Findings: {', '.join(findings)}")
    
    print("\n" + "=" * 70)
    print("SCAN COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Scan ID: {scan_id}")
    print(f"✓ Account ID: {account_id}")
    print(f"✓ Compliance scores calculated and stored")
    print(f"\nYou can now:")
    print(f"  - View detailed findings in the database")
    print(f"  - Get scores via: GET /api/scores/scan/{scan_id}")
    print(f"  - Get account scores via: GET /api/scores/account/{account_id}")


if __name__ == "__main__":
    try:
        test_complete_prowler_scan()
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
