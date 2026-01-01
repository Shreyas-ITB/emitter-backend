from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from handlers.config import MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM, MAIL_PORT, MAIL_SERVER, MAIL_STARTTLS, MAIL_SSL_TLS, MAIL_USECREDENTIALS, MAIL_REDIRECT_URI

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=MAIL_USECREDENTIALS
)

async def send_verification_email(email: str, verification_code: str, background_color: str = "#f5f5f5", button_color: str = "#51e35c"):
    """Send a verification email."""
    verification_link = f"{MAIL_REDIRECT_URI}/{verification_code}"

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: {background_color}; padding: 20px; text-align: center;">
            <h2>Welcome to Dev Platform</h2>
            <p>Thank you for signing up! Please verify your email to activate your account.</p>
            <p>The link is only valid for 10 minutes and can be used only once.</p>
            <a href="{verification_link}" style="text-decoration: none;">
                <button style="background-color: {button_color}; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                    Verify Email
                </button>
            </a>
            <p>If the button does not work, click the link below:</p>
            <p>{verification_link}</p>
            <p style="color: gray; font-size: 12px; margin-top: 20px;">This is a system-generated email. Please do not respond or reply to this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Email Verification - Dev Platform",
        recipients=[email],
        body=html,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_warn_email(email: str, username: str, background_color: str = "#fff3cd", button_color: str = "#f0ad4e"):
    """Send a warning email to the user."""
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: {background_color}; padding: 20px; text-align: center;">
            <h2>Warning for Policy Violation</h2>
            <p>Dear {username},</p>
            <p>You have been warned for violating the terms and conditions by posting inappropriate content on our platform.</p>
            <p>Please note that if this behavior continues, your account will be permanently banned from the community.</p>
            <p>We encourage you to follow our community guidelines to maintain a healthy and respectful environment.</p>
            <p style="color: gray; font-size: 12px; margin-top: 20px;">This is a system-generated email. Please do not respond or reply to this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Warning Notice - Dev Platform",
        recipients=[email],
        body=html,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_ban_email(email: str, username: str, appeal_link: str, background_color: str = "#f8d7da", button_color: str = "#dc3545"):
    """Send a ban email to the user."""
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: {background_color}; padding: 20px; text-align: center;">
            <h2>Account Banned</h2>
            <p>Dear {username},</p>
            <p>Your account has been permanently banned for repeatedly violating the terms and conditions by posting inappropriate content on our platform.</p>
            <p>This decision is final and cannot be reversed, as we have gone through a thorough review of your behavior and interactions with our community.</p>
            <p>We regret any inconvenience caused and urge you to respect community guidelines in the future.</p>
            <p style="color: gray; font-size: 12px; margin-top: 20px;">This is a system-generated email. Please do not respond or reply to this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Account Banned - Dev Platform",
        recipients=[email],
        body=html,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)