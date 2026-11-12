"""Manual scan STOP/resume test; no scan start or memory selection changes.

Resume is backed up/read back using the documented menu 0179. Other write-only
scan options are tested with invalid input only, never guessed for restoration.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--operate-resume',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'simulation':args.simulate,'cases':[],'wire':[],'scan_start_sent':False,
            'memory_group_writes':False,'prior_scan_running_state_not_queryable':True}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def check(name,value,detail=None):
        report['cases'].append({'name':name,'passed':bool(value),'detail':detail});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        def guarded(data):
            text=data.decode().strip()
            if any('?' not in c and c not in ['RAD:SCAN:STOP','RAD:SCAN:RESUMEOFF','RAD:SCAN:RESUMEON'] for c in text.split(';')):
                raise RuntimeError('Scan mutation outside allowlist')
            report['wire'].append(text);save();return original(data)
        d._send=guarded
        before=d.menus[179].value;report['resume_before']=before
        report['frequency_before']=d.radio.frequency_hz;save()
        try:
            assert not d.radio.transmitting
            d.scan.stop();check('stop_command_accepted',True)
            for value in [False,True]:
                d.scan.set_resume_enabled(value)
                actual=(d._simulation.scan.resume_enabled if args.simulate else d.menus[179].value)
                check('resume_'+str(value),actual==value,{'readback':actual,'source':'logical simulator' if args.simulate else 'CI-V menu 0179'})
            invalid=[('start',lambda:d.scan.start('INVALID')),('start_type',lambda:d.scan.start(1)),
                ('delta_low',lambda:d.scan.set_delta_span_hz(4999)),('delta_high',lambda:d.scan.set_delta_span_hz(1000001)),
                ('delta_choice',lambda:d.scan.set_delta_span_hz(12345)),('delta_type',lambda:d.scan.set_delta_span_hz(True)),
                ('select_type',lambda:d.scan.set_select_enabled(1)),('resume_type',lambda:d.scan.set_resume_enabled('ON')),
                ('assign_low',lambda:d.scan.assign_selected_memory_group(0)),('assign_high',lambda:d.scan.assign_selected_memory_group(4)),
                ('group_low',lambda:d.scan.set_memory_group(-1)),('group_high',lambda:d.scan.set_memory_group(4))]
            for name,call in invalid:
                count=len(report['wire'])
                try:call()
                except (ValueError,TypeError):check('invalid_'+name,len(report['wire'])==count)
                else:check('invalid_'+name,False)
        except BaseException as e:report['failure']=str(e);save();raise
        finally:
            try:
                d.scan.set_resume_enabled(before)
                report['resume_restored']=(d._simulation.scan.resume_enabled if args.simulate else d.menus[179].value)
                report['frequency_after']=d.radio.frequency_hz;save()
                assert report['resume_restored']==before
                assert report['frequency_after']==report['frequency_before']
            except BaseException as e:report['restore_failure']=str(e);save();raise
    print(json.dumps({'checks':len(report['cases']),'resume_restored':True,'simulation':args.simulate}))


if __name__=='__main__':main()
