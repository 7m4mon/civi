import copy
from types import SimpleNamespace
import pytest
from civi.pi.network import NetworkError
from civi.pi.transactions import Transactions, Checkpoints
from civi.pi.broker import dispatch, ActivityLog

UUID='12345678-1234-1234-1234-123456789abc'
SETTINGS={'mode':'static','address':'192.0.2.3','prefix':24,'gateway':'','dns':[]}


class Manager:
    def __init__(self):
        self.value={'interface':'eth0','uuid':UUID,'hostname':'civi','autoip_fallback_supported':True,
                    'profile':{'ipv4.addresses':'192.0.2.2/24'},'active_ipv4':'192.0.2.2/24'}
        self.commands=[]
        self.fail=False
        self.saved='192.0.2.2/24'
    def snapshot(self, interface): return copy.deepcopy(self.value)
    def runner(self, command, **kwargs):
        self.commands.append(command)
        if self.fail: return SimpleNamespace(returncode=1,stderr='Activation failed')
        if 'hostname' in command: self.value['hostname']=command[-1]
        if 'modify' in command:
            value=command[command.index('ipv4.addresses')+1]
            self.value['active_ipv4']=value or '169.254.1.2/16'
            if 'connection' in command:
                self.value['profile']['ipv4.addresses']=value
                start=command.index('ipv4.method')
                self.value['profile'].update(zip(command[start::2], command[start+1::2]))
                self.saved=value
        return SimpleNamespace(returncode=0,stderr='')


class Checkpoint:
    def __init__(self,manager): self.manager=manager; self.active=False; self.path='checkpoint'
    def create(self,interface,timeout):
        self.before=self.manager.snapshot(interface); self.active=True; self.timeout=timeout; return self.path
    def exists(self,path): return self.active
    def destroy(self,path): self.active=False
    def rollback(self,path): self.manager.value=copy.deepcopy(self.before); self.active=False


@pytest.fixture
def transaction():
    manager=Manager(); checkpoint=Checkpoint(manager)
    mdns=SimpleNamespace(disabled=lambda:False,set=lambda enabled:{'enabled':enabled})
    return Transactions(manager=manager,checkpoints=checkpoint,clock=lambda:0,mdns=mdns),manager,checkpoint


def test_apply_is_temporary_confirm_persists_and_token_required(transaction):
    tx,manager,checkpoint=transaction
    result=tx.apply(SETTINGS,60)
    token=result['pending']['token']
    assert manager.saved=='192.0.2.2/24' and checkpoint.timeout==60
    assert 'device' in manager.commands[0] and '--temporary' not in manager.commands[0]
    assert result['snapshot']['profile']['ipv4.addresses']=='192.0.2.2/24'
    assert result['snapshot']['active_ipv4']=='192.0.2.3/24'
    with pytest.raises(NetworkError): tx.confirm('invalid')
    with pytest.raises(NetworkError): tx.apply(SETTINGS)
    result=tx.confirm(token)
    assert result['pending'] is None and result['last_result']['state']=='confirmed'
    assert manager.saved=='192.0.2.3/24' and not checkpoint.active


def test_rollback_and_daemon_timeout_verify_original_settings(transaction):
    tx,manager,checkpoint=transaction
    token=tx.apply(SETTINGS)['pending']['token']
    result=tx.rollback(token)
    assert result['last_result']=={'state':'rolled_back','verified':True}
    token=tx.apply(SETTINGS)['pending']['token']
    checkpoint.rollback('checkpoint') # daemon timeout, independent of the web process
    result=tx.status()
    assert result['last_result']['state']=='rolled_back' and result['pending'] is None
    with pytest.raises(NetworkError): tx.confirm(token)
    assert manager.saved=='192.0.2.2/24'


def test_missing_checkpoint_is_not_automatically_success(transaction):
    tx,manager,checkpoint=transaction
    tx.apply(SETTINGS)
    checkpoint.active=False # vanished without restoring
    assert tx.status()['last_result']['state']=='recovery_required'


def test_failed_command_rolls_back_and_is_not_success(transaction):
    tx,manager,checkpoint=transaction
    manager.fail=True
    with pytest.raises(NetworkError): tx.apply(SETTINGS)
    assert tx.pending is None and not checkpoint.active
    assert manager.value['active_ipv4']=='192.0.2.2/24'


def test_timeout_hostname_and_helper_arbitrary_commands_rejected(transaction):
    tx,manager,checkpoint=transaction
    with pytest.raises(ValueError): tx.apply(SETTINGS,0)
    with pytest.raises(ValueError): tx.apply({**SETTINGS,'hostname':'other'})
    with pytest.raises(ValueError): dispatch(tx,{'op':'exec','command':'anything'})
    with pytest.raises(ValueError): dispatch(tx,{'op':'apply','settings':SETTINGS,'timeout':60,'interface':'wlan0'})
    assert not checkpoint.active and not manager.commands


def test_hostname_saved_separately_and_pending_change_blocks_it(transaction):
    tx,manager,checkpoint=transaction
    before=manager.snapshot('eth0')
    result=dispatch(tx,{'op':'hostname','hostname':'CIVI-Pi'})
    assert result['hostname_saved'] and result['snapshot']['hostname']=='civi-pi'
    assert manager.commands==[['nmcli','--wait','10','general','hostname','civi-pi']]
    assert not checkpoint.active
    assert all(manager.value[k]==before[k] for k in ('uuid','profile','active_ipv4'))
    tx.apply(SETTINGS)
    with pytest.raises(NetworkError,match='pending IPv4'): tx.hostname('another-name')
    tx.rollback(tx.pending['token'])
    assert tx.hostname('civi')['snapshot']['hostname']=='civi'


@pytest.mark.parametrize('name',['-bad', 'bad-', 'bad.local', 'x; reboot', 'a'*64, 'localhost', '1234', None])
def test_hostname_validation_before_privileged_command(transaction,name):
    tx,manager,_=transaction
    with pytest.raises(ValueError): tx.hostname(name)
    assert not manager.commands


@pytest.mark.parametrize('name',['', '   ', '\t\n'])
def test_blank_hostname_restores_factory_without_touching_network(transaction,name):
    tx,manager,_=transaction
    manager.value['hostname']='user-bench'
    before=copy.deepcopy(manager.value)
    result=dispatch(tx,{'op':'hostname','hostname':name})
    assert result['snapshot']['hostname']=='civi'
    assert {k:v for k,v in manager.value.items() if k!='hostname'}=={k:v for k,v in before.items() if k!='hostname'}
    assert manager.commands==[['nmcli','--wait','10','general','hostname','civi']]


def test_hostname_failed_readback_restores_previous_name(transaction):
    tx,manager,_=transaction
    runner=manager.runner
    def ignore_new_name(command,**kwargs):
        if command[-1]=='new-name': return SimpleNamespace(returncode=0,stderr='')
        return runner(command,**kwargs)
    manager.runner=ignore_new_name
    with pytest.raises(NetworkError,match='previous hostname was restored'): tx.hostname('new-name')
    assert manager.value['hostname']=='civi'


def test_hostname_failure_and_failed_restoration_is_explicit(transaction):
    tx,manager,_=transaction
    manager.fail=True
    with pytest.raises(NetworkError,match='restoration could not be verified'): tx.hostname('new-name')


def test_mdns_hostname_operation_is_bounded_and_does_not_change_system_hostname(transaction):
    tx,manager,_=transaction
    assert dispatch(tx,{'op':'mdns_hostname','hostname':'civi-2'})=={'requested_hostname':'civi-2'}
    assert manager.commands[-1][-3:]==['SetHostName','s','civi-2']
    assert manager.value['hostname']=='civi'
    with pytest.raises(ValueError): tx.mdns_hostname('invalid.local')


class Ping:
    def __init__(self): self.enabled=False; self.restored=False; self.fail=False
    def snapshot(self): return 'previous'
    def enable(self):
        self.enabled=True
        if self.fail: raise NetworkError('Ping failed')
    def restore(self,previous):
        assert previous=='previous'
        self.restored=True; self.enabled=False


def test_initialize_resets_ipv4_and_ping_without_changing_hostname(transaction):
    tx,manager,checkpoint=transaction
    tx.ping=Ping()
    tx.apply(SETTINGS) # local reset first restores an unconfirmed change
    result=dispatch(tx,{'op':'initialize'})
    assert result['initialized'] and result['ping_enabled'] and tx.ping.enabled
    assert result['mdns_enabled']
    assert result['pending'] is None and not checkpoint.active
    assert result['snapshot']['hostname']=='civi'
    profile=result['snapshot']['profile']
    assert profile['ipv4.method']=='auto' and profile['ipv4.link-local']=='fallback'
    assert profile['ipv4.addresses']==profile['ipv4.gateway']==profile['ipv4.dns']==''
    assert all('wlan0' not in cmd for cmd in manager.commands)


def test_initialize_ping_failure_restores_wired_settings_and_ping(transaction):
    tx,manager,checkpoint=transaction
    tx.ping=Ping(); tx.ping.fail=True
    before=manager.snapshot('eth0')
    with pytest.raises(NetworkError,match='Ping failed'): tx.initialize()
    assert tx.ping.restored and manager.value==before and not checkpoint.active


def test_initialize_mdns_failure_restores_network_ping_and_disabled_state(transaction):
    tx,manager,checkpoint=transaction
    tx.ping=Ping(); calls=[]
    def set_mdns(enabled):
        calls.append(enabled)
        if enabled: raise NetworkError('Avahi unavailable')
        return {'enabled':False}
    tx.mdns=SimpleNamespace(disabled=lambda:True,set=set_mdns)
    before=manager.snapshot('eth0')
    with pytest.raises(NetworkError,match='Avahi unavailable'): tx.initialize()
    assert calls==[True,False]
    assert tx.ping.restored and manager.value==before and not checkpoint.active


def test_helper_logs_state_changes_and_operations_without_tokens(transaction,caplog):
    import logging
    tx,_,_=transaction
    caplog.set_level(logging.INFO,logger='civi.lan-helper')
    activity=ActivityLog()
    activity.request(tx,{'op':'status'})
    activity.request(tx,{'op':'status'})
    assert caplog.text.count('State |')==1
    assert 'Request: status' not in caplog.text
    result=activity.request(tx,{'op':'apply','settings':SETTINGS,'timeout':60})
    token=result['pending']['token']
    activity.request(tx,{'op':'confirm','token':token})
    with pytest.raises(ValueError):
        activity.request(tx,{'op':'status','password':'do-not-log-this'})
    activity.heartbeat()
    assert 'Request: apply' in caplog.text and 'Completed: confirm' in caplog.text
    assert 'requests=5' in caplog.text
    assert token not in caplog.text and 'do-not-log-this' not in caplog.text


def test_busctl_real_json_shape_and_auto_destroyed_rollback():
    responses=[
        '{"type":"o","data":["/org/freedesktop/NetworkManager/Devices/2"]}',
        '{"type":"o","data":["/org/freedesktop/NetworkManager/Checkpoint/1"]}',
        '{"type":"a{su}","data":[{"/org/freedesktop/NetworkManager/Devices/2":0}]}',
        '{"type":"ao","data":[]}',
    ]
    calls=[]
    def runner(command,**kwargs):
        calls.append(command); return SimpleNamespace(returncode=0,stdout=responses.pop(0),stderr='')
    cp=Checkpoints(runner)
    path=cp.create('eth0',60)
    cp.rollback(path)
    assert not any('CheckpointDestroy' in command for command in calls)
