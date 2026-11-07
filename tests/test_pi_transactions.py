import copy
from types import SimpleNamespace
import pytest
from civi.pi.network import NetworkError
from civi.pi.transactions import Transactions, Checkpoints
from civi.pi.broker import dispatch

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
        if 'modify' in command:
            value=command[command.index('ipv4.addresses')+1]
            self.value['profile']['ipv4.addresses']=value
            self.value['active_ipv4']=value
            if '--temporary' not in command: self.saved=value
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
    return Transactions(manager=manager,checkpoints=checkpoint,clock=lambda:0),manager,checkpoint


def test_apply_is_temporary_confirm_persists_and_token_required(transaction):
    tx,manager,checkpoint=transaction
    result=tx.apply(SETTINGS,60)
    token=result['pending']['token']
    assert manager.saved=='192.0.2.2/24' and checkpoint.timeout==60
    assert '--temporary' in manager.commands[0]
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
