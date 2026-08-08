from schemas import AUDIT, GREET, AuditEntry, GreetingInput, GreetingOutput

from micro.service import Service

service = Service("example.api")


@service.handle(GREET)
async def greet(request: GreetingInput) -> GreetingOutput:
  body = await service.store.execute(
    """
        query Greeting($name: String!) {
          greeting(name: $name) { message }
        }
    """,
    variables={"name": request.name},
    module="example.greetings",
  )
  if body.get("errors"):
    raise RuntimeError(f"Store query failed: {body['errors']}")

  stored = body.get("data", {}).get("greeting")
  message = (
    stored["message"]
    if isinstance(stored, dict) and isinstance(stored.get("message"), str)
    else f"Hello, {request.name}!"
  )

  await service.client.emit(AUDIT, AuditEntry(action="greeted", subject=request.name))
  return GreetingOutput(message=message)
