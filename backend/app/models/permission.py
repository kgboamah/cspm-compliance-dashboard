"""
Permission Models
Location: backend/app/models/permission.py
"""
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from app.database import Base


class PermissionType(str, enum.Enum):
    """Permission action types"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


class Permission(Base):
    """Permission model - defines what actions can be performed on resources"""
    __tablename__ = "permissions"

    permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource = Column(String(100), nullable=False)
    action = Column(Enum(PermissionType), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Permission(resource={self.resource}, action={self.action})>"
    
    def to_dict(self):
        return {
            "permission_id": str(self.permission_id),
            "resource": self.resource,
            "action": self.action.value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RolePermission(Base):
    """Role-Permission junction table"""
    __tablename__ = "role_permissions"

    role = Column(String(20), primary_key=True, nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RolePermission(role={self.role}, permission_id={self.permission_id})>"
