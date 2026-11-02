"""
Framework Control model - individual controls within frameworks
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class FrameworkControl(Base):
    """
    Individual control within a compliance framework
    """
    __tablename__ = "framework_controls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(String(50), nullable=False)
    control_title = Column(String(255), nullable=False)
    control_description = Column(Text, nullable=True)
    control_category = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=True)
    
    # Relationships
    framework = relationship("ComplianceFramework", back_populates="controls")
    
    # Indexes
    __table_args__ = (
        Index('idx_framework_controls_framework_id', 'framework_id'),
        Index('idx_framework_controls_severity', 'severity'),
    )
    
    def __repr__(self):
        return f"<FrameworkControl(id={self.id}, control_id={self.control_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "framework_id": self.framework_id,
            "control_id": self.control_id,
            "control_title": self.control_title,
            "control_description": self.control_description,
            "control_category": self.control_category,
            "severity": self.severity,
        }
