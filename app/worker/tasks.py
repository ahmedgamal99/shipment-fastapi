from celery import Celery
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config import db_settings, notification_settings
from app.utils import TEMPLATE_DIR
from asgiref.sync import async_to_sync
from twilio.rest import Client

fastmail = FastMail(
    ConnectionConfig(
        **notification_settings.email_config(),
        TEMPLATE_FOLDER=TEMPLATE_DIR,
    )
)

twilio_client = Client(
    notification_settings.TWILIO_SID,
    notification_settings.TWILIO_AUTH_TOKEN,
)

app = Celery(
    "api_tasks",
    broker=db_settings.REDIS_URL(9),
    backend=db_settings.REDIS_URL(9),
    broker_connection_retry_on_startup = True
)


send_message = async_to_sync(fastmail.send_message)
@app.task
def add_log(log: str) -> None:
    with open("file.log", "a") as file:
        file.write(f"{log}\n")
        
@app.task
def send_mail(recipients: list[str], subject: str, body: str):
    send_message(
        MessageSchema(
            recipients=recipients, subject=subject, body=body, subtype=MessageType.plain
        )
    )

    return "Message Sent"


@app.task
def send_email_with_template(
    recipients: list[EmailStr],
    subject: str,
    context: dict,
    template_name: str,
):
    send_message(
        message=MessageSchema(
            recipients=recipients,
            subject=subject,
            template_body=context,
            subtype=MessageType.html,
        ),
        template_name=template_name,
    )


@app.task
def send_sms(to: str, body: str):
    twilio_client.messages.create(
        from_=notification_settings.TWILIO_NUMBER, to=to, body=body
    )
