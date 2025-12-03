from fastapi import FastAPI
from fastapi.routing import APIRoute
from scalar_fastapi import get_scalar_api_reference

from app.api.tag import APITag
from app.core.exceptions import add_exception_handlers
from app.api.router import master_router
from fastapi.middleware.cors import CORSMiddleware

# @asynccontextmanager
# async def lifespan_handler(app: FastAPI):
#     await create_tables()
#     yield
# lifespan=lifespan_handler

description = """
Delivery Management System for sellers and delivery agents

### Seller 
- Submit shipment effortlessly
- Share tracking links with customers

### Delivery Agent
- Auto accept shipments
- Track and update shipment status
- Email and SMS notifications
"""

def custom_generate_unique_id_function(route: APIRoute):
    return route.name

app = FastAPI(
    title = "FastShip", 
    description=description,
    version = "0.1.0",
    terms_of_service="https://fastship.com/terms/",
    contact={
        "name" : "FastShip Support",
        "url" : "https://fastship.com/support",
        "email" : "support@fastship.com"

    }, 
    openapi_tags=[
        {"name" : APITag.SHIPMENT, "description" : "Operations related to shipments"},
        {"name" : APITag.SELLER, "description" : "Operations related to sellers"},
        {"name" : APITag.PARTNER, "description" : "Operations related to partners"},
    ],
    generate_unique_id_function=custom_generate_unique_id_function,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Add all endpoints
app.include_router(master_router)

# Add custom exception handlers
add_exception_handlers(app)

### Server running status
@app.get("/")
def root():
    return {"detail" : "Server is running"}

### Scalar API Documentation
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )


