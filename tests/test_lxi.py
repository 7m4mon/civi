import base64
import asyncio
import json
import socket
import ssl
from urllib.parse import urlsplit
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import TestClient, TestServer
from lxml import etree
from civi.server import make_web
from civi.network import Discovery, validate_settings
from civi.identification import NAMESPACE, identity, identification_xml
from civi.config import load
from civi.tls import generate

NETWORK = {'hostname':'unvalidated-host', 'interfaces':[
    {'name':'ethernet', 'ipv4':['192.0.2.7'], 'mac':'12:34:56:78:9a:bc', 'up':True,
     'visa':['TCPIP::192.0.2.7::5025::SOCKET']}]}


async def test_identification_matches_official_schema_and_escapes(service):
    service.config['manufacturer'] = 'Maker <&> Company'
    service.identified_model = 'IC-7300'
    schema = etree.XMLSchema(etree.parse(str(Path('civi/schemas/InstrumentIdentification-2.0.xsd'))))
    for connected in (False, True):
        xml = identification_xml(service, NETWORK, 'https://192.0.2.7:8443', '<b>Description</b>', connected)
        root = etree.fromstring(xml)
        schema.assertValid(root)
        assert root.find(f'{{{NAMESPACE}}}LXIVersion') is None
        assert root.find(f'{{{NAMESPACE}}}UserDescription').text == '<b>Description</b>'
        if not connected:
            assert root.find(f'{{{NAMESPACE}}}Manufacturer').text == 'Maker <&> Company'
            assert root.find(f'{{{NAMESPACE}}}ConnectedDevices/{{{NAMESPACE}}}DeviceURI').text.endswith('/devices/radio')


async def test_public_identification_welcome_and_authenticated_settings(service, monkeypatch, tmp_path):
    monkeypatch.setattr('civi.server.network_info', lambda port: NETWORK)
    service.config['network_settings_file'] = str(tmp_path/'.civi-network.json')
    discovery = Discovery()
    discovery.refresh = AsyncMock()
    password = 'test-network-password'
    auth = {'Authorization':'Basic '+base64.b64encode(('admin:'+password).encode()).decode(), 'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service, password, discovery))) as client:
        for path in ('/lxi','/lxi/','/network','/help'):
            response = await client.get(path)
            assert response.status == 200
            text = await response.text()
            assert 'CIVI' in text
        response = await client.get('/lxi')
        text = await response.text()
        assert 'TCPIP::192.0.2.7::5025::SOCKET' in text
        assert 'Not LXI conformant or certified' in text
        assert 'serial_settings' not in text and 'unvalidated-host' not in text
        response = await client.get('/lxi/identification')
        assert response.status == 200 and response.content_type == 'application/xml'
        root = etree.fromstring(await response.read())
        location = root.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'].split()[1]
        assert location.startswith(str(client.make_url('/')))
        schema = await client.get(urlsplit(location).path)
        etree.XMLSchema(etree.fromstring(await schema.read())).assertValid(root)
        assert (await client.get('/devices/radio/lxi/identification')).status == 404
        assert (await client.get('/api/status')).status == 401
        await service.execute('test','*IDN?')
        assert (await client.get('/devices/radio/lxi/identification')).status == 200
        data = {'description':'Bench <&> Radio', 'discovery':False}
        assert (await client.post('/api/network',json=data)).status == 401
        assert (await client.post('/api/network',headers={'Authorization':auth['Authorization']},json=data)).status == 403
        assert (await client.post('/api/network',headers={**auth,'Origin':'https://evil.invalid'},json=data)).status == 403
        assert (await client.post('/api/network',headers=auth,json={**data,'port':5026})).status == 400
        response = await client.post('/api/network',headers=auth,json=data)
        assert response.status == 200
        assert json.loads(Path(service.config['network_settings_file']).read_text()) == data
        assert (await response.json())['saved'] is True
        text = await (await client.get('/lxi')).text()
        assert 'Bench &lt;&amp;&gt; Radio' in text


@pytest.mark.parametrize('description', ['', 'x'*64, 'x\n', '\u3042'*22])
def test_description_rejects_invalid_service_names(description):
    with pytest.raises(ValueError): validate_settings({'description':description, 'discovery':True})


def test_saved_settings_reload_and_invalid_ports(tmp_path):
    config = tmp_path/'config.toml'
    config.write_text(Path('config.example.toml').read_text(), encoding='utf-8')
    (tmp_path/'.civi-network.json').write_text(json.dumps({'description':'Saved name','discovery':False}))
    assert load(config)['description'] == 'Saved name'
    assert load(config)['discovery'] is False
    config.write_text(config.read_text().replace('web_extra_ports = []', 'web_extra_ports = [443, 443]'))
    with pytest.raises(ValueError, match='distinct'): load(config)


async def test_discovery_txt_consistent_name_recovery_disable_and_bind(monkeypatch, config):
    from zeroconf import NonUniqueNameException
    registered = []
    removed = []
    class Zeroconf:
        def __init__(self, **kwargs): pass
        async def async_register_service(self, info):
            if info.type == '_lxi._tcp.local.' and info.name.startswith('CIVI CIVI-0001.'):
                raise NonUniqueNameException()
            registered.append(info)
        async def async_unregister_service(self, info): removed.append(info)
        async def async_close(self): pass
    monkeypatch.setattr('zeroconf.asyncio.AsyncZeroconf', Zeroconf)
    monkeypatch.setattr('civi.network.network_info', lambda: NETWORK)
    fields = {'Manufacturer':'Maker', 'Model':'CIVI/IC-7300', 'SerialNumber':'abc', 'FirmwareRevision':'0.1'}
    discovery = Discovery()
    await discovery.refresh(config, fields)
    assert len(discovery.services) == 4 and len(removed) == 1
    assert discovery.description == 'CIVI CIVI-0001 (2)'
    assert all(s.name.startswith('CIVI CIVI-0001 (2).') for s in discovery.services)
    lxi = next(s for s in discovery.services if s.type == '_lxi._tcp.local.')
    assert lxi.port == config['web_port']
    assert lxi.properties[b'Model'] == b'CIVI/IC-7300'
    assert lxi.properties[b'FirmwareVersion'] == b'0.1'
    assert next(iter(lxi.properties)) == b'txtvers'
    await discovery.refresh(config, fields)
    assert len(registered) == 5 # unchanged state does not re-register
    fields = {**fields, 'Model':'CIVI/Unknown'}
    await discovery.refresh(config, fields)
    assert next(s for s in discovery.services if s.type == '_lxi._tcp.local.').properties[b'Model'] == b'CIVI/Unknown'
    changed_network = {'interfaces':[{**NETWORK['interfaces'][0], 'ipv4':['192.0.2.8']}]}
    monkeypatch.setattr('civi.network.network_info', lambda: changed_network)
    await discovery.refresh(config, fields)
    assert all(s.addresses == [socket.inet_aton('192.0.2.8')] for s in discovery.services)
    config['discovery'] = False
    await discovery.refresh(config, fields)
    assert not discovery.services and discovery.zc is None
    config['discovery'] = True
    config['bind'] = '127.0.0.1'
    assert discovery.addresses(config) == []


async def test_production_runner_additional_https_port(config, tmp_path, monkeypatch):
    from aiohttp import ClientSession
    from civi.__main__ import run
    reservations = [socket.socket() for _ in range(3)]
    try:
        for s in reservations: s.bind(('127.0.0.1', 0))
        ports = [s.getsockname()[1] for s in reservations]
    finally:
        for s in reservations: s.close()
    cert, key = generate(tmp_path/'certs', [])
    config.update(bind='127.0.0.1', backend='mock', discovery=False,
                  scpi_port=ports[0], web_port=ports[1], web_extra_ports=[ports[2]],
                  tls_cert=str(cert), tls_key=str(key))
    monkeypatch.setenv(config['password_env'], 'mock-only-test-password')
    trust = ssl.create_default_context(cafile=str(cert))
    task = asyncio.create_task(run(config))
    try:
        async with ClientSession() as client:
            for port in ports[1:]:
                for attempt in range(50):
                    if task.done(): await task
                    try:
                        async with client.get(f'https://127.0.0.1:{port}/lxi/identification', ssl=trust) as response:
                            assert response.status == 200
                            assert response.content_type == 'application/xml'
                            break
                    except OSError:
                        if attempt == 49: raise
                        await asyncio.sleep(.02)
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
