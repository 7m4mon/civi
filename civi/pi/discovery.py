"""Pi mDNS authority: Avahi owns host records and collision probing."""
import asyncio
import socket
from ..discovery_state import load_names, save_names, names
from .broker import BrokerClient
from .network import hostname_label

DEST='org.freedesktop.Avahi'


class AvahiDiscovery:
    def __init__(self):
        self.bus=None;self.server=None;self.group=None
        self.name=None;self.hostname=None
        self.conflicted=False

    async def connect(self):
        try:
            from dbus_next.aio import MessageBus
            from dbus_next import BusType
        except ImportError as error:
            raise RuntimeError('Pi discovery needs dbus-next; install CIVI with .venv/bin/python -m pip install -e ".[pi]"') from error
        self.bus=await MessageBus(bus_type=BusType.SYSTEM).connect()
        intro=await self.bus.introspect(DEST,'/')
        self.server=self.bus.get_proxy_object(DEST,'/',intro).get_interface(DEST+'.Server')

    def interface_index(self, config):
        return socket.if_nametoindex(config.get('pi_network', {}).get('interface', 'eth0'))

    async def running_hostname(self):
        for _ in range(50):
            if await self.server.call_get_state()==2:
                fqdn=await self.server.call_get_host_name_fqdn()
                if not fqdn.endswith('.local'): raise ValueError('Avahi must use the local mDNS domain')
                hostname_label(fqdn[:-6])
                return fqdn+'.'
            await asyncio.sleep(.1)
        raise RuntimeError('Avahi hostname probing did not complete')

    async def select_hostname(self, config, desired, saved):
        current=await self.running_hostname()
        # Once per application/desired-name/reset generation, restore the saved
        # acquired name. Afterwards follow Avahi's live conflict resolution.
        key=(desired,config.get('discovery_reset_revision'))
        initialized=config.get('_avahi_hostname_initialized')==key
        if not initialized:
            target=saved['hostname'] if saved else desired
            if current!=target+'.local.':
                helper=BrokerClient(config['pi_network']['socket'])
                await asyncio.to_thread(helper.request,'mdns_hostname',hostname=target)
                current=await self.running_hostname()
                if saved and target!=desired and current!=target+'.local.':
                    # If the saved acquired name now collides, retry the user's
                    # desired name before accepting another numbered name.
                    await asyncio.to_thread(helper.request,'mdns_hostname',hostname=desired)
                    current=await self.running_hostname()
            config['_avahi_hostname_initialized']=key
        return current

    async def start(self, config, fields, desired):
        self.config=config;self.desired=desired
        self.desired_service=config['description']
        saved=load_names(config,desired,self.desired_service)
        interface=self.interface_index(config)
        try:
            await self.connect()
            self.hostname=await self.select_hostname(config,desired,saved)
            path=await self.server.call_entry_group_new()
            intro=await self.bus.introspect(DEST,path)
            self.group=self.bus.get_proxy_object(DEST,path,intro).get_interface(DEST+'.EntryGroup')
            self.group.on_state_changed(self.state_changed)
            identity={'txtvers':'1',**{('FirmwareVersion' if k=='FirmwareRevision' else k):v for k,v in fields.items()}}
            for candidate in names(self.desired_service,saved['service'] if saved else None):
                await self.group.call_reset()
                self.conflicted=False
                try:
                    for service,port in self.service_ports(config):
                        properties={'txtvers':'1','path':'/lxi'} if service in ('_http._tcp','_https._tcp') else identity
                        txt=[(k+'='+str(v)).encode('utf-8') for k,v in properties.items()]
                        if any(len(v)>255 for v in txt): raise ValueError('Discovery identity exceeds DNS-SD TXT limit')
                        # Empty host means Avahi's current, probed host. Avahi also
                        # supplies address records on the appropriate interface.
                        await self.group.call_add_service(interface,0,0,candidate,service,'local','',port,txt)
                    await self.group.call_commit()
                    for _ in range(50):
                        state=await self.group.call_get_state()
                        if state==2: break
                        if state==3 or self.conflicted: raise NameCollision()
                        if state==4: raise RuntimeError('Avahi service registration failed')
                        await asyncio.sleep(.1)
                    else: raise RuntimeError('Avahi service probing did not complete')
                    self.name=candidate
                    self.hostname=await self.running_hostname()
                    self.persist()
                    return
                except Exception as error:
                    if isinstance(error,NameCollision) or getattr(error,'type','') in (DEST+'.Collision',DEST+'.CollisionError'):
                        # Immediate local collisions must not busy-loop or
                        # prevent cancellation while continuing to retry.
                        await asyncio.sleep(.1)
                        continue
                    raise
            raise RuntimeError('Discovery service name conflicts exhausted')
        except BaseException:
            await self.close();raise

    @staticmethod
    def service_ports(config):
        return [('_http._tcp',config['web_port']),('_lxi._tcp',config['web_port']),
                ('_scpi-raw._tcp',config['scpi_port']),('_https._tcp',config['web_port'])]

    def state_changed(self,state,error):
        if state in (3,4): self.conflicted=True

    def persist(self):
        save_names(self.config,self.desired,self.desired_service,self.hostname[:-7],self.name)

    async def inspect(self):
        state=await self.group.call_get_state()
        if state in (3,4) or self.conflicted: return False
        if state!=2: return False
        hostname=await self.running_hostname()
        # Dynamic EntryGroup SRV records retain the host chosen at registration.
        # Updating our metadata alone would show the new name while peers still
        # resolve services to the old one. Let Discovery rebuild the whole group.
        if hostname!=self.hostname:return False
        self.persist()
        return True

    async def close(self):
        if self.group:
            try: await self.group.call_free()
            except Exception: pass
            self.group=None
        if self.bus:
            self.bus.disconnect()
            try: await asyncio.wait_for(self.bus.wait_for_disconnect(),2)
            except Exception: pass
            self.bus=None


class NameCollision(RuntimeError): pass
