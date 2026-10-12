import resend
from flask import current_app, render_template

def send_reset_email(user, reset_url):
    """
    Sends a password reset email using the Resend HTTPS API.
    If RESEND_API_KEY is not configured or an error occurs in test/dev,
    it logs a clear fallback message to console so development is never blocked.
    """
    api_key = current_app.config.get('RESEND_API_KEY')
    from_email = current_app.config.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')

    html_content = render_template('auth/email/reset_password_email.html', user=user, reset_url=reset_url)
    text_content = f"""Hello,

To reset your password for ResumeBuilder, visit the following link:
{reset_url}

This link is valid for 30 minutes. If you did not make this request, you can safely ignore this email.

Best regards,
The ResumeBuilder Team
"""

    if not api_key:
        current_app.logger.warning(
            f"[RESEND NOT CONFIGURED] RESEND_API_KEY is empty. "
            f"Reset email for {user.email} simulated. Reset URL: {reset_url}"
        )
        return False

    try:
        resend.api_key = api_key
        params = {
            "from": from_email,
            "to": [user.email],
            "subject": "Reset Your ResumeBuilder Password",
            "html": html_content,
            "text": text_content,
        }
        response = resend.Emails.send(params)
        current_app.logger.info(f"Password reset email sent to {user.email} via Resend. Response: {response}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email via Resend API: {e}")
        # Return False so caller can handle appropriately if needed
        return False

