from types import SimpleNamespace
import subprocess
import pytest
from civi.pi.network import IPv4Settings, NetworkError, NetworkManager, plan_changes, version_tuple

UUID = '12345678-1234-1234-1234-123456789abc'


def state(version='1.52.0'):
    return {'interface':'eth0', 'uuid':UUID, 'hostname':'civi',
            'autoip_fallback_supported':version_tuple(version) >= (1,52,0)}


def test_static_and_automatic_plans_are_data_not_executed():
    data = {'mode':'static', 'hostname':'civi-pi', 'address':'192.0.2.20',
            'prefix':24, 'gateway':'192.0.2.1', 'dns':['192.0.2.1']}
    plan = plan_changes(state(), data)
    assert plan['applied'] is False and plan['requires_rollback_and_confirmation'] is True
    assert plan['commands'][0] == ['nmcli','general','hostname','civi-pi']
    command = plan['commands'][1]
    assert command[command.index('ipv4.addresses')+1] == '192.0.2.20/24'
    assert command[command.index('ipv4.link-local')+1] == 'disabled'
    automatic = plan_changes(state(), {'mode':'automatic'})['commands'][0]
    assert automatic[automatic.index('ipv4.link-local')+1] == 'fallback'
    assert automatic[automatic.index('ipv4.addresses')+1] == ''
    assert automatic[automatic.index('ipv4.ignore-auto-dns')+1] == 'no'


def test_old_networkmanager_does_not_pretend_to_have_autoip():
    with pytest.raises(NetworkError, match='1.52'):
        plan_changes(state('1.42.4'), {'mode':'automatic'})
    plan = plan_changes(state('1.42.4'), {'mode':'static','address':'192.0.2.20','prefix':24})
    assert 'ipv4.link-local' not in plan['commands'][0]


@pytest.mark.parametrize('data', [
    {'mode':'automatic','address':'192.0.2.2'},
    {'mode':'automatic','prefix':24},
    {'mode':'automatic','hostname':'x; reboot'},
    {'mode':'automatic','hostname':'-option'},
    {'mode':'automatic','dns':['127.0.0.1']},
    {'mode':'automatic','dns':'192.0.2.1'},
    {'mode':'automatic','unexpected':1},
    {'mode':'static','address':'192.0.2.0','prefix':24},
    {'mode':'static','address':'192.0.2.255','prefix':24},
    {'mode':'static','address':'192.0.2.2','prefix':True},
    {'mode':'static','address':'192.0.2.2','prefix':24,'gateway':'192.0.3.1'},
    {'mode':'static','address':'192.0.2.2','prefix':24,'gateway':'192.0.2.2'},
    {'mode':'static','address':'224.0.0.1','prefix':24},
])
def test_invalid_input_rejected(data):
    with pytest.raises(ValueError): IPv4Settings.parse(data)


def test_snapshot_reads_actual_fields_using_uuid_not_profile_name(monkeypatch):
    monkeypatch.setattr('civi.pi.network.platform.system', lambda:'Linux')
    calls = []
    fields = {'connection.id':'Wired profile with spaces', 'connection.type':'802-3-ethernet',
              'ipv4.method':'auto', 'ipv4.addresses':'', 'ipv4.gateway':'', 'ipv4.dns':'',
              'IP4.ADDRESS':'192.0.2.10/24', 'IP4.GATEWAY':'192.0.2.1', 'IP4.DNS':'192.0.2.1', 'VERSION':'1.52.0',
              'ipv4.ignore-auto-dns':'no','ipv4.never-default':'yes','ipv4.link-local':'0'}
    def runner(command, **kwargs):
        calls.append(command)
        assert kwargs['timeout'] == 10 and kwargs['env']['LC_ALL'] == 'C'
        assert not kwargs.get('shell')
        if '--version' in command: output = 'nmcli tool, version 1.52.0'
        elif '--active' in command: output = f'{UUID}:eth0\n22222222-2222-2222-2222-222222222222:wlan0'
        elif '-g' in command: output = fields[command[command.index('-g')+1]]
        elif command[-2:] == ['general','hostname']: output = 'civi'
        else: raise AssertionError(command)
        return SimpleNamespace(returncode=0, stdout=output, stderr='')
    snapshot = NetworkManager(runner).snapshot('eth0')
    assert snapshot['uuid'] == UUID and snapshot['active_ipv4'] == '192.0.2.10/24'
    assert snapshot['profile']['connection.id'] == 'Wired profile with spaces'
    assert snapshot['autoip_fallback_supported']
    assert all(not any(x in call for x in ('modify','up','down','delete')) for call in calls)
    fields['VERSION'] = '1.42.4'
    assert NetworkManager(runner).snapshot('eth0')['autoip_fallback_supported'] is False


def test_windows_fails_before_running_any_command(monkeypatch):
    monkeypatch.setattr('civi.pi.network.platform.system', lambda:'Windows')
    def runner(*args, **kwargs): raise AssertionError('Must not execute on Windows')
    with pytest.raises(NetworkError, match='requires Linux'):
        NetworkManager(runner).snapshot('eth0')


@pytest.mark.parametrize('failure', [FileNotFoundError(), subprocess.TimeoutExpired('nmcli',10)])
def test_failures_do_not_return_success(monkeypatch, failure):
    monkeypatch.setattr('civi.pi.network.platform.system', lambda:'Linux')
    def runner(*args, **kwargs): raise failure
    with pytest.raises(NetworkError): NetworkManager(runner).snapshot('eth0')


def test_disconnected_and_invalid_interface_rejected(monkeypatch):
    monkeypatch.setattr('civi.pi.network.platform.system', lambda:'Linux')
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=0, stderr='', stdout='nmcli tool, version 1.52.0' if '--version' in command else '')
    with pytest.raises(NetworkError, match='exactly one'):
        NetworkManager(runner).snapshot('eth0')
    with pytest.raises(ValueError): NetworkManager(runner).snapshot('eth0; reboot')


@pytest.mark.parametrize('active,kind,message', [
    (f'{UUID}:eth0\n{UUID}:eth0','802-3-ethernet','exactly one'),
    (f'{UUID}:eth0','802-11-wireless','wired Ethernet'),
])
def test_ambiguous_and_non_ethernet_profiles_rejected(monkeypatch, active, kind, message):
    monkeypatch.setattr('civi.pi.network.platform.system', lambda:'Linux')
    def runner(command, **kwargs):
        if '--version' in command: output = '1.52.0'
        elif '--active' in command: output = active
        elif command[command.index('-g')+1] == 'VERSION': output = '1.52.0'
        elif command[command.index('-g')+1] == 'connection.type': output = kind
        else: output = ''
        return SimpleNamespace(returncode=0, stdout=output, stderr='')
    with pytest.raises(NetworkError, match=message): NetworkManager(runner).snapshot('eth0')
