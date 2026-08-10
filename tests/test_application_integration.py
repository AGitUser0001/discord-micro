import asyncio
import os
import signal
from pathlib import Path

import httpx2
import pytest

pytestmark = pytest.mark.skipif(
  os.getenv("MICRO_RUN_APPLICATION_INTEGRATION") != "1",
  reason=(
    "Set MICRO_RUN_APPLICATION_INTEGRATION=1 after starting the example's "
    "AGE and NATS containers."
  ),
)

_ROOT = Path(__file__).parents[1]
_APPLICATION = _ROOT / "examples" / "application"
_PROCESSES = (
  ("overseer:app", 8100),
  ("store:store", 8101),
  ("api_service:service", 8102),
  ("audit_service:service", 8103),
  ("queue_service:queue", 8104),
  ("gateway_event_service:event_service", 8105),
  ("gateway_projection:projection", 8106),
)


def test_complete_application_start_reconcile_deliver_query_and_stop() -> None:
  asyncio.run(_exercise_application())


async def _exercise_application() -> None:
  processes = [
    await asyncio.create_subprocess_exec(
      "uv",
      "run",
      "uvicorn",
      target,
      "--port",
      str(port),
      cwd=_APPLICATION,
      stdout=asyncio.subprocess.DEVNULL,
      stderr=asyncio.subprocess.PIPE,
    )
    for target, port in _PROCESSES
  ]
  try:
    async with httpx2.AsyncClient(timeout=2) as client:
      await asyncio.gather(
        *(
          _wait_ready(client, process, port)
          for process, (_, port) in zip(processes, _PROCESSES)
        )
      )
      configure = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "configure.py",
        cwd=_APPLICATION,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
      )
      stdout, stderr = await asyncio.wait_for(configure.communicate(), timeout=15)
      assert configure.returncode == 0, (stdout + stderr).decode(errors="replace")

      response = await client.post(
        "http://127.0.0.1:8102/requests/example.greet",
        json={"name": "integration"},
      )
      response.raise_for_status()
      assert response.json()["message"]

      graph = await client.post(
        "http://127.0.0.1:8101/graphql",
        json={"query": '{ greeting(name: "integration") { name message } }'},
      )
      graph.raise_for_status()
      assert "errors" not in graph.json()
  finally:
    for process in processes:
      if process.returncode is None:
        process.send_signal(signal.SIGTERM)
    results = await asyncio.gather(
      *(asyncio.wait_for(process.wait(), timeout=10) for process in processes),
      return_exceptions=True,
    )
    for process, result in zip(processes, results):
      if isinstance(result, TimeoutError):
        process.kill()
        await process.wait()


async def _wait_ready(
  client: httpx2.AsyncClient,
  process: asyncio.subprocess.Process,
  port: int,
) -> None:
  for _ in range(100):
    if process.returncode is not None:
      stderr = await process.stderr.read() if process.stderr is not None else b""
      raise AssertionError(
        f"application process on port {port} exited:\n{stderr.decode(errors='replace')}"
      )
    try:
      response = await client.get(f"http://127.0.0.1:{port}/health/live")
      if response.is_success:
        return
    except httpx2.HTTPError:
      pass
    await asyncio.sleep(0.1)
  raise AssertionError(f"application process on port {port} did not become live")
