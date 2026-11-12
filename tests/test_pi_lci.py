import base64
import json
from pathlib import Path
import pytest
from aiohttp.test_utils import TestClient, TestServer
from civi.pi.lci import reset, read_recovery, reload_recovery, write_private, read_private
from civi.pi.ping import PingResponder
from civi.pi.network import NetworkError
from civi.pi.broker import BrokerClient, HelperUnavailable
from civi.server import make_web


@pytest.fixture
def config(tmp_path):
    from civi.config import load
    value=load('config.example.toml')
    value.update(pi_network={'enabled':True},description='My radio',discovery=False,
                 network_settings_file=str(tmp_path/'.civi-network.json'))
    return value


class Helper:
    def __init__(self): self.calls=[]; self.fail=False
    def request(self,op):
        self.calls.append(op)
        if op=='initialize' and self.fail: raise NetworkError('Initialization failed')
        return {'interface':'eth0','snapshot':{'active_ipv4':'169.254.1.2/16'},
                'initialized':True,'ping_enabled':True}


def test_cancel_has_no_mutations_or_credentials(config,tmp_path):
    helper=Helper()
    assert reset(config,helper,prompt=lambda _: 'no',output=lambda _:None,wait=0) is None
    assert helper.calls==['status'] and not list(tmp_path.iterdir())


def test_absent_helper_transport_has_distinct_exception(monkeypatch):
    def fail(*args,**kwargs):raise FileNotFoundError('missing socket')
    monkeypatch.setattr('civi.pi.broker.socket.AF_UNIX',1,raising=False)
    monkeypatch.setattr('civi.pi.broker.socket.socket',fail)
    with pytest.raises(HelperUnavailable,match='LAN helper unavailable'):
        BrokerClient('/test/missing.sock').request('status')


def test_reset_cannot_contact_helper_explains_operation_and_recovery(config,tmp_path):
    class Unavailable:
        def request(self,op):
            assert op=='status'
            raise HelperUnavailable('unavailable')
    def no_prompt(text):pytest.fail('Must fail before asking for confirmation')
    with pytest.raises(NetworkError) as error:
        reset(config,Unavailable(),prompt=no_prompt,output=lambda _:None,wait=0)
    text=str(error.value)
    for expected in ['Cannot connect to the CIVI LAN helper','LAN RESET has not started',
                     'has not changed your LAN settings or Web password','CIVI desktop shortcut',
                     'Linux/sudo password','Keep the CIVI LAN helper terminal open','separate new terminal']:
        assert expected in text
    assert not list(tmp_path.iterdir())


def test_reset_transport_failure_during_initialize_does_not_claim_no_changes(config,tmp_path):
    class Lost(Helper):
        def request(self,op):
            if op=='initialize':raise HelperUnavailable('lost connection')
            return super().request(op)
    with pytest.raises(NetworkError) as error:
        reset(config,Lost(),prompt=lambda _:'LAN RESET',output=lambda _:None,wait=0)
    text=str(error.value)
    assert 'lost during LAN RESET' in text and 'may already have changed' in text
    assert 'has not changed' not in text
    assert read_recovery(config) is None


def test_helper_rejected_status_is_not_mislabelled_as_missing_helper(config):
    class Rejected:
        def request(self,op):raise NetworkError('Interface must have exactly one active profile')
    with pytest.raises(NetworkError,match='exactly one active profile') as error:
        reset(config,Rejected(),output=lambda _:None,wait=0)
    assert 'Cannot connect' not in str(error.value)


def test_reset_default_password_reused_and_names_retained(config,tmp_path):
    helper=Helper(); output=[]
    reset(config,helper,prompt=lambda _: 'LAN RESET',output=output.append,wait=0)
    first=read_recovery(config)
    assert len(first['password'])>=12
    assert json.loads(Path(config['network_settings_file']).read_text())=={'description':'My radio','discovery':True}
    assert any(first['password'] in line for line in output)
    reset(config,helper,prompt=lambda _: 'LAN RESET',output=lambda _:None,wait=0)
    second=read_recovery(config)
    assert second['password']==first['password'] and second['revision']!=first['revision']
    assert 'hostname' not in Path(config['network_settings_file']).read_text()


def test_failed_network_reset_does_not_replace_active_password(config,tmp_path):
    helper=Helper(); helper.fail=True
    with pytest.raises(NetworkError): reset(config,helper,prompt=lambda _: 'LAN RESET',output=lambda _:None,wait=0)
    assert read_recovery(config) is None
    assert not Path(config['network_settings_file']).exists()


def test_ping_saved_enabled_and_restorable(tmp_path):
    proc=tmp_path/'icmp'; proc.write_text('1\n')
    config=tmp_path/'sysctl.conf'; config.write_text('# existing\n')
    responder=PingResponder(proc,config); before=responder.snapshot()
    responder.enable()
    assert proc.read_text().strip()=='0' and 'icmp_echo_ignore_all = 0' in config.read_text()
    responder.restore(before)
    assert proc.read_text()=='1\n' and config.read_text()=='# existing\n'


def test_invalid_recovery_file_does_not_load(config,tmp_path):
    write_private(tmp_path/'.civi-lci.json',{'password':'short','revision':'r'})
    with pytest.raises(ValueError): read_recovery(config)


async def test_live_auth_reload_rejects_old_password_and_has_no_http_reset(service,config,tmp_path):
    credentials={'password':'old-test-password','revision':None}
    def auth(password):
        return {'Authorization':'Basic '+base64.b64encode(('admin:'+password).encode()).decode(),'X-CIVI-Request':'1'}
    async with TestClient(TestServer(make_web(service,lambda:credentials['password']))) as client:
        assert (await client.get('/api/status',headers=auth('old-test-password'))).status==200
        write_private(config['network_settings_file'],{'description':'My radio','discovery':True})
        write_private(tmp_path/'.civi-lci.json',{'password':'new-test-password','revision':'new'})
        assert reload_recovery(config,credentials)=='new'
        assert config['discovery'] is True
        assert (await client.get('/api/status',headers=auth('old-test-password'))).status==401
        assert (await client.get('/api/status',headers=auth('new-test-password'))).status==200
        assert (await client.post('/api/pi/network/initialize',json={},headers=auth('new-test-password'))).status==404
        assert reload_recovery(config,credentials) is None


def test_cli_refuses_remote_or_redirected_use(monkeypatch):
    from civi.pi.lci import main
    monkeypatch.setattr('sys.argv',['lci'])
    monkeypatch.setattr('civi.pi.lci.platform.system',lambda:'Linux')
    monkeypatch.setenv('SSH_CONNECTION','test')
    with pytest.raises(SystemExit) as error: main()
    assert error.value.code==1
