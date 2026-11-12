"""LAN RESET from the Pi's attached console; never an HTTP operation."""
import argparse
import json
import os
from pathlib import Path
import platform
import secrets
import sys
import tempfile
import time
from .broker import BrokerClient, HelperUnavailable
from .network import NetworkError
from ..network import validate_settings


def local_path(config, name):
    return Path(config['network_settings_file']).with_name(name)


def write_private(path, data):
    path = Path(path)
    descriptor, name = tempfile.mkstemp(prefix='.civi-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(data, stream); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally: Path(name).unlink(missing_ok=True)


def read_private(path):
    path = Path(path)
    info = path.lstat()
    if path.is_symlink() or (os.name == 'posix' and (info.st_uid != os.geteuid() or info.st_mode & 0o077)):
        raise ValueError('CIVI recovery credentials must be owned by the CIVI user with mode 600')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('password'),str) or len(data['password']) < 12:
        raise ValueError('Invalid CIVI recovery credentials')
    return data


def read_recovery(config):
    if not config.get('pi_network',{}).get('enabled'): return None
    path = local_path(config, '.civi-lci.json')
    if not path.exists(): return None
    data = read_private(path)
    if not isinstance(data.get('revision'), str) or not data['revision']:
        raise ValueError('Invalid CIVI recovery revision')
    return data


def reload_recovery(config, credentials):
    recovery = read_recovery(config)
    revision = credentials.revision if hasattr(credentials,'reset_recovery') else credentials['revision']
    if not recovery or revision == recovery['revision']: return None
    saved = json.loads(Path(config['network_settings_file']).read_text(encoding='utf-8'))
    validate_settings(saved)
    config.update(saved)
    if hasattr(credentials,'reset_recovery'): credentials.reset_recovery(recovery)
    else: credentials.update(password=recovery['password'], revision=recovery['revision'])
    return recovery['revision']


def reset(config, helper, prompt=input, output=print, wait=12):
    """Confirm before changes; credentials are displayed only on the local console."""
    instructions = ('On the Pi, open the CIVI desktop shortcut and enter the Linux/sudo password if prompted. '
                    'Keep the CIVI LAN helper terminal open. Retry bash lan-reset.sh in a separate new terminal.')
    try:
        status = helper.request('status')
    except HelperUnavailable as error:
        raise NetworkError('Cannot connect to the CIVI LAN helper; LAN RESET has not started. '
                           'LAN RESET has not changed your LAN settings or Web password. ' + instructions) from error
    output('LAN RESET — local recovery')
    output(f"Wired interface: {status['interface']}; current IPv4: {status['snapshot']['active_ipv4'] or '(none)'}")
    output('Reset wired IPv4 to DHCP + AutoIP, clear manual gateway/DNS, enable Ping and CIVI discovery, and reset the CIVI Web password to the per-device recovery default.')
    output('The current wired IP will be lost. WLAN profiles and the user-configured hostname/service name are retained. Pending wired changes will be restored before resetting.')
    output('The Web password will be shown here. No radio command is sent. Auto-negotiation, firewall rules and IPv6 are outside this reset.')
    if prompt('Type LAN RESET to continue: ') != 'LAN RESET':
        output('Cancelled. No settings changed.'); return None
    default_path = local_path(config, '.civi-lci-default.json')
    if default_path.exists():
        password = read_private(default_path)['password']
    else:
        password = secrets.token_urlsafe(24)
        write_private(default_path, {'password':password})
    settings = {'description':config['description'], 'discovery':True}
    validate_settings(settings)
    write_private(local_path(config,'.civi-lci-backup.json'),
                  {'network':status['snapshot'], 'discovery':{k:config[k] for k in ('description','discovery')}})
    try:
        result = helper.request('initialize')
    except HelperUnavailable as error:
        raise NetworkError('Connection to the CIVI LAN helper was lost during LAN RESET. '
                           'Completion could not be verified; wired LAN settings may already have changed. '
                           'Inspect the current settings on the Pi. ' + instructions) from error
    if not result.get('initialized') or not result.get('ping_enabled'):
        raise NetworkError('LAN helper did not verify initialization')
    revision = secrets.token_hex(16)
    try:
        write_private(config['network_settings_file'], settings)
        write_private(local_path(config,'.civi-lci.json'), {'revision':revision, 'password':password})
    except OSError as error:
        raise NetworkError('Wired LAN was reset but CIVI settings could not be saved; inspect the Pi locally') from error
    if result.get('waiting_for_link'):
        output('Wired LAN recovery settings saved and verified. Reconnect the Ethernet cable; DHCP / AutoIP starts automatically. No address is ready yet.')
    else:
        output('Wired LAN initialized. IPv4: ' + (result['snapshot']['active_ipv4'] or 'Waiting for DHCP / AutoIP; use Read wired LAN to inspect later.'))
    output('Web username: admin')
    output('Web recovery password: ' + password)
    output('This recovery password is now authoritative, including after manual restarts; the previous password environment variable is overridden.')
    # A running app reloads locally saved recovery settings without a Web password.
    end = time.monotonic()+wait
    while time.monotonic() < end:
        try:
            applied=json.loads(local_path(config,'.civi-lci-applied.json').read_text(encoding='utf-8'))
            if applied.get('revision')==revision:
                if applied.get('error'):
                    raise NetworkError('Network and password reset saved; live discovery failed: '+applied['error'])
                output('Running CIVI updated its Web password and discovery settings.'); return result
        except (FileNotFoundError, json.JSONDecodeError): pass
        time.sleep(.2)
    output('Settings saved. Live CIVI update was not confirmed; a stopped CIVI loads them on its next manual start.')
    return result


def main():
    parser=argparse.ArgumentParser(description='LAN RESET from the Pi local keyboard/display')
    parser.add_argument('--config',default='config.toml')
    args=parser.parse_args()
    if platform.system()!='Linux': parser.exit(1,'LAN RESET requires the Raspberry Pi/Linux target.\n')
    if os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_TTY') or not sys.stdin.isatty():
        parser.exit(1,'Use LAN RESET from the Pi attached keyboard/display terminal, not SSH or redirected input.\n')
    if os.geteuid()==0: parser.exit(1,'Run as the normal CIVI user, without sudo. Start the LAN helper separately with sudo.\n')
    try:
        from ..config import load
        config=load(args.config)
        if not config['pi_network']['enabled']: raise ValueError('Pi LAN helper must be enabled')
        reset(config,BrokerClient(config['pi_network']['socket']))
    except (ValueError,NetworkError,OSError,EOFError,KeyboardInterrupt) as error:
        parser.exit(1,f'LAN RESET: {error}\n')


if __name__=='__main__': main()
