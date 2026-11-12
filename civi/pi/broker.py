"""Manually started privileged LAN helper. No TCP listener or service install."""
import argparse
import json
import logging
import os
from pathlib import Path
import socket
import socketserver
import signal
import stat
import sys
import time
from .. import __version__, __author__
from .network import NetworkError
from .transactions import Transactions

MAX_MESSAGE = 16384
LOGGER = logging.getLogger('civi.lan-helper')


class ActivityLog:
    """Log useful state changes, without dumping requests or transaction tokens."""
    def __init__(self):
        self.started = time.monotonic()
        self.requests = 0
        self.last_state = None
        self.last_mdns = None

    def state(self, result):
        snapshot = result.get('snapshot')
        if not snapshot: return
        pending = result.get('pending')
        previous = result.get('last_result') or {}
        state = (snapshot.get('hostname'), snapshot.get('active_ipv4'),
                 snapshot.get('profile',{}).get('ipv4.method'), bool(pending), previous.get('state'))
        if state != self.last_state:
            LOGGER.info('State | hostname=%s | IPv4=%s | method=%s | pending=%s | last=%s',
                        state[0], (state[1] or '(none)').replace('\n', ', '), state[2], state[3], state[4] or '-')
            self.last_state = state

    def request(self, transactions, message):
        operation = message.get('op') if isinstance(message, dict) else None
        label = operation if operation in ('status','preview','apply','confirm','rollback','hostname','mdns_hostname','mdns','ping','ping_status','initialize','conflict_status') else 'invalid'
        self.requests += 1
        log = LOGGER.debug if label in ('status','mdns','ping_status','conflict_status') else LOGGER.info
        started = time.monotonic()
        log('Request: %s', label)
        try:
            result = dispatch(transactions, message)
        except Exception as error:
            LOGGER.warning('Request %s failed: %s', label, error)
            raise
        log('Completed: %s (%.2f s)', label, time.monotonic()-started)
        if label=='mdns' and result.get('enabled') != self.last_mdns:
            LOGGER.info('Device mDNS %s | Avahi activation %s',
                        'enabled' if result['enabled'] else 'disabled',
                        'allowed' if result['enabled'] else 'blocked')
            self.last_mdns=result['enabled']
        self.state(result)
        return result

    def heartbeat(self):
        LOGGER.info('Alive; waiting for local requests | uptime=%ds | requests=%d',
                    int(time.monotonic()-self.started), self.requests)


def dispatch(transactions, message):
    if not isinstance(message, dict): raise ValueError('Expected JSON object')
    op = message.get('op')
    allowed = {'status':{'op'},'preview':{'op','settings'},'apply':{'op','settings','timeout'},
               'confirm':{'op','token'},'rollback':{'op','token'},'hostname':{'op','hostname'},'mdns_hostname':{'op','hostname'},'mdns':{'op','enabled'},'ping':{'op','enabled'},'ping_status':{'op'},'initialize':{'op'},'conflict_status':{'op'}}
    if op not in allowed or set(message) != allowed[op]: raise ValueError('Invalid helper request')
    if op == 'status': return {**transactions.status(), 'helper_pid':os.getpid()}
    if op == 'conflict_status':
        result=transactions.conflict_guard.snapshot()
        routing=getattr(transactions,'linklocal_routes',None)
        if routing:
            status=routing.snapshot();result['autoip_routing']=status
            if not status['running'] or status['error'] or status['sample_age_seconds'] is None or status['sample_age_seconds']>20:
                result['error']=status['error'] or 'AutoIP routing monitor unavailable or stale'
        return result
    if op == 'preview': return transactions.preview(message['settings'])
    if op == 'apply': return transactions.apply(message['settings'], message['timeout'])
    if op == 'confirm':
        guard=getattr(transactions,'conflict_guard',None)
        if guard:
            with transactions.lock:
                result=transactions.confirm(message['token']);guard.clear()
                return result
        return transactions.confirm(message['token'])
    if op == 'hostname': return transactions.hostname(message['hostname'])
    if op == 'mdns_hostname': return transactions.mdns_hostname(message['hostname'])
    if op == 'mdns': return transactions.mdns_enabled(message['enabled'])
    if op == 'ping': return transactions.ping_enabled(message['enabled'])
    if op == 'ping_status': return transactions.ping_status()
    if op == 'initialize':
        guard=getattr(transactions,'conflict_guard',None)
        if guard:
            with transactions.lock:
                result=transactions.initialize();guard.clear()
                return result
        return transactions.initialize()
    return transactions.rollback(message['token'])


class HelperUnavailable(NetworkError):
    """The local helper transport failed, distinct from a rejected operation."""


class BrokerClient:
    def __init__(self, path): self.path = str(path)

    def request(self, op, **values):
        message = json.dumps({'op':op, **values}).encode()+b'\n'
        if len(message)>MAX_MESSAGE: raise ValueError('Helper request too large')
        try:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(50)
                connection.connect(self.path)
                connection.sendall(message)
                with connection.makefile('rb') as stream: raw = stream.readline(MAX_MESSAGE+1)
        except OSError as error: raise HelperUnavailable('LAN helper unavailable; start it manually on the Pi') from error
        if len(raw)>MAX_MESSAGE or not raw.endswith(b'\n'): raise NetworkError('Invalid LAN helper response')
        response = json.loads(raw)
        if not response.get('ok'): raise NetworkError(response.get('error','LAN helper failed'))
        return response['result']


def main():
    import pwd
    parser = argparse.ArgumentParser(description='CIVI wired LAN helper (manual foreground process)')
    parser.add_argument('--interface', default='eth0')
    parser.add_argument('--profile-uuid', help='Explicit wired recovery profile UUID; otherwise reuse the root-owned target')
    parser.add_argument('--owner', required=True, help='Local CIVI user allowed to access this socket')
    parser.add_argument('--socket', default='/run/civi-lan/control.sock')
    parser.add_argument('--verbose', action='store_true', help='Also log every status request')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, stream=sys.stdout,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%H:%M:%S')
    LOGGER.info('CIVI LAN helper %s | Author: %s | PID: %s', __version__, __author__, os.getpid())
    if os.geteuid() != 0: parser.exit(1,'Start this dedicated helper with sudo; run CIVI itself as the normal user.\n')
    owner = pwd.getpwnam(args.owner)
    path = Path(args.socket)
    # The root-owned directory prevents a local user replacing the privileged socket.
    path.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
    info = path.parent.lstat()
    if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
        parser.exit(1,'Socket directory must be root-owned and not writable by other users.\n')
    if path.exists() or path.is_symlink(): parser.exit(1,'Socket already exists; do not replace an active helper.\n')
    from .target import RecoveryTarget
    from .network import NetworkManager
    target=RecoveryTarget(args.interface)
    try:
        selected=args.profile_uuid or target.load()
        manager=NetworkManager(selected_uuid=selected)
        initial=manager.snapshot(args.interface)
        target.save(initial['uuid'])
        LOGGER.info('Wired recovery target: %s | active=%s | saved=%s',initial['uuid'],initial['profile_active'],target.path)
    except (ValueError,NetworkError,OSError) as error:
        parser.exit(1,f'Cannot establish wired recovery target: {error}\nStart once with the intended wired profile active, or specify --profile-uuid.\n')
    transactions = Transactions(args.interface,manager=manager)
    from .conflict import ConflictGuard
    guard=ConflictGuard(args.interface,transactions)
    transactions.conflict_guard=guard
    from .linklocal import LinkLocalRoutes
    routing=LinkLocalRoutes(args.interface,transactions,directory=path.parent)
    transactions.linklocal_routes=routing
    def stop_requested(*args):raise KeyboardInterrupt
    signal.signal(signal.SIGHUP,stop_requested)
    signal.signal(signal.SIGTERM,stop_requested)
    activity = ActivityLog()
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(5)
            try:
                raw = self.rfile.readline(MAX_MESSAGE+1)
                if len(raw)>MAX_MESSAGE or not raw.endswith(b'\n'): raise ValueError('Invalid request length')
                result = {'ok':True, 'result':activity.request(transactions,json.loads(raw))}
            except (ValueError, NetworkError, KeyError, TypeError) as error:
                # Invalid JSON/length fails before the request logger can run.
                if isinstance(error, json.JSONDecodeError): LOGGER.warning('Rejected invalid request JSON')
                result = {'ok':False,'error':str(error)}
            except (TimeoutError, ConnectionError) as error:
                LOGGER.warning('Local request connection failed: %s', type(error).__name__)
                return
            except Exception:
                LOGGER.error('Internal LAN helper failure')
                result = {'ok':False,'error':'Internal LAN helper failure'}
            try: self.wfile.write(json.dumps(result).encode()+b'\n')
            except (BrokenPipeError, ConnectionResetError): LOGGER.warning('Client disconnected before receiving the result')
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
        next_heartbeat = time.monotonic()+60
        def service_actions(self):
            if time.monotonic() >= self.next_heartbeat:
                activity.heartbeat()
                self.next_heartbeat = time.monotonic()+60
    previous_umask = os.umask(0o077)
    try:
        with Server(str(path), Handler) as server:
            os.chown(path,owner.pw_uid,owner.pw_gid)
            os.chmod(path,0o600)
            guard.start()
            routing.start()
            LOGGER.info('Interface: %s | Socket: %s | Allowed user: %s (mode 600)', args.interface, path, args.owner)
            try: activity.state(transactions.status())
            except Exception as error: LOGGER.warning('Initial LAN state unavailable: %s', error)
            LOGGER.info('Ready; waiting for local requests. Heartbeat every 60 seconds. Ctrl+C to stop. No automatic startup.')
            try: server.serve_forever(poll_interval=.2)
            except KeyboardInterrupt: pass
            finally:
                LOGGER.info('Stopping LAN helper')
                with transactions.lock:
                    if transactions.pending:
                        LOGGER.info('Restoring unconfirmed LAN settings before shutdown')
                        try:
                            activity.state(transactions.rollback(transactions.pending['token']))
                            LOGGER.info('Shutdown rollback verified')
                        except Exception: LOGGER.error('Rollback could not be verified; NetworkManager deadline remains the fallback.')
    finally:
        try:routing.close()
        except Exception as error:LOGGER.error('AutoIP routing cleanup needs inspection: %s',error)
        guard.close()
        os.umask(previous_umask)
        path.unlink(missing_ok=True)
        LOGGER.info('LAN helper stopped; socket removed')


if __name__ == '__main__': main()
