from schemas import AUDIT, AuditEntry

from micro.client import ServiceClient
from micro.service import Service

routes = ServiceClient()
service = Service("example.audit", state_receiver=routes)


@service.listen(AUDIT)
async def audit(entry: AuditEntry) -> None:
  print(f"audit: {entry.action} {entry.subject}")
