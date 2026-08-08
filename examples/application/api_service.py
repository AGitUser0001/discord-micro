import httpx2
from schemas import AUDIT, GREET, AuditEntry, GreetingInput, GreetingOutput
from topology import ApplicationTopology

from micro.client import ServiceClient
from micro.service import Service

services = ServiceClient()
topology = ApplicationTopology(services)
http = httpx2.AsyncClient(timeout=5.0)
service = Service("example.api", state_receiver=topology)


@service.handle(GREET)
async def greet(request: GreetingInput) -> GreetingOutput:
  if topology.store_url is None:
    raise RuntimeError("The overseer has not supplied a graph-store route.")

  response = await http.post(
    f"{topology.store_url}/graphql",
    json={
      "query": """
        query Greeting($name: String!) {
          greeting(name: $name) { message }
        }
      """,
      "variables": {"name": request.name},
    },
  )
  response.raise_for_status()
  body = response.json()
  if body.get("errors"):
    raise RuntimeError(f"Store query failed: {body['errors']}")

  stored = body.get("data", {}).get("greeting")
  message = (
    stored["message"]
    if isinstance(stored, dict) and isinstance(stored.get("message"), str)
    else f"Hello, {request.name}!"
  )

  await services.emit(AUDIT, AuditEntry(action="greeted", subject=request.name))
  return GreetingOutput(message=message)
