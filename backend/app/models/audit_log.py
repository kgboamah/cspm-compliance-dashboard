"""
Audit Log Model (FIXED - renamed metadata to event_metadata)
Location: backend/app/models/audit_log.py
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(50), nullable=False)
    event_category = Column(String(50), nullable=False)
    event_description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    event_metadata = Column(JSONB, nullable=True)  # CHANGED: metadata -> event_metadata
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "log_id": str(self.log_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "event_type": self.event_type,
            "event_category": self.event_category,
            "event_description": self.event_description,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.event_metadata,  # Return as 'metadata' in API
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
