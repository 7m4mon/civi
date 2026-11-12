"""Opt-in select group/filter tests on empty channels 94..99 with restoration."""
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
    p.add_argument('--initial-group',type=int,choices=range(4),
                   help='Owner-confirmed original filter; omit to skip filter writes')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--allow-scan-settings',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    channels=list(range(94,100)) if args.initial_group is not None else [99]
    r={'simulation':args.simulate,'initial_filter_owner_reported':args.initial_group,
       'filter_test_skipped':args.initial_group is None,
       'cases':[],'wire':[],'filters':[],'rf_start':False,'scratch_channels':channels,
       'select_read_source':'logical simulator state' if args.simulate else 'addressed memory 99 record'}
    def save():args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    def check(name,value):
        r['cases'].append({'name':name,'passed':bool(value)});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        if args.simulate and args.initial_group is not None:d.scan.set_memory_group(args.initial_group)
        original=d._send
        allowed={'RAD:MEM:ENABLE','RAD:VFO:ENABLE','RAD:VFO:FREQ','RAD:VFO:MODE','RAD:SQL',
                 'RAD:SCAN:STOP','RAD:SCAN:SELECTMEM','RAD:SCAN:GROUP','RAD:SCAN:SELECT',
                 'RAD:SCAN:SELECTON','RAD:SCAN:SELECTOFF'}
        def guarded(data):
            text=data.decode().strip()
            for cmd in text.split(';'):
                if '?' in cmd:continue
                head=cmd.split(' ',1)[0]
                if head in allowed:continue
                if head in ('RAD:MEM:CONTENT','RAD:MEM:SELECT') and int(cmd.split(' ',1)[1].split(',')[0]) in range(94,100):continue
                raise RuntimeError('Unapproved select mutation '+cmd)
            r['wire'].append(text);save();return original(data)
        d._send=guarded
        def state():return {s:{'hz':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle():return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        def group_read():
            if args.simulate:
                s=d._simulation.scan
                return (s.last_assigned_group or 1) if s.select_enabled else 0
            record=d.memories[99].record
            if record is None:raise RuntimeError('Test memory missing')
            return record.select_group
        check('idle_before',idle());check('split_off',not d.radio.split_enabled)
        before=r['before']=state();sql=r['sql_before']=d.gains.squelch_raw
        check('scratch_all_empty',all(d.memories[n].record is None for n in channels))
        touched=[];original_effective_group=None
        if args.simulate:d.memories.set_simulated_write_permission(True)
        try:
            d.scan.stop();d.gains.squelch_raw=255
            for i,n in enumerate(channels):
                block=MemorySettings(7100000+i*1000,'LSB')
                record=MemoryRecord(block,block,select_group=i//2+1,name=f'CIVISEL{n}')
                touched.append(n);check('scratch_'+str(n),d.memories[n].write_and_read(record)==record)
            for group in (range(4) if args.initial_group is not None else []):
                d.scan.stop();d.memories.select(94);d.memories.enable()
                d.scan.set_memory_group(group);check('filter_'+str(group)+'_accepted',True)
                if args.simulate:check('filter_'+str(group)+'_logical',d._simulation.scan.memory_group==group)
                row={'group':group,'frequencies':[]};r['filters'].append(row);save()
                try:
                    assert idle();d.scan.start('SELECTMEM')
                    for _ in range(8):
                        time.sleep(.1);row['frequencies'].append(d.radio.frequency_hz);save()
                    row['motion_observed']=len(set(row['frequencies']))>1
                    if not args.simulate:
                        eligible={7100000+i*1000 for i in range(6) if group==0 or i//2+1==group}
                        check('filter_'+str(group)+'_eligible_frequencies',all(f in eligible for f in row['frequencies']))
                finally:d.scan.stop()
            d.memories.select(99);d.memories.enable()
            d.scan.set_select_enabled(False);check('initial_select_off',group_read()==0)
            d.scan.set_select_enabled(True)
            original_effective_group=group_read();r['original_effective_select_group']=original_effective_group;save()
            check('initial_effective_group_valid',original_effective_group in (1,2,3))
            for group in [1,2,3]:
                d.scan.assign_selected_memory_group(group);check('assign_'+str(group),group_read()==group)
                d.scan.set_select_enabled(False);check('select_off_after_'+str(group),group_read()==0)
                d.scan.set_select_enabled(True);check('select_on_after_'+str(group),group_read()==group)
            check('idle_after_changes',idle())
        except BaseException as exc:r['failure']=str(exc);save();raise
        finally:
            errors=[]
            try:
                d.scan.stop()
                if original_effective_group is not None:
                    d.memories.select(99);d.memories.enable()
                    d.scan.assign_selected_memory_group(original_effective_group)
                    d.scan.set_select_enabled(False);d.scan.set_select_enabled(True)
                    check('effective_select_group_restored',group_read()==original_effective_group)
                if args.initial_group is not None:
                    d.scan.set_memory_group(args.initial_group);r['original_filter_restore_accepted']=True
                    if args.simulate:check('logical_filter_restored',d._simulation.scan.memory_group==args.initial_group)
                d.memories.select(99);d.vfos.enable()
            except BaseException as exc:errors.append(str(exc))
            for n in touched:
                try:d.memories[n].clear()
                except BaseException as exc:errors.append(f'memory {n}: {exc}')
            try:
                for s in ['SELECTED','OTHER']:
                    d.vfos[s].mode=VfoMode(**before[s]['mode']);d.vfos[s].frequency_hz=before[s]['hz']
                d.gains.squelch_raw=sql;r['after']=state()
                check('scratch_restored_empty',all(d.memories[n].record is None for n in channels))
                check('vfos_restored',r['after']==before);check('sql_restored',d.gains.squelch_raw==sql)
                check('idle_after',idle())
            except BaseException as exc:errors.append(str(exc))
            r['restore_errors']=errors;save()
            if args.simulate:d.memories.set_simulated_write_permission(False)
            if errors:raise RuntimeError('Restoration failed; consult report: '+str(errors))
    print(json.dumps({'checks':len(r['cases']),'simulation':args.simulate,
                      'filter_motion':{str(x['group']):x.get('motion_observed') for x in r['filters']},'restored':True}))


if __name__=='__main__':main()
