from pathlib import PurePosixPath
import shlex
from types import SimpleNamespace
import pytest
from civi.pi import desktop


def test_terminal_command_preserves_spaced_config_path_without_shell(monkeypatch,tmp_path):
    monkeypatch.setattr(desktop.shutil,'which',lambda name:'/usr/bin/lxterminal')
    config=tmp_path/'CIVI test'/'config.toml'
    command=desktop.terminal_command('CIVI server',config,'civi')
    arguments=shlex.split(command[2].removeprefix('--command='))
    assert arguments==[desktop.sys.executable,'-m','civi.pi.desktop','--config',str(config),'--component','civi']
    assert 'Terminal=true' in desktop.desktop_entry(PurePosixPath('/home/nom/CIVI test'))
    assert '"/home/nom/CIVI test/desktop.sh"' in desktop.desktop_entry(PurePosixPath('/home/nom/CIVI test'))


def test_repeated_launch_reuses_all_components_without_spawning(monkeypatch,tmp_path):
    monkeypatch.setenv('DISPLAY',':0')
    monkeypatch.setattr(desktop,'helper_ready',lambda config:True)
    monkeypatch.setattr(desktop,'civi_ready',lambda config:True)
    monkeypatch.setattr(desktop,'panel_pid',lambda path:123)
    from contextlib import nullcontext
    monkeypatch.setattr(desktop,'lock',lambda path:nullcontext())
    def forbidden(*args,**kwargs):raise AssertionError('Existing components must not be started again')
    monkeypatch.setattr(desktop.subprocess,'Popen',forbidden)
    desktop.launch({},tmp_path/'config.toml',tmp_path)


def test_panel_detection_matches_owner_and_config_not_other_checkouts(monkeypatch,tmp_path):
    monkeypatch.setattr(desktop.os,'getuid',lambda:1000,raising=False)
    def process(pid,owner,cwd):
        return SimpleNamespace(info={'pid':pid,'uids':SimpleNamespace(real=owner),'cwd':str(cwd),
            'cmdline':['python','-u','-m','civi.pi.panel','--config','config.toml']})
    monkeypatch.setattr(desktop.psutil,'process_iter',lambda *args:[process(1,1001,tmp_path),process(2,1000,tmp_path/'other'),process(3,1000,tmp_path)])
    assert desktop.panel_pid(tmp_path/'config.toml')==3


def test_other_instrument_on_scpi_port_is_not_reused():
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def settimeout(self,*args):pass
        def sendall(self,data):assert data==b'*IDN?\n'
        def makefile(self,*args):
            from io import BytesIO
            return BytesIO(b'Other,Instrument,ABC,1\n')
    from unittest.mock import patch
    with patch.object(desktop.socket,'create_connection',return_value=Connection()):
        with pytest.raises(RuntimeError,match='another instrument'):
            desktop.civi_ready({'bind':'0.0.0.0','scpi_port':5025,'manufacturer':'CIVI Project','serial_number':'CIVI-0001'})


def test_ctrl_c_allows_component_cleanup_instead_of_killing_child(monkeypatch,tmp_path):
    from contextlib import nullcontext
    monkeypatch.setattr(desktop,'lock',lambda path:nullcontext())
    monkeypatch.setattr(desktop,'civi_ready',lambda config:False)
    waits=[]
    class Child:
        def wait(self,timeout=None):
            waits.append(timeout)
            if len(waits)==1:raise KeyboardInterrupt
            return 0
    monkeypatch.setattr(desktop.subprocess,'Popen',lambda args:Child())
    desktop.component('civi',{},tmp_path/'config.toml',tmp_path)
    assert waits==[None,20]
