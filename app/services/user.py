from datetime import timedelta
from uuid import UUID
from app.core.exceptions import (
    InvalidToken,
    EntityNotFound,
    BadCredentials,
    ClientNotVerified,
)
from sqlalchemy import select
from app.database.models import User
from app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.config import app_settings
from app.utils import (
    decode_url_safe_token,
    generate_access_token,
    generate_url_safe_token,
)
from app.worker.tasks import send_email_with_template

password_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)


class UserService(BaseService):
    def __init__(self, model: User, session: AsyncSession):
        self.model = model
        self.session = session

    async def _add_user(self, data: dict, router_prefix: str):
        user = self.model(**data, password_hash=password_context.hash(data["password"]))

        user = await self._add(user)

        token = generate_url_safe_token(
            {
                "email": user.email,
                "id": str(user.id),
            }
        )

        # schedule sending verification email (await the coroutine so the background task is registered)
        send_email_with_template.delay(
            recipients=[user.email],
            subject=" Verify your Account with Fastship",
            context={
                "username": user.name,
                "verification_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}",
            },
            template_name="mail_email_verify.html",
        )

        return user

    async def verify_email(self, token: str):
        token_data = decode_url_safe_token(token)

        if not token_data:
            raise InvalidToken()

        user = await self._get(UUID(token_data["id"]))
        if user is None:
            raise EntityNotFound()

        user.email_verified = True
        await self._update(user)

    async def _get_by_email(self, email) -> User | None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )

    async def _generate_token(self, email, password) -> str:
        # Validate the credentials - normal get from the session will not work cuz email is not PK
        user = await self._get_by_email(email)

        # Return 401 for invalid credentials (standard Unauthorized)
        if user is None or not password_context.verify(password, user.password_hash):
            raise BadCredentials()

        if not user.email_verified:
            raise ClientNotVerified()

        token = generate_access_token(
            data={
                "user": {
                    "name": user.name,
                    "id": str(user.id),
                }
            }
        )

        return token

    async def send_password_reset_link(self, email, router_prefx: str):
        user = await self._get_by_email(email)

        token = generate_url_safe_token({"id": str(user.id)}, salt="password-reset")

        send_email_with_template.delay(
            recipients=[user.email],
            subject="FastShip Account Password Reset",
            context={
                "username": user.name,
                "reset_url": f"http://{app_settings.APP_DOMAIN}{router_prefx}/reset_password_form?token={token}",
            },
            template_name="mail_password_reset.html",
        )

    async def reset_password(self, token: str, password: str) -> bool:
        ### Returns true or false because the response template is handled from the router
        token_data = decode_url_safe_token(
            token,
            salt="password-reset",
            expiry=timedelta(days=1),
        )

        if not token_data:
            return False

        user = await self._get(UUID(token_data["id"]))
        user.password_hash = password_context.hash(password)

        await self._update(user)
        return True
