import base64
from pathlib import Path
from types import SimpleNamespace
import pytest
from aiohttp.test_utils import TestClient,TestServer
from civi.pi.ping import PingResponder
from civi.pi.network import NetworkError
from civi.pi.broker import dispatch
from civi.server import make_web


def test_ping_control_save_reload_and_recovery_enable(tmp_path):
    proc=tmp_path/'runtime';proc.write_text('0\n')
    config=tmp_path/'setting';p=PingResponder(proc,config)
    assert p.status()=={'enabled':True,'saved_enabled':None,'scope':'IPv4 on all Pi interfaces'}
    assert p.set(False)['saved']
    fresh=PingResponder(proc,config)
    assert fresh.status()['enabled'] is False and fresh.status()['saved_enabled'] is False
    fresh.enable()
    assert fresh.status()['enabled'] is True and fresh.status()['saved_enabled'] is True
    for invalid in ('false',0,None):
        with pytest.raises(ValueError):p.set(invalid)


def test_failed_runtime_write_restores_saved_file_and_state(tmp_path,monkeypatch):
    proc=tmp_path/'runtime';proc.write_text('0\n')
    config=tmp_path/'setting';config.write_text('# previous\n')
    p=PingResponder(proc,config);before=p.snapshot();original=Path.write_bytes
    count=0
    def fail_once(path,data):
        nonlocal count
        if path==proc:
            count+=1
            if count==1:raise OSError('write failed')
        return original(path,data)
    monkeypatch.setattr(Path,'write_bytes',fail_once)
    with pytest.raises(NetworkError,match='previous setting was restored'):p.set(False)
    assert p.snapshot()==before


async def test_ping_api_authentication_csrf_strict_boolean_and_failure(service):
    class Helper:
        def __init__(self):self.enabled=True;self.calls=[];self.fail=False
        def request(self,op,**values):
            self.calls.append((op,values))
            if self.fail:raise NetworkError('Write could not be verified')
            if op=='ping':self.enabled=values['enabled']
            return {'enabled':self.enabled,'saved_enabled':self.enabled,'saved':True}
    helper=Helper()
    auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service,'mock-test-password',lan_manager=helper))) as web:
        path='/api/pi/network/ping'
        assert (await web.get(path)).status==401
        assert (await web.post(path,json={'enabled':False},headers={'Authorization':auth['Authorization']})).status==403
        assert (await web.post(path,json={'enabled':False},headers={**auth,'Origin':'https://evil.invalid'})).status==403
        assert not helper.calls
        response=await web.get(path,headers=auth)
        assert response.status==200 and (await response.json())['enabled']
        assert helper.calls[-1]==('ping_status',{})
        for data in ({'enabled':'false'},{'enabled':0},{'enabled':False,'key':'other'},[]):
            assert (await web.post(path,json=data,headers=auth)).status==400
        response=await web.post(path,json={'enabled':False},headers=auth)
        assert response.status==200 and (await response.json())['enabled'] is False
        helper.fail=True
        response=await web.post(path,json={'enabled':True},headers=auth)
        assert response.status==409 and (await response.json())['error']=='Write could not be verified'


def test_helper_ping_operations_cannot_choose_sysctl_keys():
    with pytest.raises(ValueError):dispatch(None,{'op':'ping','enabled':False,'key':'net.ipv4.ip_forward'})
