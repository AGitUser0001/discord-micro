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
  message = f"Hello, {request.name}!"
  if topology.store_url is None:
    raise RuntimeError("The overseer has not supplied a graph-store route.")

  response = await http.post(
    f"{topology.store_url}/graphql",
    json={
      "query": """
        mutation SaveGreeting($name: String!, $message: String!) {
          saveGreeting(name: $name, message: $message) { name message }
        }
      """,
      "variables": {"name": request.name, "message": message},
    },
  )
  response.raise_for_status()
  body = response.json()
  if body.get("errors"):
    raise RuntimeError(f"Store rejected greeting: {body['errors']}")

  await services.emit(AUDIT, AuditEntry(action="greeted", subject=request.name))
  return GreetingOutput(message=message)
