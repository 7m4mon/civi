"""Manual VFO select/relative-setting/swap test with explicit initial selector.

No RF, stored-memory or permission writes. COPY is deliberately not exercised.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,VfoMode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--initial-vfo',choices=['A','B'],required=True)
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'simulation':args.simulate,'initial_vfo_owner_confirmed':args.initial_vfo,
            'cases':[],'wire':[],'transmit_memory_writes':False}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def check(name,condition,detail=None):
        report['cases'].append({'name':name,'passed':bool(condition),'detail':detail});save()
        if not condition:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        allowed={'RAD:VFO:SELECT','RAD:VFO:ENABLE','RAD:VFO:SWAP','RAD:VFO:FREQ','RAD:VFO:MODE'}
        def guarded(data):
            for command in data.decode().strip().split(';'):
                if '?' not in command and command.split(' ',1)[0] not in allowed:raise RuntimeError('Unapproved write '+command)
            report['wire'].append(data.decode().strip());save();return original(data)
        d._send=guarded
        def state():return {s:{'frequency':d.vfos[s].frequency_hz,'mode':asdict(d.vfos[s].mode)} for s in ['SELECTED','OTHER']}
        def idle():return not d.radio.transmitting and not d.operations.vox_enabled and d.operations.break_in=='OFF' and d.operations.tuner=='OFF'
        assert idle()
        report['baseline']=before=state();save()
        assert d.radio.frequency_hz==before['SELECTED']['frequency'],'Initial display is not the confirmed VFO'
        try:
            d.vfos.enable();check('enable_preserves_vfo_state',state()==before)
            d.vfos.select('B' if args.initial_vfo=='A' else 'A')
            check('select_other_absolute',state()=={'SELECTED':before['OTHER'],'OTHER':before['SELECTED']})
            d.vfos.select(args.initial_vfo);check('select_original_absolute',state()==before)
            for selector in ['SELECTED','OTHER']:
                view=d.vfos[selector]
                check('view_name_'+selector,view.name==selector)
                check('case_insensitive_view_'+selector,d.vfos[selector.lower()] is view)
                frequency=before[selector]['frequency']
                for target in [30000,7100000,60000000]:
                    assert idle();view.frequency_hz=target
                    check('relative_frequency_'+selector+'_'+str(target),view.frequency_hz==target)
                view.frequency_hz=frequency
                for mode in ['LSB','USB','AM','CW','RTTY','FM','CW-R','RTTY-R']:
                    value=VfoMode(mode,False,2);view.mode=value
                    check('relative_mode_'+selector+'_'+mode,view.mode==value)
                for data in [False,True]:
                    for filter_number in [1,2,3]:
                        value=VfoMode('USB',data,filter_number);view.mode=value
                        check('mode_data_filter_'+selector+'_'+str(data)+'_'+str(filter_number),view.mode==value)
                view.mode=VfoMode(**before[selector]['mode'])
                check('relative_view_restored_'+selector,state()==before)
                for bad in [29999,60000001,True]:
                    count=len(report['wire'])
                    try:view.frequency_hz=bad
                    except (ValueError,TypeError):check('invalid_frequency_'+selector+'_'+str(bad),len(report['wire'])==count)
                    else:check('invalid_frequency_'+selector+'_'+str(bad),False)
                count=len(report['wire'])
                try:view.mode='USB'
                except TypeError:check('invalid_mode_type_'+selector,len(report['wire'])==count)
                else:check('invalid_mode_type_'+selector,False)
            d.vfos.swap();check('swap_contents',state()=={'SELECTED':before['OTHER'],'OTHER':before['SELECTED']})
            d.vfos.swap();check('swap_back',state()==before)
            for bad in ['INVALID',1]:
                count=len(report['wire'])
                try:d.vfos[bad]
                except (ValueError,TypeError):check('invalid_relative_'+str(bad),len(report['wire'])==count)
                else:check('invalid_relative_'+str(bad),False)
            for bad in ['C',1]:
                count=len(report['wire'])
                try:d.vfos.select(bad)
                except (ValueError,TypeError):check('invalid_absolute_'+str(bad),len(report['wire'])==count)
                else:check('invalid_absolute_'+str(bad),False)
        except BaseException as e:report['failure']=type(e).__name__+': '+str(e);save();raise
        finally:
            try:
                assert idle();d.vfos.select(args.initial_vfo)
                for selector in ['SELECTED','OTHER']:
                    d.vfos[selector].mode=VfoMode(**before[selector]['mode'])
                    d.vfos[selector].frequency_hz=before[selector]['frequency']
                report['restored']=state();save();assert report['restored']==before
            except BaseException as e:report['restore_failure']=str(e);save();raise
    print(json.dumps({'checks':len(report['cases']),'restored':True,'simulation':args.simulate}))


if __name__=='__main__':main()
