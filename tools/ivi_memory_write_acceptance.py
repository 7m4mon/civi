"""Opt-in single empty ordinary memory write/read/clear test. Never transmits."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300, MemoryRecord, MemorySettings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource', default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--channel', type=int, default=99)
    p.add_argument('--allow-memory-write', action='store_true', required=True)
    p.add_argument('--simulate', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not 1 <= args.channel <= 99:
        p.error('Use an ordinary memory channel 1..99, never P1/P2')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {'simulation': args.simulate, 'channel': args.channel,
              'cases': [], 'wire': [], 'records': [], 'transmit_start_sent': False}
    def save():
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    def check(name, result):
        report['cases'].append({'name': name, 'passed': bool(result)})
        save()
        if not result:
            raise AssertionError(name)
    with CiviIc7300(args.resource, options={'simulate': args.simulate,
                                          'query_instrument_status': True}) as d:
        original = d._send
        def guarded(data):
            text = data.decode().strip()
            for cmd in text.split(';'):
                if '?' not in cmd and not cmd.startswith('RAD:MEM:CONTENT '+str(args.channel)+','):
                    raise RuntimeError('Unapproved write '+cmd)
            report['wire'].append(text)
            save()
            return original(data)
        d._send = guarded
        def idle():
            return (not d.radio.transmitting and not d.operations.vox_enabled
                    and d.operations.break_in == 'OFF' and d.operations.tuner == 'OFF')
        def state():
            return {s: {'frequency': d.vfos[s].frequency_hz,
                        'mode': asdict(d.vfos[s].mode)} for s in ['SELECTED', 'OTHER']}
        check('idle_before', idle())
        report['radio_before'] = before = state()
        item = d.memories[args.channel]
        old = item.record
        check('initial_slot_empty', old is None)
        report['initial_record'] = None
        save()
        if args.simulate:
            d.memories.set_simulated_write_permission(True)
        try:
            modes = ['LSB', 'USB', 'AM', 'CW', 'RTTY', 'FM', 'CW-R', 'RTTY-R']
            for i, mode in enumerate(modes):
                assert idle()
                rx = MemorySettings(7100000+i*100, mode, i % 3+1,
                                    mode in ['USB', 'LSB', 'FM'],
                                    ['OFF', 'TONE', 'TSQL'][i % 3], 88.5, 100.0)
                tx = MemorySettings(14100000+i*100, 'USB', 2)
                record = MemoryRecord(rx, tx, bool(i % 2), i % 4, 'CIVI TEST'+str(i))
                if i % 2:
                    item.record = record
                    actual = item.record
                else:
                    actual = item.write_and_read(record)
                report['records'].append({'mode': mode, 'expected': record.to_hex(),
                                          'actual': None if actual is None else actual.to_hex()})
                save()
                check('record_exact_'+mode, actual == record)
                item.clear()
                check('clear_empty_'+mode, item.record is None)
            count = len(report['wire'])
            try:
                item.record = None
            except TypeError:
                check('invalid_record_before_io', len(report['wire']) == count)
            else:
                check('invalid_record_before_io', False)
            for key in ['P1', 'P2']:
                count = len(report['wire'])
                try:
                    d.memories[key].clear()
                except ValueError:
                    check('no_clear_'+key, len(report['wire']) == count)
                else:
                    check('no_clear_'+key, False)
        except BaseException as exc:
            report['failure'] = type(exc).__name__+': '+str(exc)
            save()
            raise
        finally:
            try:
                item.clear()
                check('final_slot_empty', item.record is None)
                report['radio_after'] = state()
                check('vfos_unchanged', report['radio_after'] == before)
                check('idle_after', idle())
            except BaseException as exc:
                report['restore_failure'] = str(exc)
                save()
                raise
            if args.simulate:
                d.memories.set_simulated_write_permission(False)
    save()
    print(json.dumps({'checks': len(report['cases']), 'channel': args.channel,
                      'restored_empty': True, 'simulation': args.simulate}))


if __name__ == '__main__':
    main()
