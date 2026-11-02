"""
Compliance Framework model - ISO 27001, NIST CSF, PCI-DSS
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ComplianceFramework(Base):
    """
    Represents a compliance framework (e.g., ISO 27001, NIST CSF 2.0)
    """
    __tablename__ = "compliance_frameworks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    framework_name = Column(String(100), nullable=False)
    framework_version = Column(String(50), nullable=False)
    total_controls = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    controls = relationship("FrameworkControl", back_populates="framework", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ComplianceFramework(id={self.id}, name={self.framework_name} {self.framework_version})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "framework_name": self.framework_name,
            "framework_version": self.framework_version,
            "total_controls": self.total_controls,
            "description": self.description,
        }

