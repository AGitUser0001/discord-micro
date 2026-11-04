import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

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
    pytest.skip("nats-server is not installed; set MICRO_NATS_SERVER or add it to PATH.")
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
