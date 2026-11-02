"""
MFA API Endpoints (WITH AUDIT LOGGING)
Location: backend/app/auth/mfa_routes.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.auth.mfa_service import MFAService
from app.routers.auth import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService  # NEW
from sqlalchemy import text

router = APIRouter(prefix="/api/auth/mfa", tags=["MFA"])

class MFAEnableRequest(BaseModel):
    """Request to enable MFA"""
    mfa_email: str
    password: str

class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code"""
    email: str
    code: str

class MFAResendRequest(BaseModel):
    """Request to resend MFA code"""
    email: str

@router.post("/enable")
async def enable_mfa(
    mfa_request: MFAEnableRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable MFA for the current user"""
    from app.auth.utils import verify_password
    
    try:
        # Verify password
        if not verify_password(mfa_request.password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Update user's MFA settings
        db.execute(text("""
            UPDATE users
            SET mfa_enabled = TRUE, mfa_email = :mfa_email
            WHERE user_id = :user_id
        """), {
            "mfa_email": mfa_request.mfa_email,
            "user_id": str(current_user.user_id)
        })
        db.commit()
        
        # AUDIT LOG: MFA enabled
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        AuditService.log_mfa_change(
            db=db,
            user_id=str(current_user.user_id),
            user_email=current_user.email,
            enabled=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": "MFA enabled successfully",
            "mfa_email": mfa_request.mfa_email
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable MFA: {str(e)}"
        )

@router.post("/disable")
async def disable_mfa(
    password: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA for the current user"""
    from app.auth.utils import verify_password
    
    try:
        # Verify password
        if not verify_password(password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Disable MFA
        db.execute(text("""
            UPDATE users
            SET mfa_enabled = FALSE
            WHERE user_id = :user_id
        """), {"user_id": str(current_user.user_id)})
        
        # Invalidate all existing codes
        db.execute(text("""
            UPDATE mfa_codes
            SET used = TRUE
            WHERE user_id = :user_id AND used = FALSE
        """), {"user_id": str(current_user.user_id)})
        
        db.commit()
        
        # AUDIT LOG: MFA disabled
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        AuditService.log_mfa_change(
            db=db,
            user_id=str(current_user.user_id),
            user_email=current_user.email,
            enabled=False,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {"message": "MFA disabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable MFA: {str(e)}"
        )

@router.post("/verify")
async def verify_mfa_code(
    mfa_request: MFAVerifyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify MFA code and complete login"""
    from app.auth.utils import create_access_token
    from datetime import timedelta
    
    try:
        # Get user by email
        result = db.execute(text("""
            SELECT user_id, email, username, role, mfa_enabled
            FROM users
            WHERE email = :email AND is_active = TRUE
        """), {"email": mfa_request.email})
        user = result.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Verify MFA code
        if not MFAService.verify_code(db, str(user.user_id), mfa_request.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired verification code"
            )
        
        # Update last login
        db.execute(text("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """), {"user_id": str(user.user_id)})
        db.commit()
        
        # AUDIT LOG: Successful MFA login
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        AuditService.log_login(
            db=db,
            user_id=str(user.user_id),
            user_email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_used=True,
            success=True
        )
        
        # Get role as string
        role_str = user.role if isinstance(user.role, str) else user.role.value
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": user.email, "role": role_str},
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "username": user.username,
                "role": role_str
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )

@router.post("/resend")
async def resend_mfa_code(
    mfa_request: MFAResendRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """Resend MFA code to user's email"""
    try:
        # Get user info
        result = db.execute(text("""
            SELECT user_id, email, mfa_email, mfa_enabled
            FROM users
            WHERE email = :email AND is_active = TRUE
        """), {"email": mfa_request.email})
        user = result.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )
        
        # Get IP and user agent
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent", "")
        
        # Send new code
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
            "message": "MFA code resent successfully",
            "email": user.mfa_email or user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend code: {str(e)}"
        )

@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get MFA status for current user"""
    try:
        result = db.execute(text("""
            SELECT mfa_enabled, mfa_email
            FROM users
            WHERE user_id = :user_id
        """), {"user_id": str(current_user.user_id)})
        user_data = result.fetchone()
        
        return {
            "mfa_enabled": user_data.mfa_enabled if user_data else False,
            "mfa_email": user_data.mfa_email if user_data else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MFA status: {str(e)}"
        )
