"""
User Model for Authentication System (WITH MFA SUPPORT)
Location: backend/app/models/user.py
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    ADMIN = "admin"      # Full access - manage users, run scans, view all data
    AUDITOR = "auditor"  # Read + Export - view data, export reports, no modifications
    VIEWER = "viewer"    # Read-only - view dashboards and reports only


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Role-based access control
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # MFA (Multi-Factor Authentication) - ADDED
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_email = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role})>"
    
    def to_dict(self):
        """Convert user to dictionary (without password)"""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
