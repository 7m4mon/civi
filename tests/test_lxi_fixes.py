"""Regression coverage for the four gaps from the 2026-11-10 audit."""

import asyncio
import base64
import json
from pathlib import Path
import queue
import shutil
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiohttp.test_utils import TestClient, TestServer
from lxml import etree
import pytest

from civi.config import load
from civi.identification import identification_xml, information_page, NAMESPACE
from civi.indicator import LanIndicator
from civi.network import Discovery, lxi_interfaces
from civi.pi.panel import Panel
from civi.server import make_web

AUTH = {'Authorization': 'Basic ' + base64.b64encode(
    b'admin:test-web-password').decode(), 'X-CIVI-Request': '1'}


@pytest.mark.parametrize('suffix', [
    '', '::INSTR', '::inst0', '::inst0::INSTR',
    '::hislip0::INSTR', '::hislip0,4881::INSTR',
    '::gpib0,22::INSTR', '::hislip0,4881',
])
async def test_instr_locations_use_real_raw_mock_connection(
    driver_module, driver_address, monkeypatch, suffix
):
    import socket
    actual_port = int(driver_address.split('::')[2])
    original = socket.create_connection
    calls = []

    def redirect(address, *args, **kwargs):
        calls.append(address)
        assert address == ('127.0.0.1', 5025)
        return original(('127.0.0.1', actual_port), *args, **kwargs)

    monkeypatch.setattr(socket, 'create_connection', redirect)

    def exercise():
        with driver_module.CiviIc7300('TCPIP12::127.0.0.1' + suffix) as d:
            assert d.ivi_utility.instrument_model == 'CIVI/IC-7300'
            assert d.radio.smeter_raw == 96

    await asyncio.to_thread(exercise)
    assert calls == [('127.0.0.1', 5025)]


@pytest.mark.parametrize('prefix', ['', '#', '$'])
def test_hislip_credential_reference_never_reaches_socket(
    driver_module, monkeypatch, prefix
):
    import socket
    addresses = []

    def stop(address, *args, **kwargs):
        addresses.append(address)
        raise ConnectionRefusedError('fixture')

    monkeypatch.setattr(socket, 'create_connection', stop)
    with pytest.raises(ConnectionRefusedError, match='fixture'):
        driver_module.CiviIc7300(
            f'TCPIP7::{prefix}private-reference@example.invalid::hislip0,4880::INSTR'
        )
    assert addresses == [('example.invalid', 5025)]


def test_socket_port_and_board_are_preserved(driver_module, monkeypatch):
    import socket
    calls = []

    def stop(address, *args, **kwargs):
        calls.append(address)
        raise ConnectionRefusedError('fixture')

    monkeypatch.setattr(socket, 'create_connection', stop)
    with pytest.raises(ConnectionRefusedError):
        driver_module.CiviIc7300('tcpip123::localhost::15025::socket')
    assert calls == [('localhost', 15025)]


@pytest.mark.parametrize('resource', [
    'TCPIP::host::', 'TCPIP::host::inst0::OTHER', 'TCPIP::host::SOCKET',
    'TCPIP::host::hislip0,0::INSTR', 'TCPIP::host::hislip0,65536',
    'TCPIP::host::hislip0,bad::INSTR', 'TCPIP::@host::hislip0',
    'TCPIP::secret@host::inst0::INSTR', 'TCPIP::host\n::INSTR',
    'TCPIP::host::1::SOCKET::EXTRA',
])
def test_malformed_resource_names_rejected_without_io(driver_module, monkeypatch, resource):
    import socket

    def no_io(*args, **kwargs):
        raise AssertionError('Invalid resource attempted I/O')

    monkeypatch.setattr(socket, 'create_connection', no_io)
    with pytest.raises(ValueError):
        driver_module.CiviIc7300(resource)


@pytest.mark.parametrize('text,expected', [
    ('x' * 64, 'x' * 63), ('あ' * 22, 'あ' * 21),
    ('a' * 62 + 'あ', 'a' * 62), ('😀' * 16, '😀' * 15),
])
async def test_description_truncates_before_save_and_reload(service, tmp_path, text, expected):
    path = tmp_path / 'config.toml'
    path.write_text(Path('config.example.toml').read_text(), encoding='utf-8')
    service.config.update(load(path))
    discovery = Discovery()
    discovery.refresh = AsyncMock()
    async with TestClient(TestServer(make_web(
        service, 'test-web-password', discovery
    ))) as client:
        response = await client.post('/api/network', headers=AUTH,
                                     json={'description': text, 'discovery': True})
        assert response.status == 200
        assert (await response.json())['description'] == expected
    assert load(path)['description'] == expected
    saved = json.loads((tmp_path / '.civi-network.json').read_text(encoding='utf-8'))
    assert saved['description'] == expected
    assert len(expected.encode('utf-8')) <= 63
    assert service.config['description'] == expected
    discovery.refresh.assert_awaited_once()


async def test_truncation_does_not_hide_invalid_suffix_or_modify_on_failure(service):
    discovery = Discovery()
    discovery.refresh = AsyncMock()
    before = service.config['description']
    async with TestClient(TestServer(make_web(
        service, 'test-web-password', discovery
    ))) as client:
        response = await client.post('/api/network', headers=AUTH,
            json={'description': 'x' * 64 + '\n', 'discovery': True})
        assert response.status == 400
    assert service.config['description'] == before
    discovery.refresh.assert_not_awaited()


def network_fixture(addressed=True):
    return {'hostname': 'civi', 'interfaces': [
        {'name': name, 'ipv4': ips, 'mac': '12:34:56:78:9a:bc', 'up': True,
         'visa': [f'TCPIP::{ip}::5025::SOCKET' for ip in ips]}
        for name, ips in [('lo', ['127.0.0.1']),
                          ('eth0', ['192.0.2.7'] if addressed else []),
                          ('wlan0', ['198.51.100.7'])]]}


@pytest.mark.parametrize('addressed', [False, True])
def test_pi_xml_and_advertisement_use_only_wired_nic(service, monkeypatch, addressed):
    service.config['pi_network'] = {'enabled': True, 'interface': 'eth0'}
    network = network_fixture(addressed)
    root = etree.fromstring(identification_xml(
        service, network, 'https://192.0.2.7', 'Test'))
    schema = etree.XMLSchema(etree.parse('civi/schemas/InstrumentIdentification-2.0.xsd'))
    schema.assertValid(root)
    nodes = root.findall(f'{{{NAMESPACE}}}Interface')
    assert len(nodes) == 1 and nodes[0].attrib['InterfaceName'] == 'eth0'
    addresses = [node.text for node in nodes[0].findall(f'{{{NAMESPACE}}}IPAddress')]
    assert addresses == (['192.0.2.7'] if addressed else [])
    monkeypatch.setattr('civi.network.network_info', lambda: network)
    assert Discovery.addresses(service.config) == addresses
    html = information_page(service, network, Discovery())
    assert 'LXI wired interface' in html
    assert 'Management / non-LXI interface' in html


def test_missing_target_keeps_identity_without_claiming_management_nic(service):
    service.config['pi_network'] = {'enabled': True, 'interface': 'eth9'}
    interfaces = lxi_interfaces(service.config, network_fixture())
    assert len(interfaces) == 1 and interfaces[0]['name'] == 'eth9'
    assert interfaces[0]['ipv4'] == [] and interfaces[0]['mac'] is None


def test_avahi_uses_the_configured_interface_index(monkeypatch):
    from civi.pi.discovery import AvahiDiscovery
    seen = []
    monkeypatch.setattr('civi.pi.discovery.socket.if_nametoindex',
                        lambda name: seen.append(name) or 9)
    assert AvahiDiscovery().interface_index({'pi_network': {'interface': 'eth2'}}) == 9
    assert seen == ['eth2']


def observation(**values):
    return {'interface': 'eth0', 'hostname': 'civi', 'present': True,
            'link': True, 'addresses': ['192.0.2.7'], 'method': 'auto',
            'uuid': 'profile', 'manual': '', 'reason': 0, 'error': None, **values}


@pytest.mark.parametrize('failure', [
    {'link': False}, {'dhcp_address': None}, {'error': 'Monitor failed'},
])
def test_identify_exits_on_fault_and_needs_explicit_restart(failure):
    indicator = LanIndicator()
    indicator.update(observation(dhcp_address='192.0.2.7'))
    indicator.heartbeat(True, False)
    indicator.set_identify(True)
    indicator.update(observation(**failure))
    assert indicator.snapshot()['state'] in ('fault', 'unknown')
    assert not indicator.snapshot()['identify']
    with pytest.raises(ValueError, match='normal LAN'):
        indicator.set_identify(True)
    indicator.update(observation(dhcp_address='192.0.2.7'))
    assert indicator.snapshot()['state'] == 'normal'
    assert not indicator.snapshot()['identify']
    assert indicator.set_identify(True)['identify']


@pytest.mark.parametrize('state', ['fault', 'unknown'])
def test_local_panel_prioritizes_fault_even_if_identify_payload_is_stale(state):
    class Label:
        def __init__(self): self.values = {}
        def configure(self, **kw): self.values.update(kw)

    panel = Panel.__new__(Panel)
    panel.done, panel.updates = threading.Event(), queue.Queue()
    panel.root = SimpleNamespace(winfo_viewable=lambda: True, state=lambda: 'normal',
                                 after=lambda *args: None)
    panel.current = {'online': True, 'device': {}, 'status': {
        'state': state, 'identify': True, 'interface': 'eth0', 'link': False,
        'addresses': [], 'faults': ['LAN unavailable']}}
    for name in ('banner', 'device', 'network', 'notice'):
        setattr(panel, name, Label())
    panel.paint()
    assert not panel.showing
    assert panel.banner.values['text'] == f'LAN {state.upper()}'


def test_web_indicator_prioritizes_fault_with_real_javascript():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to execute Web indicator JavaScript')
    script = r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
(async () => {
  for (const mode of ['normal', 'fault', 'unknown']) {
    const nodes = new Map();
    const document = {getElementById(id) {
      if (!nodes.has(id)) nodes.set(id, {addEventListener(){}});
      return nodes.get(id);
    }};
    const state = {state:mode, identify:true, display_connected:true, display_acknowledged:true,
      interface:'eth0', addresses:[], faults:[], hostname:'civi'};
    vm.runInNewContext(fs.readFileSync('civi/static/indicator.js', 'utf8'), {
      document, fetch:async () => ({ok:true, json:async () => state}),
      AbortSignal:{timeout(){}}, setTimeout(){}
    });
    await new Promise(setImmediate);
    assert.equal(nodes.get('lan-lamp').className,
      'lan-lamp ' + (mode === 'normal' ? 'identifying' : mode));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
    subprocess.run([node, '-e', script], check=True, capture_output=True, text=True, timeout=15)
