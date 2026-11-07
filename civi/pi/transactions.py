"""NetworkManager-owned rollback deadlines for one wired LAN interface."""
import json
import re
import secrets
import subprocess
import threading
import time
from .network import NetworkError, NetworkManager, IPv4Settings, plan_changes, interface_name

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
    def __init__(self, interface='eth0', manager=None, checkpoints=None, clock=time.monotonic):
        self.interface = interface_name(interface)
        self.manager = manager or NetworkManager()
        self.checkpoints = checkpoints or Checkpoints()
        self.clock = clock
        self.lock = threading.RLock()
        self.pending = None
        self.last_result = None

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

    def apply(self, settings, timeout=90):
        with self.lock:
            if type(timeout) is not int or not 30 <= timeout <= 180:
                raise ValueError('Confirmation timeout must be 30-180 seconds')
            self._reconcile()
            if self.pending: raise NetworkError('Another LAN change is waiting for confirmation')
            plan = self.preview(settings)
            before = self.manager.snapshot(self.interface)
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

    def confirm(self, token):
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
