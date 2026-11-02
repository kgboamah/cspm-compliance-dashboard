"""
Audit Logging Service (FIXED - uses event_metadata)
Location: backend/app/services/audit_service.py
"""
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Service for logging security and user events"""
    
    @staticmethod
    def log_event(
        db: Session,
        user_id: Optional[str],
        event_type: str,
        event_category: str,
        event_description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None,
        status: str = "success"
    ) -> bool:
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                event_category=event_category,
                event_description=event_description,
                ip_address=ip_address,
                user_agent=user_agent,
                event_metadata=metadata,  # CHANGED: use event_metadata
                status=status
            )
            
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Audit log created: {event_type} - {event_description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def log_login(
        db: Session,
        user_id: str,
        user_email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        mfa_used: bool = False,
        success: bool = True
    ):
        """Log a login attempt"""
        status = "success" if success else "failure"
        mfa_text = " with MFA" if mfa_used else ""
        
        AuditService.log_event(
            db=db,
            user_id=user_id if success else None,
            event_type="login",
            event_category="authentication",
            event_description=f"User {user_email} logged in{mfa_text}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email, "mfa_used": mfa_used},
            status=status
        )
    
    @staticmethod
    def log_logout(
        db: Session,
        user_id: str,
        user_email: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log a logout"""
        AuditService.log_event(
            db=db,
            user_id=user_id,
            event_type="logout",
            event_category="authentication",
            event_description=f"User {user_email} logged out",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email},
            status="success"
        )
    
    @staticmethod
    def log_mfa_change(
        db: Session,
        user_id: str,
        user_email: str,
        enabled: bool,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log MFA enable/disable"""
        action = "enabled" if enabled else "disabled"
        
        AuditService.log_event(
            db=db,
            user_id=user_id,
            event_type=f"mfa_{action}",
            event_category="security",
            event_description=f"User {user_email} {action} MFA",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email, "mfa_enabled": enabled},
            status="success"
        )
    
    @staticmethod
    def log_password_change(
        db: Session,
        user_id: str,
        user_email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool = True
    ):
        """Log password change"""
        status = "success" if success else "failure"
        
        AuditService.log_event(
            db=db,
            user_id=user_id,
            event_type="password_changed",
            event_category="security",
            event_description=f"User {user_email} changed password",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email},
            status=status
        )
    
    @staticmethod
    def log_failed_login(
        db: Session,
        user_email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        reason: str = "Invalid credentials"
    ):
        """Log failed login attempt"""
        AuditService.log_event(
            db=db,
            user_id=None,
            event_type="login_failed",
            event_category="authentication",
            event_description=f"Failed login attempt for {user_email}: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email, "reason": reason},
            status="failure"
        )
    
    @staticmethod
    def log_account_created(
        db: Session,
        user_id: str,
        user_email: str,
        created_by: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log account creation"""
        AuditService.log_event(
            db=db,
            user_id=user_id,
            event_type="account_created",
            event_category="account",
            event_description=f"Account created for {user_email}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email, "created_by": created_by},
            status="success"
        )
    
    @staticmethod
    def log_account_deleted(
        db: Session,
        user_id: str,
        user_email: str,
        deleted_by: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log account deletion"""
        AuditService.log_event(
            db=db,
            user_id=user_id,
            event_type="account_deleted",
            event_category="admin",
            event_description=f"Account {user_email} deleted by {deleted_by}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": user_email, "deleted_by": deleted_by},
            status="success"
        )
