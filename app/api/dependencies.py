from typing import Annotated
from uuid import UUID

from fastapi import Depends
from app.core.exceptions import InvalidToken, ClientNotAuthorized
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DeliveryPartner, Seller
from app.database.redis import is_jti_blacklisted
from app.database.session import get_session
from app.services.delivery_partner import DeliveryPartnerService
from app.services.seller import SellerService
from app.services.shipment import ShipmentService
from app.core.security import oauth2_scheme_seller, oauth2_scheme_partner
from app.services.shipment_event import ShipmentEventService
from app.utils import decode_access_token

# Asynchronous database session dep annotation
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Access token data dep
async def _get_access_token(token: str) -> dict:
    data = decode_access_token(token)

    if data is None or await is_jti_blacklisted(data["jti"]):
        raise InvalidToken()

    return data


async def get_seller_access_token(
    token: Annotated[str, Depends(oauth2_scheme_seller)],
):
    return await _get_access_token(token)


async def get_partner_access_token(
    token: Annotated[str, Depends(oauth2_scheme_partner)],
):
    return await _get_access_token(token)


# Logged In User
async def get_current_seller(
    token_data: Annotated[dict, Depends(get_seller_access_token)], session: SessionDep
):
    seller = await session.get(Seller, UUID(token_data["user"]["id"]))
    if seller is None:
        raise ClientNotAuthorized()

    return seller


async def get_current_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)], session: SessionDep
):
    partner = await session.get(DeliveryPartner, UUID(token_data["user"]["id"]))

    if partner is None:
        raise ClientNotAuthorized()

    return partner


# Shipment service dep
def get_shipment_service(session: SessionDep):
    return ShipmentService(
        session,
        DeliveryPartnerService(session),
        ShipmentEventService(session),
    )


def get_seller_service(session: SessionDep):
    return SellerService(session)


def get_delivery_partner_service(session: SessionDep):
    return DeliveryPartnerService(session)


# Seller dep
SellerDep = Annotated[Seller, Depends(get_current_seller)]

# Partner dep
DeliveryPartnerDep = Annotated[
    DeliveryPartner,
    Depends(get_current_partner),
]

ShipmentServiceDep = Annotated[
    ShipmentService,
    Depends(get_shipment_service),
]

SellerServiceDep = Annotated[
    SellerService,
    Depends(get_seller_service),
]

DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService,
    Depends(get_delivery_partner_service),
]
