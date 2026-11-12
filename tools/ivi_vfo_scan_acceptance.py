"""Opt-in short VFO scans using existing P1/P2 and unchanged delta span."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300, VfoMode


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource', default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate', action='store_true')
    p.add_argument('--allow-scan', action='store_true', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); args.output.parent.mkdir(parents=True, exist_ok=True)
    r = {'simulation': args.simulate, 'cases': [], 'scans': [], 'wire': [],
         'rf_start': False, 'scan_edge_writes': False, 'delta_span_writes': False}
    def save(): args.output.write_text(json.dumps(r, indent=2)+'\n', encoding='utf-8')
    def check(name, result):
        r['cases'].append({'name': name, 'passed': bool(result)}); save()
        if not result: raise AssertionError(name)
    with CiviIc7300(args.resource, options={'simulate': args.simulate, 'query_instrument_status': True}) as d:
        original = d._send
        allowed = {'RAD:VFO:ENABLE','RAD:VFO:FREQ','RAD:VFO:MODE','RAD:SQL',
                   'RAD:SCAN:STOP','RAD:SCAN:AUTO','RAD:SCAN:PROGRAM',
                   'RAD:SCAN:DELTA','RAD:SCAN:FINEPROGRAM','RAD:SCAN:FINEDELTA'}
        def guarded(data):
            text = data.decode().strip()
            if any('?' not in c and c.split(' ',1)[0] not in allowed for c in text.split(';')):
                raise RuntimeError('Mutation outside scan allowlist')
            r['wire'].append(text); save(); return original(data)
        d._send = guarded
        def state(): return {s: {'hz':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle(): return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        check('idle_before', idle()); check('split_off', not d.radio.split_enabled)
        before = r['before'] = state(); sql = r['sql_before'] = d.gains.squelch_raw
        r['edges'] = {k: None if (v:=d.memories[k].record) is None else v.to_hex() for k in ['P1','P2']}; save()
        if not args.simulate:
            check('existing_edges_populated', all(r['edges'].values()))
        try:
            d.vfos.enable(); d.scan.stop(); d.gains.squelch_raw = 255
            check('sql_closed_setting', d.gains.squelch_raw == 255)
            r['squelch_open_during_test'] = d.meters.squelch_open
            for mode in ['PROGRAM','FINEPROGRAM','DELTA','FINEDELTA','AUTO']:
                d.scan.stop(); d.vfos['SELECTED'].mode = VfoMode('LSB',False,1)
                d.vfos['SELECTED'].frequency_hz = 7100000
                assert idle()
                row = {'mode':mode, 'frequencies':[]}; r['scans'].append(row); save()
                try:
                    d.scan.start(mode); check(mode+'_accepted', True)
                    for _ in range(4):
                        time.sleep(.12); row['frequencies'].append(d.radio.frequency_hz); save()
                    row['motion_observed'] = len(set(row['frequencies'])) > 1
                    if args.simulate: check(mode+'_logical_active', d._simulation.scan.mode == mode)
                    check(mode+'_idle', idle())
                finally:
                    d.scan.stop()
                stopped = []
                for _ in range(3):
                    time.sleep(.12); stopped.append(d.radio.frequency_hz)
                row['stopped_frequencies'] = stopped; save()
                check(mode+'_stop_stable', len(set(stopped))==1)
                if args.simulate: check(mode+'_logical_stopped', d._simulation.scan.mode is None)
        except BaseException as exc:
            r['failure'] = str(exc); save(); raise
        finally:
            try:
                d.scan.stop(); d.vfos.enable()
                for s in ['SELECTED','OTHER']:
                    d.vfos[s].mode = VfoMode(**before[s]['mode']); d.vfos[s].frequency_hz = before[s]['hz']
                d.gains.squelch_raw = sql
                r['after'] = state(); r['sql_after'] = d.gains.squelch_raw
                check('vfos_restored',r['after']==before); check('sql_restored',r['sql_after']==sql)
                check('edges_unchanged', {k:None if (v:=d.memories[k].record) is None else v.to_hex() for k in ['P1','P2']}==r['edges'])
                check('idle_after',idle())
            except BaseException as exc: r['restore_failure']=str(exc); save(); raise
    print(json.dumps({'simulation':args.simulate,'checks':len(r['cases']),
                      'motion':{x['mode']:x.get('motion_observed') for x in r['scans']},'restored':True}))


if __name__ == '__main__': main()
