import copy,json,os
from types import SimpleNamespace
import pytest
from civi.pi.network import NetworkManager,NetworkError
from civi.pi.target import RecoveryTarget
from civi.pi.transactions import Transactions

UUID='12345678-1234-1234-1234-123456789abc'


def test_recovery_target_is_persistent_and_interface_specific(tmp_path):
    owner=getattr(os,'geteuid',lambda:0)()
    target=RecoveryTarget('eth0',tmp_path,owner)
    assert target.load() is None
    target.save(UUID)
    assert RecoveryTarget('eth0',tmp_path,owner).load()==UUID
    assert RecoveryTarget('eth1',tmp_path,owner).load() is None
    target.path.write_text(json.dumps({'interface':'wlan0','uuid':UUID}))
    with pytest.raises(NetworkError):target.load()


@pytest.mark.parametrize('bound,mac,kind,active,success',[
    ('eth0','','802-3-ethernet','',True),
    ('','','802-3-ethernet','',True),
    ('eth1','','802-3-ethernet','',False),
    ('','aa:bb:cc:dd:ee:ff','802-3-ethernet','',False),
    ('','','802-11-wireless','',False),
    ('','','802-3-ethernet','22222222-2222-2222-2222-222222222222:eth0',False),
])
def test_inactive_profile_requires_pinned_uuid_and_matching_device(monkeypatch,bound,mac,kind,active,success):
    manager=NetworkManager(selected_uuid=UUID)
    values={'VERSION':'1.52.1','connection.type':kind,'connection.interface-name':bound,
            '802-3-ethernet.mac-address':mac,'GENERAL.HWADDR':'00:11:22:33:44:55',
            'WIRED-PROPERTIES.CARRIER':'off','GENERAL.AUTOCONNECT':'yes'}
    def read(*args):
        if args==('--version',):return '1.52.1'
        if '--active' in args:return active
        if '-g' in args:return values.get(args[args.index('-g')+1],'')
        return 'civi'
    monkeypatch.setattr(manager,'_read',read)
    if success:
        result=manager.snapshot('eth0')
        assert result['uuid']==UUID and not result['profile_active'] and not result['carrier']
    else:
        with pytest.raises(NetworkError):manager.snapshot('eth0')


class Manager:
    def __init__(self):
        self.value={'interface':'eth0','uuid':UUID,'hostname':'civi','profile_active':False,
            'carrier':False,'device_autoconnect':'no','autoip_fallback_supported':True,
            'active_ipv4':'','active_gateway':'','active_dns':'','profile':{
            'connection.type':'802-3-ethernet','connection.id':'Wired', 'connection.autoconnect':'no',
            'ipv4.method':'manual','ipv4.addresses':'192.0.2.2/24','ipv4.gateway':'',
            'ipv4.dns':'','ipv4.ignore-auto-dns':'no','ipv4.never-default':'yes',
            'ipv4.link-local':'disabled','ipv4.dhcp-timeout':'0'}}
        self.commands=[]
    def snapshot(self,interface):return copy.deepcopy(self.value)
    def runner(self,args,**kwargs):
        self.commands.append(args)
        if 'modify' in args:
            start=args.index('uuid')+2
            self.value['profile'].update(zip(args[start::2],args[start+1::2]))
        elif 'set' in args:self.value['device_autoconnect']=args[-1]
        return SimpleNamespace(returncode=0,stderr='')


def transaction():
    manager=Manager()
    ping=SimpleNamespace(snapshot=lambda:None,enable=lambda:None,restore=lambda value:None)
    mdns=SimpleNamespace(disabled=lambda:False,set=lambda enabled:{'enabled':enabled})
    return Transactions(manager=manager,ping=ping,mdns=mdns),manager


def test_disconnected_lci_saves_automatic_settings_without_activation_or_checkpoint():
    tx,manager=transaction()
    result=tx.initialize()
    assert result['initialized'] and result['waiting_for_link'] and not result['address_ready']
    assert result['pending'] is None
    assert manager.value['profile']['ipv4.method']=='auto'
    assert manager.value['profile']['ipv4.addresses']==''
    assert manager.value['profile']['connection.autoconnect']=='yes'
    assert manager.value['device_autoconnect']=='yes'
    assert not any('up' in command or 'wlan0' in command for command in manager.commands)
    with pytest.raises(NetworkError,match='active wired profile'): tx.apply({'mode':'automatic','dns':[]})


def test_inactive_but_carrier_present_requests_async_activation():
    tx,manager=transaction();manager.value['carrier']=True
    result=tx.initialize()
    assert result['initialized'] and not result['waiting_for_link']
    assert ['nmcli','--wait','0','connection','up','uuid',UUID,'ifname','eth0'] in manager.commands


def test_disconnected_failure_restores_saved_profile_and_autoconnect():
    tx,manager=transaction();before=manager.snapshot('eth0')
    tx.ping.enable=lambda:(_ for _ in ()).throw(NetworkError('Ping failure'))
    with pytest.raises(NetworkError,match='Ping failure'):tx.initialize()
    assert manager.snapshot('eth0')==before
