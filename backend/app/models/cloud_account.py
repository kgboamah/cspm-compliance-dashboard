from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database import Base

class CloudAccount(Base):
    __tablename__ = "cloud_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(255), nullable=False)
    cloud_provider = Column(String(50), nullable=False)
    account_id = Column(String(255), nullable=False, unique=True)
    regions = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    credentials = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
