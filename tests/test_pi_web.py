import base64
import pytest
from unittest.mock import AsyncMock
from aiohttp.test_utils import TestClient, TestServer
from civi.server import make_web


async def test_pi_web_authentication_apply_tx_guard_and_wired_confirmation(service):
    class Client:
        def __init__(self): self.calls=[]; self.expected='192.0.2.3'
        def request(self,op,**values):
            self.calls.append((op,values))
            if op=='status':
                return {'pending':{'token':'token','expected_ipv4':self.expected},
                        'snapshot':{'active_ipv4':self.expected+'/24'}}
            return {'ok':True}
    client=Client()
    service.config['pi_network']={'enabled':True}
    auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service,'mock-test-password',lan_manager=client))) as web:
        assert (await web.get('/api/pi/network')).status==401
        invalid=await web.get('/api/pi/network',headers={'Authorization':'Basic '+base64.b64encode(b'admin:wrong-password').decode(),'X-CIVI-Request':'1'})
        assert invalid.status==401
        assert 'WWW-Authenticate' not in invalid.headers
        assert 'Linux/sudo' in (await invalid.json())['error']
        challenge=await web.get('/api/pi/network')
        assert challenge.status==401 and challenge.headers['WWW-Authenticate'].startswith('Basic')
        assert (await web.get('/api/pi/network',headers=auth)).status==200
        assert (await web.post('/api/pi/network/apply',json={'settings':{}},headers={'Authorization':auth['Authorization']})).status==403
        assert (await web.post('/api/pi/network/apply',json={'settings':{}},headers={**auth,'Origin':'https://evil.invalid'})).status==403
        service.owner='other'
        assert (await web.post('/api/pi/network/apply',json={'settings':{}},headers=auth)).status==409
        service.owner=None
        assert (await web.post('/api/pi/network/apply',json={'settings':{}},headers=auth)).status==200
        assert client.calls[-1][1]['timeout']==90
        assert (await web.post('/api/pi/network/confirm',json={'token':'token'},headers=auth)).status==409
        assert not any(op=='confirm' for op,_ in client.calls)
        client.expected='127.0.0.1'
        assert (await web.post('/api/pi/network/confirm',json={'token':'token'},headers=auth)).status==200
        assert client.calls[-1]==('confirm',{'token':'token'})
        assert (await web.post('/api/pi/network/rollback',json={'token':'token'},headers=auth)).status==200
        assert 'Pi wired LAN configuration' in await (await web.get('/network')).text()


async def test_pi_web_disabled_in_shared_application(service):
    async with TestClient(TestServer(make_web(service,'mock-test-password'))) as web:
        auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode()}
        assert (await web.get('/api/pi/network',headers=auth)).status==501
        assert 'Pi wired LAN configuration' not in await (await web.get('/network')).text()


async def test_hostname_requires_authentication_and_csrf_marker_and_reports_discovery(service):
    class Client:
        def __init__(self): self.calls=[]
        def request(self,op,**values):
            self.calls.append((op,values))
            return {'hostname_saved':True,'snapshot':{'hostname':values['hostname']},'pending':None}
    from civi.network import Discovery
    discovery=Discovery()
    discovery.refresh=AsyncMock()
    client=Client()
    auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service,'mock-test-password',discovery,client))) as web:
        url='/api/pi/network/hostname'
        assert (await web.post(url,json={'hostname':'civi-pi'})).status==401
        assert (await web.post(url,json={'hostname':'civi-pi'},headers={'Authorization':auth['Authorization']})).status==403
        assert (await web.post(url,json={'hostname':'civi-pi'},headers={**auth,'Origin':'https://evil.invalid'})).status==403
        service.owner='other'
        assert (await web.post(url,json={'hostname':'civi-pi'},headers=auth)).status==409
        assert not client.calls
        service.owner=None
        response=await web.post(url,json={'hostname':'civi-pi'},headers=auth)
        assert response.status==200 and (await response.json())['hostname_saved']
        assert client.calls==[('hostname',{'hostname':'civi-pi'})]
        discovery.refresh.assert_awaited_once()
