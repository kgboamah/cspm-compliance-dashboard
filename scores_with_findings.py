"""
Compliance Scores API Endpoints - WITH FINDINGS BREAKDOWN
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from typing import Optional
from app.database import get_db
from app.services.scoring_service import ScoringService

router = APIRouter(
    prefix="/api/scores",
    tags=["Compliance Scores"]
)

@router.post("/{scan_id}/calculate")
async def calculate_scores(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Calculate compliance scores for a completed scan
    This endpoint analyzes scan findings and calculates
    compliance percentages for all frameworks.
    """
    try:
        scoring_service = ScoringService(db)
        scores = scoring_service.calculate_scan_scores(scan_id)
        return {
            "scan_id": str(scan_id),
            "scores": scores,
            "message": f"Calculated scores for {len(scores)} frameworks"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@router.get("/account/{account_id}")
async def get_account_scores(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get latest compliance scores for a cloud account
    Returns the most recent compliance scores from
    the latest completed scan.
    """
    scoring_service = ScoringService(db)
    scores = scoring_service.get_latest_scores(account_id)
    
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="No completed scans found for this account"
        )
    
    return {
        "account_id": str(account_id),
        "scores": scores
    }

@router.get("/scan/{scan_id}")
async def get_scan_scores(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get compliance scores for a specific scan
    """
    from app.models.compliance_score import ComplianceScore
    from app.models.compliance_framework import ComplianceFramework
    
    scores = db.query(ComplianceScore).filter(
        ComplianceScore.scan_id == scan_id
    ).all()
    
    if not scores:
        raise HTTPException(
            status_code=404,
            detail="No scores found for this scan"
        )
    
    result = []
    for score in scores:
        framework = db.query(ComplianceFramework).filter(
            ComplianceFramework.id == score.framework_id
        ).first()
        
        total_controls = score.controls_passed + score.controls_failed + score.controls_not_applicable
        
        result.append({
            "framework": framework.framework_name,
            "overall_score": float(score.overall_score),
            "controls_passed": score.controls_passed,
            "controls_failed": score.controls_failed,
            "controls_not_applicable": score.controls_not_applicable,
            "total_controls": total_controls,
            "critical_findings": score.critical_findings,
            "high_findings": score.high_findings,
            "medium_findings": score.medium_findings,
            "low_findings": score.low_findings,
            "calculated_at": score.calculated_at
        })
    
    return {
        "scan_id": str(scan_id),
        "scores": result
    }

@router.get("/scan/{scan_id}/findings")
async def get_scan_findings_breakdown(
    scan_id: UUID,
    framework: Optional[str] = Query(None, description="Filter by framework name (e.g., 'ISO 27001')"),
    severity: Optional[str] = Query(None, description="Filter by severity (Critical, High, Medium, Low)"),
    status: Optional[str] = Query(None, description="Filter by status (Pass, Fail)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of findings to return"),
    db: Session = Depends(get_db)
):
    """
    Get detailed findings breakdown for a scan
    
    Query params:
    - framework: Filter by framework name (e.g., "ISO 27001")
    - severity: Filter by severity (Critical, High, Medium, Low)
    - status: Filter by status (Pass, Fail)
    - limit: Maximum findings to return (default 100, max 1000)
    
    Returns detailed list of findings with control mappings
    """
    
    # Base query
    query = """
        SELECT 
            sf.id,
            sf.finding_details->>'check_id' as check_id,
            sf.finding_details->>'check_title' as check_title,
            sf.finding_status,
            sf.risk_level,
            sf.resource_id,
            sf.resource_type,
            sf.discovered_at,
            -- Get mapped controls
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'framework', cf.framework_name,
                        'control_id', fc.control_id,
                        'control_title', fc.control_title
                    )
                ) FILTER (WHERE cf.framework_name IS NOT NULL),
                '[]'
            ) as mapped_controls
        FROM scan_findings sf
        LEFT JOIN technical_checks tc ON tc.check_name = (sf.finding_details->>'check_id')
        LEFT JOIN control_check_mappings ccm ON ccm.check_id = tc.id
        LEFT JOIN framework_controls fc ON fc.id = ccm.control_id
        LEFT JOIN compliance_frameworks cf ON cf.id = fc.framework_id
        WHERE sf.scan_id = :scan_id
    """
    
    params = {"scan_id": str(scan_id)}
    
    # Add filters
    if framework:
        query += " AND cf.framework_name = :framework"
        params["framework"] = framework
    
    if severity:
        query += " AND sf.risk_level = :severity"
        params["severity"] = severity
    
    if status:
        query += " AND sf.finding_status = :status"
        params["status"] = status
    
    query += """
        GROUP BY sf.id, sf.finding_details, sf.finding_status, sf.risk_level, 
                 sf.resource_id, sf.resource_type, sf.discovered_at
        ORDER BY 
            CASE sf.risk_level
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END,
            sf.discovered_at DESC
        LIMIT :limit
    """
    
    params["limit"] = limit
    
    results = db.execute(text(query), params).fetchall()
    
    findings = []
    for row in results:
        findings.append({
            "finding_id": row[0],
            "check_id": row[1],
            "check_title": row[2],
            "status": row[3],
            "severity": row[4],
            "resource_id": row[5],
            "resource_type": row[6],
            "discovered_at": row[7].isoformat() if row[7] else None,
            "mapped_controls": row[8]
        })
    
    # Get summary stats
    summary_query = text("""
        SELECT 
            risk_level,
            finding_status,
            COUNT(*) as count
        FROM scan_findings
        WHERE scan_id = :scan_id
        GROUP BY risk_level, finding_status
        ORDER BY 
            CASE risk_level
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END
    """)
    
    summary_results = db.execute(summary_query, {"scan_id": str(scan_id)}).fetchall()
    
    summary = {}
    total = 0
    for row in summary_results:
        severity_level = row[0]
        status_val = row[1]
        count = row[2]
        total += count
        
        if severity_level not in summary:
            summary[severity_level] = {"Pass": 0, "Fail": 0}
        summary[severity_level][status_val] = count
    
    return {
        "scan_id": str(scan_id),
        "total_findings": total,
        "returned_findings": len(findings),
        "summary": summary,
        "findings": findings
    }
