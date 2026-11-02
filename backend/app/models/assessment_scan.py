from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class AssessmentScan(Base):
    __tablename__ = "assessment_scans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False)
    scan_type = Column(String(50), default="full")
    scan_status = Column(String(50), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    total_checks_run = Column(Integer, default=0)
    error_log = Column(Text)
    
    # Relationships
    findings = relationship("ScanFinding", back_populates="scan", cascade="all, delete-orphan")
