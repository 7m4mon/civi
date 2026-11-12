"""Persistent Web password hashes, with local LAN RESET taking precedence."""
import hashlib
import hmac
import json
import os
import secrets
import threading
from .pi.lci import local_path, read_recovery, write_private

ITERATIONS = 600000


def validate_password(new, confirmation):
    if (not isinstance(new,str) or not 12<=len(new)<=256 or
        any(ord(c)<32 or ord(c)==127 for c in new)):
        raise ValueError('New password must contain 12–256 characters and no control characters')
    if not isinstance(confirmation,str) or new != confirmation:
        raise ValueError('New passwords do not match')


def password_record(new, revision):
    salt=secrets.token_bytes(16)
    return {'version':1,'iterations':ITERATIONS,'salt':salt.hex(),
            'digest':hashlib.pbkdf2_hmac('sha256',new.encode(),salt,ITERATIONS).hex(),
            'recovery_revision':revision}


def save_local_password(config, new, confirmation):
    """Trusted local administration; no network or old password is needed."""
    validate_password(new,confirmation)
    recovery=read_recovery(config)
    revision=recovery['revision'] if recovery else None
    write_private(local_path(config,'.civi-web-auth.json'),password_record(new,revision))


def load_record(config, revision):
    path = local_path(config, '.civi-web-auth.json')
    if not path.exists(): return None
    info = path.lstat()
    if path.is_symlink() or (os.name == 'posix' and (info.st_uid != os.geteuid() or info.st_mode & 0o077)):
        raise ValueError('Saved Web credentials must belong to the CIVI user with mode 600')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict): raise ValueError('Invalid saved Web credentials')
    if data.get('recovery_revision') != revision: return None
    if (data.get('version') != 1 or data.get('iterations') != ITERATIONS or
        not isinstance(data.get('salt'),str) or len(data['salt']) != 32 or
        not isinstance(data.get('digest'),str) or len(data['digest']) != 64):
        raise ValueError('Invalid saved Web credentials')
    try: bytes.fromhex(data['salt']); bytes.fromhex(data['digest'])
    except ValueError as error: raise ValueError('Invalid saved Web credentials') from error
    return data


def has_saved_password(config):
    recovery = read_recovery(config)
    return bool(recovery or load_record(config, recovery['revision'] if recovery else None))


class PasswordStore:
    def __init__(self, config, environment_password):
        self.config = config
        self.lock = threading.RLock()
        self.cache_key = secrets.token_bytes(32)
        self.verified = None
        recovery = read_recovery(config)
        self.recovery_revision = recovery['revision'] if recovery else None
        self.revision = None # monitor acknowledgement, separate from the credential's reset generation
        self.password = recovery['password'] if recovery else environment_password
        self.record = load_record(config, self.recovery_revision)
        if not self.record and len(self.password) < 12:
            raise ValueError('Set password environment variable to at least 12 characters')
        self.saved = bool(self.record or recovery)

    def verify(self, supplied):
        if not isinstance(supplied,str) or len(supplied)>256: return False
        with self.lock:
            if self.record:
                token=hmac.digest(self.cache_key,supplied.encode(),'sha256')
                if self.verified and hmac.compare_digest(token,self.verified): return True
                digest=hashlib.pbkdf2_hmac('sha256',supplied.encode(),bytes.fromhex(self.record['salt']),ITERATIONS)
                valid=hmac.compare_digest(digest.hex(),self.record['digest'])
                if valid: self.verified=token
                return valid
            return hmac.compare_digest(supplied.encode(),self.password.encode())

    def change(self, current, new, confirmation):
        validate_password(new,confirmation)
        with self.lock:
            if not self.verify(current): raise PermissionError('Current Web password is no longer valid')
            record=password_record(new,self.recovery_revision)
            write_private(local_path(self.config,'.civi-web-auth.json'),record)
            self.record=record
            self.verified=None
            self.password='' # do not retain the new password in plaintext
            self.saved=True

    def refresh_saved(self):
        with self.lock:
            record=load_record(self.config,self.recovery_revision)
            # Removing a file must not enable an empty/fallback password in a
            # process whose plaintext password was discarded after a Web change.
            if record is None or record==self.record: return False
            self.record=record
            self.verified=None
            self.password=''
            self.saved=True
            return True

    def reset_recovery(self, recovery):
        with self.lock:
            revision = recovery['revision']
            self.record=load_record(self.config,revision)
            self.verified=None
            self.password=recovery['password']
            self.recovery_revision=revision
            self.revision=revision
            self.saved=True
