"""
Diagnostic Script - Check Models Structure
Run this to see your models structure and identify the correct imports
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("Checking Models Structure")
print("=" * 60)

# Check if app.models is a file or directory
models_path = Path(__file__).parent.parent / "app" / "models"
models_file = Path(__file__).parent.parent / "app" / "models.py"

print(f"\nChecking paths:")
print(f"  models.py file: {models_file.exists()} - {models_file}")
print(f"  models/ dir: {models_path.exists()} - {models_path}")

if models_path.exists() and models_path.is_dir():
    print(f"\n✓ Found models directory")
    print(f"\nFiles in models directory:")
    for file in sorted(models_path.glob("*.py")):
        print(f"  - {file.name}")
    
    # Try to import from models package
    print(f"\nTrying to import from app.models package:")
    try:
        import app.models
        print(f"  ✓ app.models imported successfully")
        print(f"  Available attributes: {dir(app.models)}")
    except Exception as e:
        print(f"  ✗ Failed to import app.models: {e}")

if models_file.exists():
    print(f"\n✓ Found models.py file")
    
    # Try to import from models.py
    print(f"\nTrying to import from app.models file:")
    try:
        from app import models
        print(f"  ✓ app.models imported successfully")
        print(f"  Available classes: {[name for name in dir(models) if not name.startswith('_')]}")
    except Exception as e:
        print(f"  ✗ Failed to import app.models: {e}")

# Try specific imports
print(f"\n" + "=" * 60)
print("Trying Specific Model Imports")
print("=" * 60)

# Test 1: Import from app.models
print(f"\nTest 1: from app.models import ComplianceFramework")
try:
    from app.models import ComplianceFramework
    print(f"  ✓ SUCCESS - Use: from app.models import ComplianceFramework, ...")
except ImportError as e:
    print(f"  ✗ Failed: {e}")

# Test 2: Import from app.models.__init__
print(f"\nTest 2: from app.models import (via __init__.py)")
try:
    import app.models
    if hasattr(app.models, 'ComplianceFramework'):
        print(f"  ✓ SUCCESS - ComplianceFramework available in app.models")
    else:
        print(f"  ✗ ComplianceFramework not found in app.models")
        print(f"  Available: {[x for x in dir(app.models) if not x.startswith('_')]}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 3: Import from separate files
print(f"\nTest 3: from app.models.compliance_framework import ComplianceFramework")
try:
    from app.models.compliance_framework import ComplianceFramework
    print(f"  ✓ SUCCESS - Use separate file imports")
except ImportError as e:
    print(f"  ✗ Failed: {e}")

# Test 4: Check __init__.py
init_file = models_path / "__init__.py"
if init_file.exists():
    print(f"\nChecking __init__.py contents:")
    with open(init_file, 'r') as f:
        content = f.read()
        print(f"  Length: {len(content)} characters")
        if "ComplianceFramework" in content:
            print(f"  ✓ ComplianceFramework found in __init__.py")
        else:
            print(f"  ✗ ComplianceFramework NOT in __init__.py")
        
        # Show first 500 chars
        print(f"\n  First 500 characters:")
        print(f"  {'-' * 40}")
        print(f"  {content[:500]}")
        print(f"  {'-' * 40}")

print(f"\n" + "=" * 60)
print("Diagnostic Complete")
print("=" * 60)
