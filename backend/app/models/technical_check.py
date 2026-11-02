"""
Technical Check model - automated security checks (Prowler checks)
"""
from sqlalchemy import Column, Integer, String, Text, ARRAY, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class TechnicalCheck(Base):
    """
    Automated technical check that can be executed against cloud resources
    """
    __tablename__ = "technical_checks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    check_name = Column(String(255), nullable=False, unique=True)
    check_description = Column(Text, nullable=True)
    cloud_provider = Column(String(50), nullable=False)
    cloud_service = Column(String(100), nullable=False)
    check_query = Column(JSONB, nullable=True)
    remediation_guidance = Column(Text, nullable=True)
    remediation_links = Column(ARRAY(String), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_technical_checks_cloud_provider', 'cloud_provider'),
        Index('idx_technical_checks_cloud_service', 'cloud_service'),
    )
    
    def __repr__(self):
        return f"<TechnicalCheck(id={self.id}, name={self.check_name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "check_name": self.check_name,
            "check_description": self.check_description,
            "cloud_provider": self.cloud_provider,
            "cloud_service": self.cloud_service,
            "remediation_guidance": self.remediation_guidance,
            "remediation_links": self.remediation_links,
        }
