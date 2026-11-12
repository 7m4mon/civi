"""Manual, allowlisted receive-setting boundary/enum tests and restoration.

No transmission, memory/menu/calibration writes or permission changes.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,VfoMode

CASES=[
    ('radio','preamp',['OFF','PRE1','PRE2'],['INVALID'],'RAD:PREAMP'),
    ('radio','agc',['FAST','MID','SLOW'],['INVALID'],'RAD:AGC'),
    ('radio','filter_shape',['SHARP','SOFT'],['INVALID'],'RAD:FILTER:SHAPE'),
    ('radio','attenuator_db',[0,20],[-1,21,10],'RAD:ATT'),
    ('radio','rit_offset_hz',[-9999,0,9999],[-10000,10000],'RAD:RIT:FREQ'),
    ('radio','rit_enabled',[False,True],[1],'RAD:RIT'),
    ('radio','noise_blanker_enabled',[False,True],[1],'RAD:NB'),
    ('radio','noise_reduction_enabled',[False,True],[1],'RAD:NR'),
    ('radio','automatic_notch_enabled',[False,True],[1],'RAD:ANOTCH'),
    ('radio','manual_notch_enabled',[False,True],[1],'RAD:NOTCH'),
    ('radio','notch_width',['WIDE','MID','NARROW'],['INVALID'],'RAD:NOTCH:WIDTH'),
    ('gains','rf_raw',[0,128,255],[-1,256],'RAD:RFGAIN'),
    ('gains','squelch_raw',[0,128,255],[-1,256],'RAD:SQL'),
    ('gains','noise_reduction_raw',[0,128,255],[-1,256],'RAD:NR:LEVEL'),
    ('gains','pbt_inner_raw',[0,128,255],[-1,256],'RAD:PBT:INNER'),
    ('gains','pbt_outer_raw',[0,128,255],[-1,256],'RAD:PBT:OUTER'),
]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--write-receive',action='store_true',required=True)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'simulation':args.simulate,'cases':[],'wire':[],'transmit_memory_calibration_writes':False}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        allowed={c[4] for c in CASES}|{'SENS:FREQ','RAD:MODE','RAD:VFO:MODE'}
        def guarded(data):
            for command in data.decode().strip().split(';'):
                if '?' not in command and command.split(' ',1)[0] not in allowed:
                    raise RuntimeError('Unapproved command '+command)
            report['wire'].append(data.decode().strip());save();return original(data)
        d._send=guarded
        def state():return {'hz':d.radio.frequency_hz,'mode':asdict(d.vfos['SELECTED'].mode),
                            'other_hz':d.vfos['OTHER'].frequency_hz,'other_mode':asdict(d.vfos['OTHER'].mode)}
        report['baseline']=before=state();save()
        assert not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        saved=[];restoration_errors=[]
        try:
            d.radio.frequency_hz=7100000;d.radio.mode='LSB'
            for group,name,values,invalid,header in CASES:
                instance=getattr(d,group);old=getattr(instance,name)
                saved.append((instance,group,name,old))
                report.setdefault('lsb_baseline',{})[group+'.'+name]=old;save()
            for instance,group,name,old in saved:
                spec=next(c for c in CASES if c[:2]==(group,name))
                actual_values=[]
                try:
                    for value in spec[2]:
                        assert not d.radio.transmitting
                        setattr(instance,name,value);actual=getattr(instance,name)
                        actual_values.append(actual)
                        if group=='gains' and name in ('noise_reduction_raw','pbt_inner_raw','pbt_outer_raw'):
                            # Physical NR/PBT have discrete levels within the raw
                            # 0..255 code space. Require stable/idempotent,
                            # bounded, nondecreasing readbacks, not exact echo.
                            setattr(instance,name,actual)
                            stable=getattr(instance,name)
                            passed=(type(actual) is int and 0<=actual<=255 and stable==actual
                                    and actual_values==sorted(actual_values))
                            record={'api':group+'.'+name,'input':value,'readback':actual,
                                    'coerced':actual!=value,'idempotent_readback':stable,
                                    'criterion':'bounded, stable, nondecreasing raw levels','passed':passed}
                        else:
                            passed=actual==value
                            record={'api':group+'.'+name,'input':value,'readback':actual,'passed':passed}
                        report['cases'].append(record);save()
                        if not passed:raise AssertionError('Readback/coercion requires review: '+group+'.'+name)
                    for value in spec[3]:
                        count=len(report['wire'])
                        try:setattr(instance,name,value)
                        except (ValueError,TypeError):
                            assert len(report['wire'])==count
                            report['cases'].append({'api':group+'.'+name,'invalid':value,'rejected_before_io':True,'passed':True});save()
                        else:raise AssertionError('Invalid value accepted')
                finally:
                    setattr(instance,name,old)
                    assert getattr(instance,name)==old
            report['lsb_restored']={group+'.'+name:getattr(instance,name) for instance,group,name,old in saved}
            assert report['lsb_restored']==report['lsb_baseline'];save()
        except BaseException as e:
            report['failure']=type(e).__name__+': '+str(e);save();raise
        finally:
            # Try every saved item even if one restore fails; preserve the report.
            for instance,group,name,old in reversed(saved):
                try:setattr(instance,name,old)
                except Exception as e:restoration_errors.append(group+'.'+name+': '+str(e))
            try:
                assert not d.radio.transmitting
                d.vfos['SELECTED'].mode=VfoMode(**before['mode']);d.radio.frequency_hz=before['hz']
                report['restored']=state();assert report['restored']==before
            except Exception as e:restoration_errors.append('VFO: '+str(e))
            report['restoration_errors']=restoration_errors;save()
            if restoration_errors:raise RuntimeError('Restoration requires attention: '+repr(restoration_errors))
    print(json.dumps({'simulation':args.simulate,'cases':len(report['cases']),'restored':True,'output':str(args.output)}))


if __name__=='__main__':main()
