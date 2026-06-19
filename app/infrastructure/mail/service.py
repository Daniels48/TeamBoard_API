from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings


VERIFY_EMAIL_TEMPLATE = "verify_email.html"
RESET_PASSWORD_TEMPLATE = "reset_password.html"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))



conf = ConnectionConfig(
        MAIL_USERNAME=settings.email.user,
        MAIL_PASSWORD=settings.email.password,
        MAIL_FROM=settings.email.user,
        MAIL_PORT=settings.email.port,
        MAIL_SERVER=settings.email.host,
        MAIL_STARTTLS=settings.email.starttls,
        MAIL_SSL_TLS=settings.email.ssl_tls,
    USE_CREDENTIALS=True,
)
mail = FastMail(conf)



class EmailService:

    @staticmethod
    async def send_email(email: str,subject: str,body: str) -> None:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype="html",
        )
        await mail.send_message(message)

    @staticmethod
    async def send_verification_email(email: str,token: str) -> None:

        template = env.get_template(VERIFY_EMAIL_TEMPLATE)
        body = template.render(code=token)

        await EmailService.send_email(
            email=email,
            subject="Verify your TeamBoard account",
            body=body,
        )

    @staticmethod
    async def send_reset_password_email(email: str,token: str) -> None:
        template = env.get_template(RESET_PASSWORD_TEMPLATE)
        body = template.render(code=token)

        await EmailService.send_email(
            email=email,
            subject="Reset your TeamBoard password",
            body=body,
        )

