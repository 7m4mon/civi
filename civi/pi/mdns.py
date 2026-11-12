"""Bounded Avahi device switch, including hostname replies and activation."""
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from .network import NetworkError

UNITS = ('avahi-daemon.socket', 'avahi-daemon.service')


class MdnsController:
    def __init__(self, state_dir='/var/lib/civi', units_dir='/etc/systemd/system',
                 runner=subprocess.run, proc_dir='/proc/net', owner_uid=0):
        self.directory=Path(state_dir)
        self.flag=self.directory/'mdns.disabled'
        self.units_dir=Path(units_dir)
        self.runner=runner
        self.proc_dir=Path(proc_dir)
        self.owner_uid=owner_uid

    def _check(self,path,directory=False):
        info=path.lstat()
        if (stat.S_ISLNK(info.st_mode) or
            not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)) or
            (os.name=='posix' and (info.st_uid!=self.owner_uid or info.st_mode & 0o022))):
            raise NetworkError('Unsafe CIVI mDNS control path')

    def _directory(self,path):
        if not path.exists(): path.mkdir(mode=0o755,parents=True)
        self._check(path,True)

    def _command(self,*args,allow_failure=False):
        try:
            result=self.runner(['systemctl',*args],capture_output=True,text=True,timeout=20,
                               env={**os.environ,'LC_ALL':'C','SYSTEMD_PAGER':''})
        except (OSError,subprocess.TimeoutExpired) as error:
            raise NetworkError('Avahi service control unavailable') from error
        if result.returncode and not allow_failure: raise NetworkError('Avahi service control failed; inspect the Pi locally')
        return result.stdout.strip()

    def disabled(self):
        if self.directory.exists(): self._check(self.directory,True)
        if self.flag.exists() or self.flag.is_symlink():
            self._check(self.flag)
            return True
        return False

    def _install_conditions(self,force_reload=False):
        self._directory(self.directory)
        self._check(self.units_dir,True)
        body=f'[Unit]\n# CIVI device-wide mDNS switch\nConditionPathExists=!{self.flag}\n'.encode()
        changed=False
        for unit in UNITS:
            directory=self.units_dir/(unit+'.d')
            self._directory(directory)
            path=directory/'50-civi-mdns.conf'
            if path.exists() or path.is_symlink():
                self._check(path)
                if path.read_bytes()!=body: raise NetworkError('CIVI mDNS unit condition differs; inspect the Pi locally')
            else:
                # Exclusive creation never overwrites administrator configuration.
                with path.open('xb') as stream: stream.write(body)
                path.chmod(0o644); changed=True
        if changed or force_reload: self._command('daemon-reload')

    def _states(self):
        return {unit:self._command('show','--property=ActiveState','--value',unit) for unit in UNITS}

    def _stop(self):
        # Concurrent D-Bus activation can cancel an individual stop job. Stop
        # both paths regardless, then judge the observed states, not that job.
        for unit in reversed(UNITS): self._command('stop',unit,allow_failure=True)
        states=self._states()
        if any(value not in ('inactive','failed') for value in states.values()):
            raise NetworkError('Avahi did not stop')
        return states

    def _check_no_listener(self):
        for name in ('udp','udp6'):
            path=self.proc_dir/name
            if not path.exists() and name=='udp6': continue
            try: lines=path.read_text().splitlines()[1:]
            except OSError as error: raise NetworkError('Cannot verify mDNS UDP listeners') from error
            if any(line.split()[1].rsplit(':',1)[-1].upper()=='14E9' for line in lines if len(line.split())>1):
                raise NetworkError('Another UDP 5353 listener remains; device-wide mDNS disable is not verified')

    def set(self,enabled):
        if type(enabled) is not bool: raise ValueError('mDNS enabled must be boolean')
        was_disabled=self.disabled()
        if not enabled:
            self._install_conditions(force_reload=not was_disabled)
            if not was_disabled:
                descriptor,name=tempfile.mkstemp(prefix='.mdns-',dir=self.directory)
                try:
                    with os.fdopen(descriptor,'wb') as stream:
                        stream.write(b'CIVI mDNS disabled\n');stream.flush();os.fsync(stream.fileno())
                    os.replace(name,self.flag)
                finally: Path(name).unlink(missing_ok=True)
            states=self._states()
            if any(value not in ('inactive','failed') for value in states.values()):
                self._stop()
            states=self._states()
            if any(value not in ('inactive','failed') for value in states.values()):
                raise NetworkError('Avahi did not stop')
            self._check_no_listener()
        else:
            if was_disabled: self.flag.unlink()
            try:
                states=self._states()
                if any(value!='active' for value in states.values()): self._command('start',*UNITS)
                states=self._states()
                if any(value!='active' for value in states.values()): raise NetworkError('Avahi did not start')
            except Exception:
                if was_disabled:
                    descriptor=os.open(self.flag,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                    os.close(descriptor)
                    self._stop()
                raise
        return {'enabled':enabled,'provider':'Avahi','activation_blocked':not enabled,'units':states}
