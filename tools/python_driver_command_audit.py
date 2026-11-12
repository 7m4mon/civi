"""Generate a unified gateway command/alias/exclusion inventory. No instrument I/O."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tools'), str(ROOT / 'drivers/civi-ic7300/src')]

from civi import scpi  # noqa: E402
from civi.commands import CATALOG  # noqa: E402
from civi_ic7300 import __version__  # noqa: E402
from python_driver_docs import command_mappings  # noqa: E402

BASE = {
    '*IDN': ('r', '*IDN', None, 'Constructor and identity properties'),
    '*CLS': ('w', '*CLS', None, 'Explicit queue clear only; not quarantine recovery'),
    '*OPC': ('r', '*OPC', None, 'Setter completion and explicit wait; does not prove success'),
    'SYST:ERR': ('r', 'error', None, 'Explicit/error-policy queue queries'),
    'SENS:FREQ': ('rw', 'frequency', '7100000', 'Selected VFO/memory working frequency'),
    'RAD:MODE': ('rw', 'mode', 'USB', 'Basic mode; use VfoMode for DATA/filter'),
    'READ:SMET': ('r', 'smeter', None, 'Uncalibrated raw meter'),
    'RAD:PTT': ('rw', 'ptt', 'OFF', 'Explicit start/stop; gateway guards and ownership apply'),
    'RAD:FIRM': ('r', 'firmware', None, 'Manual metadata or Unknown; not CI-V firmware auto-read'),
    'RAD:RESET': ('w', 'receive_reset', None, 'Receive baseline; distinct from *RST/Partial/LAN RESET'),
    'RAD:SCOPE:WAVE': ('r', 'scope_wave', None, 'Latest complete gateway sweep'),
}
MNEMONICS = {'SYST': 'SYSTEM', 'ERR': 'ERROR', 'SENS': 'SENSE', 'FREQ': 'FREQUENCY',
             'RAD': 'RADIO', 'SMET': 'SMETER', 'FIRM': 'FIRMWARE'}
EXCLUSIONS = [
    ('*RST', 'Gateway has no *RST; reset() uses documented RAD:RESET, not an Icom Partial/All Reset'),
    ('*OPC', 'Non-query common command is not provided; use *OPC? / wait_for_complete()'),
    ('*IDN', 'Identification is query-only'),
    ('*CLS?', 'Clear is action-only'),
    ('*STB?', 'No status-byte/SRQ subsystem in this gateway'),
    ('*ESR?', 'No event-status-register subsystem in this gateway'),
    ('*ESE?', 'No event-status-enable register in this gateway'),
    ('*SRE?', 'No service-request-enable register in this gateway'),
    ('*TST?', 'No gateway self-test command; health/connection state is not fabricated as self-test'),
    ('*WAI', 'No standalone wait action; use *OPC?'),
]


def aliases(header):
    return sorted(':'.join(tokens) for tokens in itertools.product(*[
        (token, MNEMONICS[token]) if token in MNEMONICS else (token,)
        for token in header.split(':')]))


def inventory():
    mappings = command_mappings()
    rows = []
    for header, (access, handler, sample, note) in BASE.items():
        rows.append({'header': header, 'source': 'base/special', 'gateway_access': access,
                     'handler': handler, 'sample': sample, 'note': note})
    for header, spec in CATALOG.items():
        rows.append({'header': header, 'source': 'extended', 'gateway_access': spec.access,
                     'handler': 'catalog:' + header, 'note': spec.description})
    assert len({row['header'] for row in rows}) == len(rows)
    for row in rows:
        entry = mappings.get(row['header'], {'access': set(), 'apis': []})
        row['typed_access'] = ''.join(c for c in 'rw' if c in entry['access'])
        row['apis'] = entry['apis']
        row['aliases'] = aliases(row['header'])
        row['status'] = 'mapped' if set(row['gateway_access']) <= set(row['typed_access']) else 'pending'
    sources = {p: hashlib.sha256((ROOT / p).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
               for p in ('civi/scpi.py', 'civi/commands.py', 'civi/menus.py')}
    return {'schema_version': 1, 'client_version': __version__, 'source_sha256': sources,
            'commands': rows, 'exclusions': [{'probe': p, 'reason': r} for p, r in EXCLUSIONS]}


def render():
    data = inventory()
    rows = data['commands']
    count = sum(row['status'] == 'mapped' for row in rows)
    text = [f'# Unified SCPI inventory (client {__version__})', '',
            'Generated from the gateway catalog/parser inventory and typed client mappings.',
            'A header is counted once; query/set directions are separate. Spelling aliases do not add features.', '',
            f'**{len(CATALOG)} extended + {len(BASE)} base/special = {len(rows)} canonical headers.**',
            f'**{count} mapped, {len(rows) - count} pending** in supported gateway directions.', '',
            'This is software coverage, not radio verification or IVI conformity. Scope is the CIVI ASCII',
            'gateway, not every IC-7300 function. Parser hashes in the JSON trigger re-review after changes.', '',
            '## Reading the table', '',
            'R means append ?, W means set/action. A missing direction is not implemented by the gateway.',
            'Aliases list the documented short/full tokens independently; case is ignored and leading colon',
            'is accepted. No arbitrary intermediate abbreviation is promised. Compound/relative SCPI syntax',
            'is a gateway parser feature, not a separate typed command. Simulation supports typed APIs,',
            'not every raw alias or compound form.', '',
            'Core commands now have dedicated IDN/clear/completion/firmware/PTT APIs. *OPC? is also used',
            'internally after setters; SYST:ERR? follows STATUS.md. PTT start requires explicit gateway',
            'transmit permission and ownership; PTT OFF attempts to stop CIVI-owned paths.', '',
            '| Canonical header | Source | Gateway | Typed | API | Accepted spellings | Scope / notes |',
            '|---|---|---|---|---|---|---|']
    for row in rows:
        cells = [f"`{row['header']}`", row['source'], row['gateway_access'].upper(),
                 row['typed_access'].upper() or '—', ', '.join('`' + api + '`' for api in row['apis']) or '—',
                 ', '.join('`' + alias + '`' for alias in row['aliases']), row['note']]
        text.append('| ' + ' | '.join(c.replace('|', '\\|') for c in cells) + ' |')
    text += ['', '## Unsupported forms and reasons', '',
             'These are gateway omissions/unsupported directions, not features secretly provided by raw I/O.',
             'They are outside the supported-header count above; parser tests verify rejection.', '',
             '| Unsupported probe | Reason / alternative |', '|---|---|']
    text += [f'| `{p}` | {r} |' for p, r in EXCLUSIONS]
    text += ['', '## Other interfaces outside this ASCII scope', '',
             'No VXI-11, HiSLIP, binary-block/audio transport, SRQ or arbitrary outbound CI-V passthrough is',
             'provided. OS/LAN/authentication administration remains outside this client SCPI inventory.',
             'Protected menu/calibration/link commands that the gateway does provide are included, not',
             'removed from coverage merely because their write gates default OFF.', '',
             'BASIC.md documents base APIs; EVIDENCE.md summarizes results. The verification',
             'completion plan is linked from COMPLIANCE.md.', '']
    markdown = '\n'.join(text)
    return {
        ROOT / 'drivers/civi-ic7300/src/civi_ic7300/SCPI_COVERAGE.md': markdown,
        ROOT / 'drivers/civi-ic7300/src/civi_ic7300/scpi-coverage.json': json.dumps(data, indent=2) + '\n',
        ROOT / 'docs/PYTHON_SCPI_AUDIT.md': markdown.replace('BASIC.md', '../drivers/civi-ic7300/src/civi_ic7300/BASIC.md')
                                                .replace('COMPLIANCE.md', '../drivers/civi-ic7300/src/civi_ic7300/COMPLIANCE.md')
                                                .replace('AUDIT.md', '../drivers/civi-ic7300/src/civi_ic7300/AUDIT.md'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, expected in render().items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != expected:
                raise SystemExit('Regenerate unified command audit: ' + str(path.relative_to(ROOT)))
        else:
            path.write_text(expected, encoding='utf-8')


if __name__ == '__main__':
    main()
