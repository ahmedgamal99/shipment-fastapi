from datetime import datetime, timedelta
from uuid import UUID


from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate, ShipmentReview, ShipmentUpdate
from app.core.exceptions import ClientNotAuthorized, EntityNotFound, InvalidToken
from app.database.models import DeliveryPartner, Review, Seller, Shipment, ShipmentStatus, TagName
from app.database.redis import get_shipment_verification_code
from app.services.shipment_event import ShipmentEventService
from app.utils import decode_url_safe_token

from .base import BaseService
from .delivery_partner import DeliveryPartnerService


class ShipmentService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        partner_service: DeliveryPartnerService,
        event_serivce: ShipmentEventService,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service
        self.event_service = event_serivce

    # Get a shipment by id
    async def get(self, id: UUID) -> Shipment | None:
        shipment =  await self._get(id)
        if not shipment:
            raise EntityNotFound()
        return shipment

    # Add a new shipment
    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        # Assign delivery partner to the shipment
        partner = await self.partner_service.assign_shipment(
            new_shipment,
        )
        # Add the delivery partner foreign key
        new_shipment.delivery_partner_id = partner.id

        shipment = await self._add(new_shipment)

        event = await self.event_service.add(
            shipment=shipment,
            location=seller.zip_code,
            status=ShipmentStatus.placed,
            description=f"assigned to {partner.name}",
        )

        shipment.timeline.append(event)
        return shipment

    # Update an existing shipment
    async def update(
        self, id: UUID, shipment_update: ShipmentUpdate, partner: DeliveryPartner
    ) -> Shipment:
        shipment = await self.get(id)

        if shipment.delivery_partner_id != partner.id:
            raise ClientNotAuthorized()

        if shipment_update.status == ShipmentStatus.delivered:
            code = await get_shipment_verification_code(shipment.id)

            # if no code stored or mismatch, deny authorization
            if code is None or code != shipment_update.verification_code:
                raise ClientNotAuthorized()

        update = shipment_update.model_dump(
            exclude_none=True,
            exclude=["verification_code"]
        )
        # apply shipment-level fields
        if shipment_update.estimated_delivery is not None:
            shipment.estimated_delivery = shipment_update.estimated_delivery

        # prepare event fields (location, status, description)
        event_fields = {
            k: v
            for k, v in update.items()
            if k in ("location", "status", "description")
        }

        # if event fields provided, create an event and append it
        if event_fields:
            event = await self.event_service.add(shipment=shipment, **event_fields)
            # ensure association is visible
            shipment.timeline.append(event)

        # persist shipment changes and refresh
        return await self._update(shipment)

    async def add_tag(self, id : UUID, tag_name : TagName):
        shipment = await self.get(id)

        shipment.tags.append(await tag_name.tag(self.session))

        return await self._update(shipment)

    async def remove_tag(self, id : UUID, tag_name : TagName):
        shipment = await self.get(id)

        try:
            shipment.tags.remove(await tag_name.tag(self.session))
        except ValueError:
            raise EntityNotFound()

        return await self._update(shipment)

    async def rate(self, token: str, review: ShipmentReview):
        token_data = decode_url_safe_token(token)

        if not token_data:
            raise InvalidToken()
        
        shipment = await self.get(UUID(token_data["id"]))

        new_review = Review(
            **review.model_dump(), 
            shipment_id = shipment.id
        )

        self.session.add(new_review)
        await self.session.commit()
        
    async def cancel(self, id: UUID, seller: Seller) -> Shipment:
        shipment = await self.get(id)

        if shipment is None:
            raise EntityNotFound()

        if shipment.seller_id != seller.id:
            raise ClientNotAuthorized()

        # create a cancellation event and associate it
        event = await self.event_service.add(
            shipment=shipment, status=ShipmentStatus.cancelled
        )
        shipment.timeline.append(event)

        # persist changes and return refreshed shipment
        return await self._update(shipment)

    # Delete a shipment
    async def delete(self, id: int) -> None:
        await self._delete(await self.get(id))
