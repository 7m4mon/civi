"""Reset only Web credentials from the attached Pi console."""
import argparse
import getpass
import os
import platform
import sys
from ..auth import save_local_password


def reset_password(config, prompt=input, read_password=getpass.getpass, output=print):
    output('WEB PASSWORD RESET — local administration')
    output('Set a new CIVI Web password without the previous password. LAN/IP, hostname, discovery and device recovery defaults are retained.')
    if prompt('Type PASSWORD RESET to continue: ') != 'PASSWORD RESET':
        output('Cancelled. No settings changed.'); return False
    new=read_password('New CIVI Web password (12–256 characters): ')
    confirmation=read_password('Confirm new password: ')
    save_local_password(config,new,confirmation)
    output('Web password saved. Username: admin. Updated running CIVI reloads it within about 5 seconds; a stopped CIVI uses it on its next manual start.')
    return True


def main():
    parser=argparse.ArgumentParser(description='Reset only the CIVI Web password from the Pi attached console')
    parser.add_argument('--config',default='config.toml')
    args=parser.parse_args()
    if platform.system()!='Linux': parser.exit(1,'Use this command on the Pi/Linux target.\n')
    if os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_TTY') or not sys.stdin.isatty():
        parser.exit(1,'Use the Pi attached keyboard/display terminal, not SSH or redirected input.\n')
    if os.geteuid()==0: parser.exit(1,'Run as the normal CIVI user, without sudo.\n')
    try:
        from ..config import load
        reset_password(load(args.config))
    except (ValueError,OSError,EOFError,KeyboardInterrupt) as error:
        parser.exit(1,f'WEB PASSWORD RESET: {error}\n')


if __name__=='__main__': main()
