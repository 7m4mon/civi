"""Root-owned recovery target; never select an arbitrary inactive connection."""
import json
import os
from pathlib import Path
import stat
import tempfile
from .network import interface_name,profile_uuid,NetworkError


class RecoveryTarget:
    def __init__(self,interface,directory='/var/lib/civi',owner_uid=0):
        self.interface=interface_name(interface)
        self.directory=Path(directory)
        self.path=self.directory/('lan-'+self.interface+'.json')
        self.owner_uid=owner_uid

    def _check(self,path,directory=False):
        info=path.lstat()
        if (path.is_symlink() or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            or (os.name=='posix' and (info.st_uid!=self.owner_uid or info.st_mode & 0o022))):
            raise NetworkError('Unsafe recovery target file or directory')

    def load(self):
        if self.directory.exists(): self._check(self.directory,True)
        if not self.path.exists() and not self.path.is_symlink(): return None
        self._check(self.path)
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or set(data)!={'interface','uuid'} or data['interface']!=self.interface:
            raise NetworkError('Invalid wired recovery target')
        return profile_uuid(data['uuid'])

    def save(self,uuid):
        value=profile_uuid(uuid)
        self.directory.mkdir(mode=0o755,parents=True,exist_ok=True)
        self._check(self.directory,True)
        if self.path.exists() or self.path.is_symlink(): self._check(self.path)
        descriptor,name=tempfile.mkstemp(prefix='.lan-target-',dir=self.directory)
        try:
            with os.fdopen(descriptor,'w',encoding='utf-8') as stream:
                json.dump({'interface':self.interface,'uuid':value},stream);stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)
        finally: Path(name).unlink(missing_ok=True)
