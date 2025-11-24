from enum import Enum

class APITag(str, Enum):
    SHIPMENT = "shipment"
    SELLER = "seller"
    PARTNER = "delivery partner"

