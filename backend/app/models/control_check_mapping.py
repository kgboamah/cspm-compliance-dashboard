"""
Control-Check Mapping model - links controls to technical checks
"""
from sqlalchemy import Column, Integer, ForeignKey, Index
from app.database import Base


class ControlCheckMapping(Base):
    """
    Many-to-many mapping between framework controls and technical checks
    """
    __tablename__ = "control_check_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    control_id = Column(Integer, ForeignKey("framework_controls.id", ondelete="CASCADE"), nullable=False)
    check_id = Column(Integer, ForeignKey("technical_checks.id", ondelete="CASCADE"), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_ccm_control_id', 'control_id'),
        Index('idx_ccm_check_id', 'check_id'),
    )
    
    def __repr__(self):
        return f"<ControlCheckMapping(control_id={self.control_id}, check_id={self.check_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "control_id": self.control_id,
            "check_id": self.check_id,
        }
