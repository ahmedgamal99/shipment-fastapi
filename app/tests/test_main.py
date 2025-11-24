

from httpx import AsyncClient
from app.tests import example

# @pytest.mark.asyncio
async def test_app(client : AsyncClient):
    response = await client.get("/")
    print(response.json())
    assert response.status_code == 200


