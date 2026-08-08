import asyncio

import httpx2


async def main() -> None:
  async with httpx2.AsyncClient(timeout=5.0) as client:
    registrations = [
      {
        "id": "store-1",
        "base_url": "http://127.0.0.1:8101",
        "role": "store",
        "modules": ["example.greetings"],
      },
      await service_registration(
        client,
        "api-1",
        "http://127.0.0.1:8102",
      ),
      await service_registration(
        client,
        "audit-1",
        "http://127.0.0.1:8103",
      ),
    ]
    for registration in registrations:
      response = await client.post(
        "http://127.0.0.1:8100/discovery/instances",
        json=registration,
      )
      response.raise_for_status()

    response = await client.post("http://127.0.0.1:8100/refresh")
    response.raise_for_status()
    print(f"Applied topology revision {response.json()['revision']}.")


async def service_registration(
  client: httpx2.AsyncClient,
  instance_id: str,
  base_url: str,
) -> dict[str, object]:
  response = await client.get(f"{base_url}/schema")
  response.raise_for_status()
  return {
    "id": instance_id,
    "base_url": base_url,
    "role": "service",
    "schema": response.json(),
  }


if __name__ == "__main__":
  asyncio.run(main())
