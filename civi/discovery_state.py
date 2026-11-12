"""Desired and acquired discovery names, separate from user settings."""
import json
import os
from pathlib import Path
import re
import tempfile


def names(desired, acquired=None):
    """Stream collision candidates without a fixed retry count or growing history."""
    initial = {name for name in (acquired, desired) if name}
    if acquired:
        yield acquired
    if desired and desired != acquired:
        yield desired
    number = 2
    while True:
        suffix = f' ({number})'
        if len(suffix) > 63:
            # DNS labels have finite space. Recheck candidates if that space
            # ever wraps, rather than emit an invalid label or stop retrying.
            number = 2
            continue
        candidate = desired.encode('utf-8')[:63-len(suffix)].decode('utf-8',errors='ignore')+suffix
        if candidate not in initial:
            yield candidate
        number += 1


def state_path(config):
    path=config.get('network_settings_file')
    return Path(path).with_name('.civi-discovery.json') if path else None


def load_names(config, hostname, description):
    path=state_path(config)
    if path is None or not path.exists(): return None
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('version')!=1: raise ValueError('Invalid saved discovery names')
    if (data.get('desired_hostname'),data.get('desired_service'),data.get('reset_revision')) != (
        hostname,description,config.get('discovery_reset_revision')): return None
    host,service=data.get('hostname'),data.get('service')
    if (not isinstance(host,str) or not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?',host)
        or not isinstance(service,str) or not service.strip() or len(service.encode())>63
        or any(ord(c)<32 for c in service)):
        raise ValueError('Invalid saved discovery names')
    return data


def save_names(config, desired_host, desired_service, host, service):
    path=state_path(config)
    if path is None: return
    data={'version':1,'desired_hostname':desired_host,'desired_service':desired_service,
          'hostname':host,'service':service,'reset_revision':config.get('discovery_reset_revision')}
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))==data: return
    fd,name=tempfile.mkstemp(prefix='.civi-discovery-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
        os.chmod(name,0o600);os.replace(name,path)
    finally: Path(name).unlink(missing_ok=True)
