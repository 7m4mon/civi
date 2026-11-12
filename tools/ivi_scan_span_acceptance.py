"""Opt-in delta-scan span writes; requires operator-known original span."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,VfoMode

SPANS=[5000,10000,20000,50000,100000,500000,1000000]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--initial-span-hz',type=int,choices=SPANS,required=True)
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--allow-scan-settings',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    r={'simulation':args.simulate,'initial_span_owner_reported':args.initial_span_hz,
       'cases':[],'scans':[],'wire':[],'rf_start':False,'memory_writes':False}
    def save():args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    def check(name,value):
        r['cases'].append({'name':name,'passed':bool(value)});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        if args.simulate:d.scan.set_delta_span_hz(args.initial_span_hz)
        original=d._send
        allowed={'RAD:VFO:ENABLE','RAD:VFO:FREQ','RAD:VFO:MODE','RAD:SQL','RAD:SCAN:DELTA','RAD:SCAN:STOP',
                 'RAD:SCAN:SPAN5K','RAD:SCAN:SPAN10K','RAD:SCAN:SPAN20K','RAD:SCAN:SPAN50K',
                 'RAD:SCAN:SPAN100K','RAD:SCAN:SPAN500K','RAD:SCAN:SPAN1M'}
        def guarded(data):
            text=data.decode().strip()
            if any('?' not in c and c.split(' ',1)[0] not in allowed for c in text.split(';')):raise RuntimeError('Unapproved span mutation')
            r['wire'].append(text);save();return original(data)
        d._send=guarded
        def state():return {s:{'hz':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle():return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        check('idle_before',idle());before=r['before']=state();sql=r['sql_before']=d.gains.squelch_raw
        check('display_matches_vfo',d.radio.frequency_hz==before['SELECTED']['hz'])
        try:
            d.scan.stop();d.vfos.enable();d.gains.squelch_raw=255
            d.vfos['SELECTED'].mode=VfoMode('LSB',False,1)
            for span in SPANS:
                d.scan.stop();d.vfos['SELECTED'].frequency_hz=7100000
                d.scan.set_delta_span_hz(span);check(str(span)+'_accepted',True)
                if args.simulate:check(str(span)+'_logical_span',d._simulation.scan.span_hz==span)
                row={'span_hz':span,'center_hz':7100000,'frequencies':[]};r['scans'].append(row);save()
                try:
                    assert idle();d.scan.start('DELTA')
                    for _ in range(12):
                        time.sleep(.1);row['frequencies'].append(d.radio.frequency_hz);save()
                    row['motion_observed']=len(set(row['frequencies']))>1
                    check(str(span)+'_samples_in_requested_range',all(7100000-span<=f<=7100000+span for f in row['frequencies']))
                    check(str(span)+'_idle',idle())
                finally:d.scan.stop()
                stable=[]
                for _ in range(3):time.sleep(.1);stable.append(d.radio.frequency_hz)
                row['stopped_frequencies']=stable;check(str(span)+'_stop_stable',len(set(stable))==1)
        except BaseException as exc:r['failure']=str(exc);save();raise
        finally:
            try:
                d.scan.stop();d.vfos.enable()
                # Span restoration is done in the same known-supported LSB context.
                d.vfos['SELECTED'].mode=VfoMode('LSB',False,1)
                d.scan.set_delta_span_hz(args.initial_span_hz)
                r['span_restore_command_accepted']=True
                if args.simulate:check('logical_original_span_restored',d._simulation.scan.span_hz==args.initial_span_hz)
                for s in ['SELECTED','OTHER']:
                    d.vfos[s].mode=VfoMode(**before[s]['mode']);d.vfos[s].frequency_hz=before[s]['hz']
                d.gains.squelch_raw=sql;r['after']=state()
                check('vfos_restored',r['after']==before);check('sql_restored',d.gains.squelch_raw==sql)
                check('idle_after',idle())
            except BaseException as exc:r['restore_failure']=str(exc);save();raise
    print(json.dumps({'checks':len(r['cases']),'simulation':args.simulate,
                      'motion':{str(x['span_hz']):x.get('motion_observed') for x in r['scans']},'restored':True}))


if __name__=='__main__':main()
