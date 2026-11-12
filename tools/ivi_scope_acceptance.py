"""Manual scope get/set/stream acceptance. Fixed-edge records are read only."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,DeviceError

CASES=[
    ('enabled',[False,True],[1],None,'ENABLE'),
    ('streaming_enabled',[False,True],[1],None,'STREAM'),
    ('hold_enabled',[False,True],[1],None,'HOLD'),
    ('tx_display_enabled',[False,True],[1],0,'TXDISPLAY'),
    ('vbw_enabled',[False,True],[1],None,'VBW'),
    ('marker_enabled',[False,True],[1],1,'MARKER'),
    ('mode_code',[0,1,2,3],[-1,4],None,'MODE'),
    ('edge_number',[1,2,3,4],[0,5],1,'EDGE'),
    ('speed_code',[0,1,2],[-1,3],None,'SPEED'),
    ('center_mode_code',[0,1,2],[-1,3],0,'CENTER'),
    ('display_code',[0],[1,True],None,'DISPLAY'),
    ('dual_scope_code',[0],[1,True],None,'DUAL'),
    ('span_hz',[2500,5000,10000,25000,50000,100000,250000,500000],[0,3000],0,'SPAN'),
    ('reference_db',[-20,-19.5,0,19.5,20],[-20.5,20.5,.25,True],None,'REFERENCE'),
]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--operate-scope',action='store_true',required=True)
    p.add_argument('--firmware',default='Unknown')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'simulation':args.simulate,
            'firmware_owner_reported':args.firmware,'cases':[],'edges':[],'wire':[],
            'transmit_frequency_memory_writes':False}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def check(name,condition,detail=None):
        report['cases'].append({'name':name,'passed':bool(condition),'detail':detail});save()
        if not condition:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        allowed={'RAD:SCOPE:'+c[4] for c in CASES}
        def guarded(data):
            for command in data.decode().strip().split(';'):
                if '?' not in command and command.split(' ',1)[0] not in allowed:raise RuntimeError('Unapproved mutation '+command)
            report['wire'].append(data.decode().strip());save();return original(data)
        d._send=guarded;s=d.scope
        def snapshot():return {c[0]:getattr(s,c[0]) for c in CASES}
        def radio():return {v:{'hz':d.vfos[v].frequency_hz,'mode':d.vfos[v].mode._encode()} for v in ['SELECTED','OTHER']}
        assert not d.radio.transmitting
        report['baseline']=before=snapshot();report['radio_before']=radio();save()
        try:
            for name,values,invalid,mode,header in CASES:
                if mode is not None:s.mode_code=mode
                for value in values:
                    setattr(s,name,value);actual=getattr(s,name)
                    check(name+'_'+str(value),actual==value,{'input':value,'readback':actual})
                for value in invalid:
                    count=len(report['wire'])
                    try:setattr(s,name,value)
                    except (TypeError,ValueError):check('invalid_'+name+'_'+str(value),len(report['wire'])==count)
                    else:check('invalid_'+name+'_'+str(value),False)
            s.mode_code=0;s.hold_enabled=False;s.start_stream()
            check('start_stream',s.enabled and s.streaming_enabled)
            deadline=time.monotonic()+10
            while True:
                try:sweep=s.read_sweep();break
                except DeviceError:
                    if time.monotonic()>=deadline:raise
                    time.sleep(.2)
            check('complete_sweep',not sweep.out_of_range and len(sweep.points)==475,
                  {'points':len(sweep.points),'minimum':min(sweep.points) if sweep.points else None,
                   'maximum':max(sweep.points) if sweep.points else None,'mode':sweep.mode})
            s.stop_stream();check('stop_stream',not s.streaming_enabled)
            for band in range(1,14):
                for edge in range(1,5):
                    value=s.read_fixed_edges(band,edge)
                    report['edges'].append({'band':band,'edge':edge,'lower_hz':value.lower_hz,'upper_hz':value.upper_hz});save()
            for band,edge in [(0,1),(14,1),(1,0),(1,5)]:
                count=len(report['wire'])
                try:s.read_fixed_edges(band,edge)
                except (TypeError,ValueError):check('invalid_edge_'+str(band)+'_'+str(edge),len(report['wire'])==count)
                else:check('invalid_edge_'+str(band)+'_'+str(edge),False)
        except BaseException as e:report['failure']=type(e).__name__+': '+str(e);save();raise
        finally:
            failures=[]
            def restore(name,value):
                try:setattr(s,name,value)
                except Exception as e:failures.append(name+': '+str(e))
            restore('streaming_enabled',False);restore('hold_enabled',False)
            restore('mode_code',0)
            for name in ['span_hz','center_mode_code','tx_display_enabled']:restore(name,before[name])
            restore('mode_code',1)
            for name in ['edge_number','marker_enabled']:restore(name,before[name])
            for name in ['reference_db','speed_code','vbw_enabled','display_code','dual_scope_code']:restore(name,before[name])
            for name in ['mode_code','enabled','hold_enabled','streaming_enabled']:restore(name,before[name])
            try:
                report['restored']=snapshot();report['radio_after']=radio();save()
                if report['restored']!=before:failures.append('Scope snapshot differs')
                if report['radio_after']!=report['radio_before']:failures.append('Radio VFO changed')
                if d.radio.transmitting:failures.append('Unexpected PTT state')
            except Exception as e:failures.append('Readback: '+str(e))
            report['restore_errors']=failures;report['ended_utc']=datetime.now(timezone.utc).isoformat();save()
            if failures:raise RuntimeError('Restoration requires review: '+repr(failures))
    print(json.dumps({'checks':len(report['cases']),'fixed_edge_reads':len(report['edges']),
                      'restored':True,'simulation':args.simulate}))


if __name__=='__main__':main()
