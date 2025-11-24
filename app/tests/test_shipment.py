from httpx import AsyncClient

from app.tests import example

base_url = "/shipment/"

async def test_submit_shipment_auth(client: AsyncClient):
    response = await client.post(
        base_url, 
        json = {},
    )

    assert response.status_code == 401


async def test_submit_shipment(client: AsyncClient, seller_token: str):
    response = await client.post(
        base_url,
        json=example.SHIPMENT,
        headers={"Authorization" : f"Bearer {seller_token}"}
    )

    assert response.status_code == 201

    response = await client.get(
        base_url, 
        params = {"id" : response.json()['id']}
    )

    assert response.status_code == 200