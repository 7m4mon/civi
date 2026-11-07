import base64
import pytest
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
