"""Opt-in all-slot band-stack/keyer write/read/restore. No CW send command."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300, VfoMode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--allow-storage-write',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    r={'simulation':args.simulate,'cases':[],'wire':[],'backups':{'stacks':{},'keyers':{}},
       'rf_start':False,'cw_send':False,'changed_slots':[]}
    def save():args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    def check(name,value):
        r['cases'].append({'name':name,'passed':bool(value)});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        allowed={'RAD:BAND:STACK','RAD:KEYER:TEXT','RAD:VFO:ENABLE','RAD:VFO:FREQ','RAD:VFO:MODE'}
        def guarded(data):
            text=data.decode().strip()
            if any('?' not in c and c.split(' ',1)[0] not in allowed for c in text.split(';')):
                raise RuntimeError('Unapproved storage mutation')
            r['wire'].append(text);save();return original(data)
        d._send=guarded
        def state():return {s:{'hz':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle():return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        check('idle_before',idle());before=r['vfos_before']=state()
        check('initial_vfo_display',d.radio.frequency_hz==before['SELECTED']['hz'])
        stacks={(b,s):d.band_stacks[b,s].settings for b,s in d.band_stacks}
        keyers={n:d.keyers[n].text for n in d.keyers}
        r['backups']['stacks']={f'{b}:{s}':v.to_hex() for (b,s),v in stacks.items()}
        r['backups']['keyers']={str(n):v for n,v in keyers.items()};save()
        check('all_backups_before_write',len(stacks)==33 and len(keyers)==8)
        if args.simulate:d.band_stacks.set_simulated_write_permission(True)
        touched_stacks=set();touched_keyers=set()
        bases=[1850000,3700000,7100000,10100000,14100000,18100000,21100000,24900000,28500000,50100000,2500000]
        try:
            for (band,slot),old in stacks.items():
                assert idle()
                value=replace(old,frequency_hz=bases[band-1]+slot*100,mode='USB',filter_number=2,data=True)
                if value==old:value=replace(value,frequency_hz=value.frequency_hz+10)
                touched_stacks.add((band,slot));r['changed_slots'].append(f'stack:{band}:{slot}');save()
                item=d.band_stacks[band,slot]
                try:check(f'stack_{band}_{slot}_write_read',item.write_and_read(value)==value)
                finally:item.settings=old
                check(f'stack_{band}_{slot}_restored',item.settings==old)
            for number,old in keyers.items():
                assert idle();value=f'CQ TEST, M{number} ^AR'
                if value==old:value=f'CIVI TEST M{number}'
                touched_keyers.add(number);r['changed_slots'].append(f'keyer:{number}');save()
                item=d.keyers[number]
                try:check(f'keyer_{number}_write_read',item.write_and_read(value)==value)
                finally:item.text=old
                check(f'keyer_{number}_restored',item.text==old)
        except BaseException as exc:r['failure']=str(exc);save();raise
        finally:
            errors=[]
            for band,slot in touched_stacks:
                try:
                    item=d.band_stacks[band,slot]
                    if item.settings!=stacks[band,slot]:item.settings=stacks[band,slot]
                except BaseException as exc:errors.append(f'stack:{band}:{slot}: {exc}')
            for n in touched_keyers:
                try:
                    if d.keyers[n].text!=keyers[n]:d.keyers[n].text=keyers[n]
                except BaseException as exc:errors.append(f'keyer:{n}: {exc}')
            try:
                d.vfos.enable()
                for s in ['SELECTED','OTHER']:
                    d.vfos[s].mode=VfoMode(**before[s]['mode']);d.vfos[s].frequency_hz=before[s]['hz']
                check('all_stack_backups_match',all(d.band_stacks[b,s].settings==old for (b,s),old in stacks.items()))
                check('all_keyer_backups_match',all(d.keyers[n].text==old for n,old in keyers.items()))
                r['vfos_after']=state();check('both_vfos_restored',r['vfos_after']==before)
                check('idle_after',idle())
            except BaseException as exc:errors.append(str(exc))
            r['restore_errors']=errors;save()
            if args.simulate:d.band_stacks.set_simulated_write_permission(False)
            if errors:raise RuntimeError('Restoration incomplete; consult saved backups: '+str(errors))
    print(json.dumps({'checks':len(r['cases']),'stacks':len(stacks),'keyers':len(keyers),
                      'simulation':args.simulate,'restored':True}))


if __name__=='__main__':main()
