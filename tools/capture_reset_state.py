"""Read-only post-Partial-Reset capture through a running CIVI TCP server.

The output can contain personal radio settings: keep it outside version control.
No settings, *CLS, Recover connection, or reset commands are sent.
"""

import argparse
import csv
import datetime
import json
import socket
from pathlib import Path

from civi.commands import CATALOG
from civi import menus  # noqa: F401 - populate the menu query catalog


def capture(host: str, port: int, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    result = {
        'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'host': host, 'port': port, 'read_only': True,
        'source': 'User performed IC-7300 Partial Reset immediately before capture',
        'values': {}, 'errors': {}, 'complete': False,
    }

    def save():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    with socket.create_connection((host, port), 5) as connection:
        connection.settimeout(10)
        reader = connection.makefile('rb')

        def query(command):
            connection.sendall((command + '\n').encode('ascii'))
            data = reader.readline(1048576)
            if not data.endswith(b'\n'):
                raise ConnectionError('Missing complete response')
            return data.decode('ascii').rstrip('\r\n')

        result['identity'] = query('*IDN?')
        if next(csv.reader([result['identity']]))[:2] != ['CIVI Project', 'CIVI/IC-7300']:
            save()
            raise RuntimeError('IC-7300 identity is unavailable; recover before capture')
        pending = []
        for _ in range(40):
            error = query('SYST:ERR?')
            if error.startswith('0,'):
                break
            pending.append(error)
        else:
            raise RuntimeError('Error queue did not terminate')
        result['preexisting_errors'] = pending
        commands = ['SENS:FREQ?', 'RAD:MODE?', 'RAD:PTT?', 'READ:SMET?']
        for spec in CATALOG.values():
            if 'r' not in spec.access or spec.header == 'RAD:TXINHIBIT':
                continue  # Known NAK on this IC-7300; not a capture prerequisite.
            if spec.guard == 'memory':
                continue  # Memory/user text content is outside operating reset.
            selectors = [''] if spec.selector is None else [spec.selector.sample()]
            if spec.header in ('RAD:VFO:FREQ', 'RAD:VFO:MODE'):
                selectors = ['SELECTED', 'OTHER']
            commands.extend(spec.header + '?' + (' ' + s if s else '') for s in selectors)
        try:
            for command in commands:
                reply = query(command)
                error = query('SYST:ERR?')
                if reply == 'ERROR' or not error.startswith('0,'):
                    result['errors'][command] = error
                    if error.startswith(('-365,', '-310,')):
                        raise RuntimeError('Communication fault; stopped read-only capture')
                else:
                    result['values'][command] = reply
                save()
            result['final_values'] = {c: query(c) for c in commands[:3]}
            if any(result['values'].get(c) != value for c, value in result['final_values'].items()):
                raise RuntimeError('Radio state changed during capture; retain evidence and recapture')
            result['complete'] = True
            save()
        except BaseException:
            save()
            raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=5025)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = capture(args.host, args.port, args.output)
    print(json.dumps({
        'identity': report['identity'], 'readings': len(report['values']),
        'errors': report['errors'], 'basic': report['final_values'],
        'output': str(args.output),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
