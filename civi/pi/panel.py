"""Manual local LAN/Identify display. No Web password, sudo or GPIO needed."""
import argparse
import json
import os
import platform
import queue
import re
import socket
import subprocess
import tempfile
import threading
import time
from ..indicator import PiLanReader, panel_path


def create_root(tk):
    """Keep an existing desktop cookie usable after a live hostname change."""
    display = re.fullmatch(r':(\d+)(?:\.\d+)?', os.environ.get('DISPLAY', ''))
    if not display:
        return tk.Tk()
    try:
        result = subprocess.run(['xauth', 'nlist'], capture_output=True, text=True,
                                check=True, timeout=3)
        records = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if (len(fields) == 9 and fields[0] == '0100'
                    and bytes.fromhex(fields[4]).decode() == display[1]
                    and bytes.fromhex(fields[6]) == b'MIT-MAGIC-COOKIE-1'):
                records.append((line, bytes.fromhex(fields[2]).decode()))
        if len(records) != 1 or records[0][1] == socket.gethostname():
            return tk.Tk()
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return tk.Tk()
    # Only the client's lookup family changes. The server still requires the
    # same secret cookie; its authority file and access controls are untouched.
    previous = os.environ.get('XAUTHORITY')
    with tempfile.TemporaryDirectory(prefix='civi-panel-auth-') as directory:
        path = os.path.join(directory, 'authority')
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        try:
            subprocess.run(['xauth', '-f', path, 'nmerge', '-'],
                           input='ffff' + records[0][0][4:] + '\n',
                           capture_output=True, text=True, check=True, timeout=3)
            os.environ['XAUTHORITY'] = path
            return tk.Tk()
        except (OSError, subprocess.SubprocessError):
            os.environ.pop('XAUTHORITY', None)
            if previous is not None:
                os.environ['XAUTHORITY'] = previous
            return tk.Tk()
        finally:
            if previous is None:
                os.environ.pop('XAUTHORITY', None)
            else:
                os.environ['XAUTHORITY'] = previous


def request(path, operation):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        connection.connect(str(path))
        connection.sendall(json.dumps(operation).encode()+b'\n')
        with connection.makefile('rb') as stream: data=stream.readline(16385)
    if len(data)>16384 or not data.endswith(b'\n'): raise ValueError('Invalid local panel response')
    result=json.loads(data)
    if not result.get('ok'): raise ValueError('Local display request failed')
    return result


class Panel:
    def __init__(self, root, config):
        import tkinter as tk
        self.root=root; self.path=panel_path(config)
        self.config=config
        self.done=threading.Event(); self.stop_requested=threading.Event()
        self.updates=queue.Queue(maxsize=1)
        self.visible=False; self.showing=False; self.current=None
        root.title('CIVI — local LAN status / Identify')
        root.geometry('900x560'); root.minsize(650,460); root.configure(bg='#10191e')
        self.banner=tk.Label(root,text='LAN',font=('DejaVu Sans',30,'bold'),pady=18,bg='#44515a',fg='white')
        self.banner.pack(fill='x')
        tk.Label(root,text='POWER ON',font=('DejaVu Sans',12,'bold'),
                 bg='#10191e',fg='#74d6a0',anchor='w',padx=24).pack(fill='x')
        self.device=tk.Label(root,font=('DejaVu Sans',17),bg='#10191e',fg='#dce8ed',justify='left',anchor='w',padx=24,pady=18)
        self.device.pack(fill='x')
        self.network=tk.Label(root,font=('DejaVu Sans',21),bg='#10191e',fg='#dce8ed',justify='left',anchor='w',padx=24)
        self.network.pack(fill='x')
        self.notice=tk.Label(root,font=('DejaVu Sans',13),bg='#10191e',fg='#e8c080',wraplength=830,justify='left',anchor='w',padx=24,pady=16)
        self.notice.pack(fill='x')
        tk.Button(root,text='Stop Identify',font=('DejaVu Sans',14),command=self.stop_requested.set).pack(pady=8)
        tk.Label(root,text='Keep this window visible on the Pi. F11: fullscreen · Esc: leave fullscreen',
                 font=('DejaVu Sans',11),bg='#10191e',fg='#8ca5b1').pack(side='bottom',pady=14)
        root.bind('<F11>',lambda _:root.attributes('-fullscreen',not root.attributes('-fullscreen')))
        root.bind('<Escape>',lambda _:root.attributes('-fullscreen',False))
        root.protocol('WM_DELETE_WINDOW',self.close)
        threading.Thread(target=self.poll,daemon=True).start()
        self.paint()

    def poll(self):
        reader=PiLanReader(self.config.get('pi_network',{}).get('interface','eth0'))
        while not self.done.is_set():
            try:
                if self.stop_requested.is_set():
                    request(self.path,{'op':'stop_identify'}); self.stop_requested.clear()
                packet=request(self.path,{'op':'status','visible':self.visible,'showing':self.showing})
                packet['online']=True
            except (OSError,ValueError):
                try: observation=reader()
                except Exception:
                    observation={'interface':reader.interface,'hostname':None,'addresses':[], 'link':False}
                packet={'online':False,'status':{**observation,'state':'unknown','identify':False,
                        'faults':['CIVI is unavailable. Start CIVI manually.']},'device':{}}
            try: self.updates.get_nowait()
            except queue.Empty: pass
            self.updates.put_nowait(packet)
            self.done.wait(1)

    def paint(self):
        if self.done.is_set(): return
        try: self.current=self.updates.get_nowait()
        except queue.Empty: pass
        self.visible=bool(self.root.winfo_viewable() and self.root.state()!='iconic')
        packet=self.current
        if packet:
            state=packet['status']; device=packet['device']
            self.showing=bool(packet['online'] and state['state']=='normal' and state['identify'])
            color={'normal':'#216542','fault':'#9d3037','unknown':'#695322'}.get(state['state'],'#695322')
            title='LAN '+state['state'].upper()
            if self.showing:
                color='#216542' if int(time.monotonic()*2)%2 else '#132e22'
                title='IDENTIFY — THIS CIVI DEVICE'
            elif not packet['online']: title='CIVI OFFLINE'
            self.banner.configure(bg=color,text=title)
            self.device.configure(text=f"{device.get('Model','CIVI')}   {device.get('SerialNumber','')}   Radio: {device.get('radio','unavailable')}\nHostname: {state.get('hostname') or 'Unknown'}   mDNS: {device.get('mdns_hostname') or 'Inactive'}")
            addresses=', '.join(state.get('addresses',[])) or '(no IPv4 address)'
            self.network.configure(text=f"{state['interface']}  ·  {'Link up' if state.get('link') else 'Link down'}\nIPv4: {addresses}\nMAC: {state.get('mac') or 'Unknown'}")
            faults=state.get('faults',[])
            self.notice.configure(text='\n'.join(faults) if faults else 'LAN has a usable IPv4 address. Identify keeps flashing until stopped.')
        self.root.after(250,self.paint)

    def close(self):
        self.done.set(); self.root.destroy()


def main():
    parser=argparse.ArgumentParser(description='CIVI local LAN status and Identify display')
    parser.add_argument('--config',default='config.toml')
    args=parser.parse_args()
    if platform.system()!='Linux': parser.exit(1,'Run the local panel on the Pi/Linux desktop.\n')
    try:
        import tkinter as tk
    except ImportError: parser.exit(1,'Tk is unavailable. Install python3-tk on the Pi.\n')
    from ..config import load
    try:
        config=load(args.config)
        if not config.get('pi_network',{}).get('enabled'):
            raise ValueError('Enable pi_network in config.toml and restart CIVI to use the local panel')
        root=create_root(tk)
    except (OSError,ValueError,tk.TclError) as error:
        parser.exit(1,f'Local panel could not start: {error}\nRun panel.sh from the Pi desktop terminal.\n')
    print('CIVI local LAN panel started; keep its window visible. Close the window to stop.',flush=True)
    Panel(root,config)
    root.mainloop()


if __name__=='__main__': main()
