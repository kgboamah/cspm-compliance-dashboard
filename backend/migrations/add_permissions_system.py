"""
Database Migration: Add Permissions System (FINAL - UPPERCASE ENUMS)
Location: backend/migrations/add_permissions_system.py

Uses existing permissiontype enum with UPPERCASE values (READ, WRITE, EXECUTE)
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cspm_user:cspm_password@localhost:5432/cspm_db")
engine = create_engine(DATABASE_URL)


def seed_default_permissions():
    """Seed default permissions for dashboard resources"""
    
    print("Seeding default permissions...")
    
    # Define resources and their available actions (UPPERCASE to match enum)
    resources = [
        ('dashboard', ['READ'], 'View main dashboard'),
        ('scans', ['READ', 'WRITE', 'EXECUTE'], 'Manage security scans'),
        ('findings', ['READ', 'WRITE'], 'View and manage findings'),
        ('frameworks', ['READ', 'WRITE'], 'View and manage frameworks'),
        ('trends', ['READ'], 'View compliance trends'),
        ('recurring', ['READ', 'WRITE'], 'View and manage recurring findings'),
        ('users', ['READ', 'WRITE', 'EXECUTE'], 'Manage user accounts'),
        ('reports', ['READ', 'EXECUTE'], 'View and generate reports'),
        ('settings', ['READ', 'WRITE'], 'Manage system settings'),
    ]
    
    with engine.connect() as conn:
        for resource, actions, description in resources:
            for action in actions:
                try:
                    # Cast action to permissiontype enum explicitly
                    result = conn.execute(text("""
                        INSERT INTO permissions (resource, action, description)
                        VALUES (:resource, CAST(:action AS permissiontype), :description)
                        ON CONFLICT (resource, action) DO NOTHING
                        RETURNING permission_id
                    """), {"resource": resource, "action": action, "description": description})
                    
                    if result.rowcount > 0:
                        print(f"✅ Added permission: {resource}.{action}")
                    else:
                        print(f"⚠️  Permission already exists: {resource}.{action}")
                except Exception as e:
                    print(f"❌ Error adding {resource}.{action}: {e}")
                    conn.rollback()
                    continue
        
        conn.commit()


def assign_default_role_permissions():
    """Assign permissions to roles"""
    
    print("\nAssigning permissions to roles...")
    
    with engine.connect() as conn:
        # ADMIN: Full access to everything
        print("\n🔐 Configuring ADMIN role...")
        result = conn.execute(text("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'ADMIN'::userrole, permission_id
            FROM permissions
            ON CONFLICT (role, permission_id) DO NOTHING;
        """))
        conn.commit()
        print("✅ ADMIN: Full access granted")
        
        # AUDITOR: Read all, write findings/recurring, execute reports
        print("\n🔐 Configuring AUDITOR role...")
        result = conn.execute(text("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'AUDITOR'::userrole, permission_id
            FROM permissions
            WHERE 
                action = CAST('READ' AS permissiontype)
                OR (resource IN ('findings', 'recurring') AND action = CAST('WRITE' AS permissiontype))
                OR (resource = 'reports' AND action = CAST('EXECUTE' AS permissiontype))
            ON CONFLICT (role, permission_id) DO NOTHING;
        """))
        conn.commit()
        print("✅ AUDITOR: Read all, write findings, execute reports")
        
        # VIEWER: Read-only access (except users and settings)
        print("\n🔐 Configuring VIEWER role...")
        result = conn.execute(text("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'VIEWER'::userrole, permission_id
            FROM permissions
            WHERE 
                action = CAST('READ' AS permissiontype)
                AND resource NOT IN ('users', 'settings')
            ON CONFLICT (role, permission_id) DO NOTHING;
        """))
        conn.commit()
        print("✅ VIEWER: Read-only access (limited)")


if __name__ == "__main__":
    print("=" * 70)
    print("🔧 CSPM DATABASE MIGRATION: Add Permissions System")
    print("=" * 70)
    
    try:
        seed_default_permissions()
        assign_default_role_permissions()
        
        print("\n" + "=" * 70)
        print("✅ PERMISSIONS SYSTEM MIGRATION COMPLETED!")
        print("=" * 70)
        print("\nPermission Structure:")
        print("- ADMIN: Full access to all resources")
        print("- AUDITOR: Read all, write findings, execute reports")
        print("- VIEWER: Read-only (dashboard, scans, findings, frameworks, trends)")
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
