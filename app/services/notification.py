from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.config import notification_settings
from app.utils import TEMPLATE_DIR
from twilio.rest import Client
from twilio.http.async_http_client import AsyncTwilioHttpClient
import logging

class NotificationService:
    def __init__(self, tasks: BackgroundTasks):
        self.tasks = tasks
        self.fastmail = FastMail(
            ConnectionConfig(
                **notification_settings.email_config(),
                TEMPLATE_FOLDER=TEMPLATE_DIR,
            )
        )

        self.twilio_client = Client(
            notification_settings.TWILIO_SID,
            notification_settings.TWILIO_AUTH_TOKEN,
            http_client=AsyncTwilioHttpClient(pool_connections=False),
        )
        self.logger = logging.getLogger("app.notifications")

    async def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
    ):
        self.tasks.add_task(
            self.fastmail.send_message,
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                body=body,
                subtype=MessageType.plain,
            ),
        )

    async def send_email_with_template(
        self,
        recipients: list[EmailStr],
        subject: str,
        context: dict,
        template_name: str,
    ):
        self.tasks.add_task(
            self.fastmail.send_message,
            message=MessageSchema(
                recipients=recipients,
                subject=subject,
                template_body=context,
                subtype=MessageType.html,
            ),
            template_name=template_name,
        )

    async def send_sms(self, to : str, body : str):
        try:
            await self.twilio_client.messages.create(
                from_ = notification_settings.TWILIO_NUMBER,
                to = to,
                body = body,
            )
        except Exception as exc:
            # Log and swallow errors to avoid crashing the request path. Background tasks or
            # dedicated retry logic can surface/fix transient Twilio issues.
            self.logger.exception("Failed to send SMS to %s: %s", to, exc)