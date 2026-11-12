import json
import asyncio
from itertools import islice
from types import SimpleNamespace
import pytest
from civi.discovery_state import names,load_names,save_names
from civi.pi.discovery import AvahiDiscovery,NameCollision


def test_acquired_name_reused_then_desired_retried_without_compound_suffix(config):
    save_names(config,'civi','My radio','civi-2','My radio (2)')
    saved=load_names(config,'civi','My radio')
    candidates=list(islice(names('My radio',saved['service']), 5))
    assert candidates[:3]==['My radio (2)','My radio','My radio (3)']
    assert load_names(config,'renamed','My radio') is None
    config['discovery_reset_revision']='new-reset'
    assert load_names(config,'civi','My radio') is None
    assert all(len(n.encode())<=63 for n in islice(names('あ'*21), 1200))


def test_candidates_continue_beyond_old_limit_without_duplicates():
    candidates = list(islice(names('あ'*21, 'Saved name'), 1200))
    assert len(set(candidates)) == 1200
    assert candidates[-1].endswith(' (1199)')
    assert all(len(name.encode('utf-8')) <= 63 for name in candidates)
    assert next(names('Same', 'Same')) == 'Same'


class Group:
    def __init__(self):self.current=[];self.registrations=[];self.collide={'My radio'};self.state=0
    def on_state_changed(self,callback):self.callback=callback
    async def call_reset(self):self.current=[];self.state=0
    async def call_add_service(self,*args):self.current.append(args)
    async def call_commit(self):
        self.registrations.append(self.current.copy())
        self.state=3 if self.current[0][3] in self.collide else 2
    async def call_get_state(self):return self.state
    async def call_free(self):pass


class Server:
    def __init__(self,host='civi.local'):self.host=host
    async def call_get_state(self):return 2
    async def call_get_host_name_fqdn(self):return self.host
    async def call_entry_group_new(self):return '/group'


class Bus:
    def __init__(self,group):self.group=group
    async def introspect(self,*args):return None
    def get_proxy_object(self,*args):return SimpleNamespace(get_interface=lambda _:self.group)
    def disconnect(self):pass
    async def wait_for_disconnect(self):pass


def fake_backend(monkeypatch,group,server):
    async def connect(self):self.bus=Bus(group);self.server=server
    monkeypatch.setattr(AvahiDiscovery,'connect',connect)
    monkeypatch.setattr(AvahiDiscovery,'interface_index',lambda self,config:7)


async def test_avahi_group_collision_persistence_live_hostname_and_restart(config,monkeypatch):
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    group=Group();server=Server()
    fake_backend(monkeypatch,group,server)
    backend=AvahiDiscovery()
    await backend.start(config,{'Manufacturer':'Test'},'civi')
    assert backend.name=='My radio (2)'
    assert all(len(reg)==4 and len({a[3] for a in reg})==1 for reg in group.registrations)
    assert all(a[6]=='' for a in group.current) # host records belong only to Avahi
    assert all(a[0]==7 for a in group.current) # advertise on the selected wired NIC only
    server.host='civi-2.local'
    assert not await backend.inspect()
    await backend.close()
    backend=AvahiDiscovery()
    await backend.start(config,{'Manufacturer':'Test'},'civi')
    assert load_names(config,'civi','My radio')['hostname']=='civi-2'
    await backend.close()
    group.registrations.clear()
    restarted=AvahiDiscovery()
    await restarted.start(config,{'Manufacturer':'Test'},'civi')
    assert group.registrations[0][0][3]=='My radio (2)'
    group.state=3
    assert not await restarted.inspect()
    await restarted.close()


async def test_saved_hostname_restored_through_fixed_helper_operation(config,monkeypatch):
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    save_names(config,'civi','My radio','civi-2','My radio (2)')
    group=Group();server=Server()
    fake_backend(monkeypatch,group,server)
    calls=[]
    def request(self,op,**values):
        calls.append((op,values));server.host=values['hostname']+'.local'
    monkeypatch.setattr('civi.pi.discovery.BrokerClient.request',request)
    backend=AvahiDiscovery();await backend.start(config,{},'civi')
    assert calls==[('mdns_hostname',{'hostname':'civi-2'})]
    assert backend.hostname=='civi-2.local.'
    await backend.close()


async def test_synchronous_avahi_collision_error_retries_entire_group(config,monkeypatch):
    class CollisionError(RuntimeError): type='org.freedesktop.Avahi.CollisionError'
    class LocalGroup(Group):
        async def call_add_service(self,*args):
            if args[3]=='My radio': raise CollisionError('Local name collision')
            await super().call_add_service(*args)
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    group=LocalGroup();fake_backend(monkeypatch,group,Server())
    backend=AvahiDiscovery();await backend.start(config,{},'civi')
    assert backend.name=='My radio (2)' and len(group.current)==4
    await backend.close()


async def test_avahi_continues_past_101_and_saves_success(config, monkeypatch):
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    group=Group()
    group.collide=set(islice(names('My radio'), 110))
    fake_backend(monkeypatch,group,Server())
    real_sleep=asyncio.sleep
    delays=[]
    async def yield_only(delay):
        delays.append(delay)
        await real_sleep(0)
    monkeypatch.setattr('civi.pi.discovery.asyncio.sleep',yield_only)
    backend=AvahiDiscovery()
    try:
        await backend.start(config,{},'civi')
        assert backend.name=='My radio (111)'
        assert load_names(config,'civi','My radio')['service']==backend.name
        assert len(group.registrations)==111
        assert all(len(reg)==4 and len({a[3] for a in reg})==1 for reg in group.registrations)
        assert delays==[.1]*110
    finally:
        await backend.close()


async def test_permanent_avahi_collision_can_be_cancelled_and_frees_group(config,monkeypatch):
    class AlwaysCollision(Group):
        async def call_commit(self):
            self.state=3
        async def call_free(self):
            self.freed=True
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    group=AlwaysCollision()
    fake_backend(monkeypatch,group,Server())
    backend=AvahiDiscovery()
    task=asyncio.create_task(backend.start(config,{},'civi'))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task,1)
    assert group.freed and backend.group is None and backend.bus is None


async def test_permanent_zeroconf_collision_can_be_cancelled_and_closes_socket(config,monkeypatch):
    from civi.network import Discovery
    from zeroconf import NonUniqueNameException
    closed=[]
    collided=asyncio.Event()
    class AlwaysCollision:
        def __init__(self,**kwargs):pass
        async def async_register_service(self,info):
            collided.set()
            raise NonUniqueNameException()
        async def async_close(self):closed.append(True)
    monkeypatch.setattr('zeroconf.asyncio.AsyncZeroconf',AlwaysCollision)
    monkeypatch.setattr(Discovery,'addresses',staticmethod(lambda config:['192.0.2.77']))
    config['pi_network']={'enabled':False}
    discovery=Discovery()
    task=asyncio.create_task(discovery.start(config,{}))
    await asyncio.wait_for(collided.wait(),1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task,1)
    assert closed==[True] and discovery.zc is None and not discovery.services


async def test_saved_hostname_collision_retries_original_desired_name(config,monkeypatch):
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'})
    save_names(config,'civi','My radio','civi-2','My radio (2)')
    group=Group();server=Server();fake_backend(monkeypatch,group,server)
    calls=[]
    def request(self,op,**values):
        calls.append(values['hostname'])
        server.host='civi-3.local' if values['hostname']=='civi-2' else 'civi.local'
    monkeypatch.setattr('civi.pi.discovery.BrokerClient.request',request)
    backend=AvahiDiscovery();await backend.start(config,{},'civi')
    assert calls==['civi-2','civi'] and backend.hostname=='civi.local.'
    await backend.close()


async def test_live_host_change_rebuilds_services_before_publishing_metadata(config,monkeypatch):
    from civi.network import Discovery
    config.update(description='My radio',pi_network={'enabled':True,'socket':'/unused'},bind='0.0.0.0')
    group=Group();server=Server();fake_backend(monkeypatch,group,server)
    monkeypatch.setattr(Discovery,'addresses',staticmethod(lambda config:['192.0.2.77']))
    monkeypatch.setattr(Discovery,'server_name',staticmethod(lambda config:'civi.local.'))
    operations=[]
    def request(self,op,**values):operations.append(op);return {'enabled':True}
    monkeypatch.setattr('civi.pi.discovery.BrokerClient.request',request)
    discovery=Discovery()
    try:
        await discovery.refresh(config,{'Manufacturer':'Test'})
        registered=len(group.registrations)
        old_backend=discovery.avahi
        server.host='civi-2.local'
        await discovery.refresh(config,{'Manufacturer':'Test'})
        assert discovery.avahi is not old_backend
        assert len(group.registrations)>registered
        assert discovery.hostname=='civi-2.local.'
        assert all(service.server=='civi-2.local.' for service in discovery.services)
        assert load_names(config,'civi','My radio')['hostname']=='civi-2'
        assert 'mdns_hostname' not in operations # follow live collision recovery
    finally:await discovery.close()
