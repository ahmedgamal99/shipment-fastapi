from typing import Sequence
from app.core.exceptions import DeliveryPartnerNotAvailable
from sqlmodel import select
from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from app.database.models import DeliveryPartner, Location, Shipment
from app.services.user import UserService


class DeliveryPartnerService(UserService):
    def __init__(self, session):
        super().__init__(DeliveryPartner, session)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        partner: DeliveryPartner = await self._add_user(
            delivery_partner.model_dump(), router_prefix="partner"
        )

        for zip_code in delivery_partner.serviceable_zip_codes:
            location = await self.session.get(Location, zip_code)
            partner.servicable_locations.append(
                location if location else Location(zip_code)
            )

        return self._update(partner)

    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        # await scalars() to get a ScalarResult, then call .all()
        # Join DeliveryPartner to Location via the relationship and filter by zip code
        stmt = (
            select(DeliveryPartner)
            .join(DeliveryPartner.servicable_locations)
            .where(Location.zip_code == zipcode)
        )

        result = await self.session.scalars(stmt)
        return result.all()

    async def assign_shipment(self, shipment: Shipment):
        eligible_partners = await self.get_partners_by_zipcode(shipment.destination)

        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                # Persist association if needed; session will pick this up when committing
                return partner

        raise DeliveryPartnerNotAvailable()

    async def update(self, partner: DeliveryPartner):
        return await self._update(partner)

    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)
