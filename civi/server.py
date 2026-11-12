import asyncio
import base64
import hmac
import secrets
from pathlib import Path
from aiohttp import web
from .errors import CiviError
from .network import network_info, Discovery
from .identification import identification_xml, information_page, identity, SCHEMA_PATH, STANDARD_SCHEMA_PATH
from .lxi_api import identification_errors, PROBLEM_SCHEMA_PATH
from .commands import CATALOG

AUTH_PASSWORD = getattr(web, 'RequestKey', web.AppKey)('civi_authenticated_password', str)


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


def make_web(service, password, discovery=None, lan_manager=None, indicator=None):
    discovery = discovery or Discovery()
    if indicator is None:
        from .indicator import LanIndicator
        indicator=LanIndicator(service.config.get('pi_network',{}).get('interface','eth0'))
    @web.middleware
    async def response_headers(request, handler):
        # Include rejected authentication, router errors and XML ProblemDetails.
        try: response = await handler(request)
        except web.HTTPException as error: response = error
        response.headers.update({"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                                 "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'"})
        if isinstance(response, web.HTTPException): raise response
        return response

    @web.middleware
    async def security(request, handler):
        if request.path.startswith("/api/"):
            try:
                scheme, token = request.headers.get("Authorization", "").split(" ", 1)
                user, supplied = base64.b64decode(token, validate=True).decode().split(":", 1)
                if hasattr(password,'verify'):
                    valid = scheme.lower() == 'basic' and user == 'admin' and await asyncio.to_thread(password.verify,supplied)
                else:
                    current_password = password() if callable(password) else password
                    valid = scheme.lower() == "basic" and user == "admin" and hmac.compare_digest(supplied.encode(), current_password.encode())
            except (ValueError, UnicodeError): valid = False
            if not valid:
                # Form-based fetch requests handle authentication in the page.
                # A Basic challenge here would open a second browser login dialog.
                challenge = {} if request.headers.get('X-CIVI-Request') == '1' else {'WWW-Authenticate':'Basic realm="CIVI"'}
                return web.json_response({'error':'Invalid or missing current CIVI Web password. After LAN RESET, use the recovery password displayed locally. This is separate from the Linux/sudo password.'},
                                         status=401, headers={**challenge,'Cache-Control':'no-store'})
            if request.method != "GET" and request.headers.get("X-CIVI-Request") != "1":
                raise web.HTTPForbidden(text="X-CIVI-Request required")
            origin = request.headers.get("Origin")
            if origin and origin != f"{request.scheme}://{request.host}": raise web.HTTPForbidden(text="Cross origin denied")
            request[AUTH_PASSWORD] = supplied
        try: response = await handler(request)
        except CiviError as e: response = web.json_response({"error": e.message, "code": e.code}, status=409)
        except (ValueError, KeyError, TypeError): response = web.json_response({"error": "Invalid request"}, status=400)
        return response

    app = web.Application(middlewares=[response_headers, identification_errors, security], client_max_size=8192)

    def owner(request):
        token = request.headers.get("X-CIVI-Session", "")
        client = "web-" + token
        if client not in service.clients: raise web.HTTPUnauthorized(text="Session expired")
        service.touch(client)
        return client

    async def index(request): return web.FileResponse(Path(__file__).parent / "static/index.html")
    def network_snapshot(): return network_info(service.config['scpi_port'])
    async def welcome(request):
        return web.Response(text=information_page(service, network_snapshot(), discovery, indicator=indicator.snapshot()), content_type='text/html')
    async def lan_page(request):
        return web.Response(text=information_page(service, network_snapshot(), discovery, settings=True, indicator=indicator.snapshot()), content_type='text/html')
    async def lan_status(request): return web.json_response(indicator.snapshot())
    async def identify(request):
        data=await request.json()
        if not isinstance(data,dict) or set(data)!={'enabled'} or type(data['enabled']) is not bool:
            raise ValueError('Expected Identify boolean')
        try: result=indicator.set_identify(data['enabled'])
        except ValueError as error: return web.json_response({'error':str(error)},status=409)
        service.log(None,'Identify '+('enabled' if data['enabled'] else 'disabled'))
        return web.json_response(result)
    async def identification(request):
        # The instrument is the gateway. Radio availability is separate; closing
        # the gateway itself is not a completed, operational identification read.
        if service.closing: raise web.HTTPServiceUnavailable()
        return web.Response(body=identification_xml(service, network_snapshot(), f'{request.scheme}://{request.host}',
                            discovery.description or service.config['description']), content_type='text/xml')
    async def radio_identification(request):
        if service.closing: raise web.HTTPServiceUnavailable()
        if not service.identified_model: raise web.HTTPNotFound(text='No identified radio')
        if service.backend.state != 'connected': raise web.HTTPServiceUnavailable()
        return web.Response(body=identification_xml(service, network_snapshot(), f'{request.scheme}://{request.host}',
                            'Connected CI-V radio', connected=True), content_type='text/xml')
    async def schema(request):
        body = await asyncio.to_thread((Path(__file__).parent / 'schemas/InstrumentIdentification-2.0.xsd').read_bytes)
        return web.Response(body=body, content_type='application/xml')
    async def problem_schema(request):
        body = await asyncio.to_thread((Path(__file__).parent / 'schemas/LXIProblemDetails-1.0.xsd').read_bytes)
        return web.Response(body=body, content_type='application/xml')
    async def help_page(request): return web.FileResponse(Path(__file__).parent / 'static/help.html')
    async def change_password(request):
        if not hasattr(password,'change'):
            raise web.HTTPNotImplemented(text='Persistent Web password management is unavailable')
        data=await request.json()
        if not isinstance(data,dict) or set(data)!={'new_password','confirm_password'}:
            raise ValueError('Expected new password and confirmation')
        try:
            await asyncio.to_thread(password.change,request[AUTH_PASSWORD],data['new_password'],data['confirm_password'])
        except PermissionError:
            return web.json_response({'error':'Current Web password is no longer valid. Sign in again.'},status=401)
        except ValueError as error:
            return web.json_response({'error':str(error)},status=400)
        except OSError:
            return web.json_response({'error':'Could not save the password. The current password is unchanged.'},status=503)
        service.log(None,'Web password changed and saved')
        return web.json_response({'saved':True})
    async def network_settings(request):
        data = await request.json()
        try: await discovery.configure(service.config, data, identity(service))
        except OSError: raise web.HTTPServiceUnavailable(text='Could not save discovery settings')
        service.log(None, 'Discovery settings saved; network adapter configuration unchanged')
        return web.json_response({'saved':True, 'description':service.config['description'],
                                 'active':bool(discovery.services), 'error':discovery.last_error})
    async def pi_lan(request):
        if lan_manager is None: raise web.HTTPNotImplemented(text='Pi LAN helper is not enabled')
        from .pi.network import NetworkError
        operation = request.match_info.get('operation','status')
        try:
            if operation == 'status': return web.json_response(await asyncio.to_thread(lan_manager.request,'status'))
            if operation == 'ping' and request.method=='GET':
                return web.json_response(await asyncio.to_thread(lan_manager.request,'ping_status'))
            data = await request.json()
            if operation == 'ping':
                if not isinstance(data,dict) or set(data)!={'enabled'} or type(data['enabled']) is not bool:
                    raise ValueError('Expected Ping enabled boolean')
                values={'enabled':data['enabled']}
            elif operation == 'hostname':
                if set(data) != {'hostname'}: raise ValueError('Expected hostname')
                if service.owner or service.cache.get('ptt'):
                    raise web.HTTPConflict(text='Stop transmission before changing the hostname')
                values = {'hostname':data['hostname']}
            elif operation in ('preview','apply'):
                if set(data) != {'settings'}: raise ValueError('Expected settings')
                if operation == 'apply' and (service.owner or service.cache.get('ptt')):
                    raise web.HTTPConflict(text='Stop transmission before changing LAN settings')
                values = {'settings':data['settings']}
                if operation == 'apply': values['timeout'] = 90
            else:
                if operation not in ('confirm','rollback') or set(data) != {'token'}: raise ValueError('Invalid LAN operation')
                values = {'token':data['token']}
                if operation == 'confirm':
                    status = await asyncio.to_thread(lan_manager.request,'status')
                    pending = status.get('pending')
                    addresses = status['snapshot']['active_ipv4'].splitlines()
                    local_ip = request.transport.get_extra_info('sockname')[0]
                    expected = pending.get('expected_ipv4') if pending else None
                    if (expected and local_ip != expected) or (not expected and local_ip not in [ip.split('/')[0] for ip in addresses]):
                        raise web.HTTPConflict(text='Reconnect through the changed wired IPv4 address before confirming')
            result = await asyncio.to_thread(lan_manager.request,operation,**values)
            if operation == 'hostname':
                try: await discovery.refresh(service.config, identity(service))
                except Exception: pass # The saved OS setting remains; report discovery failure separately.
                result['discovery_error'] = discovery.last_error
            service.log(None,f'Pi LAN operation: {operation}')
            return web.json_response(result)
        except NetworkError as error:
            return web.json_response({'error':str(error)},status=409)
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
    app.router.add_get('/lxi', welcome)
    app.router.add_get('/lxi/', welcome)
    app.router.add_get('/network', lan_page)
    app.router.add_get('/lan-status',lan_status)
    app.router.add_post('/api/identify',identify)
    app.router.add_get('/lxi/identification', identification)
    app.router.add_get('/devices/radio/lxi/identification', radio_identification)
    app.router.add_get(SCHEMA_PATH, schema)
    app.router.add_get(STANDARD_SCHEMA_PATH, schema)
    app.router.add_get(PROBLEM_SCHEMA_PATH, problem_schema)
    app.router.add_get('/help', help_page)
    app.router.add_static("/static/", Path(__file__).parent / "static")
    app.router.add_get("/api/status", status)
    app.router.add_post('/api/network', network_settings)
    app.router.add_post('/api/password', change_password)
    app.router.add_get('/api/pi/network',pi_lan)
    app.router.add_get('/api/pi/network/{operation:ping}',pi_lan)
    for operation in ('preview','apply','confirm','rollback','hostname','ping'):
        app.router.add_post('/api/pi/network/{operation:'+operation+'}',pi_lan)
    app.router.add_get('/api/commands',commands)
    app.router.add_get('/api/scope',scope)
    app.router.add_post("/api/session", session)
    app.router.add_post("/api/heartbeat", heartbeat)
    app.router.add_post("/api/scpi", command)
    app.router.add_post("/api/serial", serial_settings)
    app.router.add_post("/api/recover", recover)
    app.router.add_post("/api/release", release)
    return app
