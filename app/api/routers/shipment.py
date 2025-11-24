from typing import Annotated
from uuid import UUID
from app.api.tag import APITag
from app.config import app_settings
from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates

from app.api.dependencies import (
    DeliveryPartnerDep,
    SellerDep,
    SessionDep,
    ShipmentServiceDep,
)
from app.api.schemas.shipment import (
    ShipmentCreate,
    ShipmentRead,
    ShipmentReview,
    ShipmentUpdate,
)
from app.database.models import Shipment, TagName
from app.utils import TEMPLATE_DIR
from app.core.exceptions import BadRequest, EntityNotFound, NothingToUpdate
from fastapi import status


router = APIRouter(prefix="/shipment", tags=[APITag.SHIPMENT])

templates = Jinja2Templates(TEMPLATE_DIR)


###  a shipment by id
@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    return await service.get(id)


### Tracking details of shipment
@router.get("/track", include_in_schema=False)
async def get_tracking(request: Request, id: str, service: ShipmentServiceDep):
    """
    Track a shipment by UUID passed as a query parameter. This route
    accepts a raw string so we can strip accidental whitespace and
    return a cleaner 400 error when the UUID is invalid instead of
    exposing the low-level pydantic parse error.
    """
    # strip accidental leading/trailing whitespace that often comes from
    # user input or UI bugs (e.g. " 4ff6a7d4-...")
    shipment_id_raw = (id or "").strip()

    try:
        shipment_id = UUID(shipment_id_raw)
    except Exception:
        raise BadRequest()

    shipment = await service.get(shipment_id)

    if not shipment:
        raise EntityNotFound()

    context = shipment.model_dump()
    context["status"] = shipment.status
    context["partner"] = shipment.delivery_partner.name
    context["timeline"] = shipment.timeline

    # Jinja2Templates expects the template context to include the request
    # under the 'request' key.
    context_with_request = {"request": request, **context}

    return templates.TemplateResponse("track.html", context_with_request)


### Create a new shipment with content and weight
@router.post(
    "/",
    response_model=ShipmentRead,
    name="Create Shipment",
    description="Submit a new shipment",
    status_code=status.HTTP_201_CREATED,
    responses = {
        status.HTTP_201_CREATED: {"description": "Shipment created successfully", "content": {"application/json": { "example": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "content": "Books",
            "weight": 2.5,
            "status": "placed",
            "estimated_delivery": "2024-07-01T12:00:00Z",
            "seller_id": "987e6543-e21b-12d3-a456-426614174000",
            "delivery_partner_id": "456e7890-e21b-12d3-a456-426614174000",
            "timeline": [],
            "tags": []
        }}}},
        status.HTTP_406_NOT_ACCEPTABLE: {"description": "Delivery partner cannot accept more shipments"},
    }
)
async def submit_shipment(
    seller: SellerDep,
    shipment: ShipmentCreate,
    service: ShipmentServiceDep,
) -> Shipment:
    return await service.add(shipment, seller)


### Update fields of a shipment
@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    shipment_update: ShipmentUpdate,
    partner: DeliveryPartnerDep,
    service: ShipmentServiceDep,
):
    # Update data with given fields
    update = shipment_update.model_dump(exclude_none=True)

    if not update:
        raise NothingToUpdate()

    return await service.update(id, shipment_update, partner)


### Get all shipments with a tag
@router.get("/tagged", response_model=list[ShipmentRead])
async def get_shipment_with_tag(tag_name: TagName, session: SessionDep):
    tag = await tag_name.tag(session)
    return tag.shipments


### Add a tag to a shipment
@router.get("/tag", response_model=ShipmentRead)
async def add_tag_to_shipment(id: UUID, tag_name: TagName, service: ShipmentServiceDep):
    return await service.add_tag(id, tag_name)


### Add a tag to a shipment
@router.delete("/remove_tag", response_model=ShipmentRead)
async def remove_tag_from_shipment(
    id: UUID, tag_name: TagName, service: ShipmentServiceDep
):
    return await service.remove_tag(id, tag_name)


### Cancel a shipment by id
@router.post("/{id}/cancel", response_model=ShipmentRead)
async def cancel_shipment(id: UUID, seller: SellerDep, service: ShipmentServiceDep):
    """Cancel a shipment. Requires the authenticated seller who owns the shipment."""
    return await service.cancel(id, seller)


@router.get("/review")
async def submit_review_page(request: Request, token: str):
    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context={
            "review_url": f"http://{app_settings.APP_DOMAIN}/shipment/review?token={token}"
        },
        template_name="mail_delivered.html",
    )


### Submit a review for a shipment
@router.post("/review")
async def submit_review(
    token: str,
    rating: Annotated[int, Form(ge=1, le=5)],
    comment: Annotated[str | None, Form()],
    service: ShipmentServiceDep,
):
    await service.rate(token, ShipmentReview(rating=rating, comment=comment))
    return {"detail": "Review submitted"}
