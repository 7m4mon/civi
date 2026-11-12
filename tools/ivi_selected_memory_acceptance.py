"""Opt-in selected-memory actions on empty ordinary channel 99. No RF start."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300, VfoMode


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource', default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate', action='store_true')
    p.add_argument('--allow-memory-write', action='store_true', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {'simulation': args.simulate, 'channel': 99, 'cases': [], 'wire': [],
              'rf_start': False, 'selected_memory_after': 99}
    def save():
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    def check(name, value):
        report['cases'].append({'name': name, 'passed': bool(value)})
        save()
        if not value:
            raise AssertionError(name)
    with CiviIc7300(args.resource, options={'simulate': args.simulate,
                                          'query_instrument_status': True}) as d:
        original = d._send
        actions = {'RAD:MEM:SELECT 99', 'RAD:MEM:ENABLE', 'RAD:MEM:WRITE',
                   'RAD:MEM:TOVFO', 'RAD:MEM:CLEAR', 'RAD:MEM:CONTENT 99,FF',
                   'RAD:VFO:ENABLE'}
        def guarded(data):
            for cmd in data.decode().strip().split(';'):
                header = cmd.split(' ', 1)[0]
                if '?' not in cmd and cmd not in actions and header not in ('RAD:VFO:FREQ', 'RAD:VFO:MODE'):
                    raise RuntimeError('Unapproved mutation '+cmd)
            report['wire'].append(data.decode().strip())
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
        check('split_off_before', not d.radio.split_enabled)
        before = report['before'] = state()
        check('initial_display_matches_vfo', d.radio.frequency_hz == before['SELECTED']['frequency'])
        check('channel_99_initially_empty', d.memories[99].record is None)
        if args.simulate:
            d.memories.set_simulated_write_permission(True)
        try:
            d.memories.select('99')
            check('select_empty_channel', d.memories[99].record is None)
            d.vfos.enable()
            d.vfos['SELECTED'].frequency_hz = 7100000
            d.vfos['SELECTED'].mode = VfoMode('LSB', False, 1)
            check('store_source_frequency', d.radio.frequency_hz == 7100000)
            check('store_source_mode', d.radio.mode == 'LSB')
            assert idle()
            d.memories.store_current_in_selected()
            record = d.memories[99].record
            report['stored_record'] = None if record is None else record.to_hex()
            check('stored_record_exists', record is not None)
            check('stored_frequency', record.receive.frequency_hz == 7100000)
            check('stored_mode_data_filter', (record.receive.mode, record.receive.data, record.receive.filter_number) == ('LSB', False, 1))
            check('stored_split_off', not record.split_enabled)
            d.vfos['SELECTED'].frequency_hz = 7150000
            d.vfos['SELECTED'].mode = VfoMode('USB', True, 3)
            check('vfo_distinct_before_copy', d.vfos['SELECTED'].frequency_hz == 7150000)
            d.memories.enable()
            check('memory_display_frequency', d.radio.frequency_hz == 7100000)
            check('memory_display_mode', d.radio.mode == 'LSB')
            assert idle()
            d.memories.copy_selected_to_vfo()
            d.vfos.enable()
            check('copied_vfo_frequency', d.vfos['SELECTED'].frequency_hz == 7100000)
            check('copied_vfo_mode', d.vfos['SELECTED'].mode == VfoMode('LSB', False, 1))
            check('other_vfo_unchanged', state()['OTHER'] == before['OTHER'])
            d.memories.select(99)
            check('reselected_same_record', d.memories[99].record == record)
            d.memories.enable()
            check('clear_source_memory_display', d.radio.frequency_hz == 7100000 and d.radio.mode == 'LSB')
            assert idle()
            d.memories.clear_selected()
            check('legacy_clear_readback_empty', d.memories[99].record is None)
            d.vfos.enable()
            for bad in [0, 102, 'BAD', None]:
                count = len(report['wire'])
                try:
                    d.memories.select(bad)
                except (ValueError, TypeError):
                    check('invalid_selector_'+str(bad), len(report['wire']) == count)
                else:
                    check('invalid_selector_'+str(bad), False)
        except BaseException as exc:
            report['failure'] = type(exc).__name__+': '+str(exc)
            save()
            raise
        finally:
            try:
                d.vfos.enable()
                if d.memories[99].record is not None:
                    d.memories[99].clear()
                check('final_channel_empty', d.memories[99].record is None)
                for selector in ['SELECTED', 'OTHER']:
                    d.vfos[selector].mode = VfoMode(**before[selector]['mode'])
                    d.vfos[selector].frequency_hz = before[selector]['frequency']
                report['after'] = state()
                check('both_vfos_restored', report['after'] == before)
                check('display_restored', d.radio.frequency_hz == before['SELECTED']['frequency'])
                check('split_still_off', not d.radio.split_enabled)
                check('idle_after', idle())
            except BaseException as exc:
                report['restore_failure'] = str(exc)
                save()
                raise
            if args.simulate:
                d.memories.set_simulated_write_permission(False)
    print(json.dumps({'checks': len(report['cases']), 'simulation': args.simulate,
                      'both_vfos_restored': True, 'channel_99_empty': True}))


if __name__ == '__main__':
    main()
