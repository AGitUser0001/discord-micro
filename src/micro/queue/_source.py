from typing import Protocol


class QueueDelivery(Protocol):
  """One item received from a queue backend."""

  @property
  def payload(self) -> bytes: ...

  async def acknowledge(self) -> None: ...

  async def retry(self) -> None: ...


class QueueSource(Protocol):
  """A competing consumer bound to one queue channel."""

  async def start(self) -> None: ...

  async def receive(self) -> QueueDelivery: ...

  async def close(self) -> None: ...
