import asyncio
import ssl
import base64
import pytest
from aiohttp import ClientSession, web
from civi.server import scpi_client, make_web
from civi.tls import generate
from civi.backend import CivBackend, load_profile, bcd_encode
from civi.service import ControlService
from tests.test_civ import FakeSerial, frame


async def test_tcp_lf_query_and_no_set_response(service):
    server = await asyncio.start_server(lambda r,w: scpi_client(r,w,service), "127.0.0.1", 0, limit=4096)
    port = server.sockets[0].getsockname()[1]
    r, w = await asyncio.open_connection("127.0.0.1",port)
    try:
        w.write(b"SENS:FREQ 7.3MHz\n*OPC?\nSENS:FREQ?\n")
        await w.drain()
        assert await asyncio.wait_for(r.readline(),2) == b"1\n"
        assert await r.readline() == b"7300000\n"
    finally:
        w.close(); await w.wait_closed(); server.close(); await server.wait_closed()
        await asyncio.sleep(0.1)


async def test_https_auth_csrf_and_shared_operations(service,tmp_path):
    cert,key = generate(tmp_path, [])
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert,key)
    runner = web.AppRunner(make_web(service,"testing-password"))
    await runner.setup()
    site = web.TCPSite(runner,"127.0.0.1",0,ssl_context=ctx)
    await site.start()
    port=site._server.sockets[0].getsockname()[1]
    trust=ssl.create_default_context(cafile=str(cert))
    url=f"https://127.0.0.1:{port}"
    try:
        async with ClientSession() as client:
            async with client.get(url+"/",ssl=trust) as r:
                assert r.status==200; assert "CIVI" in await r.text()
            async with client.get(url+"/api/status",ssl=trust) as r: assert r.status==401
            auth={"Authorization": "Basic "+base64.b64encode(b"admin:testing-password").decode()}
            async with client.post(url+"/api/session",headers=auth,json={},ssl=trust) as r: assert r.status==403
            headers={**auth,"X-CIVI-Request":"1"}
            async with client.post(url+"/api/session",headers=headers,json={},ssl=trust) as r:
                assert r.status==200; headers["X-CIVI-Session"]=(await r.json())["session"]
            async def web_cmd(i):
                async with client.post(url+"/api/scpi",headers=headers,json={"command":f"SENS:FREQ {7200000+i};FREQ?"},ssl=trust) as r:
                    assert r.status==200; return (await r.json())["response"]
            jobs=[]
            for i in range(10):
                jobs += [web_cmd(i),service.execute("test",f"SENS:FREQ {7100000+i};FREQ?")]
            assert await asyncio.gather(*jobs) == [v for i in range(10) for v in [str(7200000+i),str(7100000+i)]]
            async with client.get(url+"/api/status",headers=auth,ssl=trust) as r:
                s=await r.json(); assert s["backend"]=="mock"; assert s["lxi_certified"] is False
                assert s['radio_firmware'] == 'Unknown'
                assert s['radio_firmware_source'] == 'unknown'
            async with client.get(url+'/api/commands',headers=auth,ssl=trust) as r:
                catalog=(await r.json())['commands']
                assert len(catalog)==339
                readonly=next(c for c in catalog if c['header']=='RAD:MENU:0074')
                assert readonly['access']=='r' and readonly['set_example'] is None
            async with client.get(url+'/api/scope',headers=auth,ssl=trust) as r:
                assert await r.json()=={'enabled':False,'sweep':None}
            async with client.post(url+"/api/heartbeat",headers={**headers,"Origin":"https://evil.invalid"},json={},ssl=trust) as r: assert r.status==403
            async with client.post(url+"/api/recover",headers=headers,json={},ssl=trust) as r: assert r.status==400
            async with client.post(url+"/api/release",headers=headers,json={},ssl=trust) as r: assert r.status==200
    finally: await runner.cleanup()


async def test_web_survives_silent_radio_and_reports_recovery(config):
    config['serial']['timeout'] = 0.02
    silent = FakeSerial([[]])
    backend = CivBackend(load_profile(), config['serial'], lambda: silent)
    service = ControlService(backend, config)
    service.connect('test')
    await service.start()
    runner = web.AppRunner(make_web(service, 'test-offline-password'))
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    url = f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
    try:
        async with ClientSession() as client:
            async with client.get(url + '/health') as response:
                assert await response.json() == {'gateway':'online','radio':'disconnected','ready':False}
            assert await service.execute('test', 'SENS:FREQ?') == 'ERROR'
            async with client.get(url + '/') as response:
                html = await response.text()
                assert response.status == 200
                assert 'lang="en"' in html
                assert 'Waiting for radio' in html
                assert 'Turn on your radio' in html
            async with client.get(url + '/health') as response:
                assert await response.json() == {'gateway':'online','radio':'quarantined','ready':False}
            async with client.get(url + '/api/status') as response:
                assert response.status == 401 # Readiness does not bypass operation auth.
            replacement = FakeSerial([
                [frame(b'\x03' + bcd_encode(7100000,5))],
                [frame(b'\x1c\x00\x00')],
            ])
            backend.factory = lambda: replacement
            await service.admin('test', 'recover')
            async with client.get(url + '/health') as response:
                assert await response.json() == {'gateway':'online','radio':'connected','ready':True}
    finally:
        await runner.cleanup()
        await service.close()
