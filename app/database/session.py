
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import db_settings

engine = create_async_engine(
    url=db_settings.POSTGRES_URL, 
    echo = True,
)

async def create_tables():
    # Import models to ensure they're registered with SQLModel metadata
    from .models import Shipment  # noqa: F401
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
        

async def get_session():
    async_session = sessionmaker(
        bind=engine,
        class_= AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

