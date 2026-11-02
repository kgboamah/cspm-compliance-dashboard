#!/usr/bin/env python3
"""
Import Prowler compliance framework mappings into CSPM database.
Populates: compliance_frameworks, framework_controls, control_check_mappings
"""

import json
import psycopg2

# Database connection
conn = psycopg2.connect(
    host="postgres",
    port="5432",
    database="cspm_dashboard",
    user="cspm_user",
    password="cspm_password"
)

# Prowler compliance file paths
COMPLIANCE_FILES = {
    'ISO 27001': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/iso27001_2013_aws.json',
    'NIST CSF': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/nist_csf_1.1_aws.json',
    'PCI-DSS': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/pci_3.2.1_aws.json',
    'CIS AWS': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/cis_2.0_aws.json',
    'GDPR': '/usr/local/lib/python3.11/site-packages/prowler/compliance/aws/gdpr_aws.json'
}

def import_framework(framework_name, compliance_file):
    """Import a single compliance framework and its controls."""
    
    print(f"\n=== Importing {framework_name} ===")
    
    with open(compliance_file) as f:
        data = json.load(f)
    
    requirements = data.get('Requirements', [])
    print(f"Found {len(requirements)} requirements/controls")
    
    cur = conn.cursor()
    
    # Get or create framework
    cur.execute("""
        SELECT id FROM compliance_frameworks WHERE framework_name = %s
    """, (framework_name,))
    
    existing_fw = cur.fetchone()
    
    if existing_fw:
        framework_id = existing_fw[0]
        # Update existing framework
        cur.execute("""
            UPDATE compliance_frameworks 
            SET framework_version = %s, description = %s
            WHERE id = %s
        """, (data.get('Version', '1.0'), data.get('Description', '')[:500], framework_id))
    else:
        # Insert new framework
        cur.execute("""
            INSERT INTO compliance_frameworks 
            (framework_name, framework_version, description)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (framework_name, data.get('Version', '1.0'), data.get('Description', '')[:500]))
        framework_id = cur.fetchone()[0]
    
    conn.commit()
    
    # Track statistics
    controls_added = 0
    mappings_added = 0
    
    for req in requirements:
        # Extract control information
        req_id = req.get('Id', 'Unknown')
        control_title = req.get('Name', req.get('Description', ''))[:200]
        control_description = req.get('Description', '')[:500]
        
        # Get category from attributes
        attributes = req.get('Attributes', [{}])
        category = 'General'
        if attributes:
            category = attributes[0].get('Category', attributes[0].get('Section', 'General'))[:100]
        
        # Get prowler check IDs
        prowler_checks = req.get('Checks', [])
        
        if not prowler_checks:
            continue
        
        try:
            # Check if control already exists
            cur.execute("""
                SELECT id FROM framework_controls
                WHERE framework_id = %s AND control_id = %s
            """, (framework_id, req_id))
            
            existing = cur.fetchone()
            
            if existing:
                # Update existing control
                control_db_id = existing[0]
                cur.execute("""
                    UPDATE framework_controls 
                    SET control_title = %s,
                        control_description = %s,
                        control_category = %s
                    WHERE id = %s
                """, (control_title, control_description, category, control_db_id))
            else:
                # Insert new control
                cur.execute("""
                    INSERT INTO framework_controls 
                    (framework_id, control_id, control_title, control_description, control_category)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (framework_id, req_id, control_title, control_description, category))
                
                control_db_id = cur.fetchone()[0]
            
            controls_added += 1
            
            # Map to technical checks
            for prowler_check_id in prowler_checks:
                # Find technical check by check_name (which contains prowler check ID)
                cur.execute("""
                    SELECT id FROM technical_checks 
                    WHERE check_name = %s
                """, (prowler_check_id,))
                
                result = cur.fetchone()
                if result:
                    tech_check_id = result[0]
                    
                    # Create mapping
                    cur.execute("""
                        INSERT INTO control_check_mappings 
                        (control_id, check_id)
                        VALUES (%s, %s)
                        ON CONFLICT (control_id, check_id) DO NOTHING
                    """, (control_db_id, tech_check_id))
                    
                    if cur.rowcount > 0:
                        mappings_added += 1
            
            conn.commit()
            
        except Exception as e:
            print(f"  Error processing control {req_id}: {e}")
            conn.rollback()
            continue
    
    # Update total_controls count
    cur.execute("""
        UPDATE compliance_frameworks 
        SET total_controls = (
            SELECT COUNT(*) FROM framework_controls WHERE framework_id = %s
        )
        WHERE id = %s
    """, (framework_id, framework_id))
    conn.commit()
    
    print(f"✅ Added {controls_added} controls")
    print(f"✅ Created {mappings_added} control-to-check mappings")
    
    cur.close()

def main():
    print("=" * 60)
    print("Prowler Compliance Framework Import")
    print("=" * 60)
    
    cur = conn.cursor()
    
    # Show current state
    cur.execute("""
        SELECT cf.framework_name, COUNT(fc.id) 
        FROM compliance_frameworks cf
        LEFT JOIN framework_controls fc ON cf.id = fc.framework_id
        GROUP BY cf.framework_name
    """)
    existing = cur.fetchall()
    print("\nExisting controls in database:")
    for fw, count in existing:
        print(f"  {fw}: {count}")
    
    # Clear existing data
    print("\n⚠️  Clearing existing compliance data...")
    cur.execute("DELETE FROM control_check_mappings")
    cur.execute("DELETE FROM framework_controls")
    cur.execute("DELETE FROM compliance_frameworks WHERE framework_name != 'Custom'")
    conn.commit()
    
    # Import each framework
    for framework_name, filepath in COMPLIANCE_FILES.items():
        import_framework(framework_name, filepath)
    
    # Show final stats
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE - Final Statistics:")
    print("=" * 60)
    
    cur.execute("""
        SELECT 
            cf.framework_name,
            cf.total_controls,
            COUNT(DISTINCT ccm.check_id) as mapped_checks
        FROM compliance_frameworks cf
        LEFT JOIN framework_controls fc ON cf.id = fc.framework_id
        LEFT JOIN control_check_mappings ccm ON fc.id = ccm.control_id
        GROUP BY cf.framework_name, cf.total_controls
        ORDER BY cf.framework_name
    """)
    
    for fw, controls, checks in cur.fetchall():
        print(f"{fw}:")
        print(f"  Controls: {controls}")
        print(f"  Mapped to {checks} unique Prowler checks")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
