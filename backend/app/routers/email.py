"""
Email Alerts API Endpoints - COMPLETE WITH PDF EMAIL
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

from app.database import get_db
from app.services.email_service import email_service

router = APIRouter(
    prefix="/api/email",
    tags=["Email Alerts"]
)

class TestEmailRequest(BaseModel):
    email: EmailStr

class AlertSettingsRequest(BaseModel):
    email: EmailStr
    critical_alerts: bool = True
    scan_completion: bool = True
    weekly_summary: bool = False

@router.post("/test")
async def send_test_email(request: TestEmailRequest):
    """Send test email to verify configuration"""

    success = email_service.send_email(
        to_email=request.email,
        subject="✅ CSPM Dashboard - Email Configuration Test",
        html_body="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #0891B2;">Email Configuration Successful! ✅</h2>
            <p>Your CSPM Compliance Dashboard email alerts are now configured and working correctly.</p>
            <p>You will receive:</p>
            <ul>
                <li>Critical finding alerts (immediate)</li>
                <li>Scan completion notifications</li>
                <li>Weekly compliance summaries (optional)</li>
            </ul>
            <p style="color: #6B7280; font-size: 12px; margin-top: 30px;">
                This is a test message from CSPM Compliance Dashboard
            </p>
        </body>
        </html>
        """,
        text_body="Email configuration test successful! Your CSPM Dashboard alerts are working."
    )

    if success:
        return {"message": "Test email sent successfully", "email": request.email}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check SMTP configuration.")

@router.post("/alert/critical-findings")
async def send_critical_findings_alert(
    account_id: UUID,
    scan_id: UUID,
    to_email: EmailStr,
    db: Session = Depends(get_db)
):
    """Send alert for critical findings"""
    from app.models.compliance_score import ComplianceScore

    # Get scores for scan
    scores = db.query(ComplianceScore).filter(
        ComplianceScore.scan_id == scan_id
    ).all()

    if not scores:
        raise HTTPException(status_code=404, detail="No scores found for scan")

    critical_count = sum(s.critical_findings for s in scores)
    high_count = sum(s.high_findings for s in scores)

    # Only send if there are critical findings
    if critical_count == 0:
        return {"message": "No critical findings - alert not sent"}

    success = email_service.send_critical_findings_alert(
        to_email=to_email,
        critical_count=critical_count,
        high_count=high_count,
        scan_id=str(scan_id),
        account_id=str(account_id)
    )

    if success:
        return {
            "message": "Critical findings alert sent",
            "email": to_email,
            "critical_count": critical_count,
            "high_count": high_count
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send alert email")

@router.post("/alert/scan-completion")
async def send_scan_completion_alert(
    scan_id: UUID,
    to_email: EmailStr,
    db: Session = Depends(get_db)
):
    """Send notification when scan completes"""
    from app.models.compliance_score import ComplianceScore
    from app.models.assessment_scan import AssessmentScan

    # Get scan
    scan = db.query(AssessmentScan).filter(
        AssessmentScan.id == scan_id
    ).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Get scores
    scores = db.query(ComplianceScore).filter(
        ComplianceScore.scan_id == scan_id
    ).all()

    if not scores:
        raise HTTPException(status_code=404, detail="No scores calculated for scan")

    total_findings = sum(
        s.critical_findings + s.high_findings + s.medium_findings + s.low_findings
        for s in scores
    )
    critical_count = sum(s.critical_findings for s in scores)
    high_count = sum(s.high_findings for s in scores)
    avg_compliance = sum(float(s.overall_score) for s in scores) / len(scores)

    success = email_service.send_scan_completion_notification(
        to_email=to_email,
        scan_id=str(scan_id),
        total_findings=total_findings,
        critical_count=critical_count,
        high_count=high_count,
        compliance_score=avg_compliance
    )

    if success:
        return {
            "message": "Scan completion notification sent",
            "email": to_email,
            "scan_id": str(scan_id)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.post("/send-pdf-report")
async def send_pdf_report(
    account_id: UUID,
    to_email: EmailStr,
    db: Session = Depends(get_db)
):
    """
    Send the latest PDF compliance report via email
    """
    try:
        from app.models.assessment_scan import AssessmentScan
        
        # Get latest scan for this account
        latest_scan = db.query(AssessmentScan).filter(
            AssessmentScan.account_id == account_id,
            AssessmentScan.scan_status == "Completed"
        ).order_by(AssessmentScan.completed_at.desc()).first()
        
        if not latest_scan:
            raise HTTPException(status_code=404, detail="No completed scans found")
        
        # Generate PDF report using existing scores endpoint logic
        from app.routers.scores import export_pdf_report
        pdf_response = await export_pdf_report(account_id, db)
        
        #Extract bytes from response
        pdf_content = b''
        async for chunk in pdf_response.body_iterator:
            pdf_content += chunk
        
        # Email setup
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("FROM_EMAIL", smtp_username)
        from_name = os.getenv("FROM_NAME", "CSPM Security Dashboard")
        
        # Create email with PDF attachment
        msg = MIMEMultipart()
        msg['Subject'] = f"📊 CSPM Compliance Report - {latest_scan.completed_at.strftime('%Y-%m-%d')}"
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        
        # HTML email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📊 CSPM Compliance Report</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Executive Security Assessment</p>
                </div>
                <div class="content">
                    <p>Your comprehensive Cloud Security Posture Management (CSPM) compliance report is attached.</p>
                    
                    <h3 style="color: #1f2937;">Report Contents:</h3>
                    <ul style="color: #4b5563; line-height: 1.8;">
                        <li>Security Posture Overview</li>
                        <li>Severity Distribution Analysis</li>
                        <li>Compliance Trends</li>
                        <li>Framework Performance Comparison</li>
                        <li>Recurring Findings Analysis</li>
                        <li>Strategic Recommendations</li>
                    </ul>
                    
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        Report Date: {latest_scan.completed_at.strftime('%B %d, %Y')}<br>
                        Scan ID: {latest_scan.id}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach PDF
        pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
        pdf_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f'CSPM_Compliance_Report_{latest_scan.completed_at.strftime("%Y%m%d")}.pdf'
        )
        msg.attach(pdf_attachment)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return {
            "message": "PDF report sent successfully",
            "email": to_email,
            "scan_id": str(latest_scan.id),
            "report_date": latest_scan.completed_at.strftime('%Y-%m-%d')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error sending PDF report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send PDF report: {str(e)}")

@router.get("/settings/{account_id}")
async def get_email_settings(account_id: UUID):
    """Get email alert settings for account"""
    # For now, return default settings
    # In production, this would fetch from database
    return {
        "account_id": str(account_id),
        "email": "user@example.com",
        "critical_alerts": True,
        "scan_completion": True,
        "weekly_summary": False
    }

@router.post("/settings/{account_id}")
async def update_email_settings(
    account_id: UUID,
    settings: AlertSettingsRequest
):
    """Update email alert settings"""
    # For now, just return the settings
    # In production, this would save to database
    return {
        "message": "Email settings updated",
        "account_id": str(account_id),
        "settings": settings.dict()
    }
