"""NetworkManager-owned rollback deadlines for one wired LAN interface."""
import json
import os
import re
import secrets
import subprocess
import threading
import time
from .network import NetworkError, NetworkManager, IPv4Settings, plan_changes, interface_name, hostname_label

DEST = 'org.freedesktop.NetworkManager'
ROOT = '/org/freedesktop/NetworkManager'


class Checkpoints:
    def __init__(self, runner=None):
        self.runner = runner or subprocess.run

    def call(self, method, signature, *args):
        try:
            result = self.runner(['busctl','--system','--json=short','--timeout=15',
                                  'call',DEST,ROOT,DEST,method,signature,*map(str,args)],
                                 capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise NetworkError('NetworkManager checkpoint call failed') from error
        if result.returncode:
            raise NetworkError(result.stderr.strip() or 'Checkpoint call failed')
        try: return json.loads(result.stdout)['data'] if result.stdout.strip() else []
        except (ValueError, KeyError, TypeError) as error: raise NetworkError('Invalid checkpoint response') from error

    def create(self, interface, timeout):
        device = self.call('GetDeviceByIpIface','s',interface)[0]
        checkpoint = self.call('CheckpointCreate','aouu',1,device,timeout,0)[0]
        if not re.fullmatch(ROOT + r'/Checkpoint/[0-9]+', checkpoint):
            raise NetworkError('Invalid checkpoint path')
        return checkpoint

    def exists(self, path):
        # Introspection is unnecessary: reading Checkpoints also works after a timeout.
        try:
            result = self.runner(['busctl','--system','--json=short','--timeout=15',
                                  'get-property',DEST,ROOT,DEST,'Checkpoints'],
                                 capture_output=True,text=True,timeout=20)
        except (OSError, subprocess.TimeoutExpired) as error: raise NetworkError('Cannot inspect checkpoints') from error
        if result.returncode: raise NetworkError('Cannot inspect checkpoints')
        try:
            data = json.loads(result.stdout)['data']
            if len(data)==1 and isinstance(data[0],list): data=data[0]
            return path in data
        except (ValueError, KeyError, TypeError) as error: raise NetworkError('Invalid checkpoint list') from error

    def destroy(self, path): self.call('CheckpointDestroy','o',path)

    def rollback(self, path):
        data = self.call('CheckpointRollback','o',path)
        # busctl represents a dictionary as a JSON object, wrapped in the output tuple.
        results = data[0] if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) else data
        if not isinstance(results, dict) or not results or any(value != 0 for value in results.values()):
            raise NetworkError('NetworkManager reported a rollback failure')
        if self.exists(path): self.destroy(path)


class Transactions:
    def __init__(self, interface='eth0', manager=None, checkpoints=None, clock=time.monotonic, ping=None, mdns=None):
        self.interface = interface_name(interface)
        self.manager = manager or NetworkManager()
        self.checkpoints = checkpoints or Checkpoints()
        self.clock = clock
        self.lock = threading.RLock()
        self.pending = None
        self.last_result = None
        if ping is None:
            from .ping import PingResponder
            ping = PingResponder()
        self.ping = ping
        from .mdns import MdnsController
        self.mdns = mdns if mdns is not None else MdnsController()

    def _reconcile(self):
        if self.pending and not self.checkpoints.exists(self.pending['checkpoint']):
            # A vanished checkpoint is not proof that restoration succeeded.
            previous = self.pending['before']
            current = self.manager.snapshot(self.interface)
            restored = (current['uuid'] == previous['uuid'] and current['profile'] == previous['profile']
                        and current['active_ipv4'] == previous['active_ipv4'])
            self.last_result = {'state':'rolled_back' if restored else 'recovery_required',
                                'reason':'Checkpoint ended without confirmation', 'verified':restored}
            self.pending = None

    def status(self):
        with self.lock:
            self._reconcile()
            public = None
            if self.pending:
                public = {key:self.pending[key] for key in ('token','settings','expected_ipv4')}
                public['remaining_seconds'] = max(0,int(self.pending['deadline']-self.clock()))
            return {'interface':self.interface, 'snapshot':self.manager.snapshot(self.interface),
                    'pending':public, 'last_result':self.last_result}

    def preview(self, settings):
        with self.lock:
            state = self.manager.snapshot(self.interface)
            parsed = IPv4Settings.parse(settings)
            if parsed.hostname and parsed.hostname != state['hostname']:
                raise ValueError('Hostname changes are not yet supported by the rollback transaction')
            return plan_changes(state, settings)

    def initialize(self):
        """Local-only recovery; the broker does not expose this through HTTP."""
        with self.lock:
            self._reconcile()
            if self.pending: self.rollback(self.pending['token'])
            state=self.manager.snapshot(self.interface)
            if not state.get('profile_active',True):
                return self._initialize_disconnected(state)
            previous_ping = self.ping.snapshot()
            previous_mdns = self.mdns.disabled()
            result = self.apply({'mode':'automatic','dns':[]}, timeout=180)
            token = result['pending']['token']
            try:
                self.ping.enable()
                self.mdns.set(True)
                def verify(current):
                    profile = current['profile']
                    if (profile.get('ipv4.method') != 'auto' or profile.get('ipv4.addresses') or
                        profile.get('ipv4.gateway') or profile.get('ipv4.dns') or
                        profile.get('ipv4.ignore-auto-dns') != 'no' or
                        profile.get('ipv4.never-default') != 'no' or
                        profile.get('ipv4.dhcp-timeout') != '2147483647' or
                        profile.get('ipv4.link-local') not in ('fallback','4')):
                        raise NetworkError('LAN initialization could not verify the saved DHCP/AutoIP settings')
                result = self.confirm(token, verify=verify)
                return {**result, 'initialized':True, 'ping_enabled':True, 'mdns_enabled':True}
            except Exception:
                try:
                    if self.pending: self.rollback(token)
                    self.ping.restore(previous_ping)
                    self.mdns.set(not previous_mdns)
                except Exception as error:
                    raise NetworkError('LAN initialization failed and restoration could not be verified; inspect the Pi locally') from error
                raise

    @staticmethod
    def _verify_automatic_profile(current):
        p=current['profile']
        if (p.get('ipv4.method')!='auto' or p.get('ipv4.addresses') or p.get('ipv4.gateway') or p.get('ipv4.dns')
            or p.get('ipv4.ignore-auto-dns')!='no' or p.get('ipv4.never-default')!='no'
            or p.get('ipv4.dhcp-timeout')!='2147483647' or p.get('ipv4.link-local') not in ('fallback','4')):
            raise NetworkError('LAN initialization could not verify the saved DHCP/AutoIP settings')

    def _initialize_disconnected(self,before):
        """Persist recovery settings without trying to reapply an inactive device."""
        if before.get('device_autoconnect') not in ('yes','no'):
            raise NetworkError('Cannot verify wired device autoconnect state')
        plan=plan_changes(before,{'mode':'automatic','dns':[]})
        previous_ping=self.ping.snapshot();previous_mdns=self.mdns.disabled()
        mutable=[key for key in before['profile'] if key.startswith('ipv4.') or key=='connection.autoconnect']
        restore=['nmcli','connection','modify','uuid',before['uuid']]
        for key in mutable: restore.extend((key,before['profile'][key]))
        try:
            self._command([*plan['commands'][0],'connection.autoconnect','yes'])
            self._command(['nmcli','device','set',self.interface,'autoconnect','yes'])
            current=self.manager.snapshot(self.interface)
            if current['uuid']!=before['uuid']: raise NetworkError('Recovery profile changed unexpectedly')
            self._verify_automatic_profile(current)
            if current['profile'].get('connection.autoconnect')!='yes' or current.get('device_autoconnect')!='yes':
                raise NetworkError('Cannot verify wired autoconnect recovery settings')
            self.ping.enable();self.mdns.set(True)
            if current.get('carrier'):
                # Configuration is saved; NM can acquire an address asynchronously.
                self._command(['nmcli','connection','up','uuid',before['uuid'],'ifname',self.interface],wait=0)
            self.last_result={'state':'initialized_waiting_for_address' if current.get('carrier') else 'initialized_waiting_for_link',
                              'verified':True}
            return {**self.status(),'initialized':True,'ping_enabled':True,'mdns_enabled':True,
                    'waiting_for_link':not current.get('carrier'), 'address_ready':False}
        except Exception:
            try:
                self._command(restore)
                self._command(['nmcli','device','set',self.interface,'autoconnect',before['device_autoconnect']])
                self.ping.restore(previous_ping);self.mdns.set(not previous_mdns)
                current=self.manager.snapshot(self.interface)
                if current['uuid']!=before['uuid'] or current['profile']!=before['profile'] or current.get('device_autoconnect')!=before['device_autoconnect']:
                    raise NetworkError('Original disconnected configuration did not match')
            except Exception as error:
                raise NetworkError('Disconnected LAN reset failed; restoration could not be verified. Inspect the Pi locally') from error
            raise

    def hostname(self, hostname):
        """Save the system hostname separately from checkpointed IPv4 changes."""
        from ..defaults import DEFAULT_HOSTNAME
        name = hostname_label(DEFAULT_HOSTNAME if isinstance(hostname,str) and not hostname.strip() else hostname)
        with self.lock:
            self._reconcile()
            if self.pending:
                raise NetworkError('Confirm or restore the pending IPv4 change before saving a hostname')
            before = self.manager.snapshot(self.interface)
            if name != before['hostname']:
                try:
                    self._command(['nmcli','general','hostname',name])
                    current = self.manager.snapshot(self.interface)
                    if current['hostname'] != name:
                        raise NetworkError('Saved hostname did not match the requested name')
                    if any(current[key] != before[key] for key in ('uuid','profile','active_ipv4')):
                        raise NetworkError('LAN settings changed while saving the hostname; inspect wired LAN')
                except Exception as error:
                    try:
                        self._command(['nmcli','general','hostname',before['hostname']])
                        if self.manager.snapshot(self.interface)['hostname'] != before['hostname']:
                            raise NetworkError('Hostname restoration did not match')
                    except Exception as restore_error:
                        raise NetworkError('Hostname save failed and restoration could not be verified; inspect the Pi locally') from restore_error
                    raise NetworkError('Hostname save failed; the previous hostname was restored') from error
            return {**self.status(), 'hostname_saved':True}

    def mdns_hostname(self, hostname):
        name=hostname_label(hostname)
        with self.lock:
            self._reconcile()
            if self.pending: raise NetworkError('Finish the pending IPv4 change before restoring an mDNS hostname')
            try:
                result=self.manager.runner(['busctl','--system','--timeout=10','call','org.freedesktop.Avahi',
                    '/','org.freedesktop.Avahi.Server','SetHostName','s',name],
                    capture_output=True,text=True,timeout=15,env={**os.environ,'LC_ALL':'C'})
            except (OSError,subprocess.TimeoutExpired) as error: raise NetworkError('Could not request the Avahi hostname') from error
            if result.returncode: raise NetworkError(result.stderr.strip() or 'Avahi hostname request failed')
            return {'requested_hostname':name}

    def mdns_enabled(self,enabled):
        with self.lock:
            return self.mdns.set(enabled)

    def ping_enabled(self,enabled):
        with self.lock:
            return self.ping.set(enabled)

    def ping_status(self):
        with self.lock:
            return self.ping.status()

    def apply(self, settings, timeout=90):
        with self.lock:
            if type(timeout) is not int or not 30 <= timeout <= 180:
                raise ValueError('Confirmation timeout must be 30-180 seconds')
            self._reconcile()
            if self.pending: raise NetworkError('Another LAN change is waiting for confirmation')
            plan = self.preview(settings)
            before = self.manager.snapshot(self.interface)
            if not before.get('profile_active',True):
                raise NetworkError('Temporary Web changes require an active wired profile; use local LAN RESET for disconnected recovery')
            modify = plan['commands'][0]
            checkpoint = self.checkpoints.create(self.interface, timeout)
            token = secrets.token_urlsafe(24)
            self.pending = {'checkpoint':checkpoint, 'token':token,'settings':settings.copy(),
                            'expected_ipv4':settings.get('address') if settings['mode']=='static' else None,
                            'deadline':self.clock()+timeout, 'before':before, 'modify':modify}
            self.last_result = None
            try:
                # Reapply to the device only. Editing a Netplan-backed profile with
                # --temporary can leave a tombstone when it is later persisted.
                self._command(['nmcli','device','modify',self.interface,*modify[5:]], wait=20)
                current = self.manager.snapshot(self.interface)
                if settings['mode'] == 'static':
                    wanted = f"{settings['address']}/{settings['prefix']}"
                    if wanted not in current['active_ipv4'].splitlines():
                        raise NetworkError('The requested IPv4 address is not active')
                if not self.checkpoints.exists(checkpoint): raise NetworkError('Confirmation deadline expired while applying')
                return self.status()
            except BaseException:
                try: self.rollback(token)
                except Exception:
                    self.last_result = {'state':'recovery_required','verified':False}
                raise

    def _command(self, command, wait=10):
        try:
            result = self.manager.runner([command[0],'--wait',str(wait),*command[1:]],
                                         capture_output=True,text=True,timeout=wait+5)
        except (OSError, subprocess.TimeoutExpired) as error: raise NetworkError('LAN change command failed') from error
        if result.returncode: raise NetworkError(result.stderr.strip() or 'LAN change command failed')

    def _require(self, token):
        self._reconcile()
        if not self.pending or not secrets.compare_digest(str(token),self.pending['token']):
            raise NetworkError('No matching pending LAN transaction')
        return self.pending

    def confirm(self, token, verify=None):
        with self.lock:
            pending = self._require(token)
            if self.clock() >= pending['deadline']: raise NetworkError('Confirmation deadline expired')
            try:
                self._command(pending['modify'])
                current = self.manager.snapshot(self.interface)
                if current['uuid'] != pending['before']['uuid']:
                    raise NetworkError('The saved connection profile changed unexpectedly')
                if pending['expected_ipv4'] and pending['expected_ipv4'] not in [ip.split('/')[0] for ip in current['active_ipv4'].splitlines()]:
                    raise NetworkError('The confirmed wired IPv4 is no longer active')
                if verify: verify(current)
                self.checkpoints.destroy(pending['checkpoint'])
            except Exception:
                try: self.rollback(token)
                except Exception: pass
                raise
            self.pending = None
            self.last_result = {'state':'confirmed','verified':True}
            return self.status()

    def rollback(self, token):
        with self.lock:
            pending = self._require(token)
            self.checkpoints.rollback(pending['checkpoint'])
            self.pending = None
            current = self.manager.snapshot(self.interface)
            verified = (current['uuid']==pending['before']['uuid'] and current['profile']==pending['before']['profile']
                        and current['active_ipv4']==pending['before']['active_ipv4'])
            self.last_result = {'state':'rolled_back' if verified else 'recovery_required', 'verified':verified}
            if not verified: raise NetworkError('Rollback completed but original IPv4 settings were not verified')
            return self.status()
