"""Generate the complete public-member index. Classification is not a conformance test."""

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import inspect
import json
from pathlib import Path
import re
import sys
from typing import ForwardRef, get_overloads, is_typeddict

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'drivers/civi-ic7300/src/civi_ic7300'
sys.path[:0] = [str(ROOT / 'drivers/civi-ic7300/src')]
import civi_ic7300 as api  # noqa: E402
from civi_ic7300 import bands, controls, driver, errors, interfaces, menus, operations, scan, storage  # noqa: E402

GROUPS = [
    (driver, 'API.md', 'CiviIc7300 Radio Utility DirectIo DriverOptions GatewayIdentification'),
    (controls, 'API.md', 'Gains Meters Scope Vfo VfoCollection VfoMode ScopeEdges ScopeSweep DataFilter'),
    (menus, 'API.md', 'MenuItem MenuCollection MenuDefinition MenuKind AudioFilter Bandwidth RgbColor'),
    (storage, 'STORAGE.md', 'MemorySettings MemoryRecord MemoryItem MemoryCollection KeyerItem KeyerCollection'),
    (storage, 'HIERARCHY.md', 'BandStackItem BandStackSlotCollection BandStackBand BandStackBandCollection BandStackCollection'),
    (bands, 'BANDS.md', 'BandEdges Bands'), (scan, 'SCAN.md', 'ScanControl'),
    (operations, 'OPERATIONS.md', 'RadioOperations'),
    (interfaces, 'API.md', 'IviUtility IviDirectIo'),
    (errors, 'API.md', 'ErrorQueryResult DeviceError ProtocolError QueryError'),
]
CLASSES = {name: (getattr(module, name), guide) for module, guide, names in GROUPS for name in names.split()}
CLASSES['GatewayIdentification'] = (driver.GatewayIdentification, 'BASIC.md')
CLASSES['DataFilter'] = (controls.DataFilter, 'BANDS.md')

# Exact direct SCPI contracts for non-descriptor members. Any new public I/O
# member must be classified here; it cannot silently acquire a local/no-I/O label.
IO = {}


def rule(classes, members, commands, usage):
    for cls in classes.split():
        for member in members.split():
            IO[cls + '.' + member] = (commands, usage)


rule('CiviIc7300', 'query', 'caller-supplied ASCII program', 'Atomically send one program and read one response; raw status remains explicit.')
rule('Utility IviUtility', 'instrument_manufacturer instrument_model identification', '*IDN?', 'Read gateway identity; the full record is distinct from radio firmware.')
rule('Utility IviUtility', 'error_query error_query_all raise_on_device_error', 'SYST:ERR?', 'Read/consume this client error queue explicitly, independently of the status option.')
rule('Utility IviUtility', 'reset', 'RAD:RESET', 'Select the documented receive baseline with a reset-specific timeout; no automatic rollback.')
rule('Utility', 'clear_status', '*CLS', 'Explicitly clear this client error queue; no serial quarantine recovery.')
rule('Utility', 'wait_for_complete', '*OPC?', 'Require completion reply 1; completion alone does not prove prior success.')
rule('DirectIo IviDirectIo', 'write_bytes write_string', 'caller-supplied ASCII program', 'Write one LF-framed program; raw I/O never adds status queries.')
rule('DirectIo IviDirectIo', 'read_bytes read_string', 'receive pending response; no command sent', 'Read one LF-framed response; synchronize separate raw write/read pairs externally.')
rule('Radio', 'frequency_hz', 'SENS:FREQ', 'Read/write selected operating frequency, whole Hz, 30000..60000000.')
rule('Radio', 'mode', 'RAD:MODE', 'Read/write canonical mode; use VfoMode for DATA and filter together.')
rule('Radio', 'smeter_raw', 'READ:SMET?', 'Read uncalibrated raw integer 0..255, not dBm.')
rule('Radio', 'attenuator_db', 'RAD:ATT', 'Read/write 0 or 20 dB attenuator setting, not a meter.')
rule('Radio', 'data_filter', 'RAD:DATA', 'Read/write DataFilter; DATA OFF reads and writes have different filter constraints (BANDS.md).')
rule('Radio', 'firmware_revision', 'RAD:FIRM?', 'Read manual radio firmware metadata or Unknown; not CI-V auto-read.')
rule('Vfo', 'frequency_hz', 'RAD:VFO:FREQ', 'Read/write relative SELECTED/OTHER VFO frequency in whole Hz, 30000..60000000.')
rule('Vfo', 'mode', 'RAD:VFO:MODE', 'Read/write one complete mode/DATA/filter record.')
for member, command in [('select', 'SELECT'), ('enable', 'ENABLE'), ('copy_selected_to_other', 'COPY'), ('swap', 'SWAP')]:
    rule('VfoCollection', member, 'RAD:VFO:' + command, 'Operate on VFO context; selection is shared with other clients. See API.md for values.')
rule('Scope', 'read_sweep', 'RAD:SCOPE:WAVE?', 'Read a complete sweep; does not enable streaming.')
rule('Scope', 'read_fixed_edges write_fixed_edges', 'RAD:SCOPE:FIXEDGE', 'Read/write stored edges using band 1..13, edge 1..4 and whole-kHz boundaries in Hz.')
rule('Scope', 'start_stream', 'RAD:SCOPE:STREAM; RAD:SCOPE:ENABLE', 'Enable transfer then operation; checked mode attempts transfer restoration on second-stage failure.')
rule('Scope', 'stop_stream', 'RAD:SCOPE:STREAM', 'Disable transfer while preserving scope operation; checks follow STATUS.md.')
rule('MenuItem', 'value write_and_read', 'RAD:MENU:nnnn', 'Read/write item-specific typed value; definition/MENUS.md supplies range, step, unit and write gate.')
rule('MemoryItem', 'record clear write_and_read', 'RAD:MEM:CONTENT', 'Read/write complete memory record; None means empty. Addressed clear supports 1..99, not P1/P2.')
for member, command in [('select', 'SELECT'), ('enable', 'ENABLE'), ('store_current_in_selected', 'WRITE'),
                        ('copy_selected_to_vfo', 'TOVFO'), ('clear_selected', 'CLEAR')]:
    rule('MemoryCollection', member, 'RAD:MEM:' + command, 'Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md.')
rule('BandStackItem', 'settings write_and_read', 'RAD:BAND:STACK', 'Read/write full settings at band 1..11, slot 1..3; flat/nested views share state.')
rule('KeyerItem', 'text write_and_read', 'RAD:KEYER:TEXT', 'Read/write up to 70 supported ASCII characters in M1..M8; storage only, no CW output.')
for member, command in [('default_edges', 'RAD:BAND:EDGES?'), ('factory_count', 'RAD:TXBAND:COUNT?'),
                        ('user_count', 'RAD:TXBAND:USERCOUNT?'), ('read_factory', 'RAD:TXBAND:READ?'),
                        ('read_user', 'RAD:TXBAND:USER?'), ('write_user', 'RAD:TXBAND:USER'),
                        ('write_and_read_user', 'RAD:TXBAND:USER')]:
    rule('Bands', member, command, 'Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md.')
for member, command in [('start', 'mode action'), ('stop', 'STOP'), ('set_delta_span_hz', 'SPAN*'),
                        ('set_select_enabled', 'SELECTOFF/SELECTON'), ('set_resume_enabled', 'RESUMEOFF/RESUMEON'),
                        ('assign_selected_memory_group', 'SELECT'), ('set_memory_group', 'GROUP')]:
    rule('ScanControl', member, 'RAD:SCAN:' + command, 'Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion.')
for member, command in [('send_cw', 'RAD:CW:SEND'), ('stop_cw', 'RAD:CW:STOP'),
                        ('play_voice', 'RAD:VOICE'), ('stop_voice', 'RAD:VOICE'), ('speak', 'RAD:SPEECH'),
                        ('power_on', 'RAD:POWER:ON'), ('power_off', 'RAD:POWER:OFF'),
                        ('start_transmit', 'RAD:PTT ON'), ('stop_transmit', 'RAD:PTT OFF')]:
    rule('RadioOperations', member, command, 'Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied.')

LOCAL = set('name number band slot slots bands definition driver_version driver_vendor supported_instrument_models simulation_enabled simulate query_instrument_status query_instrument_status_enabled io_timeout_ms'.split())
LOCAL.update('radio vfos gains meters scope menus memories band_stacks keyers scan operations ivi_utility ivi_direct_io'.split())
LOCAL.update('audio_filter_item bandwidth_item boolean_item date_item integer_item rgb_item scope_edges_item text_item time_item utc_offset_item'.split())
LOCAL.update('set_simulated_write_permission set_simulated_write_permissions set_simulated_calibration_permission set_simulated_permissions'.split())
LOCAL.update('to_bytes from_bytes to_hex from_hex to_write_hex simple display_name checked close __enter__ __exit__ __getitem__ __iter__ __len__'.split())
SPECIAL = {'__enter__', '__exit__', '__getitem__', '__iter__', '__len__'}


def signature(obj):
    text = str(inspect.signature(obj))
    return re.sub(r"(: | -> )'([^']+)'", r'\1\2', text)


def annotation(value):
    return value.__forward_arg__ if isinstance(value, ForwardRef) else str(value)


def members(cls):
    if issubclass(cls, Enum) or is_typeddict(cls) or issubclass(cls, BaseException):
        return []
    return [(name, value) for name, value in inspect.getmembers(cls)
            if (not name.startswith('_') or name in SPECIAL)
            and (isinstance(value, (property, controls.Setting)) or inspect.isroutine(value))]


def inventory():
    missing_exports = set(api.__all__) - set(CLASSES) - {'MenuValue'}
    if missing_exports:
        raise ValueError('Unclassified public exports: ' + ', '.join(sorted(missing_exports)))
    result = []
    for name, (cls, guide) in CLASSES.items():
        if not (SOURCE / guide).exists():
            raise ValueError('Missing detail guide ' + guide)
        group = {'class': name, 'guide': guide, 'members': []}
        if issubclass(cls, Enum):
            group['enum_values'] = {key: value.value for key, value in cls.__members__.items()}
        elif is_typeddict(cls):
            group['fields'] = [{'name': key, 'type': annotation(value), 'access': 'optional dictionary key'}
                               for key, value in cls.__annotations__.items()]
        else:
            try:
                group['constructor'] = signature(cls)
            except (TypeError, ValueError):
                group['constructor'] = '(*args) — standard Python exception constructor'
            if is_dataclass(cls):
                group['fields'] = [{'name': field.name, 'type': str(field.type),
                                    'access': 'read-only' if cls.__dataclass_params__.frozen else 'read/write Python value'}
                                   for field in fields(cls)]
        for member, value in members(cls):
            key = name + '.' + member
            if isinstance(value, controls.Setting):
                command, usage = value.header, value.__doc__
                kind = 'read/write' if value.writable else 'read-only'
                prototypes = [member + ': ' + type(value.default).__name__]
            else:
                if key in IO:
                    command, usage = IO[key]
                elif member in LOCAL:
                    command = 'None (local metadata/view/configuration or record conversion)'
                    usage = inspect.getdoc(value) or 'Local operation; argument bounds and returned-view/value semantics are specified in the linked guide.'
                else:
                    raise ValueError('Public member lacks a help contract: ' + key)
                if isinstance(value, property):
                    kind = 'read/write' if value.fset is not None else 'read-only'
                    prototypes = [member + ' getter' + signature(value.fget)]
                    if value.fset is not None:
                        prototypes.append(member + ' setter' + signature(value.fset))
                else:
                    kind = 'method'
                    prototypes = [member + signature(overload) for overload in get_overloads(value)] or [member + signature(value)]
                    if key == 'CiviIc7300.checked':
                        prototypes = ['checked(self) -> ContextManager[CiviIc7300]']
            group['members'].append({'name': member, 'access': kind, 'signatures': prototypes,
                                     'scpi': command, 'usage': usage.split('\n\n')[0]})
        if name == 'DeviceError':
            group['fields'] = [{'name': 'errors', 'type': 'tuple[ErrorQueryResult, ...]', 'access': 'Python attribute containing extracted device errors'}]
        result.append(group)
    return {'client_version': api.__version__, 'scope': 'driver-defined public members and selected collection/context protocols; standard-library inherited APIs excluded', 'classes': result,
            'type_aliases': {'MenuValue': str(api.MenuValue)}}


def render():
    data = inventory()
    total = sum(len(group['members']) + len(group.get('fields', [])) for group in data['classes'])
    lines = [f'# Public API reference (client {api.__version__})', '',
             f"{len(data['classes'])} public/returned types; {total} member/field entries.", '',
             'Generated signatures/types/access and explicit SCPI contracts are indexed below. Linked guides',
             'supply argument ranges, units, detailed behavior and examples. New unclassified exports or',
             'members fail generation. This index is not an automated proof of semantic documentation',
             'completeness or IVI conformity. See EVIDENCE.md for implementation/mock/hardware boundaries.', '',
             'Scope: driver-defined public members and selected collection/context protocols. Standard',
             'Python exception/string/Enum inherited APIs are not duplicated here.', '',
             '## Common contracts and exceptions', '',
             '- Invalid types/values: TypeError/ValueError before I/O where validated; detailed guide lists constraints.',
             '- DeviceError: errors read from this client queue when checks are ON or explicitly requested.',
             '- QueryError: gateway ERROR sentinel, with the queue preserved when not automatically inspected.',
             '- ProtocolError: invalid framing/replies; transport failures use OSError/TimeoutError/ConnectionError.',
             '- RuntimeError: closed-session I/O or a simulation-only permission method used on a real connection.',
             '- AttributeError: attempting a read-only assignment; NotImplementedError: unsupported simulator/raw features.',
             '- STATUS.md governs checks. Setters normally append *OPC?; ON/checked() may add SYST:ERR? queries.',
             '- Local metadata/view construction does not send SCPI. Closing TCP may trigger gateway stop attempts.',
             '- Pure record conversions/constructors return the documented value/record, without instrument I/O.',
             '- Collection constructors take an owning driver; applications normally obtain views through root references.',
             '- Abstract IviUtility/IviDirectIo types describe contracts and cannot be instantiated directly.', '',
             '## Development environments', '',
             'Python >=3.11 is required. Current execution/build/type evidence is Windows 11 (25H2),',
             'CPython 3.14.5 x64. Interactive shells, scripts and IDEs use the same Python API; no IDE plugin',
             'is required or separately verified. Other Python/OS combinations remain unverified.', '']
    for group in data['classes']:
        lines += ['## ' + group['class'], '', f"Details/valid values: [{group['guide']}]({group['guide']}).",
                  'Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.', '']
        if 'constructor' in group:
            lines += ['Constructor: `' + group['class'] + group['constructor'] + '`.', '']
        if 'enum_values' in group:
            lines += ['Enum values: `' + json.dumps(group['enum_values']) + '`.', '']
        if group.get('fields'):
            lines += ['| Field | Type | Access |', '|---|---|---|']
            lines += [f"| `{field['name']}` | `{field['type']}` | {field['access']} |" for field in group['fields']]
            lines += ['']
        if group['members']:
            lines += ['| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |', '|---|---|---|---|']
            for member in group['members']:
                values = ['<br>'.join('`' + s + '`' for s in member['signatures']), member['access'],
                          member['scpi'], member['usage'].replace('\n', ' ')]
                lines.append('| ' + ' | '.join(value.replace('|', '\\|') for value in values) + ' |')
            lines += ['']
    lines += ['## Type aliases', '', '`MenuValue = ' + data['type_aliases']['MenuValue'] + '`.', '',
              '## IVI Foundation notice', '', (SOURCE / 'IVI_NOTICE.md').read_text(encoding='utf-8').split('\n', 1)[1].strip(), '']
    return {SOURCE / 'REFERENCE.md': '\n'.join(lines),
            SOURCE / 'public-api.json': json.dumps(data, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, expected in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != expected:
                raise SystemExit('Regenerate public help: ' + str(path.relative_to(ROOT)))
        else:
            path.write_text(expected, encoding='utf-8')


if __name__ == '__main__':
    main()
