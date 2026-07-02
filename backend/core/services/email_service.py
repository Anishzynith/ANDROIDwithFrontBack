from django.conf import settings
from django.core.mail import EmailMultiAlternatives,get_connection


class EmailService:
    @staticmethod
    def send_email(subject, body_text, body_html, recipient):
        connection = get_connection(timeout=getattr(settings, "EMAIL_TIMEOUT", 10))
        message = EmailMultiAlternatives(
            subject,
            body_text,
            getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            [recipient],
            connection=connection
        )
        message.attach_alternative(body_html, "text/html")
        message.send(fail_silently=False)

    @classmethod
    def send_otp(cls, email, otp_code, purpose):
        subject_by_purpose = {
            "REGISTER": "Email Verification OTP",
            "PASSWORD_RESET": "Password Reset OTP",
            "EMAIL_CHANGE": "Email Change OTP",
            "LOGIN": "Login OTP",
        }
        subject = subject_by_purpose.get(purpose, "Verification OTP")
        body_text = f"Your verification OTP is: {otp_code}\n\nThis OTP will expire in 5 minutes."
        body_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f6fb; margin: 0; padding: 0;">
                <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 40px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 12px 35px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background: #4f46e5; padding: 32px; text-align: center; color: #ffffff;">
                            <h1 style="margin: 0; font-size: 28px;">{subject}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px; color: #334155;">
                            <p style="font-size: 16px; margin: 0 0 16px;">Your verification OTP is:</p>
                            <div style="margin: 24px 0; padding: 24px; border-radius: 12px; background: #eef2ff; text-align: center;">
                                <span style="display: inline-block; font-size: 32px; letter-spacing: 0.16em; font-weight: 700; color: #312e81;">{otp_code}</span>
                            </div>
                            <p style="font-size: 16px; margin: 0 0 24px;">This OTP will expire in 5 minutes.</p>
                            <p style="font-size: 16px; margin: 0; color: #64748b;">If you did not request this, please ignore this email.</p>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        cls.send_email(subject, body_text, body_html, email)

