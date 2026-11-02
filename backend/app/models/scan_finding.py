from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class ScanFinding(Base):
    __tablename__ = "scan_findings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Map Python attribute 'assessment_scan_id' to database column 'scan_id'
    assessment_scan_id = Column('scan_id', UUID(as_uuid=True), ForeignKey("assessment_scans.id", ondelete="CASCADE"), nullable=False)
    
    # Map Python attribute 'check_id' to database column 'check_id' (which is integer FK)
    check_id = Column('check_id', Integer, ForeignKey("technical_checks.id", ondelete="CASCADE"), nullable=False)
    
    resource_id = Column(String(500), nullable=False)
    resource_type = Column(String(100), nullable=False)
    
    # Map Python attributes to database columns with different names
    status = Column('finding_status', String(20), nullable=False)
    severity = Column('risk_level', String(20))
    
    # Additional fields from database
    finding_details = Column(JSONB)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to scan
    scan = relationship("AssessmentScan", back_populates="findings")
    
    # Relationship to technical check
    technical_check = relationship("TechnicalCheck")