import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Self

import pytest


def _free_port() -> int:
  with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    return sock.getsockname()[1]


def _wait_for_port(port: int, process: subprocess.Popen[bytes]) -> None:
  deadline = time.monotonic() + 10
  while time.monotonic() < deadline:
    if process.poll() is not None:
      raise RuntimeError("nats-server exited during startup.")
    with socket.socket() as sock:
      if sock.connect_ex(("127.0.0.1", port)) == 0:
        return
    time.sleep(0.05)
  raise RuntimeError("nats-server did not start listening.")


@pytest.fixture
def nats_url(tmp_path: Path) -> Iterator[str]:
  """A fresh JetStream-enabled nats-server for one test."""
  binary = os.environ.get("MICRO_NATS_SERVER") or shutil.which("nats-server")
  if binary is None:
    pytest.skip(
      "nats-server is not installed; set MICRO_NATS_SERVER or add it to PATH."
    )
  port = _free_port()
  process = subprocess.Popen(
    [binary, "-js", "-a", "127.0.0.1", "-p", str(port), "-sd", str(tmp_path / "js")],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  try:
    _wait_for_port(port, process)
    yield f"nats://127.0.0.1:{port}"
  finally:
    process.terminate()
    try:
      process.wait(timeout=10)
    except subprocess.TimeoutExpired:
      process.kill()


class EngineReply:
  def __init__(self, status_code: int, body: object) -> None:
    self.status_code = status_code
    self._body = body

  def json(self) -> Any:
    return self._body


class EngineHarness:
  """Drives a GraphEngine synchronously with `/topology` and `/graphql` calls."""

  def __init__(self, executor: object) -> None:
    import asyncio

    from micro.store import GraphEngine

    self.engine = GraphEngine(executor)  # type: ignore[arg-type]
    self._runner = asyncio.Runner()

  def __enter__(self) -> Self:
    self._runner.run(self.engine.executor.start())
    return self

  def __exit__(self, *exc_info: object) -> None:
    self._runner.run(self.engine.executor.close())
    self._runner.close()

  def post(self, path: str, *, json: dict[str, object]) -> EngineReply:
    from micro.store import GraphModule, GraphQLBody

    if path == "/topology":
      modules = [GraphModule.model_validate(item) for item in json["modules"]]  # type: ignore[union-attr]
      try:
        self._runner.run(self.engine.apply_modules(modules))
      except Exception as exc:
        return EngineReply(409, {"errors": [{"message": str(exc)}]})
      return EngineReply(204, None)
    if path == "/graphql":
      body = GraphQLBody.model_validate(json)
      return EngineReply(200, self._runner.run(self.engine.execute(body)))
    raise ValueError(path)
