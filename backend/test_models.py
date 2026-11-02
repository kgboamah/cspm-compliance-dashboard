"""
Test script to verify models are working
"""
from app.database import engine, Base
from app.models import (
    CloudAccount,
    ComplianceFramework,
    FrameworkControl,
    TechnicalCheck,
    ControlCheckMapping,
    AssessmentScan,
    ScanFinding,
    ComplianceScore,
)

def test_models():
    """Test that all models can be imported and have correct structure"""
    print("Testing models...")
    
    models = [
        CloudAccount,
        ComplianceFramework,
        FrameworkControl,
        TechnicalCheck,
        ControlCheckMapping,
        AssessmentScan,
        ScanFinding,
        ComplianceScore,
    ]
    
    for model in models:
        print(f"✓ {model.__name__} - Table: {model.__tablename__}")
        
        # Check that model has required attributes
        assert hasattr(model, '__tablename__'), f"{model.__name__} missing __tablename__"
        assert hasattr(model, 'to_dict'), f"{model.__name__} missing to_dict method"
    
    print("\n✅ All models loaded successfully!")
    print(f"✅ Total models: {len(models)}")
    
    # Note: We're not creating tables here because they already exist
    # from the schema.sql that ran when Docker started
    
if __name__ == "__main__":
    test_models()
