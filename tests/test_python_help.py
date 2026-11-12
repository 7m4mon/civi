"""Public help drift detection, notice integrity and documented error reply behavior."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def help_tool():
    spec = importlib.util.spec_from_file_location('driver_help', ROOT / 'tools/python_driver_help.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_help_covers_public_types_and_signatures_without_drift():
    tool = help_tool()
    data = tool.inventory()
    assert len(data['classes']) == 43
    assert sum(len(c['members']) + len(c.get('fields', [])) for c in data['classes']) == 311
    classes = {row['class']: row for row in data['classes']}
    slots = next(m for m in classes['BandStackCollection']['members'] if m['name'] == '__getitem__')
    assert len(slots['signatures']) == 2
    assert 'BandStackBand' in slots['signatures'][0] and 'BandStackItem' in slots['signatures'][1]
    assert "tone_mode: str = 'OFF'" in classes['MemorySettings']['constructor']
    checked = next(m for m in classes['CiviIc7300']['members'] if m['name'] == 'checked')
    assert 'ContextManager[CiviIc7300]' in checked['signatures'][0]
    assert all(field['type'] == 'bool' for field in classes['DriverOptions']['fields'])
    for path, expected in tool.render().items():
        assert path.read_text(encoding='utf-8') == expected


def test_new_public_member_requires_explicit_help_classification(monkeypatch):
    tool = help_tool()
    monkeypatch.setattr(tool.driver.Radio, 'undocumented_control', property(lambda self: 0), raising=False)
    with pytest.raises(ValueError, match='undocumented_control'):
        tool.inventory()


def test_new_export_requires_help_type_mapping(monkeypatch):
    tool = help_tool()
    monkeypatch.setattr(tool.api, '__all__', [*tool.api.__all__, 'UndocumentedExport'])
    with pytest.raises(ValueError, match='UndocumentedExport'):
        tool.inventory()


def test_notice_matches_source_record_and_is_visible_in_help():
    tool = help_tool()
    notice = (tool.SOURCE / 'IVI_NOTICE.md').read_text(encoding='utf-8')
    body = notice.split('\n\n', 1)[1].split('\n\nSource:', 1)[0]
    record = json.loads((tool.SOURCE / 'notice-source.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(body.encode('utf-8')).hexdigest() == record['notice_sha256']
    assert record['url'].startswith('https://raw.githubusercontent.com/IviFoundation/IviDrivers/')
    assert body in tool.render()[tool.SOURCE / 'REFERENCE.md']


@pytest.mark.parametrize('reply', ['', 'bad,"message"', '1', '1,"unterminated', '1,"message",extra', '1.0,"message"'])
def test_malformed_error_reply_is_protocol_error(driver_module, monkeypatch, reply):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        monkeypatch.setattr(d, 'query', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            d.ivi_utility.error_query()


def test_error_reply_code_and_quoted_message(driver_module, monkeypatch):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        monkeypatch.setattr(d, 'query', lambda *args: '+1,"message, ""quoted"""')
        result = d.ivi_utility.error_query()
        assert (result.code, result.message) == (1, 'message, "quoted"')
        monkeypatch.setattr(d, 'query', lambda *args: '0,"No error"')
        assert d.ivi_utility.error_query() is None
