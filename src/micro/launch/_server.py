"""The NATS server nodes connect to, run on its own: `micro server start`."""

import asyncio
import shutil
import signal
from contextlib import suppress
from pathlib import Path

from micro.log import Logger

from ._config import DeploymentConfig

log = Logger("micro.server")


async def reachable(host: str, port: int) -> bool:
  """Whether something accepts connections at host:port."""
  try:
    _, writer = await asyncio.open_connection(host, port)
  except OSError:
    return False
  writer.close()
  with suppress(Exception):
    await writer.wait_closed()
  return True


class NatsServer:
  """A local nats-server for a deployment: JetStream on, data in `store_dir`.

  It runs in its own session, so a terminal's Ctrl-C reaches whoever started it
  and not the server, which is stopped last.
  """

  def __init__(self, config: DeploymentConfig, path: str | Path) -> None:
    self.config = config
    self.root = Path(path).resolve().parent
    self._process: asyncio.subprocess.Process | None = None

  @property
  def address(self) -> tuple[str, int]:
    local = self.config.local_nats()
    if local is None:
      raise ValueError(
        f"nats = {self.config.nats[0]!r} is not this machine; "
        "start the server on the host it names."
      )
    return local

  def command(self) -> list[str]:
    settings = self.config.nats_server
    host, port = self.address
    store = (self.root / settings.store_dir).resolve()
    binary = shutil.which(settings.binary) or settings.binary
    return [
      binary,
      "-js",
      "-a",
      host,
      "-p",
      str(port),
      "-sd",
      str(store),
      *settings.args,
    ]

  async def reachable(self) -> bool:
    return await reachable(*self.address)

  async def start(self) -> None:
    """Start nats-server and wait until it accepts connections."""
    if not self.config.nats_server.enabled:
      raise ValueError(
        "[nats_server] is disabled in micro.toml; this deployment uses its own server."
      )
    command = self.command()
    Path(command[command.index("-sd") + 1]).mkdir(parents=True, exist_ok=True)
    try:
      self._process = await asyncio.create_subprocess_exec(
        *command, start_new_session=True
      )
    except FileNotFoundError as error:
      raise FileNotFoundError(
        f"{command[0]!r} was not found; install nats-server (for example "
        "`brew install nats-server`) or set [nats_server] binary in micro.toml."
      ) from error
    host, port = self.address
    log.info(
      "Started nats-server on %s:%d (store %s)",
      host,
      port,
      command[command.index("-sd") + 1],
    )
    while not await reachable(host, port):
      if self._process.returncode is not None:
        raise RuntimeError("nats-server exited during startup.")
      await asyncio.sleep(0.05)

  async def stop(self) -> None:
    process, self._process = self._process, None
    if process is None:
      return
    with suppress(ProcessLookupError):
      process.send_signal(signal.SIGTERM)
    await process.wait()

  async def run(self) -> int:
    """Run in the foreground until interrupted, or until nats-server exits."""
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    signals = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
      signals.append(signal.SIGHUP)
    for sig in signals:
      with suppress(NotImplementedError, RuntimeError):
        loop.add_signal_handler(sig, stop.set)
    await self.start()
    assert self._process is not None
    exited = asyncio.create_task(self._process.wait())
    interrupted = asyncio.create_task(stop.wait())
    await asyncio.wait((exited, interrupted), return_when=asyncio.FIRST_COMPLETED)
    crashed = exited.done()
    for task in (exited, interrupted):
      task.cancel()
    code = self._process.returncode if crashed else 0
    await self.stop()
    return int(code or 0)
