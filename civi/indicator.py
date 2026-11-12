"""LAN status and Identify state, independent of radio control."""
import asyncio
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import stat
import time
from .network import network_info


def panel_path(config):
    return Path(config['network_settings_file']).with_name('.civi-panel.sock')


def usable(address):
    try:
        ip=ipaddress.IPv4Address(address.split('/')[0])
        return not (ip.is_loopback or ip.is_unspecified or ip.is_multicast or int(ip)==0xffffffff)
    except (ValueError,AttributeError): return False


class PiLanReader:
    """Read-only OS observations; no privileged helper or radio command."""
    def __init__(self, interface='eth0', conflict_reader=None):
        from .pi.network import NetworkManager, interface_name
        self.interface=interface_name(interface)
        self.manager=NetworkManager()
        self.conflict_reader=conflict_reader

    def __call__(self):
        net=network_info()
        nic=next((i for i in net['interfaces'] if i['name']==self.interface),None)
        result={'interface':self.interface,'hostname':net['hostname'],'present':bool(nic),
                'link':bool(nic and nic['up']),'addresses':nic['ipv4'] if nic else [],
                'mac':nic.get('mac') if nic else None,'method':None,'uuid':None,'manual':'',
                'dhcp_address':None,'reason':None,'error':None}
        if not nic: return result
        try: result['link']=Path('/sys/class/net',self.interface,'carrier').read_text().strip()=='1'
        except OSError: pass
        try:
            read=self.manager._read
            uuid=read('-g','GENERAL.CON-UUID','device','show',self.interface)
            result['uuid']=uuid if re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',uuid) else None
            reason=read('-g','GENERAL.REASON','device','show',self.interface)
            match=re.match(r'(\d+)',reason)
            result['reason']=int(match[1]) if match else None
            result['nm_state']=read('-g','GENERAL.STATE','device','show',self.interface)
            if result['uuid']:
                applied=self.manager.applied_ipv4(self.interface)
                result['method']=applied['method']
                result['manual']=','.join(applied['addresses'])
                options=read('-g','DHCP4.OPTION','device','show',self.interface)
                match=re.search(r'\bip_address\s*=\s*(\d+\.\d+\.\d+\.\d+)',options)
                if match and match[1] in result['addresses']: result['dhcp_address']=match[1]
        except Exception:
            result['error']='NetworkManager status could not be read'
        if self.conflict_reader:
            try:
                guard=self.conflict_reader()
                result['runtime_conflict']=guard.get('fault')
                if not guard.get('running') or guard.get('error') or guard.get('sample_age_seconds') is None or guard['sample_age_seconds']>20:
                    result['guard_error']=guard.get('error') or 'Duplicate IPv4 guard is unavailable or stale'
            except Exception:result['guard_error']='Duplicate IPv4 guard unavailable; restart the updated LAN helper'
        return result


class LanIndicator:
    def __init__(self, interface='eth0', clock=time.monotonic):
        self.interface, self.clock=interface,clock
        self.observation=None
        self.sampled=None
        self.identify=False
        self.panel_seen=None
        self.panel_visible=False
        self.panel_showing=False
        self.generation=None
        self.last_link=False
        self.last_ips=()
        self.reset_faults()

    def reset_faults(self):
        self.identify=False
        self.had_lease=False
        self.lease_lost=False
        self.duplicate_ips=None

    def update(self, observation):
        self.observation=dict(observation)
        self.sampled=self.clock()
        if observation.get('error'): return
        generation=(observation.get('uuid'),observation.get('method'),observation.get('manual'))
        link=bool(observation.get('link'))
        # A missing UUID during a transition is not a user reinitialization.
        if ((observation.get('uuid') and generation!=self.generation) or not link or not self.last_link):
            self.reset_faults()
        if observation.get('uuid'): self.generation=generation
        ips=tuple(ip for ip in observation.get('addresses',[]) if usable(ip))
        if link:
            if observation.get('dhcp_address') in ips:
                self.had_lease=True; self.lease_lost=False
            elif self.had_lease and observation.get('method')=='auto': self.lease_lost=True
            if observation.get('reason')==64: self.duplicate_ips=ips or self.last_ips
            elif self.duplicate_ips is not None and ips and ips!=self.duplicate_ips: self.duplicate_ips=None
        self.last_link=link
        self.last_ips=ips

    def heartbeat(self, visible, showing):
        if type(visible) is not bool or type(showing) is not bool: raise ValueError('Expected display booleans')
        self.panel_seen=self.clock()
        self.panel_visible=visible
        self.panel_showing=showing

    def set_identify(self, enabled):
        if type(enabled) is not bool: raise ValueError('Expected Identify boolean')
        if enabled and not self.snapshot()['display_connected']:
            raise ValueError('Start the local Pi panel with bash panel.sh and keep its window visible')
        if enabled and self.snapshot()['state'] != 'normal':
            raise ValueError('Restore normal LAN status before starting Identify')
        self.identify=enabled
        return self.snapshot()

    def snapshot(self):
        now=self.clock()
        connected=self.panel_seen is not None and now-self.panel_seen<=5 and self.panel_visible
        obs=self.observation or {}
        faults=[]
        state='normal'
        if self.sampled is None or now-self.sampled>10:
            state='unknown'; faults.append('LAN observations are unavailable or stale')
        elif obs.get('error'):
            state='unknown'; faults.append(obs['error'])
        else:
            if not obs.get('present'): faults.append('Wired interface not found')
            elif not obs.get('link'): faults.append('LAN cable disconnected / no carrier')
            elif not any(usable(ip) for ip in obs.get('addresses',[])): faults.append('No usable IPv4 address')
            if self.duplicate_ips is not None: faults.append('Duplicate IPv4 address reported by NetworkManager')
            if obs.get('runtime_conflict'):
                conflict=obs['runtime_conflict']
                faults.append('Duplicate IPv4 address '+conflict['address']+(' detected; wired LAN disconnected' if conflict.get('disconnected') else ' detected; disconnection not verified'))
            if self.lease_lost: faults.append('Previously acquired DHCP address lost; waiting for a new lease')
            if faults: state='fault'
            if obs.get('guard_error'):
                faults.append(obs['guard_error'])
                if state=='normal':state='unknown'
        if state != 'normal':
            self.identify=False
        return {'interface':self.interface,'hostname':obs.get('hostname'),
                'addresses':obs.get('addresses',[]),'mac':obs.get('mac'),
                'link':bool(obs.get('link')),'method':obs.get('method'),
                'state':state,'faults':faults,'identify':self.identify,
                'display_connected':connected,
                'display_acknowledged':connected and self.panel_showing==self.identify,
                'sample_age_seconds':round(now-self.sampled,1) if self.sampled is not None else None}


class LocalPanelServer:
    def __init__(self, path, indicator, details):
        self.path=Path(path); self.indicator=indicator; self.details=details
        self.server=None

    async def start(self):
        if self.path.exists() or self.path.is_symlink():
            info=self.path.lstat()
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=os.geteuid():
                raise OSError('Local panel socket path is not a socket owned by the CIVI user')
            try:
                reader,writer=await asyncio.open_unix_connection(str(self.path))
            except (ConnectionRefusedError,FileNotFoundError): self.path.unlink(missing_ok=True)
            else:
                writer.close(); await writer.wait_closed()
                raise OSError('A local panel server is already running')
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        previous=os.umask(0o077)
        try: listener.bind(str(self.path))
        except BaseException:
            listener.close(); raise
        finally: os.umask(previous)
        os.chmod(self.path,0o600)
        listener.setblocking(False)
        try: self.server=await asyncio.start_unix_server(self.handle,sock=listener,limit=2048)
        except BaseException:
            listener.close(); self.path.unlink(missing_ok=True); raise

    async def handle(self,reader,writer):
        try:
            raw=await asyncio.wait_for(reader.readline(),2)
            if len(raw)>1024 or not raw.endswith(b'\n'): raise ValueError('Invalid panel request')
            data=json.loads(raw)
            if not isinstance(data,dict): raise ValueError('Expected panel request')
            if set(data)=={'op','visible','showing'} and data['op']=='status':
                self.indicator.heartbeat(data['visible'],data['showing'])
            elif data=={'op':'stop_identify'}: self.indicator.set_identify(False)
            else: raise ValueError('Invalid panel operation')
            result={'ok':True,'status':self.indicator.snapshot(),'device':self.details()}
        except (ValueError,TypeError,asyncio.TimeoutError): result={'ok':False,'error':'Invalid local panel request'}
        try:
            writer.write(json.dumps(result).encode()+b'\n'); await writer.drain()
        except (ConnectionError,OSError): pass
        finally:
            writer.close()
            try: await writer.wait_closed()
            except OSError: pass

    async def close(self):
        if self.server:
            self.server.close(); await self.server.wait_closed()
            self.path.unlink(missing_ok=True)
