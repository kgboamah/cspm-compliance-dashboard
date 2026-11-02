"""
Test Compliance Scoring
"""

import requests
import time

BASE_URL = "http://localhost:8000"


def test_scoring():
    """Test compliance scoring workflow"""
    print("=" * 60)
    print("Testing Compliance Scoring")
    print("=" * 60)
    
    # Assuming you have a completed scan
    # Replace with your actual scan_id
    scan_id = input("\nEnter scan ID from a completed scan: ")
    
    if not scan_id:
        print("No scan ID provided. Exiting.")
        return
    
    # Step 1: Calculate scores
    print(f"\n1. Calculating scores for scan {scan_id}...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/scores/{scan_id}/calculate"
        )
        
        if response.status_code != 200:
            print(f"❌ Calculation failed: {response.text}")
            return
        
        data = response.json()
        print(f"✓ Calculated scores for {len(data['scores'])} frameworks")
        
        # Display scores
        print("\n📊 Compliance Scores:")
        for score in data['scores']:
            print(f"\n  {score['framework']}:")
            print(f"    Overall Score: {score['overall_score']}%")
            print(f"    Passed: {score['controls_passed']}/{score['total_controls']}")
            print(f"    Failed: {score['controls_failed']}")
            if 'controls_not_applicable' in score:
                print(f"    N/A: {score['controls_not_applicable']}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 2: Get scan scores
    print(f"\n2. Retrieving saved scores...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/scores/scan/{scan_id}"
        )
        
        if response.status_code != 200:
            print(f"❌ Retrieval failed: {response.text}")
            return
        
        print("✓ Scores retrieved successfully")
        
        # Display detailed breakdown
        data = response.json()
        print("\n📋 Detailed Score Breakdown:")
        for score in data['scores']:
            print(f"\n  {score['framework']}:")
            print(f"    Overall Score: {score['overall_score']}%")
            print(f"    Total Controls: {score['total_controls']}")
            print(f"    Passed: {score['controls_passed']}")
            print(f"    Failed: {score['controls_failed']}")
            if 'controls_not_applicable' in score:
                print(f"    N/A: {score['controls_not_applicable']}")
            if 'critical_findings' in score:
                print(f"    Critical Findings: {score['critical_findings']}")
            if 'high_findings' in score:
                print(f"    High Findings: {score['high_findings']}")
            if 'medium_findings' in score:
                print(f"    Medium Findings: {score['medium_findings']}")
            if 'low_findings' in score:
                print(f"    Low Findings: {score['low_findings']}")
            print(f"    Calculated: {score.get('calculated_at', 'N/A')}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("Scoring Test Complete!")
    print("=" * 60)


def test_account_scores():
    """Test retrieving account scores"""
    print("\n" + "=" * 60)
    print("Testing Account Scores Retrieval")
    print("=" * 60)
    
    account_id = input("\nEnter cloud account ID: ")
    
    if not account_id:
        print("No account ID provided. Exiting.")
        return
    
    print(f"\nRetrieving latest scores for account {account_id}...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/scores/account/{account_id}"
        )
        
        if response.status_code == 404:
            print("❌ No completed scans found for this account")
            return
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.text}")
            return
        
        data = response.json()
        print("✓ Scores retrieved successfully")
        
        print("\n📊 Latest Compliance Scores:")
        for score in data['scores']:
            print(f"\n  {score['framework']}:")
            print(f"    Overall Score: {score['overall_score']}%")
            print(f"    Passed: {score['controls_passed']}/{score['total_controls']}")
            print(f"    Failed: {score['controls_failed']}")
            if 'controls_not_applicable' in score:
                print(f"    N/A: {score['controls_not_applicable']}")
            print(f"    Scan Date: {score.get('scan_date', 'N/A')}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("CSPM Compliance Scoring Test Suite")
    print("=" * 60)
    
    print("\nSelect test to run:")
    print("1. Test scoring calculation and retrieval")
    print("2. Test account scores retrieval")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        test_scoring()
    elif choice == "2":
        test_account_scores()
    elif choice == "3":
        test_scoring()
        test_account_scores()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()