import os
import socket
import ssl
import subprocess
import sys
import time
import urllib.request
import json
import pytest
from pathlib import Path
from civi.tls import generate


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]


@pytest.mark.parametrize("radio_available", [True, False])
def test_production_entrypoint_mock_https_and_tcp(tmp_path, radio_available):
    generate(tmp_path / "certs", [])
    scpi,web=free_port(),free_port()
    config=Path("config.example.toml").read_text().replace('"0.0.0.0"','"127.0.0.1"').replace('scpi_port = 5025',f'scpi_port = {scpi}').replace('web_port = 8443',f'web_port = {web}').replace('discovery = true','discovery = false')
    if not radio_available:
        # A nonexistent serial path, never the user's real COM port.
        config = config.replace('backend = "mock"', 'backend = "civ"').replace('"COM3"', json.dumps(str(tmp_path / 'missing-serial-device')))
    path=tmp_path / "config.toml"
    path.write_text(config)
    env={**os.environ,"CIVI_PASSWORD":"mock-startup-test-password"}
    proc=subprocess.Popen([sys.executable,"-m","civi","--config",str(path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+10
        while True:
            assert proc.poll() is None, proc.communicate()
            try:
                connection=socket.create_connection(("127.0.0.1",scpi),timeout=0.2)
                break
            except OSError:
                if time.monotonic()>deadline: raise
                time.sleep(0.05)
        with connection:
            connection.settimeout(2)
            connection.sendall(b"*IDN?\n")
            expected_model = b'IC-7300' if radio_available else b'Unknown'
            assert connection.recv(1024) == b'CIVI Project,CIVI/' + expected_model + b',CIVI-0001,0.1.0\n'
        ctx=ssl.create_default_context(cafile=str(tmp_path/"certs/cert.pem"))
        with urllib.request.urlopen(f"https://127.0.0.1:{web}/",context=ctx,timeout=3) as response:
            assert response.status==200
            assert b"CIVI" in response.read()
        if not radio_available:
            time.sleep(2.3) # Allow the background radio probe to fail.
        with urllib.request.urlopen(f"https://127.0.0.1:{web}/health",context=ctx,timeout=3) as response:
            health=json.load(response)
            assert health == {"gateway":"online", "radio":"connected" if radio_available else "disconnected", "ready":radio_available}
        assert proc.poll() is None
    finally:
        proc.terminate()
        proc.communicate(timeout=5)
