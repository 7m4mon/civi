import asyncio
import base64
import json
import os
import sys
import pytest
from aiohttp.test_utils import TestClient, TestServer
from civi.indicator import LanIndicator, LocalPanelServer, PiLanReader
from civi.server import make_web


def observation(**values):
    return {'interface':'eth0','hostname':'civi2','present':True,'link':True,
            'addresses':['169.254.1.2'],'method':'auto','uuid':'profile','manual':'',
            'reason':0,'error':None,'dhcp_address':None,**values}


def test_normal_autoip_link_failure_and_stale_observation():
    clock=[0]; indicator=LanIndicator(clock=lambda:clock[0])
    assert indicator.snapshot()['state']=='unknown'
    indicator.update(observation())
    assert indicator.snapshot()['state']=='normal' # no initial DHCP lease is not a fault
    indicator.update(observation(link=False))
    assert indicator.snapshot()['state']=='fault'
    assert 'carrier' in indicator.snapshot()['faults'][0]
    indicator.update(observation())
    clock[0]=11
    assert indicator.snapshot()['state']=='unknown'


def test_identify_requires_visible_panel_and_stays_on_until_stopped():
    clock=[0]; indicator=LanIndicator(clock=lambda:clock[0])
    indicator.update(observation())
    with pytest.raises(ValueError,match='panel.sh'): indicator.set_identify(True)
    indicator.heartbeat(False,False)
    with pytest.raises(ValueError): indicator.set_identify(True)
    indicator.heartbeat(True,False)
    assert not indicator.set_identify(True)['display_acknowledged']
    indicator.heartbeat(True,True)
    assert indicator.snapshot()['display_acknowledged']
    indicator.update(observation(link=False))
    assert indicator.snapshot()['state']=='fault' and not indicator.snapshot()['identify']
    clock[0]=100
    assert not indicator.snapshot()['identify'] and not indicator.snapshot()['display_connected']
    assert not indicator.set_identify(False)['identify']


def test_dhcp_loss_latched_even_with_autoip_and_cleared_by_new_lease_or_reset():
    indicator=LanIndicator()
    indicator.update(observation(addresses=['192.0.2.2'],dhcp_address='192.0.2.2'))
    indicator.update(observation())
    assert indicator.snapshot()['state']=='fault'
    indicator.update(observation())
    assert indicator.lease_lost
    indicator.update(observation(addresses=['192.0.2.3'],dhcp_address='192.0.2.3'))
    assert indicator.snapshot()['state']=='normal'
    indicator.update(observation())
    assert indicator.lease_lost
    indicator.reset_faults(); indicator.update(observation())
    assert indicator.snapshot()['state']=='normal'


def test_duplicate_reason_and_monitor_failure_do_not_report_normal():
    indicator=LanIndicator()
    indicator.update(observation(reason=64))
    assert indicator.snapshot()['state']=='fault'
    indicator.update(observation(reason=0))
    assert indicator.snapshot()['state']=='fault'
    indicator.update(observation(uuid=None))
    assert indicator.snapshot()['state']=='fault' # an activation transition is not a reset
    indicator.update(observation(addresses=['169.254.1.3']))
    assert indicator.snapshot()['state']=='normal'
    indicator.update(observation(error='Monitor unavailable'))
    assert indicator.snapshot()['state']=='unknown'


def test_reader_uses_device_reason_and_actual_dhcp_options(monkeypatch):
    monkeypatch.setattr('civi.indicator.network_info',lambda:{'hostname':'civi2','interfaces':[
        {'name':'eth0','up':True,'ipv4':['192.0.2.3'],'mac':'12:34:56:78:9a:bc'}]})
    reader=PiLanReader()
    values={'GENERAL.CON-UUID':'12345678-1234-1234-1234-123456789abc',
            'GENERAL.REASON':'64 (ip-address-duplicate)','GENERAL.STATE':'100 (connected)',
            'ipv4.method':'auto','ipv4.addresses':'','DHCP4.OPTION':'ip_address = 192.0.2.3\nexpiry = 123'}
    monkeypatch.setattr(reader.manager,'_read',lambda *args:values[args[1]])
    monkeypatch.setattr(reader.manager,'applied_ipv4',lambda interface:{'method':'auto','addresses':[]})
    result=reader()
    assert result['reason']==64 and result['dhcp_address']=='192.0.2.3'


async def test_web_identify_authentication_and_no_false_display_success(service):
    indicator=LanIndicator();indicator.update(observation())
    service.config['pi_network']['enabled']=True
    auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service,'mock-test-password',indicator=indicator))) as web:
        assert (await web.get('/lan-status')).status==200
        assert 'LAN status / Identify' in await (await web.get('/lxi')).text()
        assert (await web.post('/api/identify',json={'enabled':True})).status==401
        assert (await web.post('/api/identify',json={'enabled':True},headers={'Authorization':auth['Authorization']})).status==403
        assert (await web.post('/api/identify',json={'enabled':True},headers={**auth,'Origin':'https://evil.invalid'})).status==403
        assert (await web.post('/api/identify',json={'enabled':'true'},headers=auth)).status==400
        response=await web.post('/api/identify',json={'enabled':True},headers=auth)
        assert response.status==409 and 'panel.sh' in (await response.json())['error']
        indicator.heartbeat(True,False)
        assert (await web.post('/api/identify',json={'enabled':True},headers=auth)).status==200
        assert (await (await web.get('/lan-status')).json())['identify']
        assert (await web.post('/api/identify',json={'enabled':False},headers=auth)).status==200


async def test_web_publishes_verified_runtime_conflict(service):
    indicator=LanIndicator()
    indicator.update(observation(addresses=[],runtime_conflict={'address':'192.0.2.88','disconnected':True}))
    async with TestClient(TestServer(make_web(service,'mock-test-password',indicator=indicator))) as web:
        response=await web.get('/lan-status')
        state=await response.json()
        assert state['state']=='fault'
        assert any('192.0.2.88' in reason and 'disconnected' in reason for reason in state['faults'])


@pytest.mark.skipif(sys.platform!='linux',reason='Unix asyncio socket integration runs on Pi/Linux')
async def test_local_panel_socket_permissions_acknowledgement_and_cleanup(tmp_path):
    indicator=LanIndicator();indicator.update(observation())
    path=tmp_path/'panel.sock'
    server=LocalPanelServer(path,indicator,lambda:{'Model':'CIVI/Mock'})
    await server.start()
    try:
        assert path.stat().st_mode & 0o777==0o600
        async def rpc(message):
            reader,writer=await asyncio.open_unix_connection(str(path))
            writer.write(json.dumps(message).encode()+b'\n');await writer.drain()
            response=json.loads(await reader.readline())
            writer.close();await writer.wait_closed()
            return response
        assert (await rpc({'op':'status','visible':True,'showing':False}))['ok']
        indicator.set_identify(True)
        assert (await rpc({'op':'status','visible':True,'showing':True}))['status']['display_acknowledged']
        assert not (await rpc({'op':'hostname','value':'other'}))['ok']
        assert not (await rpc({'op':'stop_identify'}))['status']['identify']
        other=LocalPanelServer(path,indicator,lambda:{})
        with pytest.raises(OSError,match='already running'): await other.start()
        assert path.exists()
    finally: await server.close()
    assert not path.exists()
