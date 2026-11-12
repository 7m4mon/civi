"""Typed constructor options and release-artifact corruption detection."""

import importlib.util
from pathlib import Path
import tomllib
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_typed_options_no_network(driver_module, monkeypatch):
    import socket
    def no_socket(*args, **kwargs):
        raise AssertionError('Typed simulation attempted network I/O')
    monkeypatch.setattr(socket, 'create_connection', no_socket)
    options = driver_module.DriverOptions(simulate=True, query_instrument_status=True)
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options=options) as d:
        assert d.ivi_utility.simulation_enabled
        assert d.ivi_utility.query_instrument_status_enabled
        options['simulate'] = False  # Constructor copies options, without a mutable shared setting.
        assert d.ivi_utility.simulation_enabled
        assert d.radio.frequency_hz == 14100000


def test_release_docs_synchronized():
    tool = load_tool('python_driver_release_docs')
    for path, expected in tool.render().items():
        assert path.read_text(encoding='utf-8') == expected


@pytest.mark.parametrize('corruption', [None, 'version', 'typing', 'compliance', 'identity'])
def test_wheel_metadata_and_document_integrity(tmp_path, corruption):
    tool = load_tool('python_driver_artifact_check')
    project = tomllib.loads((tool.PACKAGE / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    version = '99.0.0' if corruption == 'version' else project['version']
    keywords = 'wrong' if corruption == 'identity' else 'CIVI Project,CIVI/IC-7300,SCPI'
    readme = (tool.PACKAGE / 'README.md').read_text(encoding='utf-8')
    metadata = (f"Metadata-Version: 2.4\nName: {project['name']}\nVersion: {version}\n"
                f"Requires-Python: {project['requires-python']}\nKeywords: {keywords}\n\n" + readme)
    wheel = tmp_path / 'fixture.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('civi_ic7300.dist-info/METADATA', metadata)
        for file in tool.SOURCE.iterdir():
            if not file.is_file() or file.suffix not in ('.py', '.md', '.json') and file.name != 'py.typed':
                continue
            if corruption == 'typing' and file.name == 'py.typed':
                continue
            data = file.read_bytes()
            if corruption == 'compliance' and file.name == 'README.md':
                data = b'Broken README without compliance text'
            archive.writestr('civi_ic7300/' + file.name, data)
    if corruption:
        with pytest.raises(ValueError):
            tool.check(wheel)
    else:
        assert tool.check(wheel)[0] == project['version']
