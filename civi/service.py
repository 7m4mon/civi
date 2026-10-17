import asyncio
import time
import itertools
from collections import deque
from . import __version__, scpi
from .errors import CiviError, ErrorQueue


class ControlService:
    def __init__(self, backend, config):
        self.backend, self.config = backend, config
        self.queue = asyncio.PriorityQueue(maxsize=128)
        self.sequence = itertools.count()
        self.clients = {}
        self.errors = {}
        self.logs = deque(maxlen=200)
        self.cache = {"frequency": None, "mode": None, "smeter": None, "ptt": None}
        self.owner = None
        self.tx_started = 0
        self.tasks = []
        self.last_poll = 0
        self.closing = False
        self.radio_model_id = None
        self.identified_model = None

    def clear_identity(self):
        self.radio_model_id = None
        self.identified_model = None

    async def identify(self):
        if self.radio_model_id is not None or "model_id_get" not in self.backend.profile["commands"]:
            return
        self.radio_model_id = await self.radio("model_id_get")
        if self.radio_model_id == self.backend.profile.get("model_id"):
            self.identified_model = self.backend.profile["model"]

    async def start(self):
        self.tasks = [asyncio.create_task(self._worker()), asyncio.create_task(self._watchdog()), asyncio.create_task(self._monitor())]

    def connect(self, client, web=False):
        self.clients[client] = (time.monotonic(), web)
        self.errors.setdefault(client, ErrorQueue())

    def touch(self, client):
        if client in self.clients:
            self.clients[client] = (time.monotonic(), self.clients[client][1])

    async def disconnect(self, client):
        self.clients.pop(client, None)
        if self.owner == client:
            await self._submit(None, "stop", None)
        self.errors.pop(client, None)

    async def execute(self, client, line):
        return await self._submit(client, "scpi", line)

    async def admin(self, client, kind, value=None):
        return await self._submit(client, kind, value)

    async def _submit(self, client, kind, value):
        if self.closing and kind != "stop":
            raise CiviError(-200, "Service shutting down")
        f = asyncio.get_running_loop().create_future()
        priority = 0 if kind == "stop" else 2 if kind == "poll" else 1
        await self.queue.put((priority, next(self.sequence), client, kind, value, f))
        return await asyncio.shield(f)

    def log(self, client, message, code=0):
        self.logs.append({"time": time.time(), "client": client, "message": message, "code": code})

    def record(self, client, error):
        if client in self.errors: self.errors[client].add(error)
        self.log(client, error.message, error.code)

    async def radio(self, op, value=None):
        try:
            result = await asyncio.to_thread(self.backend.call, op, value)
        except CiviError:
            self.cache = dict.fromkeys(self.cache)
            self.clear_identity()
            raise
        key = op.rsplit("_", 1)[0]
        if key in self.cache: self.cache[key] = result if op.endswith("get") else value
        return result

    async def _stop(self):
        try:
            await self.radio("ptt_set", False)
            self.owner = None
            self.log(None, "PTT OFF acknowledged")
        except CiviError as e:
            self.record(self.owner, e)
            # Keep ownership, retry OFF on watchdog; never report a successful stop.

    async def _command(self, client, key, query, arg):
        errors = self.errors[client]
        if key == "*IDN":
            try: await self.identify()
            except CiviError as e: self.record(client, e)
            model = self.identified_model or "Unknown"
            return f'{self.config["manufacturer"]},CIVI/{model},{self.config["serial_number"]},{__version__}'
        if key == "firmware": return self.config.get("radio_firmware") or "Unknown"
        if key == "*CLS": errors.clear(); return None
        if key == "*OPC": return "1"
        if key == "error": return errors.pop()
        if key not in self.backend.profile["features"]: raise CiviError(-241, "Unsupported feature")
        if query:
            value = await self.radio(key + "_get")
            return ("ON" if value else "OFF") if key == "ptt" else str(value)
        if key == "frequency":
            value = scpi.frequency(arg)
            if not any(lo <= value <= hi for lo, hi in self.backend.profile["frequency_ranges"]):
                raise CiviError(-222, "Frequency outside profile range")
        elif key == "mode":
            value = arg.upper()
            if value not in self.backend.profile["modes"]: raise CiviError(-222, "Unsupported mode")
        elif key == "ptt":
            if arg.upper() not in ("ON", "OFF"): raise CiviError(-224, "PTT requires ON or OFF")
            value = arg.upper() == "ON"
            if value:
                if not self.config["transmit"]["enabled"]: raise CiviError(-203, "Transmit control disabled")
                if self.owner and self.owner != client: raise CiviError(-200, "PTT owned by another client")
                if self.owner is None:
                    # ON timeout is ambiguous; own it before sending so OFF is attempted.
                    self.owner, self.tx_started = client, time.monotonic()
        await self.radio(key + "_set", value)
        if key == "ptt" and not value: self.owner = None

    async def _line(self, client, line):
        replies, parent = [], ""
        for part in line.split(";"):
            if client not in self.clients: break
            if self.owner and (self.owner not in self.clients or time.monotonic() - self.tx_started >= self.config["transmit"]["max_seconds"]):
                await self._stop()
            try:
                key, query, arg, parent = scpi.parse(part, parent)
                r = await self._command(client, key, query, arg)
                if r is not None: replies.append(r)
            except CiviError as e:
                self.record(client, e)
                # Failed queries get an explicit sentinel to keep TCP framing aligned.
                head = part.strip().split(None, 1)
                if head and "?" in head[0]: replies.append("ERROR")
        self.log(client, line[:1024])
        return ";".join(replies) if replies else None

    async def _worker(self):
        while True:
            _, _, client, kind, value, f = await self.queue.get()
            try:
                if kind == "stop":
                    await self._stop(); result = None
                elif kind == "poll":
                    await self.identify()
                    for key in self.cache:
                        if key not in self.backend.profile["features"]: continue
                        if self.owner and (self.owner not in self.clients or time.monotonic() - self.tx_started >= self.config["transmit"]["max_seconds"]):
                            await self._stop()
                        await self.radio(key + "_get")
                    result = None
                elif client not in self.clients:
                    result = None # Disconnected clients cannot execute queued mutations.
                elif kind == "scpi": result = await self._line(client, value)
                elif kind == "recover":
                    self.clear_identity()
                    await asyncio.to_thread(self.backend.recover)
                    if await self.radio("ptt_get"):
                        raise CiviError(-200, "Radio still transmitting; return to RX before recovery")
                    self.owner = None
                    result = None
                elif kind == "serial":
                    if self.owner: raise CiviError(-200, "PTT stop required before settings change")
                    # Preserve quarantine across settings edits.
                    state = self.backend.state
                    await asyncio.to_thread(self.backend.close)
                    self.config["serial"].update(value)
                    if hasattr(self.backend, "settings"): self.backend.settings.update(value)
                    if state == "quarantined": self.backend.state = state
                    self.cache = dict.fromkeys(self.cache)
                    self.clear_identity()
                    result = None
                else: raise CiviError(-200, "Unknown service operation")
                if not f.done(): f.set_result(result)
            except CiviError as e:
                self.record(client, e)
                if not f.done(): f.set_exception(e)
            except Exception as e:
                self.log(client, f"Internal failure: {type(e).__name__}", -310)
                if not f.done(): f.set_exception(CiviError(-310, "Internal service failure"))
            finally: self.queue.task_done()

    async def _watchdog(self):
        while True:
            await asyncio.sleep(0.25)
            now = time.monotonic()
            for client, (seen, web) in list(self.clients.items()):
                if web and now - seen > self.config["transmit"]["web_lease_seconds"]:
                    await self.disconnect(client)
            if self.owner and (self.owner not in self.clients or now - self.tx_started >= self.config["transmit"]["max_seconds"]):
                await self._submit(None, "stop", None)
    async def _monitor(self):
        while True:
            await asyncio.sleep(2)
            if self.queue.empty():
                if self.backend.state != "quarantined":
                    try: await self._submit(None, "poll", None)
                    except CiviError: pass

    def snapshot(self):
        return {"manufacturer": self.config["manufacturer"], "model": "CIVI", "serial": self.config["serial_number"],
                "version": __version__, "radio": self.backend.profile["model"], "backend": self.config["backend"],
                "radio_model": self.identified_model or "Unknown", "radio_model_id": self.radio_model_id,
                "radio_firmware": self.config.get("radio_firmware") or "Unknown",
                "radio_firmware_source": "manual" if self.config.get("radio_firmware") else "unknown",
                "connection": self.backend.state, "values": self.cache.copy(), "tx_enabled": self.config["transmit"]["enabled"],
                "tx_owner": self.owner, "smeter": self.backend.profile["smeter"], "modes": list(self.backend.profile["modes"]),
                "serial_settings": self.config["serial"].copy(), "logs": list(self.logs), "lxi_certified": False}

    async def close(self):
        self.closing = True
        self.clients.clear()
        # Keep the worker alive until its synchronous serial call has returned.
        # Cancelling to_thread does not stop the underlying serial thread.
        for t in self.tasks[1:]: t.cancel()
        await asyncio.gather(*self.tasks[1:], return_exceptions=True)
        if self.owner: await self._submit(None, "stop", None)
        await self.queue.join()
        for t in self.tasks[:1]: t.cancel()
        await asyncio.gather(*self.tasks[:1], return_exceptions=True)
        await asyncio.to_thread(self.backend.close)
