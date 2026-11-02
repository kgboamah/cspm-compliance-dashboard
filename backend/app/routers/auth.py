"""
Authentication Router - WITH AUDIT LOGGING
Location: backend/app/routers/auth.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Annotated

from app.database import get_db
from app.models.user import User, UserRole as DBUserRole
from app.schemas.auth import (
    UserRegister, UserLogin, UserResponse, Token,
    LoginResponse, MessageResponse, PasswordChange, UserUpdate,
    UserSettings, PasswordResetRequest, PasswordResetVerify
)
from app.auth.utils import (
    get_password_hash, verify_password, create_access_token,
    get_current_user_email, validate_password_strength, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.auth.mfa_service import MFAService
from app.services.audit_service import AuditService  # NEW: Audit logging

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ============================================
# DEPENDENCY: Get Current User
# ============================================

async def get_current_user(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from database"""
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active"""
    return current_user

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
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
    
    # Check if this is the first user (make them admin)
    user_count = db.query(User).count()
    role = DBUserRole.ADMIN if user_count == 0 else DBUserRole[user_data.role.value.upper()]
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=role,
        is_active=True,
        is_verified=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # AUDIT LOG: Account created
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    AuditService.log_account_created(
        db=db,
        user_id=str(new_user.user_id),
        user_email=new_user.email,
        created_by="self-registration",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return new_user.to_dict()

@router.post("/login", response_model=LoginResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email and password (WITH MFA SUPPORT)"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    # Find user by email
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user:
        # AUDIT LOG: Failed login - user not found
        AuditService.log_failed_login(
            db=db,
            user_email=user_credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="User not found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        # AUDIT LOG: Failed login - wrong password
        AuditService.log_failed_login(
            db=db,
            user_email=user_credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Invalid password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        # AUDIT LOG: Failed login - account inactive
        AuditService.log_failed_login(
            db=db,
            user_email=user_credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Account inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # === MFA CHECK ===
    if user.mfa_enabled:
        success = MFAService.create_and_send_code(
            db=db,
            user_id=str(user.user_id),
            user_email=user.email,
            mfa_email=user.mfa_email or user.email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send MFA code"
            )
        
        return {
            "mfa_required": True,
            "email": user.email,
            "message": "MFA code sent to your email"
        }
    
    # MFA not enabled - proceed with normal login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # AUDIT LOG: Successful login (no MFA)
    AuditService.log_login(
        db=db,
        user_id=str(user.user_id),
        user_email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        mfa_used=False,
        success=True
    )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login (for Swagger UI)"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user.to_dict()

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout current user"""
    # AUDIT LOG: User logout
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    AuditService.log_logout(
        db=db,
        user_id=str(current_user.user_id),
        user_email=current_user.email,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "message": f"User {current_user.username} logged out successfully",
        "success": True
    }

@router.put("/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        # AUDIT LOG: Failed password change
        AuditService.log_password_change(
            db=db,
            user_id=str(current_user.user_id),
            user_email=current_user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    # AUDIT LOG: Successful password change
    AuditService.log_password_change(
        db=db,
        user_id=str(current_user.user_id),
        user_email=current_user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True
    )
    
    return {
        "message": "Password changed successfully",
        "success": True
    }

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    
    if profile_data.email is not None:
        existing = db.query(User).filter(
            User.email == profile_data.email,
            User.user_id != current_user.user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = profile_data.email
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user.to_dict()

# ============================================
# SETTINGS ENDPOINT
# ============================================

@router.get("/settings", response_model=UserSettings)
async def get_user_settings(current_user: User = Depends(get_current_active_user)):
    """Get current user's security settings"""
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_email": current_user.mfa_email,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }

# ============================================
# PASSWORD RESET ENDPOINTS
# ============================================

@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request password reset - sends code to user's email"""
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    if not user:
        return {
            "message": "If an account exists with this email, a reset code has been sent",
            "success": True
        }
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    success = MFAService.create_and_send_code(
        db=db,
        user_id=str(user.user_id),
        user_email=user.email,
        mfa_email=user.email,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset code"
        )
    
    return {
        "message": "If an account exists with this email, a reset code has been sent",
        "success": True
    }

@router.post("/password-reset/verify", response_model=MessageResponse)
async def verify_password_reset(
    reset_data: PasswordResetVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify reset code and change password"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset code"
        )
    
    is_valid = MFAService.verify_code(
        db=db,
        user_id=str(user.user_id),
        code=reset_data.code
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset code"
        )
    
    validate_password_strength(reset_data.new_password)
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # AUDIT LOG: Password reset
    AuditService.log_event(
        db=db,
        user_id=str(user.user_id),
        event_type="password_reset",
        event_category="security",
        event_description=f"Password reset for {user.email}",
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"email": user.email},
        status="success"
    )
    
    return {"message": "Password successfully reset", "success": True}

# ============================================
# ADMIN ENDPOINTS (User Management)
# ============================================

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)"""
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).all()
    return [user.to_dict() for user in users]

@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user (Admin only)"""
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
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
    
    # AUDIT LOG: Account deleted
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    AuditService.log_account_deleted(
        db=db,
        user_id=str(user.user_id),
        user_email=user.email,
        deleted_by=current_user.email,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.delete(user)
    db.commit()
    
    return {
        "message": f"User {user.username} deleted successfully",
        "success": True
    }
