from app.celery_app import celery_app
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
import asyncio

# Email server configuration — created once when the file loads
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD, #type: ignore
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_application_confirmation(self, applicant_email: str, job_title: str, company_name: str):
    try:
        # Build the email message
        message = MessageSchema(
            subject=f"Application Received — {job_title}",
            recipients=[applicant_email], # type: ignore
            body=f"""
Hi,

Your application for {job_title} at {company_name} has been received successfully.

We will get back to you soon.

Best regards,
Job Board Team
            """,
            subtype=MessageType.plain
        )

        # Send the email
        fm = FastMail(mail_config)
        asyncio.run(fm.send_message(message))

    except Exception as exc:
        raise self.retry(exc=exc)