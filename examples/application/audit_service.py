from schemas import AUDIT, AuditEntry

from micro.service import Service

service = Service("example.audit")


@service.listen(AUDIT)
async def audit(entry: AuditEntry) -> None:
  print(f"audit: {entry.action} {entry.subject}")
