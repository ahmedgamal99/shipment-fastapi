from redis.asyncio import Redis
from uuid import UUID

from app.config import db_settings


_token_blacklist = Redis(
    host=db_settings.REDIS_HOST,
    port=int(db_settings.REDIS_PORT),
    db=0,
)

_shipment_verification_codes = Redis(
    host=db_settings.REDIS_HOST,
    port=int(db_settings.REDIS_PORT),
    db=1,
    decode_responses=True
)
async def add_jti_to_blacklist(jti: str):
    await _token_blacklist.set(jti, "blacklisted")


async def is_jti_blacklisted(jti: str) -> bool:
    try:
        return bool(await _token_blacklist.exists(jti))
    except Exception:
        # If Redis is unavailable, treat token as NOT blacklisted so the app
        # doesn't fail-open on auth checks — callers can decide how strict to be.
        return False

async def add_shipment_verification_code(id: UUID, code : int):
    # store as string; consider adding TTL if desired
    await _shipment_verification_codes.set(str(id), str(code))

async def get_shipment_verification_code(id: UUID) -> int | None:
    """Return the stored verification code as an int, or None if missing."""
    v = await _shipment_verification_codes.get(str(id))
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        # Unexpected format — return None so callers treat as missing
        return None