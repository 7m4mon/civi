"""Manual VFO COPY direction and frequency/mode/DATA/filter restoration test."""
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
    p.add_argument('--initial-vfo', choices=['A', 'B'], required=True)
    p.add_argument('--allow-vfo-copy', action='store_true', required=True)
    p.add_argument('--simulate', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {'simulation': args.simulate, 'initial_vfo_owner_confirmed': args.initial_vfo,
              'cases': [], 'wire': [], 'copies': [], 'rf_start': False,
              'stored_record_writes': False}
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
        allowed = {'RAD:VFO:SELECT', 'RAD:VFO:ENABLE', 'RAD:VFO:COPY',
                   'RAD:VFO:FREQ', 'RAD:VFO:MODE'}
        def guarded(data):
            text = data.decode().strip()
            for cmd in text.split(';'):
                if '?' not in cmd and cmd.split(' ', 1)[0] not in allowed:
                    raise RuntimeError('Unapproved mutation '+cmd)
            report['wire'].append(text)
            save()
            return original(data)
        d._send = guarded
        def state():
            return {s: {'frequency': d.vfos[s].frequency_hz,
                        'mode': asdict(d.vfos[s].mode)} for s in ['SELECTED', 'OTHER']}
        def idle():
            return (not d.radio.transmitting and not d.operations.vox_enabled
                    and d.operations.break_in == 'OFF' and d.operations.tuner == 'OFF')
        check('idle_before', idle())
        check('split_off_before', not d.radio.split_enabled)
        before = report['before'] = state()
        check('display_matches_selected_vfo', d.radio.frequency_hz == before['SELECTED']['frequency'])
        try:
            d.vfos.enable()
            for source, hz, mode, other_hz, other_mode in [
                ('A', 7100000, VfoMode('LSB', False, 1), 14100000, VfoMode('USB', True, 3)),
                ('B', 14100000, VfoMode('USB', True, 3), 7100000, VfoMode('LSB', False, 1)),
            ]:
                d.vfos.select(source)
                d.vfos['SELECTED'].mode = mode
                d.vfos['SELECTED'].frequency_hz = hz
                d.vfos['OTHER'].mode = other_mode
                d.vfos['OTHER'].frequency_hz = other_hz
                initial = state()
                check(source+'_source_setup', initial['SELECTED'] == {'frequency': hz, 'mode': asdict(mode)})
                check(source+'_destination_distinct', initial['OTHER'] == {'frequency': other_hz, 'mode': asdict(other_mode)})
                assert idle()
                d.vfos.copy_selected_to_other()
                actual = state()
                report['copies'].append({'source': source, 'before': initial, 'after': actual})
                check(source+'_source_unchanged', actual['SELECTED'] == initial['SELECTED'])
                check(source+'_destination_frequency', actual['OTHER']['frequency'] == hz)
                check(source+'_destination_mode_data_filter', actual['OTHER']['mode'] == asdict(mode))
                check(source+'_display_matches_source', d.radio.frequency_hz == hz and d.radio.mode == mode.mode)
                check(source+'_still_idle', idle())
                d.vfos.copy_selected_to_other()
                check(source+'_repeated_copy_idempotent', state() == actual)
        except BaseException as exc:
            report['failure'] = type(exc).__name__+': '+str(exc)
            save()
            raise
        finally:
            try:
                d.vfos.select(args.initial_vfo)
                for selector in ['SELECTED', 'OTHER']:
                    d.vfos[selector].mode = VfoMode(**before[selector]['mode'])
                    d.vfos[selector].frequency_hz = before[selector]['frequency']
                report['after'] = state()
                check('both_vfo_records_restored', report['after'] == before)
                check('display_restored', d.radio.frequency_hz == before['SELECTED']['frequency'])
                check('split_still_off', not d.radio.split_enabled)
                check('idle_after', idle())
            except BaseException as exc:
                report['restore_failure'] = str(exc)
                save()
                raise
    print(json.dumps({'checks': len(report['cases']), 'simulation': args.simulate,
                      'both_vfos_restored': True, 'initial_vfo_reselected': args.initial_vfo}))


if __name__ == '__main__':
    main()
