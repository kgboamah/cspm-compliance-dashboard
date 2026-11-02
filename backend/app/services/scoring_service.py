"""
Compliance Scoring Service - FIXED VERSION
Calculates compliance scores based on scan findings
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Dict, List
from uuid import UUID
from datetime import datetime

from app.models.assessment_scan import AssessmentScan
from app.models.scan_finding import ScanFinding
from app.models.compliance_framework import ComplianceFramework
from app.models.framework_control import FrameworkControl
from app.models.technical_check import TechnicalCheck
from app.models.control_check_mapping import ControlCheckMapping
from app.models.compliance_score import ComplianceScore


class ScoringService:
    """Service for calculating compliance scores"""

    def __init__(self, db: Session):
        """Initialize scoring service"""
        self.db = db

    def calculate_scan_scores(self, scan_id: UUID) -> List[Dict]:
        """
        Calculate compliance scores for a completed scan

        Args:
            scan_id: Assessment scan ID

        Returns:
            List of score dictionaries per framework
        """
        # Get scan
        scan = self.db.query(AssessmentScan).filter(
            AssessmentScan.id == scan_id
        ).first()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        # Check scan status
        if scan.scan_status != "Completed":
            raise ValueError(f"Scan {scan_id} is not completed (status: {scan.scan_status})")

        # Get all frameworks
        frameworks = self.db.query(ComplianceFramework).all()

        scores = []
        for framework in frameworks:
            score_data = self._calculate_framework_score(
                scan_id=scan_id,
                scan=scan,
                framework=framework
            )

            # Store score in database
            score_record = self._save_score(
                scan_id=scan_id,
                account_id=scan.account_id,
                framework_id=framework.id,
                score_data=score_data
            )

            scores.append({
                "framework": framework.framework_name,
                "score_id": score_record.id,
                "overall_score": float(score_data['overall_score']),
                "controls_passed": score_data['controls_passed'],
                "controls_failed": score_data['controls_failed'],
                "controls_not_applicable": score_data['controls_not_applicable'],
                "total_controls": score_data['total_controls']
            })

        return scores

    def _calculate_framework_score(
        self,
        scan_id: UUID,
        scan: AssessmentScan,
        framework: ComplianceFramework
    ) -> Dict:
        """
        Calculate score for a specific framework

        Args:
            scan_id: Assessment scan ID
            scan: Assessment scan object
            framework: Compliance framework

        Returns:
            Dictionary with score breakdown
        """
        # Get all controls for this framework
        controls = self.db.query(FrameworkControl).filter(
            FrameworkControl.framework_id == framework.id
        ).all()

        if not controls:
            return {
                "overall_score": 0.0,
                "total_controls": 0,
                "controls_passed": 0,
                "controls_failed": 0,
                "controls_not_applicable": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0
            }

        # Calculate per-control scores
        passed_count = 0
        failed_count = 0
        na_count = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for control in controls:
            control_result = self._evaluate_control(
                scan_id=scan_id,
                control=control
            )

            if control_result['status'] == 'PASS':
                passed_count += 1
            elif control_result['status'] == 'FAIL':
                failed_count += 1
                # Count findings by severity
                critical_count += control_result.get('critical_findings', 0)
                high_count += control_result.get('high_findings', 0)
                medium_count += control_result.get('medium_findings', 0)
                low_count += control_result.get('low_findings', 0)
            elif control_result['status'] == 'N/A':
                na_count += 1

        # Calculate overall percentage
        applicable_controls = len(controls) - na_count
        if applicable_controls == 0:
            overall_score = 0.0
        else:
            overall_score = (passed_count / applicable_controls) * 100

        return {
            "overall_score": round(overall_score, 2),
            "total_controls": len(controls),
            "controls_passed": passed_count,
            "controls_failed": failed_count,
            "controls_not_applicable": na_count,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
            "low_findings": low_count
        }

    def _evaluate_control(
        self,
        scan_id: UUID,
        control: FrameworkControl
    ) -> Dict:
        """
        Evaluate a single control based on scan findings

        Args:
            scan_id: Assessment scan ID
            control: Framework control

        Returns:
            Dictionary with control evaluation
        """
        # Get technical checks mapped to this control
        mappings = self.db.query(ControlCheckMapping).filter(
            ControlCheckMapping.control_id == control.id
        ).all()

        if not mappings:
            # No checks mapped = Not Applicable
            return {
                "control_id": control.control_id,
                "status": "N/A",
                "passed_checks": 0,
                "failed_checks": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0
            }

        # Get check IDs
        check_ids = [m.check_id for m in mappings]

        # Get technical check names for these IDs
        tech_checks = self.db.query(TechnicalCheck).filter(
            TechnicalCheck.id.in_(check_ids)
        ).all()
        
        check_names = [tc.check_name for tc in tech_checks]

        if not check_names:
            return {
                "control_id": control.control_id,
                "status": "N/A",
                "passed_checks": 0,
                "failed_checks": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0
            }

        # FIXED: Query findings using JSON field and correct column names
        # Use raw SQL for JSON querying
        query = text("""
            SELECT 
                finding_status,
                risk_level
            FROM scan_findings
            WHERE scan_id = :scan_id
            AND finding_details->>'check_id' = ANY(:check_names)
        """)
        
        result = self.db.execute(
            query, 
            {"scan_id": str(scan_id), "check_names": check_names}
        ).fetchall()

        if not result:
            # Checks exist but no findings = Not run
            return {
                "control_id": control.control_id,
                "status": "N/A",
                "passed_checks": 0,
                "failed_checks": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 0
            }

        # FIXED: Use correct values - "Pass"/"Fail" not "PASS"/"FAIL"
        # And use correct column names from result
        passed = sum(1 for row in result if row[0] == "Pass")
        failed = sum(1 for row in result if row[0] == "Fail")

        # FIXED: Count by severity - "Critical"/"High"/"Medium"/"Low"
        critical = sum(1 for row in result if row[0] == "Fail" and row[1] == "Critical")
        high = sum(1 for row in result if row[0] == "Fail" and row[1] == "High")
        medium = sum(1 for row in result if row[0] == "Fail" and row[1] == "Medium")
        low = sum(1 for row in result if row[0] == "Fail" and row[1] == "Low")

        # Determine control status
        if failed == 0:
            status = "PASS"
        elif passed == 0:
            status = "FAIL"
        else:
            status = "PARTIAL"  # Some checks passed, some failed

        return {
            "control_id": control.control_id,
            "status": status,
            "passed_checks": passed,
            "failed_checks": failed,
            "critical_findings": critical,
            "high_findings": high,
            "medium_findings": medium,
            "low_findings": low
        }

    def _save_score(
        self,
        scan_id: UUID,
        account_id: UUID,
        framework_id: int,
        score_data: Dict
    ) -> ComplianceScore:
        """
        Save compliance score to database

        Args:
            scan_id: Assessment scan ID
            account_id: Cloud account ID
            framework_id: Compliance framework ID
            score_data: Score breakdown

        Returns:
            ComplianceScore record
        """
        # Check if score already exists
        existing = self.db.query(ComplianceScore).filter(
            ComplianceScore.scan_id == scan_id,
            ComplianceScore.framework_id == framework_id
        ).first()

        if existing:
            # Update existing
            existing.overall_score = score_data['overall_score']
            existing.controls_passed = score_data['controls_passed']
            existing.controls_failed = score_data['controls_failed']
            existing.controls_not_applicable = score_data['controls_not_applicable']
            existing.critical_findings = score_data['critical_findings']
            existing.high_findings = score_data['high_findings']
            existing.medium_findings = score_data['medium_findings']
            existing.low_findings = score_data['low_findings']
            existing.calculated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new score
        score = ComplianceScore(
            scan_id=scan_id,
            account_id=account_id,
            framework_id=framework_id,
            overall_score=score_data['overall_score'],
            controls_passed=score_data['controls_passed'],
            controls_failed=score_data['controls_failed'],
            controls_not_applicable=score_data['controls_not_applicable'],
            critical_findings=score_data['critical_findings'],
            high_findings=score_data['high_findings'],
            medium_findings=score_data['medium_findings'],
            low_findings=score_data['low_findings'],
            calculated_at=datetime.utcnow()
        )

        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)

        return score

    def get_latest_scores(self, cloud_account_id: UUID) -> List[Dict]:
        """
        Get latest compliance scores for a cloud account

        Args:
            cloud_account_id: Cloud account ID

        Returns:
            List of latest scores per framework
        """
        # Get most recent completed scan
        latest_scan = self.db.query(AssessmentScan).filter(
            AssessmentScan.account_id == cloud_account_id,
            AssessmentScan.scan_status == "Completed"
        ).order_by(
            AssessmentScan.completed_at.desc()
        ).first()

        if not latest_scan:
            return []

        # Get scores for this scan
        scores = self.db.query(ComplianceScore).filter(
            ComplianceScore.scan_id == latest_scan.id
        ).all()

        result = []
        for score in scores:
            framework = self.db.query(ComplianceFramework).filter(
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
                "scan_date": latest_scan.completed_at
            })

        return result
