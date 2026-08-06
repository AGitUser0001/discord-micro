from micro.service import EventSchema, EventScope, RequestSchema, Service

service = Service("hello")

Greeting = EventSchema[dict](
  id="example.greeting",
  scope=EventScope.keyed("name"),
  payload={
    "type": "object",
    "properties": {"name": {"type": "string", "minLength": 1}},
    "required": ["name"],
    "additionalProperties": False,
  },
)

GreetingRequest = RequestSchema[dict, dict](
  id="example.get-greeting",
  input={
    "type": "object",
    "properties": {"name": {"type": "string", "minLength": 1}},
    "required": ["name"],
    "additionalProperties": False,
  },
  output={
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
    "additionalProperties": False,
  },
)


@service.listen(Greeting)
async def greet(event: dict) -> None:
  print(f"Hello, {event['name']}!")


@service.handle(GreetingRequest)
async def get_greeting(request: dict) -> dict:
  return {"message": f"Hello, {request['name']}!"}
