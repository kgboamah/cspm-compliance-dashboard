"""
Email Service - COMPLETE with All 5 Alert Types
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "CSPM Security Dashboard")

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Internal method to send email via SMTP
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Attach both plain text and HTML versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            print(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify SMTP configuration"""
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">✅ Email Configuration Successful!</h2>
            <p>Your CSPM Security Dashboard email alerts are properly configured.</p>
            <p>You will receive notifications for:</p>
            <ul>
                <li>Critical security findings</li>
                <li>Scan completion updates</li>
                <li>Weekly security summaries</li>
                <li>Recurring security issues</li>
            </ul>
        </body>
        </html>
        """
        
        text_content = """
        Email Configuration Successful!
        
        Your CSPM Security Dashboard email alerts are properly configured.
        """
        
        return self._send_email(
            to_email,
            "✅ CSPM Dashboard - Email Test Successful",
            html_content,
            text_content
        )

    def send_critical_findings_alert(
        self,
        account_id: str,
        scan_id: str,
        to_email: str,
        critical_count: int,
        high_count: int
    ) -> bool:
        """Send alert for critical security findings"""
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .alert-box {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-number {{ font-size: 36px; font-weight: bold; color: #dc2626; }}
                .action-btn {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">🚨 URGENT: Critical Security Issues Detected</h1>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <p style="margin: 0; font-weight: 600;">⚠️ Your latest security scan has identified <strong>{critical_count} critical</strong> and <strong>{high_count} high-severity</strong> security issues that require immediate attention.</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-number">{critical_count}</div>
                            <div>Critical Issues</div>
                        </div>
                        <div class="stat">
                            <div class="stat-number" style="color: #ea580c;">{high_count}</div>
                            <div>High-Severity Issues</div>
                        </div>
                    </div>
                    
                    <h3 style="color: #1f2937;">Recommended Actions</h3>
                    <ol style="color: #4b5563; line-height: 1.8;">
                        <li><strong>Review findings immediately</strong> - Critical issues pose immediate security risks</li>
                        <li><strong>Assign remediation tasks</strong> - Delegate to security team within 24 hours</li>
                        <li><strong>Implement compensating controls</strong> - Deploy temporary mitigations if immediate fixes aren't possible</li>
                        <li><strong>Notify stakeholders</strong> - Alert relevant teams and management</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/findings" class="action-btn">View Critical Findings Dashboard</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 12px; text-align: center; margin-top: 20px;">
                        Scan ID: {scan_id}<br>
                        Account ID: {account_id}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        URGENT: Critical Security Issues Detected
        
        Your latest security scan has identified:
        - {critical_count} Critical Issues
        - {high_count} High-Severity Issues
        
        These require immediate attention.
        
        Recommended Actions:
        1. Review findings immediately
        2. Assign remediation tasks within 24 hours
        3. Implement compensating controls
        4. Notify stakeholders
        
        View details: http://localhost:3000/findings
        
        Scan ID: {scan_id}
        Account ID: {account_id}
        """
        
        return self._send_email(
            to_email,
            f"🚨 URGENT: {critical_count} Critical Security Issues Detected",
            html_content,
            text_content
        )

    def send_scan_completion_alert(
        self,
        scan_id: str,
        to_email: str,
        total_findings: int,
        critical_count: int,
        high_count: int,
        medium_count: int,
        low_count: int
    ) -> bool:
        """Send notification when scan completes"""
        
        # Calculate compliance score color
        if critical_count > 0:
            score_color = "#dc2626"
            score_label = "Critical"
        elif high_count > 5:
            score_color = "#ea580c"
            score_label = "Needs Attention"
        elif medium_count > 10:
            score_color = "#ca8a04"
            score_label = "Fair"
        else:
            score_color = "#16a34a"
            score_label = "Good"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .findings-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .finding-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid; }}
                .action-btn {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">✅ Security Scan Complete</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{total_findings} Total Findings Identified</p>
                </div>
                
                <div class="content">
                    <div style="background-color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <div style="font-size: 14px; color: #6b7280; margin-bottom: 5px;">Overall Security Posture</div>
                        <div style="font-size: 28px; font-weight: bold; color: {score_color};">{score_label}</div>
                    </div>
                    
                    <h3 style="color: #1f2937;">Findings Summary</h3>
                    <div class="findings-grid">
                        <div class="finding-card" style="border-left-color: #dc2626;">
                            <div style="font-size: 24px; font-weight: bold; color: #dc2626;">{critical_count}</div>
                            <div style="color: #6b7280; font-size: 14px;">Critical</div>
                        </div>
                        <div class="finding-card" style="border-left-color: #ea580c;">
                            <div style="font-size: 24px; font-weight: bold; color: #ea580c;">{high_count}</div>
                            <div style="color: #6b7280; font-size: 14px;">High</div>
                        </div>
                        <div class="finding-card" style="border-left-color: #ca8a04;">
                            <div style="font-size: 24px; font-weight: bold; color: #ca8a04;">{medium_count}</div>
                            <div style="color: #6b7280; font-size: 14px;">Medium</div>
                        </div>
                        <div class="finding-card" style="border-left-color: #16a34a;">
                            <div style="font-size: 24px; font-weight: bold; color: #16a34a;">{low_count}</div>
                            <div style="color: #6b7280; font-size: 14px;">Low</div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard" class="action-btn">View Full Dashboard</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 12px; text-align: center;">
                        Scan ID: {scan_id}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Security Scan Complete
        
        {total_findings} Total Findings Identified
        
        Findings Summary:
        - Critical: {critical_count}
        - High: {high_count}
        - Medium: {medium_count}
        - Low: {low_count}
        
        Overall Security Posture: {score_label}
        
        View full dashboard: http://localhost:3000/dashboard
        
        Scan ID: {scan_id}
        """
        
        return self._send_email(
            to_email,
            f"✅ Security Scan Complete - {total_findings} Findings Identified",
            html_content,
            text_content
        )

    def send_weekly_summary(
        self,
        account_id: str,
        to_email: str,
        date_range: str,
        scans_completed: int,
        avg_compliance_score: float,
        trend: str,
        top_priorities: list
    ) -> bool:
        """Send weekly security summary report"""
        
        trend_indicator = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
        trend_color = "#16a34a" if trend == "improving" else "#dc2626" if trend == "declining" else "#6b7280"
        
        priorities_html = ""
        for i, priority in enumerate(top_priorities[:5], 1):
            priorities_html += f"<li style='margin: 10px 0;'>{priority}</li>"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1f2937; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; }}
                .action-btn {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📊 Weekly Security Summary</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{date_range}</p>
                </div>
                
                <div class="content">
                    <h3 style="color: #1f2937;">Overview</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div style="font-size: 28px; font-weight: bold; color: #2563eb;">{scans_completed}</div>
                            <div style="color: #6b7280; font-size: 14px;">Scans Completed</div>
                        </div>
                        <div class="stat-card">
                            <div style="font-size: 28px; font-weight: bold; color: #16a34a;">{avg_compliance_score:.1f}%</div>
                            <div style="color: #6b7280; font-size: 14px;">Avg Compliance</div>
                        </div>
                        <div class="stat-card">
                            <div style="font-size: 28px; color: {trend_color};">{trend_indicator}</div>
                            <div style="color: #6b7280; font-size: 14px; text-transform: capitalize;">{trend}</div>
                        </div>
                    </div>
                    
                    <h3 style="color: #1f2937; margin-top: 30px;">Top Priority Items</h3>
                    <ol style="color: #4b5563; line-height: 1.8;">
                        {priorities_html}
                    </ol>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/dashboard" class="action-btn">View Full Dashboard</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 12px; text-align: center;">
                        Account ID: {account_id}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Weekly Security Summary
        {date_range}
        
        Overview:
        - Scans Completed: {scans_completed}
        - Average Compliance Score: {avg_compliance_score:.1f}%
        - Trend: {trend}
        
        Top Priority Items:
        """
        for i, priority in enumerate(top_priorities[:5], 1):
            text_content += f"\n{i}. {priority}"
        
        text_content += f"""
        
        View full dashboard: http://localhost:3000/dashboard
        
        Account ID: {account_id}
        """
        
        return self._send_email(
            to_email,
            f"📊 Weekly Security Summary: {date_range}",
            html_content,
            text_content
        )

    def send_recurring_findings_alert(
        self,
        account_id: str,
        to_email: str,
        recurring_by_severity: dict
    ) -> bool:
        """Send alert about recurring security findings by severity"""
        try:
            # Count total recurring issues
            total_recurring = sum(len(items) for items in recurring_by_severity.values())
            
            # Build severity breakdown
            severity_rows = ""
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                if severity in recurring_by_severity:
                    count = len(recurring_by_severity[severity])
                    color = {
                        'Critical': '#dc2626',
                        'High': '#ea580c',
                        'Medium': '#ca8a04',
                        'Low': '#65a30d'
                    }.get(severity, '#6b7280')
                    
                    severity_rows += f"""
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                            <span style="display: inline-block; padding: 4px 12px; background-color: {color}; color: white; border-radius: 4px; font-weight: 600;">
                                {severity}
                            </span>
                        </td>
                        <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center; font-weight: 600; font-size: 18px;">
                            {count}
                        </td>
                    </tr>
                    """
            
            # HTML email body
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #dc2626; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .alert-box {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }}
                    .stats-table {{ width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; margin: 20px 0; }}
                    .action-btn {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; font-size: 24px;">🔁 Recurring Security Issues Detected</h1>
                        <p style="margin: 10px 0 0 0; opacity: 0.9;">Persistent vulnerabilities require immediate attention</p>
                    </div>
                    
                    <div class="content">
                        <div class="alert-box">
                            <p style="margin: 0; font-weight: 600;">⚠️ <strong>{total_recurring} recurring security issues</strong> have been detected across multiple scans.</p>
                            <p style="margin: 10px 0 0 0; font-size: 14px;">These issues persist across scans and indicate systemic security gaps that need remediation.</p>
                        </div>
                        
                        <h2 style="color: #1f2937; margin-top: 30px;">Recurring Issues by Severity</h2>
                        <table class="stats-table">
                            <thead>
                                <tr style="background-color: #f3f4f6;">
                                    <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Severity Level</th>
                                    <th style="padding: 12px; text-align: center; border-bottom: 2px solid #e5e7eb;">Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                {severity_rows}
                            </tbody>
                        </table>
                        
                        <h3 style="color: #1f2937; margin-top: 30px;">Why This Matters</h3>
                        <ul style="color: #4b5563; line-height: 1.8;">
                            <li><strong>Recurring issues indicate incomplete remediation</strong> - These vulnerabilities persist despite previous scan alerts</li>
                            <li><strong>Higher risk of exploitation</strong> - Attackers often target persistent, known vulnerabilities</li>
                            <li><strong>Compliance failures</strong> - Recurring issues may lead to audit failures and regulatory penalties</li>
                        </ul>
                        
                        <h3 style="color: #1f2937; margin-top: 30px;">Recommended Actions</h3>
                        <ol style="color: #4b5563; line-height: 1.8;">
                            <li>Review the recurring findings in detail</li>
                            <li>Assign dedicated resources for remediation</li>
                            <li>Implement automated controls to prevent recurrence</li>
                            <li>Schedule follow-up scans to verify fixes</li>
                        </ol>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/findings" class="action-btn">View Recurring Findings Dashboard</a>
                        </div>
                        
                        <div class="footer">
                            <p>This is an automated alert from your CSPM Security Dashboard</p>
                            <p>Account ID: {account_id}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            RECURRING SECURITY ISSUES DETECTED
            
            {total_recurring} recurring security issues have been detected across multiple scans.
            
            Recurring Issues by Severity:
            """
            
            for severity in ['Critical', 'High', 'Medium', 'Low']:
                if severity in recurring_by_severity:
                    count = len(recurring_by_severity[severity])
                    text_content += f"\n{severity}: {count}"
            
            text_content += """
            
            These issues persist across scans and require immediate attention.
            
            View full details: http://localhost:3000/findings
            """
            
            # Send email
            subject = f"🔁 {total_recurring} Recurring Security Issues Detected"
            return self._send_email(to_email, subject, html_content, text_content)
            
        except Exception as e:
            print(f"Error sending recurring findings alert: {e}")
            return False

# Create singleton instance
email_service = EmailService()
