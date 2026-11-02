"""
Security Scans API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.cloud_account import CloudAccount
from app.models.assessment_scan import AssessmentScan
from app.models.scan_finding import ScanFinding
from app.services.prowler_service import ProwlerService
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/scans",
    tags=["Security Scans"]
)


# Pydantic schemas
class ScanRequest(BaseModel):
    """Request to start a security scan"""
    account_id: UUID
    scan_type: str = "Full"
    regions: Optional[list[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "scan_type": "Full",
                "regions": ["us-east-1", "us-west-2"]
            }
        }


class ScanResponse(BaseModel):
    """Response from starting a scan"""
    scan_id: UUID
    status: str
    account_id: UUID
    message: str


class FindingResponse(BaseModel):
    """Individual scan finding"""
    id: int
    check_id: int
    resource_id: str
    resource_type: str
    status: str
    severity: str


@router.post("/start")
async def start_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a security scan on a cloud account

    This endpoint initiates a Prowler security scan in the background.
    The scan may take 5-15 minutes to complete depending on account size.
    """

    # Get cloud account
    account = db.query(CloudAccount).filter(
        CloudAccount.id == scan_request.account_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Cloud account not found")

    if not account.is_active:
        raise HTTPException(status_code=400, detail="Cloud account is not active")

    # Create assessment scan record
    scan = AssessmentScan(
        account_id=account.id,
        scan_type=scan_request.scan_type,
        scan_status="Running",  # Correct field name
        started_at=datetime.utcnow()
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Start scan in background
    background_tasks.add_task(
        execute_scan,
        scan_id=scan.id,
        account_id=account.id,
        regions=scan_request.regions or account.regions
    )

    return {
        "scan_id": str(scan.id),
        "status": "Running",
        "account_id": str(account.id),
        "message": f"Scan started. This may take 5-15 minutes. Check scan status at /api/scans/{scan.id}"
    }


def execute_scan(
    scan_id: UUID,
    account_id: UUID,
    regions: list[str]
):
    """
    Execute Prowler scan in background

    This function runs asynchronously after start_scan returns.
    """

    from app.database import SessionLocal
    db = SessionLocal()

    try:
        # Get scan record
        scan = db.query(AssessmentScan).filter(
            AssessmentScan.id == scan_id
        ).first()

        if not scan:
            print(f"[Scan] Error: Scan {scan_id} not found")
            return

        # Get account
        account = db.query(CloudAccount).filter(
            CloudAccount.id == account_id
        ).first()

        if not account:
            print(f"[Scan] Error: Account {account_id} not found")
            scan.scan_status = "Failed"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return

        # Initialize Prowler
        prowler = ProwlerService()

        # Get AWS credentials from account
        credentials = account.credentials  # JSONB field
        access_key = credentials.get('access_key_id')
        secret_key = credentials.get('secret_access_key')

        if not access_key or not secret_key:
            print(f"[Scan] Error: Missing AWS credentials")
            scan.scan_status = "Failed"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return

        # Run Prowler scan
        print(f"[Scan] Executing Prowler scan {scan_id} for account {account.account_id}")
        print(f"[Scan] Regions: {regions}")

        result = prowler.run_scan(
            cloud_provider="AWS",
            access_key=access_key,
            secret_key=secret_key,
            regions=regions,
            account_id=str(account.account_id)
        )

        if not result.get('success', False):
            print(f"[Scan] Prowler scan failed: {result.get('error', 'Unknown error')}")
            scan.scan_status = "Failed"
            scan.completed_at = datetime.utcnow()
            db.commit()
            return

        # Store findings in database
        findings_stored = 0
        passed_count = 0
        failed_count = 0

        print(f"[Scan] Processing {len(result.get('findings', []))} findings")

        # Get or create a mapping from Prowler check_id (string) to technical_check.id (integer)
        from app.models.technical_check import TechnicalCheck

        for finding_data in result.get('findings', []):
            try:
                prowler_check_id = finding_data['check_id']

                # Try to find matching technical check by check_name
                tech_check = db.query(TechnicalCheck).filter(
                    TechnicalCheck.check_name == prowler_check_id
                ).first()

                if not tech_check:
                    # Create placeholder technical check for unmapped Prowler checks
                    tech_check = TechnicalCheck(
                        check_name=prowler_check_id,
                        check_description=finding_data.get('check_title', ''),
                        cloud_provider='aws',
                        cloud_service=finding_data.get('service_name', 'unknown')
                    )
                    db.add(tech_check)
                    db.flush()  # Get the ID without committing

                # Store finding with integer check_id FK
                finding = ScanFinding(
                    assessment_scan_id=scan.id,  # Model uses assessment_scan_id
                    check_id=tech_check.id,  # Integer FK to technical_checks
                    resource_id=finding_data.get('resource_id', 'unknown')[:500],  # Truncate to fit VARCHAR(500)
                    resource_type=finding_data.get('resource_type', 'unknown')[:100],  # Truncate to fit VARCHAR(100)
                    status=finding_data['status'].capitalize(),  # Pass/Fail/Error/N/A (database constraint)
                    severity=finding_data['severity'].capitalize(),  # Critical/High/Medium/Low/Info
                    finding_details=finding_data  # Store full finding as JSON including prowler check_id
                )
                db.add(finding)
                findings_stored += 1

                # Count pass/fail
                if finding_data['status'].upper() == 'PASS':
                    passed_count += 1
                elif finding_data['status'].upper() == 'FAIL':
                    failed_count += 1

            except Exception as e:
                print(f"[Scan] Error storing finding: {e}")
                import traceback
                traceback.print_exc()
                continue

        # Update scan record
        scan.scan_status = "Completed"
        scan.completed_at = datetime.utcnow()
        scan.total_checks_run = findings_stored

        db.commit()

        print(f"[Scan] Completed scan {scan_id}")
        print(f"[Scan] Findings: {findings_stored} total, {passed_count} passed, {failed_count} failed")

    except Exception as e:
        print(f"[Scan] Error executing scan {scan_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update scan record with error
        try:
            scan = db.query(AssessmentScan).filter(
                AssessmentScan.id == scan_id
            ).first()

            if scan:
                scan.scan_status = "Failed"
                scan.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass

    finally:
        db.close()


@router.get("/account/{account_id}")
async def get_account_scans(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all scans for a specific cloud account
    Returns scans in reverse chronological order (newest first)
    """
    
    scans = db.query(AssessmentScan).filter(
        AssessmentScan.account_id == account_id
    ).order_by(
        AssessmentScan.started_at.desc()
    ).all()
    
    return {
        "account_id": str(account_id),
        "total_scans": len(scans),
        "scans": [
            {
                "scan_id": str(scan.id),
                "scan_status": scan.scan_status,
                "started_at": scan.started_at.isoformat(),
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "total_checks_run": scan.total_checks_run,
                "findings_count": scan.findings_count
            }
            for scan in scans
        ]
    }


@router.get("/{scan_id}")
async def get_scan_status(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get status of a security scan
    """

    scan = db.query(AssessmentScan).filter(
        AssessmentScan.id == scan_id
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "scan_id": str(scan.id),
        "account_id": str(scan.account_id),
        "scan_status": scan.scan_status,  # Correct field name
        "scan_type": scan.scan_type,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at,
        "total_checks_run": scan.total_checks_run,
        "error_log": scan.error_log
    }


@router.get("/{scan_id}/findings")
async def get_scan_findings(
    scan_id: UUID,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get findings from a completed scan

    Optional filters:
    - severity: Filter by severity (critical, high, medium, low)
    - status: Filter by status (PASS, FAIL)
    - limit: Maximum number of findings to return (default 100)
    """

    # Verify scan exists
    scan = db.query(AssessmentScan).filter(
        AssessmentScan.id == scan_id
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Build query
    query = db.query(ScanFinding).filter(
        ScanFinding.assessment_scan_id == scan_id
    )

    # Apply filters
    if severity:
        query = query.filter(ScanFinding.severity == severity.lower())

    if status:
        query = query.filter(ScanFinding.status == status.upper())

    # Get findings
    findings = query.limit(limit).all()

    return {
        "scan_id": str(scan_id),
        "total_findings": len(findings),
        "findings": [
            {
                "id": f.id,
                "check_id": f.check_id,
                "resource_id": f.resource_id,
                "resource_type": f.resource_type,
                "status": f.status,
                "severity": f.severity,
                "finding_details": f.finding_details
            }
            for f in findings
        ]
    }


@router.get("/prowler-checks")
async def get_prowler_checks():
    """
    Get catalog of available Prowler security checks
    """

    prowler = ProwlerService()
    catalog = prowler.get_check_catalog()

    return catalog
