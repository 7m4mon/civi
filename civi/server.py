import asyncio
import base64
import hmac
import secrets
from pathlib import Path
from aiohttp import web
from .errors import CiviError
from .network import network_info
from .commands import CATALOG


async def scpi_client(reader, writer, service):
    client = "tcp-" + secrets.token_hex(8)
    service.connect(client)
    messages = asyncio.Queue(maxsize=32)
    async def receive():
        while True:
            try: raw = await reader.readline()
            except (ValueError, asyncio.LimitOverrunError): break
            if not raw or not raw.endswith(b"\n"): break
            try: line = raw.decode("ascii").strip()
            except UnicodeDecodeError:
                service.record(client, CiviError(-102, "ASCII required")); continue
            if not line: continue
            try: messages.put_nowait(line)
            except asyncio.QueueFull:
                service.record(client, CiviError(-350, "Input backlog exceeded")); break
    async def consume():
        while True:
            line = await messages.get()
            response = await service.execute(client, line)
            if response is not None:
                writer.write((response + "\n").encode("ascii", errors="replace"))
                await writer.drain()
    receiver = asyncio.create_task(receive())
    consumer = asyncio.create_task(consume())
    try:
        done, _ = await asyncio.wait([receiver, consumer], return_when=asyncio.FIRST_COMPLETED)
        for task in done: await task
    except (ConnectionError, OSError): pass
    finally:
        await service.disconnect(client)
        receiver.cancel(); consumer.cancel()
        await asyncio.gather(receiver, consumer, return_exceptions=True)
        writer.close()
        try: await writer.wait_closed()
        except (ConnectionError, OSError): pass


def make_web(service, password):
    @web.middleware
    async def security(request, handler):
        if request.path.startswith("/api/"):
            try:
                scheme, token = request.headers.get("Authorization", "").split(" ", 1)
                user, supplied = base64.b64decode(token, validate=True).decode().split(":", 1)
                valid = scheme.lower() == "basic" and user == "admin" and hmac.compare_digest(supplied.encode(), password.encode())
            except (ValueError, UnicodeError): valid = False
            if not valid: return web.json_response({"error": "Authentication required"}, status=401, headers={"WWW-Authenticate": 'Basic realm="CIVI"'})
            if request.method != "GET" and request.headers.get("X-CIVI-Request") != "1":
                raise web.HTTPForbidden(text="X-CIVI-Request required")
            origin = request.headers.get("Origin")
            if origin and origin != f"{request.scheme}://{request.host}": raise web.HTTPForbidden(text="Cross origin denied")
        try: response = await handler(request)
        except CiviError as e: response = web.json_response({"error": e.message, "code": e.code}, status=409)
        except (ValueError, KeyError, TypeError): response = web.json_response({"error": "Invalid request"}, status=400)
        response.headers.update({"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                                 "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"})
        return response

    app = web.Application(middlewares=[security], client_max_size=8192)

    def owner(request):
        token = request.headers.get("X-CIVI-Session", "")
        client = "web-" + token
        if client not in service.clients: raise web.HTTPUnauthorized(text="Session expired")
        service.touch(client)
        return client

    async def index(request): return web.FileResponse(Path(__file__).parent / "static/index.html")
    async def health(request):
        # Public readiness only: no serial settings, identity, or operation logs.
        return web.json_response({"gateway": "online", "radio": service.backend.state,
                                  "ready": service.backend.state == "connected"})
    async def status(request):
        data = service.snapshot()
        data["network"] = network_info(service.config["scpi_port"])
        return web.json_response(data)
    async def commands(request):
        return web.json_response({'commands':[spec.public() for spec in CATALOG.values()],
                                  'permissions':service.config.get('permissions',{}),
                                  'note':'Protocol codes and raw meter values; hardware verification is separate.'})
    async def scope(request):
        wave = service.backend.scope.snapshot()
        return web.json_response({'enabled':service.backend.scope_stream,'sweep':wave})
    async def session(request):
        if sum(webclient for _, webclient in service.clients.values()) >= 64: raise web.HTTPServiceUnavailable()
        token = secrets.token_hex(24)
        service.connect("web-" + token, web=True)
        return web.json_response({"session": token})
    async def heartbeat(request): owner(request); return web.json_response({"ok": True})
    async def command(request):
        client = owner(request)
        data = await request.json()
        line = data["command"]
        if not isinstance(line, str) or not 1 <= len(line) <= 4096 or "\n" in line or "\r" in line: raise ValueError()
        response = await service.execute(client, line)
        # Set errors are available even though SCPI emits no ordinary reply.
        return web.json_response({"response": response, "error": service.errors[client].pop()})
    async def serial_settings(request):
        data = await request.json()
        if set(data) != {"port", "baud", "radio_address", "controller_address", "timeout"}: raise ValueError()
        if not isinstance(data["port"], str) or not 1 <= len(data["port"]) <= 256: raise ValueError()
        for k in ("radio_address", "controller_address"):
            if type(data[k]) is not int or not 1 <= data[k] <= 239: raise ValueError()
        if data["radio_address"] == data["controller_address"]: raise ValueError()
        if type(data["baud"]) is not int or not 300 <= data["baud"] <= 115200: raise ValueError()
        if not isinstance(data["timeout"], (float, int)) or not 0.05 <= data["timeout"] <= 30: raise ValueError()
        await service.admin(owner(request), "serial", data)
        return web.json_response({"ok": True, "persistent": False})
    async def recover(request):
        if (await request.json()).get("link_reset_confirmed") is not True: raise ValueError()
        await service.admin(owner(request), "recover")
        return web.json_response({"ok": True})
    async def release(request):
        await service.disconnect(owner(request)); return web.json_response({"ok": True})
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/lxi", index) # Welcome alias; no claim of LXI compliance.
    app.router.add_static("/static/", Path(__file__).parent / "static")
    app.router.add_get("/api/status", status)
    app.router.add_get('/api/commands',commands)
    app.router.add_get('/api/scope',scope)
    app.router.add_post("/api/session", session)
    app.router.add_post("/api/heartbeat", heartbeat)
    app.router.add_post("/api/scpi", command)
    app.router.add_post("/api/serial", serial_settings)
    app.router.add_post("/api/recover", recover)
    app.router.add_post("/api/release", release)
    return app
