from micro.service import EventSchema, EventScope, Service

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


@service.listen(Greeting)
async def greet(event: dict) -> None:
  print(f"Hello, {event['name']}!")
