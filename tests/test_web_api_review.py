"""Gateway identification semantics and every Web mutation's access boundary."""
import base64
from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock

import pytest
from aiohttp.test_utils import TestClient, TestServer
from lxml import etree, html

from civi.auth import PasswordStore
from civi.identification import NAMESPACE
from civi.network import Discovery
from civi.server import make_web

PASSWORD = 'review-test-password'
AUTH = {'Authorization': 'Basic ' + base64.b64encode(('admin:' + PASSWORD).encode()).decode(),
        'X-CIVI-Request': '1'}
MUTATIONS = ['/api/identify', '/api/network', '/api/password',
             *('/api/pi/network/' + action for action in
               ('preview', 'apply', 'confirm', 'rollback', 'hostname', 'ping')),
             *('/api/' + action for action in
               ('session', 'heartbeat', 'scpi', 'serial', 'recover', 'release'))]
NETWORK = {'hostname': 'desired-os-name', 'interfaces': [
    {'name': 'eth0', 'ipv4': ['192.0.2.7'], 'mac': '12:34:56:78:9a:bc',
     'up': True, 'visa': ['TCPIP::192.0.2.7::5025::SOCKET']}]}


def headers(response):
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']


async def test_all_mutations_reject_unauthenticated_and_cross_origin(service, tmp_path):
    store = PasswordStore(service.config, PASSWORD)
    app = make_web(service, store, lan_manager=Mock())
    actual = {r.resource.canonical for r in app.router.routes() if r.method == 'POST'}
    # Parameterized helper routes have a canonical placeholder, expand separately.
    assert actual == set(MUTATIONS) - {p for p in MUTATIONS if '/pi/network/' in p} | {
        '/api/pi/network/{operation}'}
    async with TestClient(TestServer(app)) as client:
        for path in MUTATIONS:
            for auth in ({}, {'Authorization': 'Basic !!!'},
                         {**AUTH, 'Authorization': 'Basic ' + base64.b64encode(b'admin:wrong').decode()}):
                response = await client.post(path, json={}, headers=auth)
                assert response.status == 401, path
                headers(response)
            response = await client.post(path, json={}, headers={'Authorization': AUTH['Authorization']})
            assert response.status == 403, path
            headers(response)
            response = await client.post(path, json={}, headers={**AUTH, 'Origin': 'https://evil.invalid'})
            assert response.status == 403, path
            headers(response)
        assert not Path(service.config['network_settings_file']).exists()
        assert not service.config.get('discovery_reset_revision')
        # Rotation invalidates all mutation routes, not just the password form.
        store.change(PASSWORD, 'replacement-password', 'replacement-password')
        for path in MUTATIONS:
            response = await client.post(path, json={}, headers=AUTH)
            assert response.status == 401, path
        assert service.owner is None


@pytest.mark.parametrize('state', ['disconnected', 'connecting', 'quarantined', 'connected'])
async def test_gateway_identity_remains_available_without_radio(service, monkeypatch, state):
    monkeypatch.setattr('civi.server.network_info', lambda port: NETWORK)
    service.backend.state = state
    service.clear_identity()
    schema = etree.XMLSchema(etree.parse('civi/schemas/InstrumentIdentification-2.0.xsd'))
    async with TestClient(TestServer(make_web(service, PASSWORD))) as client:
        response = await client.get('/lxi/identification', headers={'Accept': 'text/xml'})
        assert response.status == 200 and response.content_type == 'text/xml'
        headers(response)
        root = etree.fromstring(await response.read())
        schema.assertValid(root)
        assert root.find(f'{{{NAMESPACE}}}ConnectedDevices') is None
        assert root.find(f'{{{NAMESPACE}}}Model').text == 'CIVI/Unknown'
        assert (await client.get('/devices/radio/lxi/identification')).status == 404
        page = await client.get('/lxi')
        assert page.status == 200 and state in await page.text()
        # Conditional requests cannot make changing identification a cached 304.
        response = await client.get('/lxi/identification', headers={'If-None-Match': '*', 'If-Modified-Since': 'Wed, 21 Oct 2037 07:28:00 GMT'})
        assert response.status == 200


async def test_closing_and_stale_child_identity_do_not_report_success(service, monkeypatch):
    monkeypatch.setattr('civi.server.network_info', lambda port: NETWORK)
    service.identified_model = 'IC-7300'
    service.backend.state = 'disconnected'
    problem_schema = etree.XMLSchema(etree.parse('civi/schemas/LXIProblemDetails-1.0.xsd'))
    async with TestClient(TestServer(make_web(service, PASSWORD))) as client:
        response = await client.get('/devices/radio/lxi/identification')
        assert response.status == 503
        problem_schema.assertValid(etree.fromstring(await response.read()))
        service.closing = True
        try:
            for path in ('/lxi/identification', '/devices/radio/lxi/identification'):
                response = await client.get(path)
                assert response.status == 503
                headers(response)
                problem_schema.assertValid(etree.fromstring(await response.read()))
        finally:
            service.closing = False


async def test_methods_and_schema_headers(service):
    async with TestClient(TestServer(make_web(service, PASSWORD))) as client:
        for path in ('/lxi/identification', '/lxi/schemas/InstrumentIdentification/2.0',
                     '/lxi/schemas/LXIProblemDetails/1.0', '/InstrumentIdentification/2.0'):
            get = await client.get(path)
            body = await get.read()
            head = await client.head(path)
            assert head.status == 200 and await head.read() == b''
            assert head.content_type == get.content_type
            assert int(head.headers['Content-Length']) == len(body)
            headers(head)
            for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                response = await client.request(method, path, json={})
                assert response.status == 405
                assert set(response.headers['Allow'].split(',')) == {'GET', 'HEAD'}
                assert response.content_type == 'application/xml'
                headers(response)
        for path in ('/missing', '/api/missing', '/lxi/missing'):
            response = await client.get(path)
            assert response.status == (401 if path.startswith('/api/') else 404)
            headers(response)


@pytest.mark.parametrize('discovery_enabled,registered,error,expected', [
    (True, True, None, 'actual-2.local.'),
    (False, True, None, '192.0.2.7'),
    (True, False, None, '192.0.2.7'),
    (True, True, 'Registration failed', '192.0.2.7'),
])
async def test_actual_hostname_and_safe_html(service, monkeypatch, discovery_enabled, registered, error, expected):
    monkeypatch.setattr('civi.server.network_info', lambda port: NETWORK)
    service.config['discovery'] = discovery_enabled
    service.config['manufacturer'] = '<script>alert("x")</script>'
    service.config['pi_network']['enabled'] = True
    discovery = Discovery()
    discovery.hostname = 'actual-2.local.'
    discovery.services = [object()] if registered else []
    discovery.last_error = error
    async with TestClient(TestServer(make_web(service, PASSWORD, discovery))) as client:
        for path in ('/lxi', '/network'):
            response = await client.get(path)
            tree = html.fromstring(await response.text())
            assert tree.xpath('//dt[text()="Hostname"]/following-sibling::dd[1]/text()') == [expected]
            assert not tree.xpath('//script[not(@src)]')
            ids = tree.xpath('//@id')
            assert len(ids) == len(set(ids))
            assert tree.get('lang') == 'en'
            assert tree.xpath('//meta[@name="viewport"]')
            for label in tree.xpath('//label'):
                assert label.xpath('.//input | .//select') or label.get('for')
            if path == '/network':
                assert tree.get_element_by_id('pi-subnet').text.startswith('Subnet mask: 255.255.255.0')


def test_subnet_display_with_real_javascript():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to execute Web JavaScript')
    script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const nodes=new Map();
const document={getElementById(id) {
  if(!nodes.has(id)) nodes.set(id,{value:id==='pi-prefix'?'24':'',addEventListener(event,fn){this[event]=fn;}});
  return nodes.get(id);
}};
vm.runInNewContext(fs.readFileSync('civi/static/network.js','utf8'),{document,setInterval(){},location:{hash:''}});
const input=nodes.get('pi-prefix'),output=nodes.get('pi-subnet');
for(const [prefix,mask] of [['1','128.0.0.0'],['16','255.255.0.0'],['24','255.255.255.0'],['31','255.255.255.254'],['32','255.255.255.255']]) {
  input.value=prefix;input.input();assert.ok(output.textContent.includes(mask+' (/'+prefix+')'));
}
for(const value of ['','0','33','1.5','bad']) {input.value=value;input.input();assert.ok(output.textContent.startsWith('Enter a prefix'));}
'''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True, timeout=15)
