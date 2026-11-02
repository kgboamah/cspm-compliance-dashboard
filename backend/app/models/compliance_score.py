"""
Compliance Score model - aggregated compliance scores
"""
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.database import Base


class ComplianceScore(Base):
    """
    Aggregated compliance score for an account/framework/scan combination
    """
    __tablename__ = "compliance_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("cloud_accounts.id", ondelete="CASCADE"), nullable=False)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("assessment_scans.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=False)
    controls_passed = Column(Integer, default=0, nullable=False)
    controls_failed = Column(Integer, default=0, nullable=False)
    controls_not_applicable = Column(Integer, default=0, nullable=False)
    critical_findings = Column(Integer, default=0, nullable=False)
    high_findings = Column(Integer, default=0, nullable=False)
    medium_findings = Column(Integer, default=0, nullable=False)
    low_findings = Column(Integer, default=0, nullable=False)
    calculated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    
    # Indexes
    __table_args__ = (
        Index('idx_compliance_scores_account_id', 'account_id'),
        Index('idx_compliance_scores_framework_id', 'framework_id'),
        Index('idx_compliance_scores_scan_id', 'scan_id'),
    )
    
    def __repr__(self):
        return f"<ComplianceScore(id={self.id}, score={self.overall_score})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "account_id": str(self.account_id),
            "framework_id": self.framework_id,
            "scan_id": str(self.scan_id),
            "overall_score": float(self.overall_score),
            "controls_passed": self.controls_passed,
            "controls_failed": self.controls_failed,
            "controls_not_applicable": self.controls_not_applicable,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "medium_findings": self.medium_findings,
            "low_findings": self.low_findings,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }
