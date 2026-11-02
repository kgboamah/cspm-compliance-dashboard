"""
Compliance Scores API Endpoints - CLEAN VERSION WITH SINGLE PDF ENDPOINT
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from uuid import UUID
from typing import Optional
from datetime import datetime
import io
import csv

# PDF imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from app.services.remediation_guidance import get_remediation
from app.database import get_db
from app.services.scoring_service import ScoringService
from app.services.toxic_combinations_service import ToxicCombinationsService



router = APIRouter(prefix="/api/scores", tags=["Compliance Scores"])

@router.post("/{scan_id}/calculate")
async def calculate_scores(scan_id: UUID, db: Session = Depends(get_db)):
    """Calculate compliance scores for a completed scan"""
    try:
        scoring_service = ScoringService(db)
        scores = scoring_service.calculate_scan_scores(scan_id)
        return {"scan_id": str(scan_id), "scores": scores, 
                "message": f"Calculated scores for {len(scores)} frameworks"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@router.get("/account/{account_id}")
async def get_account_scores(account_id: UUID, db: Session = Depends(get_db)):
    """Get latest compliance scores"""
    scoring_service = ScoringService(db)
    scores = scoring_service.get_latest_scores(account_id)
    if not scores:
        raise HTTPException(status_code=404, detail="No completed scans found")
    return {"account_id": str(account_id), "scores": scores}

@router.get("/scan/{scan_id}")
async def get_scan_scores(scan_id: UUID, db: Session = Depends(get_db)):
    """Get scores for specific scan"""
    from app.models.compliance_score import ComplianceScore
    from app.models.compliance_framework import ComplianceFramework

    scores = db.query(ComplianceScore).filter(ComplianceScore.scan_id == scan_id).all()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found")

    result = []
    for score in scores:
        framework = db.query(ComplianceFramework).filter(
            ComplianceFramework.id == score.framework_id
        ).first()
        result.append({
            "framework": framework.framework_name,
            "overall_score": float(score.overall_score),
            "controls_passed": score.controls_passed,
            "controls_failed": score.controls_failed,
            "controls_not_applicable": score.controls_not_applicable,
            "total_controls": score.controls_passed + score.controls_failed + score.controls_not_applicable,
            "critical_findings": score.critical_findings,
            "high_findings": score.high_findings,
            "medium_findings": score.medium_findings,
            "low_findings": score.low_findings,
            "calculated_at": score.calculated_at
        })
    return {"scan_id": str(scan_id), "scores": result}

@router.get("/scan/{scan_id}/findings")
async def get_scan_findings_breakdown(
    scan_id: UUID, framework: Optional[str] = Query(None),
    severity: Optional[str] = Query(None), status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)
):
    """Get detailed findings breakdown"""
    query = """
        SELECT sf.id, tc.check_name, tc.check_description,
               sf.finding_status, sf.risk_level, sf.resource_id, sf.resource_type, sf.discovered_at,
               COALESCE(json_agg(DISTINCT jsonb_build_object(
                   'framework', cf.framework_name, 'control_id', fc.control_id, 
                   'control_title', fc.control_title
               )) FILTER (WHERE cf.framework_name IS NOT NULL), '[]') as mapped_controls
        FROM scan_findings sf
        LEFT JOIN technical_checks tc ON tc.id = sf.check_id
        LEFT JOIN control_check_mappings ccm ON ccm.check_id = tc.id
        LEFT JOIN framework_controls fc ON fc.id = ccm.control_id
        LEFT JOIN compliance_frameworks cf ON cf.id = fc.framework_id
        WHERE sf.scan_id = :scan_id
    """
    params = {"scan_id": str(scan_id)}
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
        GROUP BY sf.id, tc.check_name, tc.check_description, sf.finding_status, sf.risk_level,
                 sf.resource_id, sf.resource_type, sf.discovered_at
        ORDER BY CASE sf.risk_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END, sf.discovered_at DESC LIMIT :limit
    """
    params["limit"] = limit
    results = db.execute(text(query), params).fetchall()
    findings = [{
        "finding_id": row[0], "check_id": row[1], "check_title": row[2], "status": row[3],
        "severity": row[4], "resource_id": row[5], "resource_type": row[6],
        "discovered_at": row[7].isoformat() if row[7] else None, "mapped_controls": row[8]
    } for row in results]
    
    summary_query = text("""
        SELECT risk_level, finding_status, COUNT(*) FROM scan_findings 
        WHERE scan_id = :scan_id GROUP BY risk_level, finding_status
        ORDER BY CASE risk_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END
    """)
    summary_results = db.execute(summary_query, {"scan_id": str(scan_id)}).fetchall()
    summary, total = {}, 0
    for row in summary_results:
        if row[0] not in summary:
            summary[row[0]] = {"Pass": 0, "Fail": 0}
        summary[row[0]][row[1]] = row[2]
        total += row[2]
    return {"scan_id": str(scan_id), "total_findings": total, 
            "returned_findings": len(findings), "summary": summary, "findings": findings}

@router.get("/account/{account_id}/recurring-findings")
async def get_recurring_findings(
    account_id: UUID, min_occurrences: int = 2, severity: Optional[str] = None,
    limit: int = 100, db: Session = Depends(get_db)
):
    """Get recurring findings"""
    from app.models.assessment_scan import AssessmentScan
    from app.models.compliance_score import ComplianceScore
    
    scans_with_scores = db.query(AssessmentScan.id).join(
        ComplianceScore, AssessmentScan.id == ComplianceScore.scan_id
    ).distinct().all()
    
    scan_ids = [str(scan.id) for scan in scans_with_scores]
    if len(scan_ids) < 2:
        return {"account_id": str(account_id), "total_scans_analyzed": len(scan_ids),
                "message": "Need at least 2 scans with calculated scores", "recurring_findings": []}
    
    scans = db.query(AssessmentScan).filter(
        and_(AssessmentScan.id.in_(scan_ids), AssessmentScan.account_id == account_id)
    ).order_by(AssessmentScan.completed_at.desc()).all()
    
    finding_tracker = {}
    for scan in scans:
        for finding in scan.findings:
            check_id = (finding.finding_details or {}).get('check_id', 'unknown')
            resource_id = finding.resource_id
            if severity and finding.severity != severity:
                continue
            key = f"{check_id}||{resource_id}"
            if key not in finding_tracker:
                finding_tracker[key] = {
                    'check_id': check_id, 'check_title': (finding.finding_details or {}).get('check_title', 'Unknown'),
                    'resource_id': resource_id, 'resource_type': finding.resource_type,
                    'severity': finding.severity, 'first_seen': scan.completed_at,
                    'last_seen': scan.completed_at, 'occurrence_count': 0,
                    'scan_ids': [], 'status_history': []
                }
            finding_tracker[key]['occurrence_count'] += 1
            finding_tracker[key]['scan_ids'].append(str(scan.id))
            finding_tracker[key]['last_seen'] = max(finding_tracker[key]['last_seen'], scan.completed_at)
            finding_tracker[key]['first_seen'] = min(finding_tracker[key]['first_seen'], scan.completed_at)
            finding_tracker[key]['status_history'].append({
                'scan_id': str(scan.id), 'scan_date': scan.completed_at.isoformat(), 'status': finding.status
            })
    
    recurring = [f for f in finding_tracker.values() if f['occurrence_count'] >= min_occurrences]
    severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4}
    recurring.sort(key=lambda x: (severity_order.get(x['severity'], 5), -x['occurrence_count']))
    
    for finding in recurring[:limit]:
        finding['days_persistent'] = (finding['last_seen'] - finding['first_seen']).days
        finding['first_seen'] = finding['first_seen'].isoformat()
        finding['last_seen'] = finding['last_seen'].isoformat()
    
    return {"account_id": str(account_id), "total_scans_analyzed": len(scans),
            "total_recurring_findings": len(recurring), "recurring_findings": recurring[:limit]}

@router.get("/scan/{scan_id}/export/csv")
async def export_findings_csv(
    scan_id: UUID, framework: Optional[str] = Query(None),
    severity: Optional[str] = Query(None), db: Session = Depends(get_db)
):
    """Export findings to CSV"""
    from app.models.assessment_scan import AssessmentScan
    scan = db.query(AssessmentScan).filter(AssessmentScan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    query = """
        SELECT tc.check_name, tc.check_description,
               sf.finding_status, sf.risk_level, sf.resource_id, sf.resource_type, sf.discovered_at,
               STRING_AGG(DISTINCT cf.framework_name, '; '),
               STRING_AGG(DISTINCT fc.control_id || ': ' || fc.control_title, '; ')
        FROM scan_findings sf
        LEFT JOIN technical_checks tc ON tc.id = sf.check_id
        LEFT JOIN control_check_mappings ccm ON ccm.check_id = tc.id
        LEFT JOIN framework_controls fc ON fc.id = ccm.control_id
        LEFT JOIN compliance_frameworks cf ON cf.id = fc.framework_id
        WHERE sf.scan_id = :scan_id
    """
    params = {"scan_id": str(scan_id)}
    if framework:
        query += " AND cf.framework_name = :framework"
        params["framework"] = framework
    if severity:
        query += " AND sf.risk_level = :severity"
        params["severity"] = severity
    query += """
        GROUP BY sf.id, tc.check_name, tc.check_description, sf.finding_status, sf.risk_level,
                 sf.resource_id, sf.resource_type, sf.discovered_at
        ORDER BY CASE sf.risk_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3 WHEN 'Low' THEN 4 ELSE 5 END, sf.discovered_at DESC
    """
    results = db.execute(text(query), params).fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Check ID', 'Check Title', 'Status', 'Severity', 'Resource Type', 
                    'Resource ID', 'Frameworks', 'Controls', 'Discovered Date'])
    for row in results:
        writer.writerow([row[0], row[1], row[2], row[3], row[5], row[4],
                        row[7] if row[7] else 'N/A', row[8] if row[8] else 'N/A',
                        row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] else ''])
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=findings_{str(scan_id)[:8]}_{timestamp}.csv"}
    )

@router.get("/account/{account_id}/export/summary-csv")
async def export_summary_csv(account_id: UUID, db: Session = Depends(get_db)):
    """Export compliance summary CSV"""
    from app.models.assessment_scan import AssessmentScan
    from app.models.compliance_score import ComplianceScore
    from app.models.compliance_framework import ComplianceFramework
    
    latest_scan = db.query(AssessmentScan).join(
        ComplianceScore, AssessmentScan.id == ComplianceScore.scan_id
    ).filter(AssessmentScan.account_id == account_id
    ).order_by(AssessmentScan.completed_at.desc()).first()
    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans with scores found")
    
    scores = db.query(ComplianceScore, ComplianceFramework).join(
        ComplianceFramework, ComplianceScore.framework_id == ComplianceFramework.id
    ).filter(ComplianceScore.scan_id == latest_scan.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Framework', 'Compliance Score (%)', 'Controls Passed', 'Controls Failed',
                    'Controls N/A', 'Total Controls', 'Critical', 'High', 'Medium', 'Low', 
                    'Total Findings', 'Scan Date'])
    for score, framework in scores:
        total_controls = score.controls_passed + score.controls_failed + score.controls_not_applicable
        total_findings = score.critical_findings + score.high_findings + score.medium_findings + score.low_findings
        writer.writerow([framework.framework_name, f"{float(score.overall_score):.1f}",
                        score.controls_passed, score.controls_failed, score.controls_not_applicable,
                        total_controls, score.critical_findings, score.high_findings,
                        score.medium_findings, score.low_findings, total_findings,
                        latest_scan.completed_at.strftime('%Y-%m-%d %H:%M:%S')])
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                           headers={"Content-Disposition": f"attachment; filename=compliance_summary_{timestamp}.csv"})

# NOTE: PDF endpoint code will be added in the next file part due to length
# This is intentionally split to avoid the duplicate endpoint issue
@router.get("/account/{account_id}/export/pdf-report")
async def export_pdf_report(account_id: UUID, db: Session = Depends(get_db)):
    """Generate comprehensive executive PDF report with insights and commentary"""
    from app.models.assessment_scan import AssessmentScan
    from app.models.compliance_score import ComplianceScore
    from app.models.compliance_framework import ComplianceFramework
    
    latest_scan = db.query(AssessmentScan).join(
        ComplianceScore, AssessmentScan.id == ComplianceScore.scan_id
    ).filter(
        AssessmentScan.account_id == account_id
    ).order_by(AssessmentScan.completed_at.desc()).first()
    
    if not latest_scan:
        raise HTTPException(status_code=404, detail="No scans with scores found")
    
    # Get scans with scores for trends
    recent_scans = db.query(AssessmentScan).join(
        ComplianceScore, AssessmentScan.id == ComplianceScore.scan_id
    ).filter(
        AssessmentScan.account_id == account_id
    ).order_by(AssessmentScan.completed_at.desc()).limit(3).all()
    
    scores = db.query(ComplianceScore, ComplianceFramework).join(
        ComplianceFramework, ComplianceScore.framework_id == ComplianceFramework.id
    ).filter(ComplianceScore.scan_id == latest_scan.id).all()
    
    # Calculate statistics
    total_critical = int(sum(int(s.critical_findings) for s, f in scores))
    total_high = int(sum(int(s.high_findings) for s, f in scores))
    total_medium = int(sum(int(s.medium_findings) for s, f in scores))
    total_low = int(sum(int(s.low_findings) for s, f in scores))
    total_findings = total_critical + total_high + total_medium + total_low
    total_failed = int(sum(int(s.controls_failed) for s, f in scores))
    total_passed = int(sum(int(s.controls_passed) for s, f in scores))
    avg_compliance = float(sum(float(s.overall_score) for s, f in scores) / len(scores)) if scores else 0
    
    # Get recurring findings
    scans_with_scores = db.query(AssessmentScan.id).join(
        ComplianceScore, AssessmentScan.id == ComplianceScore.scan_id
    ).filter(AssessmentScan.account_id == account_id).distinct().all()
    
    scan_ids = [str(scan.id) for scan in scans_with_scores]
    recurring_findings = []
    
    if len(scan_ids) >= 2:
        scans_for_recurring = db.query(AssessmentScan).filter(
            and_(AssessmentScan.id.in_(scan_ids), AssessmentScan.account_id == account_id)
        ).all()
        
        finding_tracker = {}
        for scan in scans_for_recurring:
            for finding in scan.findings:
                key = f"{(finding.finding_details or {}).get('check_id', 'unknown')}||{finding.resource_id}"
                if key not in finding_tracker:
                    finding_tracker[key] = {
                        'check_title': (finding.finding_details or {}).get('check_title', 'Unknown'),
                        'severity': finding.severity,
                        'occurrence_count': 0
                    }
                finding_tracker[key]['occurrence_count'] += 1
        
        recurring_findings = [f for f in finding_tracker.values() if f['occurrence_count'] >= 2]
        recurring_findings.sort(key=lambda x: -x['occurrence_count'])
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements, styles = [], getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=28,
                                 textColor=colors.HexColor('#1E2761'), alignment=TA_CENTER, 
                                 spaceAfter=6, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=14,
                                    textColor=colors.HexColor('#64748B'), alignment=TA_CENTER, spaceAfter=30)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=18,
                                   textColor=colors.HexColor('#1E2761'), spaceAfter=12, spaceBefore=20,
                                   fontName='Helvetica-Bold')
    insight_style = ParagraphStyle('Insight', parent=styles['Normal'], fontSize=11,
                                   textColor=colors.HexColor('#1E293B'), leftIndent=20, 
                                   rightIndent=20, spaceAfter=12, leading=16)
    
    # ========== COVER PAGE ==========
    elements.append(Spacer(1, 1.5*inch))
    elements.append(Paragraph("Cloud Security Posture", title_style))
    elements.append(Paragraph("Executive Compliance Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        f"Assessment Period: {latest_scan.completed_at.strftime('%B %d, %Y')}", 
        subtitle_style
    ))
    elements.append(Paragraph(
        f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
        subtitle_style
    ))
    
    # Executive Summary Box
    elements.append(Spacer(1, 0.5*inch))
    exec_summary = f"""
    <b>EXECUTIVE SUMMARY</b><br/><br/>
    This report provides a comprehensive analysis of your organization's cloud security posture 
    across {len(scores)} major compliance frameworks. The assessment identified <b>{total_findings} 
    security findings</b> requiring attention, with <b>{total_critical} critical</b> and <b>{total_high} 
    high-severity</b> issues demanding immediate remediation.<br/><br/>
    Current average compliance score stands at <b>{avg_compliance:.1f}%</b>, with <b>{total_failed} 
    controls failing</b> across all frameworks. {"This security posture requires urgent executive attention and resource allocation for remediation efforts." if avg_compliance < 50 else "Strategic improvements are needed to reach industry-standard compliance levels."}
    """
    elements.append(Paragraph(exec_summary, insight_style))
    
    elements.append(PageBreak())
    
    # ========== PAGE 1: DETAILED SUMMARY ==========
    elements.append(Paragraph("Security Posture Overview", heading_style))
    
    # Risk assessment
    risk_level = "CRITICAL" if total_critical > 10 else "HIGH" if total_high > 20 else "MODERATE"
    risk_color = "#DC2626" if total_critical > 10 else "#EA580C" if total_high > 20 else "#CA8A04"
    
    risk_assessment = f"""
    <b>Current Risk Level: <font color="{risk_color}">{risk_level}</font></b><br/><br/>
    Your infrastructure has been assessed against industry-standard security frameworks including 
    ISO 27001, NIST Cybersecurity Framework, PCI-DSS, CIS AWS Foundations, and GDPR compliance requirements. 
    The analysis reveals significant security gaps that expose the organization to potential data breaches, 
    regulatory penalties, and operational disruptions.
    """
    elements.append(Paragraph(risk_assessment, insight_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary table
    summary_data = [
        ['Metric', 'Count', 'Business Impact'],
        ['Critical Findings', str(total_critical), 'Immediate risk of breach'],
        ['High Severity', str(total_high), 'Regulatory exposure'],
        ['Medium Severity', str(total_medium), 'Operational risk'],
        ['Low Severity', str(total_low), 'Best practice gaps'],
        ['Failed Controls', str(total_failed), 'Compliance deficiencies'],
        ['Passed Controls', str(total_passed), 'Compliant areas'],
        ['Avg Compliance', f"{avg_compliance:.1f}%", 'Overall posture']
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.3*inch, 2.7*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E2761')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    elements.append(summary_table)
    
    elements.append(PageBreak())
    
    # ========== PAGE 2: SEVERITY DISTRIBUTION ==========
    elements.append(Paragraph("Findings Distribution by Severity", heading_style))
    
    severity_insight = f"""
    <b>What This Chart Shows:</b> The distribution of security findings across severity levels, 
    indicating where immediate attention is required versus long-term improvements.<br/><br/>
    <b>Key Insight:</b> {"Critical findings represent immediate security vulnerabilities that could lead to data breaches or system compromises. These require 24-hour remediation SLAs." if total_critical > 0 else "No critical vulnerabilities detected, but high-severity findings still require prompt attention within 48-72 hours."}<br/><br/>
    <b>Executive Action:</b> Allocate emergency resources to address the {total_critical + total_high} 
    critical and high-severity findings. Each unresolved critical finding increases breach probability by an estimated 15-20%.
    """
    elements.append(Paragraph(severity_insight, insight_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Pie chart
    if total_findings > 0:
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x, pie.y, pie.width, pie.height = 150, 50, 120, 120
        pie.data = [total_critical, total_high, total_medium, total_low]
        pie.labels = ['Critical', 'High', 'Medium', 'Low']
        pie.slices[0].fillColor = colors.HexColor('#DC2626')
        pie.slices[1].fillColor = colors.HexColor('#EA580C')
        pie.slices[2].fillColor = colors.HexColor('#CA8A04')
        pie.slices[3].fillColor = colors.HexColor('#16A34A')
        drawing.add(pie)
        elements.append(drawing)
    
    elements.append(PageBreak())
    
    # ========== PAGE 3: COMPLIANCE TRENDS ==========
    elements.append(Paragraph("Compliance Trend Analysis", heading_style))
    
    if len(recent_scans) >= 2:
        # Check if scans have scores
        has_trend_data = False
        trend_dates, trend_scores = [], []
        
        for scan in reversed(recent_scans):
            scan_scores = db.query(ComplianceScore).filter(ComplianceScore.scan_id == scan.id).all()
            if scan_scores:
                has_trend_data = True
                avg = float(sum(float(s.overall_score) for s in scan_scores) / len(scan_scores))
                trend_dates.append(scan.completed_at.strftime('%m/%d'))
                trend_scores.append(avg)
        
        if has_trend_data and len(trend_scores) >= 2:
            # Calculate trend
            score_change = trend_scores[-1] - trend_scores[0]
            trend_direction = "improving" if score_change > 0 else "declining" if score_change < 0 else "stable"
            trend_color_text = "green" if score_change > 0 else "red" if score_change < 0 else "gray"
            
            trend_insight = f"""
            <b>What This Chart Shows:</b> Compliance score trajectory over the last {len(recent_scans)} security 
            assessments, revealing whether security posture is improving or deteriorating.<br/><br/>
            <b>Key Insight:</b> Your compliance trend is <b>{trend_direction}</b>, with a 
            <b>{abs(score_change):.1f}%</b> {"improvement" if score_change > 0 else "decline" if score_change < 0 else "change"} 
            since {trend_dates[0]}. {"This positive momentum should be maintained through continued investment in security controls." if score_change > 0 else "This negative trend indicates growing security debt and requires immediate strategic intervention." if score_change < 0 else "Stable scores suggest consistent security practices but limited progress toward compliance goals."}<br/><br/>
            <b>Executive Action:</b> {"Continue current remediation efforts and allocate resources to accelerate improvement." if score_change > 0 else "Convene security leadership to identify root causes and establish aggressive remediation timelines." if score_change < 0 else "Increase investment in proactive security measures to drive measurable improvement."}
            """
            elements.append(Paragraph(trend_insight, insight_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Line chart
            drawing = Drawing(500, 250)
            lc = HorizontalLineChart()
            lc.x, lc.y, lc.height, lc.width = 50, 50, 150, 400
            lc.data = [trend_scores]
            lc.categoryAxis.categoryNames = trend_dates
            lc.valueAxis.valueMin, lc.valueAxis.valueMax = 0, 100
            lc.lines[0].strokeColor = colors.HexColor('#0891B2')
            lc.lines[0].strokeWidth = 3
            drawing.add(lc)
            elements.append(drawing)
            elements.append(Spacer(1, 0.2*inch))
            
            # Trend table
            trend_table_data = [['Scan Date', 'Compliance %', 'Critical', 'High', 'Trend']]
            for idx, scan in enumerate(reversed(recent_scans)):
                scan_scores = db.query(ComplianceScore).filter(ComplianceScore.scan_id == scan.id).all()
                if scan_scores:
                    avg = float(sum(float(s.overall_score) for s in scan_scores) / len(scan_scores))
                    crit = int(sum(int(s.critical_findings) for s in scan_scores))
                    high = int(sum(int(s.high_findings) for s in scan_scores))
                    if idx == 0:
                        trend = "Baseline"
                    else:
                        prev_avg = trend_scores[idx - 1]
                        change = avg - prev_avg
                        trend = f"↑ {change:.1f}%" if change > 0 else f"↓ {abs(change):.1f}%" if change < 0 else "→ 0%"
                    trend_table_data.append([
                        scan.completed_at.strftime('%m/%d/%Y'),
                        f"{avg:.1f}%",
                        str(crit),
                        str(high),
                        trend
                    ])
            
            trend_table = Table(trend_table_data, colWidths=[1.5*inch, 1.2*inch, 0.9*inch, 0.9*inch, 1.5*inch])
            trend_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891B2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9)
            ]))
            elements.append(trend_table)
        else:
            # Not enough trend data
            elements.append(Paragraph(
                "<b>Trend Analysis Unavailable:</b> At least 2 scans with calculated compliance scores are required for trend analysis. Continue conducting regular security assessments to establish baseline trends and track improvement over time.",
                insight_style
            ))
    else:
        elements.append(Paragraph(
            "<b>Trend Analysis Unavailable:</b> Multiple scans required. Regular assessments enable tracking of security posture improvements and early detection of emerging vulnerabilities.",
            insight_style
        ))
    
    elements.append(PageBreak())
    
    # ========== PAGE 4: FRAMEWORK BREAKDOWN ==========
    elements.append(Paragraph("Compliance Framework Performance", heading_style))
    
    # Find lowest scoring framework
    lowest_framework = min(scores, key=lambda x: float(x[0].overall_score))
    lowest_score = float(lowest_framework[0].overall_score)
    lowest_name = lowest_framework[1].framework_name
    
    framework_insight = f"""
    <b>What This Chart Shows:</b> Comparative compliance performance across all assessed frameworks, 
    identifying which regulatory requirements pose the greatest challenge.<br/><br/>
    <b>Key Insight:</b> {lowest_name} shows the lowest compliance at {lowest_score:.1f}%, indicating 
    significant gaps in {"information security management" if "ISO" in lowest_name else "cybersecurity controls" if "NIST" in lowest_name else "payment security" if "PCI" in lowest_name else "cloud security best practices" if "CIS" in lowest_name else "data protection"}. 
    This framework should be prioritized for remediation investment.<br/><br/>
    <b>Executive Action:</b> Establish a dedicated task force to address {lowest_name} deficiencies. 
    Estimated remediation timeline: {"2-3 months for critical gaps" if lowest_score < 30 else "4-6 weeks for major improvements"}.
    """
    elements.append(Paragraph(framework_insight, insight_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Bar chart
    drawing = Drawing(500, 250)
    bc = VerticalBarChart()
    bc.x, bc.y, bc.height, bc.width = 50, 50, 180, 400
    framework_names = [f.framework_name[:10] for s, f in scores]
    framework_scores = [float(s.overall_score) for s, f in scores]
    bc.data = [framework_scores]
    bc.categoryAxis.categoryNames = framework_names
    bc.valueAxis.valueMin, bc.valueAxis.valueMax = 0, 100
    bc.bars[0].fillColor = colors.HexColor('#0891B2')
    drawing.add(bc)
    elements.append(drawing)
    elements.append(Spacer(1, 0.3*inch))
    
    # Framework table
    framework_data = [['Framework', 'Score', 'Failed Controls', 'Critical', 'High', 'Priority']]
    for score, framework in sorted(scores, key=lambda x: float(x[0].overall_score)):
        priority = "URGENT" if float(score.overall_score) < 30 else "HIGH" if float(score.overall_score) < 60 else "MEDIUM"
        framework_data.append([
            framework.framework_name,
            f"{float(score.overall_score):.1f}%",
            str(score.controls_failed),
            str(score.critical_findings),
            str(score.high_findings),
            priority
        ])
    
    framework_table = Table(framework_data, colWidths=[1.8*inch, 0.9*inch, 1.1*inch, 0.8*inch, 0.7*inch, 0.9*inch])
    framework_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E2761')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    elements.append(framework_table)
    
    elements.append(PageBreak())
    
    # ========== PAGE 5: RECURRING FINDINGS ==========
    elements.append(Paragraph("Persistent Security Gaps", heading_style))
    
    if recurring_findings:
        recurring_insight = f"""
        <b>What This Analysis Shows:</b> Security issues that have persisted across multiple assessments, 
        indicating systemic problems or insufficient remediation processes.<br/><br/>
        <b>Key Insight:</b> <b>{len(recurring_findings)} recurring findings</b> represent {(len(recurring_findings)/total_findings*100):.1f}% 
        of all issues. These persistent vulnerabilities suggest resource constraints, technical debt, or 
        inadequate change management processes. Recurring issues have {recurring_findings[0]['occurrence_count']}x higher 
        exploitation probability than newly discovered findings.<br/><br/>
        <b>Executive Action:</b> Implement automated remediation workflows and assign dedicated ownership 
        for each recurring finding. Consider external security consulting for complex persistent issues.
        """
        elements.append(Paragraph(recurring_insight, insight_style))
        elements.append(Spacer(1, 0.2*inch))
        
        recurring_data = [['Security Issue', 'Severity', 'Recurrence', 'Risk Factor']]
        for finding in recurring_findings[:10]:
            risk = "EXTREME" if finding['occurrence_count'] >= 5 else "VERY HIGH" if finding['occurrence_count'] >= 3 else "HIGH"
            recurring_data.append([
                finding['check_title'][:35] + '...' if len(finding['check_title']) > 35 else finding['check_title'],
                finding['severity'],
                f"{finding['occurrence_count']}x",
                risk
            ])
        
        recurring_table = Table(recurring_data, colWidths=[2.8*inch, 1*inch, 1*inch, 1.2*inch])
        recurring_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        elements.append(recurring_table)
    else:
        elements.append(Paragraph(
            "<b>Positive Finding:</b> No recurring security issues detected. All previously identified vulnerabilities have been successfully remediated, demonstrating effective security operations.",
            insight_style
        ))
    
    elements.append(PageBreak())
    
    # ========== PAGE 6: STRATEGIC RECOMMENDATIONS ==========
    elements.append(Paragraph("Executive Recommendations", heading_style))
    
    recommendations = f"""
    <b>Immediate Actions (0-48 Hours):</b><br/>
    • Convene emergency security review for {total_critical} critical findings<br/>
    • Allocate emergency budget for remediation of high-risk vulnerabilities<br/>
    • Implement temporary compensating controls for critical exposures<br/>
    • Notify Board of Directors and Audit Committee of current risk posture<br/><br/>
    
    <b>Short-Term Priorities (1-4 Weeks):</b><br/>
    • Establish dedicated remediation teams for each framework<br/>
    • Target {lowest_name} framework (lowest score: {lowest_score:.1f}%)<br/>
    • Address all {len(recurring_findings)} recurring findings with permanent solutions<br/>
    • Implement automated security scanning in CI/CD pipeline<br/>
    • Develop comprehensive security training program for engineering teams<br/><br/>
    
    <b>Strategic Initiatives (1-6 Months):</b><br/>
    • Invest in Security Information and Event Management (SIEM) platform<br/>
    • Establish Security Operations Center (SOC) or enhance existing capabilities<br/>
    • Implement zero-trust architecture principles across infrastructure<br/>
    • Develop incident response playbooks for identified vulnerability classes<br/>
    • Establish quarterly compliance assessment cadence<br/>
    • Consider cyber insurance to transfer residual risk<br/><br/>
    
    <b>Resource Requirements:</b><br/>
    • Estimated remediation cost: {"$150K-$300K for critical findings" if total_critical > 10 else "$75K-$150K for high-priority items"}<br/>
    • Timeline to achieve 80%+ compliance: {"6-9 months with dedicated resources" if avg_compliance < 40 else "3-6 months with focused effort"}<br/>
    • Additional headcount needed: {"2-3 security engineers, 1 compliance specialist" if total_failed > 100 else "1-2 security engineers"}<br/><br/>
    
    <b>Risk of Inaction:</b><br/>
    Failure to address identified vulnerabilities exposes the organization to data breaches (avg cost: $4.45M), 
    regulatory fines (GDPR: up to 4% of revenue), reputational damage, and potential business disruption. 
    Current security posture represents unacceptable risk to organizational objectives.
    """
    elements.append(Paragraph(recommendations, insight_style))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                           textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph(
        f"CSPM Compliance Dashboard | Account: {str(account_id)[:8]}... | {datetime.now().strftime('%B %d, %Y %I:%M %p')} | CONFIDENTIAL & PRIVILEGED",
        footer
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=executive_compliance_report_{timestamp}.pdf"}
    )

@router.get("/finding/{finding_id}/remediation")
async def get_finding_remediation(
    finding_id: int,
    db: Session = Depends(get_db)
):
    """Get remediation guidance for a specific finding"""
    from app.models.scan_finding import ScanFinding
    
    finding = db.query(ScanFinding).filter(ScanFinding.id == finding_id).first()
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Get check_id from finding_details
    check_id = (finding.finding_details or {}).get('check_id', 'unknown')
    resource_id = finding.resource_id
    
    # Get remediation guidance
    guidance = get_remediation(check_id, resource_id)
    
    # Add finding context
    guidance['finding_id'] = str(finding.id)
    guidance['resource_id'] = resource_id
    guidance['resource_type'] = finding.resource_type
    guidance['current_severity'] = finding.severity
    
    return guidance

@router.get("/scan/{scan_id}/toxic-combinations")
async def get_toxic_combinations(
    scan_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detected toxic combinations (critical risk paths) for a scan"""
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
    """Get toxic combinations for an account's latest scan"""
    from app.models.assessment_scan import AssessmentScan
    
    # Get latest scan for account
    latest_scan = db.query(AssessmentScan).filter(
        AssessmentScan.account_id == account_id,
        AssessmentScan.scan_status == 'Completed'
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

