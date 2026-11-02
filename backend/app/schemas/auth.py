"""
Authentication Schemas (Pydantic Models) - UPDATED WITH SETTINGS SUPPORT
Location: backend/app/schemas/auth.py
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
import re

class UserRole(str, Enum):
    """User roles matching database enum"""
    ADMIN = "admin"
    AUDITOR = "auditor"
    VIEWER = "viewer"

# ============================================
# REQUEST SCHEMAS
# ============================================

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: str  # Changed from EmailStr to str to allow .local domains
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.VIEWER
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format (relaxed to allow .local and internal domains)"""
        # Simple email regex that allows .local domains
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Ensure username is alphanumeric with underscores/hyphens"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v

class UserLogin(BaseModel):
    """Schema for user login"""
    email: str  # Changed from EmailStr to str
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format if provided"""
        if v is not None:
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v

# ============================================
# MFA & SETTINGS SCHEMAS (NEW)
# ============================================

class MFAVerifyRequest(BaseModel):
    """Schema for MFA code verification"""
    email: str
    code: str = Field(..., min_length=6, max_length=6)

class MFAToggleRequest(BaseModel):
    """Schema for enabling/disabling MFA"""
    enable: bool
    mfa_email: Optional[str] = None
    
    @validator('mfa_email')
    def validate_mfa_email(cls, v, values):
        """Validate MFA email if enabling MFA"""
        if values.get('enable') and not v:
            raise ValueError('MFA email required when enabling MFA')
        if v:
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
            return v.lower()
        return v

class MFAEmailUpdate(BaseModel):
    """Schema for updating MFA email"""
    mfa_email: str
    
    @validator('mfa_email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class UserSettings(BaseModel):
    """Schema for user security settings"""
    mfa_enabled: bool
    mfa_email: Optional[str]
    email: str
    username: str
    full_name: Optional[str]
    role: str
    created_at: str
    last_login: Optional[str]

class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordResetVerify(BaseModel):
    """Schema for password reset verification"""
    email: str
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)

# ============================================
# RESPONSE SCHEMAS
# ============================================

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for decoded token data"""
    email: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    user_id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: Optional[str]
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Schema for login response - supports both normal login and MFA"""
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    # MFA fields
    mfa_required: Optional[bool] = None
    email: Optional[str] = None
    message: Optional[str] = None

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True
