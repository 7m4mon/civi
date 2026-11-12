import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from civi.pi.mdns import MdnsController,UNITS
from civi.pi.network import NetworkError
from civi.pi.broker import dispatch
from civi.network import Discovery


class Systemd:
    def __init__(self):
        self.states={unit:'active' for unit in UNITS};self.commands=[];self.fail=None
    def __call__(self,args,**kwargs):
        self.commands.append(args)
        if args[1]==self.fail: return SimpleNamespace(returncode=1,stdout='',stderr='failure')
        if args[1] in ('start','stop'):
            self.states.update({unit:'active' if args[1]=='start' else 'inactive' for unit in args[2:]})
        return SimpleNamespace(returncode=0,stdout=self.states[args[-1]] if args[1]=='show' else '',stderr='')


@pytest.fixture
def controller(tmp_path):
    units=tmp_path/'units';units.mkdir(mode=0o755)
    proc=tmp_path/'proc';proc.mkdir();(proc/'udp').write_text('header\n')
    runner=Systemd()
    return MdnsController(tmp_path/'state',units,runner,proc,getattr(os,'geteuid',lambda:0)()),runner


def test_disable_blocks_service_and_socket_and_survives_controller_restart(controller):
    control,runner=controller
    assert control.set(False)['activation_blocked']
    assert control.disabled()
    for unit in UNITS:
        assert f'ConditionPathExists=!{control.flag}' in (control.units_dir/(unit+'.d')/'50-civi-mdns.conf').read_text()
        assert runner.states[unit]=='inactive'
    restarted=MdnsController(control.directory,control.units_dir,runner,control.proc_dir,control.owner_uid)
    assert restarted.disabled()
    assert restarted.set(True)['enabled'] and not restarted.disabled()
    assert set(runner.states.values())=={'active'}
    assert all(args[0]=='systemctl' and args[1] in ('show','daemon-reload','stop','start') for args in runner.commands)


def test_other_udp_publisher_and_stop_failure_are_not_success(controller):
    control,runner=controller
    (control.proc_dir/'udp').write_text('header\n 0: 00000000:14E9 00000000:0000\n')
    with pytest.raises(NetworkError,match='Another UDP 5353'): control.set(False)
    assert control.disabled()
    (control.proc_dir/'udp').write_text('header\n')
    runner.states={unit:'active' for unit in UNITS};runner.fail='stop'
    with pytest.raises(NetworkError,match='did not stop'): control.set(False)


def test_failed_enable_restores_block_flag(controller):
    control,runner=controller
    control.set(False);runner.fail='start'
    with pytest.raises(NetworkError): control.set(True)
    assert control.disabled() and set(runner.states.values())=={'inactive'}


def test_cancelled_stop_job_is_accepted_only_if_final_state_stopped(controller):
    control,runner=controller
    def cancel(args,**kwargs):
        result=runner(args,**kwargs)
        if args[1]=='stop': result.returncode=1
        return result
    control.runner=cancel
    assert control.set(False)['enabled'] is False
    assert set(runner.states.values())=={'inactive'}


def test_refuses_foreign_dropin_and_non_boolean(controller):
    control,runner=controller
    directory=control.units_dir/(UNITS[0]+'.d');directory.mkdir(mode=0o755)
    path=directory/'50-civi-mdns.conf';path.write_text('administrator data')
    path.chmod(0o644)
    with pytest.raises(NetworkError,match='differs'): control.set(False)
    assert path.read_text()=='administrator data'
    with pytest.raises(ValueError): control.set('false')


async def test_discovery_disables_device_and_retries_failed_helper(config,monkeypatch):
    config.update(discovery=False,pi_network={'enabled':True,'socket':'/test'})
    discovery=Discovery();discovery.close=AsyncMock()
    calls=[]
    def request(self,op,**values):
        calls.append((op,values));return {'enabled':values['enabled']}
    monkeypatch.setattr('civi.pi.broker.BrokerClient.request',request)
    await discovery.refresh(config,{})
    assert calls==[('mdns',{'enabled':False})] and discovery.device_mdns=={'enabled':False}
    assert discovery.last_error is None
    def fail(*a,**k): raise NetworkError('Helper unavailable')
    monkeypatch.setattr('civi.pi.broker.BrokerClient.request',fail)
    with pytest.raises(NetworkError): await discovery.refresh(config,{})
    assert discovery.device_mdns is None and discovery.signature is None
    assert 'Helper unavailable' in discovery.last_error
    monkeypatch.setattr('civi.pi.broker.BrokerClient.request',request)
    await discovery.refresh(config,{})
    assert discovery.device_mdns=={'enabled':False}


def test_helper_does_not_accept_arbitrary_service_names():
    with pytest.raises(ValueError): dispatch(None,{'op':'mdns','enabled':False,'unit':'ssh.service'})
