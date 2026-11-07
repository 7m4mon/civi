"""Manually started privileged LAN helper. No TCP listener or service install."""
import argparse
import json
import os
from pathlib import Path
import socket
import socketserver
import stat
from .network import NetworkError
from .transactions import Transactions

MAX_MESSAGE = 16384


def dispatch(transactions, message):
    if not isinstance(message, dict): raise ValueError('Expected JSON object')
    op = message.get('op')
    allowed = {'status':{'op'},'preview':{'op','settings'},'apply':{'op','settings','timeout'},
               'confirm':{'op','token'},'rollback':{'op','token'}}
    if op not in allowed or set(message) != allowed[op]: raise ValueError('Invalid helper request')
    if op == 'status': return {**transactions.status(), 'helper_pid':os.getpid()}
    if op == 'preview': return transactions.preview(message['settings'])
    if op == 'apply': return transactions.apply(message['settings'], message['timeout'])
    if op == 'confirm': return transactions.confirm(message['token'])
    return transactions.rollback(message['token'])


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
        except OSError as error: raise NetworkError('LAN helper unavailable; start it manually on the Pi') from error
        if len(raw)>MAX_MESSAGE or not raw.endswith(b'\n'): raise NetworkError('Invalid LAN helper response')
        response = json.loads(raw)
        if not response.get('ok'): raise NetworkError(response.get('error','LAN helper failed'))
        return response['result']


def main():
    import pwd
    parser = argparse.ArgumentParser(description='CIVI wired LAN helper (manual foreground process)')
    parser.add_argument('--interface', default='eth0')
    parser.add_argument('--owner', required=True, help='Local CIVI user allowed to access this socket')
    parser.add_argument('--socket', default='/run/civi-lan/control.sock')
    args = parser.parse_args()
    if os.geteuid() != 0: parser.exit(1,'Start this dedicated helper with sudo; run CIVI itself as the normal user.\n')
    owner = pwd.getpwnam(args.owner)
    path = Path(args.socket)
    # The root-owned directory prevents a local user replacing the privileged socket.
    path.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
    info = path.parent.lstat()
    if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
        parser.exit(1,'Socket directory must be root-owned and not writable by other users.\n')
    if path.exists() or path.is_symlink(): parser.exit(1,'Socket already exists; do not replace an active helper.\n')
    transactions = Transactions(args.interface)
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(5)
            raw = self.rfile.readline(MAX_MESSAGE+1)
            try:
                if len(raw)>MAX_MESSAGE or not raw.endswith(b'\n'): raise ValueError('Invalid request length')
                result = {'ok':True, 'result':dispatch(transactions,json.loads(raw))}
            except (ValueError, NetworkError, KeyError, TypeError) as error:
                result = {'ok':False,'error':str(error)}
            except Exception:
                result = {'ok':False,'error':'Internal LAN helper failure'}
            try: self.wfile.write(json.dumps(result).encode()+b'\n')
            except (BrokenPipeError, ConnectionResetError): pass
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True
    previous_umask = os.umask(0o077)
    try:
        with Server(str(path), Handler) as server:
            os.chown(path,owner.pw_uid,owner.pw_gid)
            os.chmod(path,0o600)
            print(f'CIVI LAN helper: {args.interface}, socket {path}; Ctrl+C to stop. No automatic startup.',flush=True)
            try: server.serve_forever(poll_interval=.2)
            except KeyboardInterrupt: pass
            finally:
                with transactions.lock:
                    if transactions.pending:
                        try: transactions.rollback(transactions.pending['token'])
                        except Exception: print('Rollback could not be verified; NetworkManager deadline remains the fallback.',flush=True)
    finally:
        os.umask(previous_umask)
        path.unlink(missing_ok=True)


if __name__ == '__main__': main()
