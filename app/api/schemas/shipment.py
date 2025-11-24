from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import SQLModel

from app.database.models import ShipmentEvent, ShipmentStatus, Tag, TagName


class BaseShipment(SQLModel):
    content: str = Field(max_length=255)
    weight: float = Field(le=25)
    destination: int = Field(
        description = "ZIP code of the shipment destination",
        examples=[11001, 11002]
    )

class TagRead(BaseModel):
    name: TagName
    instruction: str

class ShipmentRead(BaseShipment):
    id : UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime | None = None
    tags : list[TagRead]


class ShipmentCreate(BaseShipment):
    """ Shipment creation schema """
    client_contact_email : EmailStr
    # Phone numbers should be strings (allow +, leading zeros). Make optional.
    client_contact_phone: str | None = None
    

class ShipmentUpdate(BaseModel):
    location : int | None = Field(default = None)
    status: ShipmentStatus | None = Field(default=None)
    verification_code : int | None = Field(default=None)
    description : str | None = Field(default= None)
    estimated_delivery: datetime | None = Field(default=None)

class ShipmentReview(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment : str | None = Field(default=None)