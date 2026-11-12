"""Fixed Linux Ping responder setting used by the privileged LAN helper."""
from pathlib import Path
from .network import NetworkError


class PingResponder:
    def __init__(self, proc='/proc/sys/net/ipv4/icmp_echo_ignore_all', config='/etc/sysctl.d/90-civi-lan.conf'):
        self.proc, self.config = Path(proc), Path(config)

    def snapshot(self):
        if self.config.is_symlink(): raise NetworkError('CIVI sysctl settings must not be a symbolic link')
        return (self.proc.read_bytes(), self.config.read_bytes() if self.config.exists() else None)

    def _save(self, value):
        if self.config.is_symlink(): raise NetworkError('CIVI sysctl settings must not be a symbolic link')
        if value is None:
            self.config.unlink(missing_ok=True)
        else:
            # Write via an exclusive temporary file in the root-owned directory.
            import os, tempfile
            descriptor, name = tempfile.mkstemp(prefix='.civi-', dir=self.config.parent)
            try:
                with os.fdopen(descriptor, 'wb') as stream:
                    stream.write(value); stream.flush(); os.fsync(stream.fileno())
                os.chmod(name, 0o644)
                os.replace(name, self.config)
            finally: Path(name).unlink(missing_ok=True)

    def enable(self):
        return self.set(True)

    def status(self):
        runtime,saved=self.snapshot()
        value=runtime.strip()
        if value not in (b'0',b'1'): raise NetworkError('Unknown IPv4 Ping responder state')
        import re
        entries=re.findall(rb'^\s*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([01])\s*$',saved or b'',re.M)
        return {'enabled':value==b'0','saved_enabled':entries[-1]==b'0' if entries else None,
                'scope':'IPv4 on all Pi interfaces'}

    def set(self,enabled):
        if type(enabled) is not bool: raise ValueError('Ping enabled must be boolean')
        previous=self.snapshot()
        value=b'0' if enabled else b'1'
        try:
            self._save(b'# CIVI: persistent IPv4 Ping responder setting\nnet.ipv4.icmp_echo_ignore_all = '+value+b'\n')
            self.proc.write_bytes(value+b'\n')
            result=self.status()
            if result['enabled']!=enabled or result['saved_enabled']!=enabled:
                raise NetworkError('IPv4 Ping setting could not be verified')
            return {**result,'saved':True}
        except Exception as error:
            try: self.restore(previous)
            except Exception as restore_error:
                raise NetworkError('Ping change failed and restoration could not be verified; inspect the Pi locally') from restore_error
            raise NetworkError('Ping change failed; the previous setting was restored') from error

    def restore(self, previous):
        self._save(previous[1]); self.proc.write_bytes(previous[0])
        if self.snapshot()!=previous: raise NetworkError('Previous IPv4 Ping setting could not be restored')
