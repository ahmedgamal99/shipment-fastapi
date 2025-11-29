from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import EmailStr
from app.api.schemas.shipment import ShipmentRead
from app.api.tag import APITag
from app.core.exceptions import NothingToUpdate
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import (
    DeliveryPartnerDep,
    DeliveryPartnerServiceDep,
    get_partner_access_token,
)
from app.database.redis import add_jti_to_blacklist

from app.api.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)

router = APIRouter(prefix="/partner", tags=[APITag.PARTNER])


@router.post("/signup", response_model=DeliveryPartnerRead)
async def register_delivery_partner(
    partner: DeliveryPartnerCreate, service: DeliveryPartnerServiceDep
):
    return await service.add(partner)


@router.post("/token")
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    token = await service.token(request_form.username, request_form.password)
    return {"access_token": token, "type": "jwt"}

### Email Password Reset Link
@router.get("/forgot_password")
async def forgot_password(email: EmailStr, service: DeliveryPartnerServiceDep):
    await service.send_password_reset_link(email, router.prefix)
    return {"detail": "Check your email for password reset link"}

### Update the delivery partner
@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    # Update data with given fields
    update = partner_update.model_dump(exclude_none=True)

    if not update:
        raise NothingToUpdate()

    return await service.update(partner.sqlmodel_update(update))

@router.get("/me", response_model=DeliveryPartnerRead)
async def get_delivery_partner(partner: DeliveryPartnerDep):
    return partner

@router.get("/shipments", response_model=list[ShipmentRead])
async def get_shipments(partner: DeliveryPartnerDep):
    return partner.shipments

### Verify Seller Account
@router.get("/verify")
async def verify_delivery_partner_email(token: str, service: DeliveryPartnerServiceDep):
    await service.verify_email(token)
    return {"detail": "Account Verified"}


### Logout the Seller
@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    await add_jti_to_blacklist(token_data["jti"])
    return {"detail": "Successfully logged out"}
