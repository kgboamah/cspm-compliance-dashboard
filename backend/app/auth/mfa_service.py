"""
MFA Service - Multi-Factor Authentication (FIXED IMPORT)
Location: backend/app/auth/mfa_service.py

Handles MFA code generation, storage, and verification
"""
import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app.services.email_service import email_service  # FIXED IMPORT


class MFAService:
    """Service for handling MFA operations"""
    
    @staticmethod
    def generate_code() -> str:
        """Generate a 6-digit MFA code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_and_send_code(
        db: Session,
        user_id: str,
        user_email: str,
        mfa_email: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """
        Generate MFA code, store in database, and send via email
        
        Args:
            db: Database session
            user_id: User's UUID
            user_email: User's display email (for email content)
            mfa_email: Actual email to send code to
            ip_address: Optional IP address of request
            user_agent: Optional user agent string
            
        Returns:
            True if code sent successfully, False otherwise
        """
        try:
            # Generate 6-digit code
            code = MFAService.generate_code()
            
            # Set expiration (5 minutes from now)
            expires_at = datetime.utcnow() + timedelta(minutes=5)
            
            # Invalidate any existing unused codes for this user
            db.execute(text("""
                UPDATE mfa_codes 
                SET used = TRUE 
                WHERE user_id = :user_id AND used = FALSE
            """), {"user_id": user_id})
            
            # Store new code in database
            db.execute(text("""
                INSERT INTO mfa_codes 
                (user_id, code, expires_at, ip_address, user_agent, created_at, used)
                VALUES 
                (:user_id, :code, :expires_at, :ip_address, :user_agent, CURRENT_TIMESTAMP, FALSE)
            """), {
                "user_id": user_id,
                "code": code,
                "expires_at": expires_at,
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            
            db.commit()
            
            # Build HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #028090 0%, #02c39a 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">🛡️ CSPM Security</h1>
                </div>
                
                <div style="padding: 40px; background: #f8f9fa; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #2d3748; margin-top: 0;">Login Verification Required</h2>
                    
                    <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                        Hello! A login attempt was made for your account:
                    </p>
                    
                    <p style="color: #718096; font-size: 14px;">
                        <strong>Account:</strong> {user_email}
                    </p>
                    
                    <div style="background: white; border-left: 4px solid #028090; padding: 20px; margin: 30px 0; border-radius: 5px;">
                        <p style="color: #4a5568; margin: 0 0 10px 0; font-size: 14px;">Your verification code is:</p>
                        <h1 style="color: #028090; margin: 0; font-size: 48px; letter-spacing: 8px; text-align: center; font-family: 'Courier New', monospace;">
                            {code}
                        </h1>
                    </div>
                    
                    <p style="color: #e53e3e; font-size: 14px; background: #fff5f5; padding: 15px; border-radius: 5px; border-left: 4px solid #e53e3e;">
                        ⚠️ <strong>Security Notice:</strong> This code expires in 5 minutes. If you didn't request this code, please ignore this email and secure your account.
                    </p>
                    
                    <p style="color: #718096; font-size: 13px; margin-top: 30px;">
                        <strong>Security Tip:</strong> Never share this code with anyone. CSPM will never ask you for your verification code via email or phone.
                    </p>
                </div>
                
                <div style="text-align: center; padding: 20px; color: #a0aec0; font-size: 12px;">
                    <p>Cloud Security Posture Management Dashboard</p>
                    <p>This is an automated security email. Please do not reply.</p>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            CSPM Security - Login Verification
            
            Account: {user_email}
            
            Your verification code is: {code}
            
            This code expires in 5 minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            # Send email using the existing email service
            success = email_service._send_email(
                to_email=mfa_email,
                subject="🔐 Your CSPM Login Verification Code",
                html_content=html_body,
                text_content=text_body
            )
            
            if success:
                print(f"✅ MFA code sent to {mfa_email}")
            else:
                print(f"❌ Failed to send MFA code to {mfa_email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending MFA code: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def verify_code(
        db: Session,
        user_id: str,
        code: str
    ) -> bool:
        """
        Verify MFA code for a user
        
        Args:
            db: Database session
            user_id: User's UUID
            code: 6-digit code to verify
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Find valid code
            result = db.execute(text("""
                SELECT code_id, expires_at 
                FROM mfa_codes 
                WHERE user_id = :user_id 
                  AND code = :code 
                  AND used = FALSE
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
                LIMIT 1
            """), {"user_id": user_id, "code": code})
            
            row = result.fetchone()
            
            if not row:
                print(f"❌ Invalid or expired MFA code for user {user_id}")
                return False
            
            # Mark code as used
            db.execute(text("""
                UPDATE mfa_codes 
                SET used = TRUE 
                WHERE code_id = :code_id
            """), {"code_id": row[0]})
            
            db.commit()
            
            print(f"✅ MFA code verified for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying MFA code: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """
        Delete expired MFA codes (cleanup task)
        
        Returns:
            Number of codes deleted
        """
        try:
            result = db.execute(text("""
                DELETE FROM mfa_codes 
                WHERE expires_at < CURRENT_TIMESTAMP
                RETURNING code_id
            """))
            
            count = len(result.fetchall())
            db.commit()
            
            if count > 0:
                print(f"🗑️ Cleaned up {count} expired MFA codes")
            
            return count
            
        except Exception as e:
            print(f"❌ Error cleaning up MFA codes: {e}")
            db.rollback()
            return 0
