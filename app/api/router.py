from fastapi import APIRouter

from .routers import shipment, seller, delivery_partner

master_router = APIRouter()
master_router.include_router(shipment.router)
master_router.include_router(seller.router)
master_router.include_router(delivery_partner.router)