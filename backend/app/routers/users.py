"""
User Management Router (Admin Only)
Location: backend/app/routers/users.py

Endpoints for managing users and permissions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User, UserRole as DBUserRole
from app.models.permission import Permission, RolePermission
from app.schemas.auth import UserResponse
from app.routers.auth import get_current_active_user
from app.auth.utils import get_password_hash, validate_password_strength
from app.auth.permissions import get_user_permissions, has_permission
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["User Management"])


# ============================================
# SCHEMAS
# ============================================

class UserCreate(BaseModel):
    """Schema for creating a new user (admin only)"""
    email: str
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(None, max_length=255)
    role: str = Field(..., description="admin, auditor, or viewer")


class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: str = Field(None, max_length=255)
    role: str = Field(None, description="admin, auditor, or viewer")
    is_active: bool = None


class PermissionResponse(BaseModel):
    """Schema for permission response"""
    permission_id: str
    resource: str
    action: str
    description: str = None


class UserPermissionsResponse(BaseModel):
    """Schema for user with permissions"""
    user: UserResponse
    permissions: List[dict]


# ============================================
# HELPER FUNCTIONS
# ============================================

def check_admin(current_user: User):
    """Check if current user is admin"""
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


# ============================================
# USER MANAGEMENT ENDPOINTS
# ============================================

@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only)
    """
    check_admin(current_user)
    
    users = db.query(User).all()
    return [user.to_dict() for user in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (Admin only)
    """
    check_admin(current_user)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Validate role
    role_upper = user_data.role.upper()
    if role_upper not in ['ADMIN', 'AUDITOR', 'VIEWER']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be admin, auditor, or viewer"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email.lower(),
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=DBUserRole[role_upper],
        is_active=True,
        is_verified=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user.to_dict()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (Admin only)
    """
    check_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user (Admin only)
    """
    check_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if str(current_user.user_id) == user_id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.role is not None:
        role_upper = user_data.role.upper()
        if role_upper not in ['ADMIN', 'AUDITOR', 'VIEWER']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be admin, auditor, or viewer"
            )
        user.role = DBUserRole[role_upper]
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user.to_dict()


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (Admin only)
    """
    check_admin(current_user)
    
    # Prevent self-deletion
    if str(current_user.user_id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user.username} deleted successfully"}


# ============================================
# PERMISSIONS ENDPOINTS
# ============================================

@router.get("/permissions/all", response_model=List[dict])
async def list_all_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all available permissions (Admin only)
    """
    check_admin(current_user)
    
    permissions = db.query(Permission).all()
    return [p.to_dict() for p in permissions]


@router.get("/{user_id}/permissions", response_model=List[dict])
async def get_user_permissions_endpoint(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get permissions for a specific user (Admin only)
    """
    check_admin(current_user)
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permissions = get_user_permissions(user.role.value, db)
    return permissions


@router.get("/role/{role}/permissions", response_model=List[dict])
async def get_role_permissions(
    role: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get permissions for a role (Admin only)
    """
    check_admin(current_user)
    
    role_upper = role.upper()
    if role_upper not in ['ADMIN', 'AUDITOR', 'VIEWER']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    permissions = get_user_permissions(role, db)
    return permissions
