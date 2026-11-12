"""Opt-in short memory scans with six empty scratch channels (94..99)."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,MemoryRecord,MemorySettings,VfoMode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--allow-memory-write',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    r={'simulation':args.simulate,'cases':[],'wire':[],'scans':[],'rf_start':False,
       'scan_group_writes':False,'delta_span_writes':False,'scratch_channels':list(range(94,100))}
    def save():args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    def check(name,result):
        r['cases'].append({'name':name,'passed':bool(result)});save()
        if not result:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        allowed={'RAD:MEM:ENABLE','RAD:VFO:ENABLE','RAD:VFO:FREQ','RAD:VFO:MODE','RAD:SQL',
                 'RAD:SCAN:STOP','RAD:SCAN:MEMORY','RAD:SCAN:SELECTMEM','RAD:SCAN:AUTO'}
        def guarded(data):
            text=data.decode().strip()
            for cmd in text.split(';'):
                if '?' in cmd:continue
                head=cmd.split(' ',1)[0]
                if head in allowed:continue
                if head in ('RAD:MEM:CONTENT','RAD:MEM:SELECT') and int(cmd.split(' ',1)[1].split(',')[0]) in range(94,100):continue
                raise RuntimeError('Unapproved mutation '+cmd)
            r['wire'].append(text);save();return original(data)
        d._send=guarded
        def state():return {s:{'hz':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle():return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        check('idle_before',idle());check('split_off',not d.radio.split_enabled)
        before=r['before']=state();sql=r['sql_before']=d.gains.squelch_raw
        empty={n:d.memories[n].record for n in range(94,100)}
        check('all_scratch_channels_empty',all(v is None for v in empty.values()))
        r['initial_records']={str(n):None for n in empty};save()
        if args.simulate:d.memories.set_simulated_write_permission(True)
        touched=[]
        try:
            d.scan.stop();d.gains.squelch_raw=255
            for i,n in enumerate(empty):
                value=MemoryRecord.simple(MemorySettings(7100000+i*1000,'LSB'),f'CIVISCAN{n}')
                value=MemoryRecord(value.receive,value.transmit,select_group=i//2+1,name=value.name)
                touched.append(n);check('write_scratch_'+str(n),d.memories[n].write_and_read(value)==value)
            for mode in ['MEMORY','SELECTMEM','AUTO']:
                d.memories.select(94);d.memories.enable();assert idle()
                row={'mode':mode,'frequencies':[]};r['scans'].append(row);save()
                try:
                    d.scan.start(mode);check(mode+'_accepted',True)
                    for _ in range(6):
                        time.sleep(.12);row['frequencies'].append(d.radio.frequency_hz);save()
                    row['motion_observed']=len(set(row['frequencies']))>1
                    if args.simulate:check(mode+'_logical_active',d._simulation.scan.mode==mode)
                    check(mode+'_idle',idle())
                finally:d.scan.stop()
                stopped=[]
                for _ in range(3):time.sleep(.12);stopped.append(d.radio.frequency_hz)
                row['stopped_frequencies']=stopped;save();check(mode+'_stop_stable',len(set(stopped))==1)
        except BaseException as exc:r['failure']=str(exc);save();raise
        finally:
            errors=[]
            try:d.scan.stop();d.memories.select(99);d.vfos.enable()
            except BaseException as exc:errors.append(str(exc))
            for n in touched:
                try:d.memories[n].clear()
                except BaseException as exc:errors.append(f'memory {n}: {exc}')
            try:
                for s in ['SELECTED','OTHER']:
                    d.vfos[s].mode=VfoMode(**before[s]['mode']);d.vfos[s].frequency_hz=before[s]['hz']
                d.gains.squelch_raw=sql;r['after']=state();r['sql_after']=d.gains.squelch_raw
                check('all_scratch_channels_restored_empty',all(d.memories[n].record is None for n in empty))
                check('both_vfos_restored',r['after']==before);check('sql_restored',r['sql_after']==sql)
                check('idle_after',idle())
            except BaseException as exc:errors.append(str(exc))
            r['restore_errors']=errors;save()
            if args.simulate:d.memories.set_simulated_write_permission(False)
            if errors:raise RuntimeError('Restoration failed: '+str(errors))
    print(json.dumps({'checks':len(r['cases']),'simulation':args.simulate,
                      'motion':{x['mode']:x.get('motion_observed') for x in r['scans']},'restored':True}))


if __name__=='__main__':main()
