from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class ScanFinding(Base):
    __tablename__ = "scan_findings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_scan_id = Column(UUID(as_uuid=True), ForeignKey("assessment_scans.id", ondelete="CASCADE"), nullable=False)
    check_id = Column(String(255), nullable=False)
    check_title = Column(String(500))
    service_name = Column(String(100))
    resource_id = Column(String(500))
    resource_type = Column(String(100))
    status = Column(String(50))
    status_extended = Column(Text)
    severity = Column(String(50))
    region = Column(String(50))
    compliance_frameworks = Column(JSONB, default=dict)
    raw_result = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to scan
    scan = relationship("AssessmentScan", back_populates="findings")
