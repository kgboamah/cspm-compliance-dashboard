"""
Cloud Account Schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class CloudAccountBase(BaseModel):
    """Base schema"""
    account_name: str
    cloud_provider: str
    account_id: str
    regions: List[str] = []
    is_active: bool = True


class CloudAccountCreate(CloudAccountBase):
    """Create schema"""
    credentials: Dict[str, Any] = {}


class CloudAccountUpdate(BaseModel):
    """Update schema"""
    account_name: Optional[str] = None
    cloud_provider: Optional[str] = None
    regions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    credentials: Optional[Dict[str, Any]] = None


class CloudAccountResponse(CloudAccountBase):
    """Response schema"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
