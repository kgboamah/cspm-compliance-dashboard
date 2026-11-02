"""
Audit Logs Router - FIXED (ambiguous column names)
Location: backend/app/routers/audit_logs.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User, UserRole as DBUserRole
from app.routers.auth import get_current_active_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])

class AuditLogResponse(BaseModel):
    log_id: str
    user_id: Optional[str]
    user_email: Optional[str]
    event_type: str
    event_category: str
    event_description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[dict]
    status: str
    created_at: str

class AuditLogsListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

@router.get("/", response_model=AuditLogsListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_category: Optional[str] = Query(None, description="Filter by category"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: Optional[int] = Query(7, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit logs (Admin only)"""
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    offset = (page - 1) * page_size
    
    where_conditions = []
    params = {"offset": offset, "limit": page_size}
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        where_conditions.append("al.created_at >= :cutoff_date")  # FIXED: al.created_at
        params["cutoff_date"] = cutoff_date
    
    if event_type:
        where_conditions.append("al.event_type = :event_type")
        params["event_type"] = event_type
    
    if event_category:
        where_conditions.append("al.event_category = :event_category")
        params["event_category"] = event_category
    
    if user_id:
        where_conditions.append("al.user_id = :user_id")
        params["user_id"] = user_id
    
    if status:
        where_conditions.append("al.status = :status")
        params["status"] = status
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM audit_logs al WHERE {where_clause}"
    count_result = db.execute(text(count_query), params).fetchone()
    total = count_result.total if count_result else 0
    
    # Get logs with user info
    query = f"""
        SELECT 
            al.log_id,
            al.user_id,
            u.email as user_email,
            al.event_type,
            al.event_category,
            al.event_description,
            al.ip_address,
            al.user_agent,
            al.event_metadata,
            al.status,
            al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.user_id
        WHERE {where_clause}
        ORDER BY al.created_at DESC
        LIMIT :limit OFFSET :offset
    """
    
    result = db.execute(text(query), params)
    logs = []
    
    for row in result:
        logs.append({
            "log_id": str(row.log_id),
            "user_id": str(row.user_id) if row.user_id else None,
            "user_email": row.user_email,
            "event_type": row.event_type,
            "event_category": row.event_category,
            "event_description": row.event_description,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "metadata": row.event_metadata,
            "status": row.status,
            "created_at": row.created_at.isoformat()
        })
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/stats")
async def get_audit_stats(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit log statistics (Admin only)"""
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    event_counts_query = """
        SELECT event_type, COUNT(*) as count
        FROM audit_logs
        WHERE created_at >= :cutoff_date
        GROUP BY event_type
        ORDER BY count DESC
    """
    event_counts = db.execute(text(event_counts_query), {"cutoff_date": cutoff_date}).fetchall()
    
    failed_logins_query = """
        SELECT COUNT(*) as count
        FROM audit_logs
        WHERE event_type = 'login_failed' 
        AND created_at >= :cutoff_date
    """
    failed_logins = db.execute(text(failed_logins_query), {"cutoff_date": cutoff_date}).fetchone()
    
    category_query = """
        SELECT event_category, COUNT(*) as count
        FROM audit_logs
        WHERE created_at >= :cutoff_date
        GROUP BY event_category
        ORDER BY count DESC
    """
    categories = db.execute(text(category_query), {"cutoff_date": cutoff_date}).fetchall()
    
    total_query = """
        SELECT COUNT(*) as total
        FROM audit_logs
        WHERE created_at >= :cutoff_date
    """
    total = db.execute(text(total_query), {"cutoff_date": cutoff_date}).fetchone()
    
    return {
        "total_events": total.total if total else 0,
        "failed_logins": failed_logins.count if failed_logins else 0,
        "event_types": [{"type": row.event_type, "count": row.count} for row in event_counts],
        "categories": [{"category": row.event_category, "count": row.count} for row in categories],
        "time_period_days": days
    }

@router.get("/export/csv")
async def export_audit_logs_csv(
    days: int = Query(30, description="Number of days to export"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export audit logs as CSV (Admin only)"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    if current_user.role != DBUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            al.log_id,
            u.email as user_email,
            al.event_type,
            al.event_category,
            al.event_description,
            al.ip_address,
            al.status,
            al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.user_id
        WHERE al.created_at >= :cutoff_date
        ORDER BY al.created_at DESC
    """
    
    result = db.execute(text(query), {"cutoff_date": cutoff_date})
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Log ID', 'User Email', 'Event Type', 'Category', 'Description', 'IP Address', 'Status', 'Timestamp'])
    
    for row in result:
        writer.writerow([
            str(row.log_id),
            row.user_email or 'N/A',
            row.event_type,
            row.event_category,
            row.event_description,
            row.ip_address or 'N/A',
            row.status,
            row.created_at.isoformat()
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
