# PowerShell script to add Toxic Combinations endpoints to scores.py

Write-Host "🚀 Adding Toxic Combinations endpoints to scores.py..." -ForegroundColor Cyan

# Read the current scores.py
$scoresPath = "backend/app/routers/scores.py"
$content = Get-Content $scoresPath -Raw

# Check if already added
if ($content -match "ToxicCombinationsService") {
    Write-Host "⚠️  Toxic Combinations already added to scores.py!" -ForegroundColor Yellow
    exit 0
}

# 1. Add import at the top (after the remediation_guidance import)
$importToAdd = "from app.services.toxic_combinations_service import ToxicCombinationsService"
$content = $content -replace "(from app.services.remediation_guidance import get_remediation)", "`$1`nfrom app.services.toxic_combinations_service import ToxicCombinationsService"

# 2. Add endpoints at the end
$endpointsToAdd = @"


# ============================================
# TOXIC COMBINATIONS ENDPOINTS
# ============================================

@router.get("/scan/{scan_id}/toxic-combinations")
async def get_toxic_combinations(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    ""\"Get detected toxic combinations (critical risk paths) for a scan""\"
    try:
        combinations = ToxicCombinationsService.detect_toxic_combinations(
            str(scan_id), db
        )
        
        summary = ToxicCombinationsService.get_risk_summary(str(scan_id), db)
        
        return {
            "scan_id": str(scan_id),
            "summary": summary,
            "combinations": combinations
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect toxic combinations: {str(e)}"
        )


@router.get("/account/{account_id}/toxic-combinations")
async def get_account_toxic_combinations(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    ""\"Get toxic combinations for an account's latest scan""\"
    from app.models.assessment_scan import AssessmentScan
    
    # Get latest scan for account
    latest_scan = db.query(AssessmentScan).filter(
        AssessmentScan.account_id == account_id,
        AssessmentScan.status == 'Completed'
    ).order_by(AssessmentScan.completed_at.desc()).first()
    
    if not latest_scan:
        return {
            "account_id": str(account_id),
            "summary": {
                "total_combinations": 0,
                "critical_combinations": 0,
                "high_combinations": 0,
                "average_risk_score": 0,
                "highest_risk_score": 0,
                "requires_immediate_action": 0
            },
            "combinations": []
        }
    
    combinations = ToxicCombinationsService.detect_toxic_combinations(
        str(latest_scan.id), db
    )
    
    summary = ToxicCombinationsService.get_risk_summary(str(latest_scan.id), db)
    
    return {
        "account_id": str(account_id),
        "scan_id": str(latest_scan.id),
        "summary": summary,
        "combinations": combinations
    }
"@

# Append endpoints to the end of the file
$content = $content + $endpointsToAdd

# Write back to file
Set-Content $scoresPath $content

Write-Host "✅ Successfully added Toxic Combinations endpoints!" -ForegroundColor Green
Write-Host "📝 Changes made:" -ForegroundColor Cyan
Write-Host "   1. Added import: ToxicCombinationsService" -ForegroundColor White
Write-Host "   2. Added endpoint: GET /scan/{scan_id}/toxic-combinations" -ForegroundColor White
Write-Host "   3. Added endpoint: GET /account/{account_id}/toxic-combinations" -ForegroundColor White
