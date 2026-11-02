"""
Database Seeding Script
Populates database with compliance frameworks, controls, and check mappings
Uses actual model column names based on inspection
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from sqlalchemy import inspect
import json

# Import models
from app.models.compliance_framework import ComplianceFramework
from app.models.framework_control import FrameworkControl
from app.models.technical_check import TechnicalCheck
from app.models.control_check_mapping import ControlCheckMapping

print("✓ Models imported successfully")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def get_model_columns(model):
    """Get list of column names for a model"""
    return [column.key for column in inspect(model).mapper.column_attrs]


def load_json(filename):
    """Load JSON data from file"""
    file_path = Path(__file__).parent / "data" / filename
    with open(file_path, "r") as f:
        return json.load(f)


def seed_frameworks(db):
    """Seed compliance frameworks"""
    print("\nSeeding Compliance Frameworks...")
    
    framework_columns = get_model_columns(ComplianceFramework)
    print(f"  Available columns: {framework_columns}")
    
    frameworks_data = load_json("compliance_frameworks.json")
    added_count = 0
    
    for data in frameworks_data:
        existing = db.query(ComplianceFramework).filter(
            ComplianceFramework.framework_name == data["name"]
        ).first()
        
        if not existing:
            framework = ComplianceFramework(
                framework_name=data["name"],
                framework_version=data["version"],
                description=data["description"]
            )
            db.add(framework)
            added_count += 1
            print(f"  ✓ Added framework: {data['name']}")
        else:
            print(f"  - Framework exists: {data['name']}")
    
    db.commit()
    print(f"✓ Seeded {added_count} new frameworks")


def seed_controls(db):
    """Seed framework controls"""
    print("\nSeeding Framework Controls...")
    
    control_columns = get_model_columns(FrameworkControl)
    
    controls_data = load_json("framework_controls.json")
    added_count = 0
    
    for data in controls_data:
        framework = db.query(ComplianceFramework).filter(
            ComplianceFramework.framework_name == data["framework_name"]
        ).first()
        
        if not framework:
            print(f"  ✗ Framework not found: {data['framework_name']}")
            continue
        
        existing = db.query(FrameworkControl).filter(
            FrameworkControl.framework_id == framework.id,
            FrameworkControl.control_id == data["control_id"]
        ).first()
        
        if not existing:
            control_dict = {
                "framework_id": framework.id,
                "control_id": data["control_id"],
                "control_title": data["title"],
                "control_description": data["description"]
            }
            
            # Add optional fields that exist
            if "control_category" in control_columns:
                control_dict["control_category"] = data.get("category")
            if "severity" in control_columns:
                control_dict["severity"] = data.get("severity")
            
            control = FrameworkControl(**control_dict)
            db.add(control)
            added_count += 1
            print(f"  ✓ Added control: {data['control_id']}")
        else:
            print(f"  - Control exists: {data['control_id']}")
    
    db.commit()
    print(f"✓ Seeded {added_count} new controls")


def seed_checks_and_mappings(db):
    """Seed technical checks and mappings"""
    print("\nSeeding Technical Checks and Control-Check Mappings...")
    
    check_columns = get_model_columns(TechnicalCheck)
    mapping_columns = get_model_columns(ControlCheckMapping)
    print(f"  TechnicalCheck columns: {check_columns}")
    print(f"  ControlCheckMapping columns: {mapping_columns}")
    
    mappings_data = load_json("check_mappings.json")
    checks_created = 0
    mappings_created = 0
    
    for check_data in mappings_data:
        # TechnicalCheck uses 'check_name' not 'check_id'
        check = db.query(TechnicalCheck).filter(
            TechnicalCheck.check_name == check_data["check_id"]
        ).first()
        
        if not check:
            # Map JSON fields to actual database columns
            check_dict = {
                "check_name": check_data["check_id"],  # check_id → check_name
                "check_description": check_data.get("description", check_data["check_title"])
            }
            
            # Map service → cloud_service
            if "cloud_service" in check_columns:
                check_dict["cloud_service"] = check_data.get("service", "aws")
            
            # Map to cloud_provider
            if "cloud_provider" in check_columns:
                check_dict["cloud_provider"] = "aws"
            
            # Add remediation fields if they exist
            if "remediation_guidance" in check_columns:
                check_dict["remediation_guidance"] = check_data.get("remediation", check_data["check_title"])
            
            if "remediation_links" in check_columns:
                check_dict["remediation_links"] = []
            
            # Add check_query if it exists
            if "check_query" in check_columns:
                check_dict["check_query"] = f"SELECT * FROM {check_data.get('service', 'aws')}"
            
            check = TechnicalCheck(**check_dict)
            db.add(check)
            db.flush()
            checks_created += 1
            print(f"  ✓ Created check: {check_data['check_id']}")
        else:
            print(f"  - Check exists: {check_data['check_id']}")
        
        # Create mappings
        for control_mapping in check_data.get("controls", []):
            framework_name = control_mapping["framework"]
            control_id_str = control_mapping["control_id"]
            
            framework = db.query(ComplianceFramework).filter(
                ComplianceFramework.framework_name == framework_name
            ).first()
            
            if not framework:
                continue
            
            control = db.query(FrameworkControl).filter(
                FrameworkControl.framework_id == framework.id,
                FrameworkControl.control_id == control_id_str
            ).first()
            
            if not control:
                print(f"    ✗ Control not found: {control_id_str}")
                continue
            
            # Check if mapping exists
            existing_mapping = db.query(ControlCheckMapping).filter(
                ControlCheckMapping.control_id == control.id,
                ControlCheckMapping.check_id == check.id
            ).first()
            
            if not existing_mapping:
                mapping = ControlCheckMapping(
                    control_id=control.id,
                    check_id=check.id
                )
                db.add(mapping)
                mappings_created += 1
    
    db.commit()
    print(f"✓ Created {checks_created} new checks")
    print(f"✓ Created {mappings_created} new control-check mappings")


def verify_seeding(db):
    """Verify data was seeded correctly"""
    print("\n" + "=" * 60)
    print("Database Seeding Complete!")
    print("=" * 60)
    
    frameworks_count = db.query(ComplianceFramework).count()
    controls_count = db.query(FrameworkControl).count()
    checks_count = db.query(TechnicalCheck).count()
    mappings_count = db.query(ControlCheckMapping).count()
    
    print(f"\nStatistics:")
    print(f"  Frameworks: {frameworks_count}")
    print(f"  Controls: {controls_count}")
    print(f"  Technical Checks: {checks_count}")
    print(f"  Control-Check Mappings: {mappings_count}")
    
    print("\nSample Frameworks:")
    for framework in db.query(ComplianceFramework).limit(4).all():
        controls = db.query(FrameworkControl).filter(
            FrameworkControl.framework_id == framework.id
        ).count()
        print(f"  - {framework.framework_name} v{framework.framework_version} ({controls} controls)")
    
    print("\nSample Technical Checks:")
    for check in db.query(TechnicalCheck).limit(7).all():
        mappings = db.query(ControlCheckMapping).filter(
            ControlCheckMapping.check_id == check.id
        ).count()
        service = getattr(check, 'cloud_service', 'N/A')
        print(f"  - {check.check_name}")
        print(f"    Service: {service} | Mappings: {mappings}")
    
    print("\nSample Mappings:")
    for mapping in db.query(ControlCheckMapping).limit(5).all():
        control = db.query(FrameworkControl).filter(
            FrameworkControl.id == mapping.control_id
        ).first()
        check = db.query(TechnicalCheck).filter(
            TechnicalCheck.id == mapping.check_id
        ).first()
        
        if control and check:
            framework = db.query(ComplianceFramework).filter(
                ComplianceFramework.id == control.framework_id
            ).first()
            print(f"  - {framework.framework_name} {control.control_id} → {check.check_name}")


def main():
    """Main seeding function"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Starting Database Seeding Process")
        print("=" * 60)
        
        seed_frameworks(db)
        seed_controls(db)
        seed_checks_and_mappings(db)
        verify_seeding(db)
        
        print("\n✓ All data seeded successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()