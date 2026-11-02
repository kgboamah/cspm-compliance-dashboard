"""
Permission Utilities
Location: backend/app/auth/permissions.py

Functions for checking user permissions
"""
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.permission import Permission, RolePermission
from app.auth.utils import get_current_user_email


def get_user_permissions(user_role: str, db: Session) -> list:
    """
    Get all permissions for a user role
    
    Args:
        user_role: User's role (admin, auditor, viewer)
        db: Database session
    
    Returns:
        List of permission dictionaries
    """
    permissions = db.query(Permission).join(
        RolePermission, 
        Permission.permission_id == RolePermission.permission_id
    ).filter(
        RolePermission.role == user_role.upper()
    ).all()
    
    return [p.to_dict() for p in permissions]


def has_permission(user_role: str, resource: str, action: str, db: Session) -> bool:
    """
    Check if a role has a specific permission
    
    Args:
        user_role: User's role
        resource: Resource name (e.g., 'scans', 'findings')
        action: Action type ('read', 'write', 'execute')
        db: Database session
    
    Returns:
        True if role has permission, False otherwise
    """
    permission = db.query(Permission).join(
        RolePermission,
        Permission.permission_id == RolePermission.permission_id
    ).filter(
        RolePermission.role == user_role.upper(),
        Permission.resource == resource,
        Permission.action == action
    ).first()
    
    return permission is not None


def require_permission(resource: str, action: str):
    """
    Decorator to require specific permission for an endpoint
    
    Usage:
        @router.get("/scans")
        @require_permission("scans", "read")
        async def get_scans(current_user: User = Depends(get_current_active_user)):
            ...
    """
    def decorator(func):
        async def wrapper(*args, current_user: User = None, db: Session = None, **kwargs):
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session required"
                )
            
            # Check permission
            if not has_permission(current_user.role.value, resource, action, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {resource}.{action} not allowed for role {current_user.role.value}"
                )
            
            return await func(*args, current_user=current_user, db=db, **kwargs)
        
        return wrapper
    return decorator


async def get_current_user_with_permissions(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current user with their permissions
    
    Returns:
        Dictionary with user info and permissions list
    """
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
    
    # Get user permissions
    permissions = get_user_permissions(user.role.value, db)
    
    return {
        "user": user.to_dict(),
        "permissions": permissions
    }
