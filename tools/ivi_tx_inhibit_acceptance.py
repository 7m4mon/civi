"""Manual TX Inhibit get/set/restore test; never starts transmission.

Only RAD:TXINHIBIT ON/OFF writes are permitted. PTT/VOX/break-in/tuner
must remain OFF. Firmware version is owner-supplied, not queried by CI-V.
"""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,__version__


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--firmware',default='Unknown',help='Owner-read MAIN firmware; never inferred by this tool')
    p.add_argument('--set-inhibit',action='store_true',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'client_version':__version__,
        'simulation':args.simulate,'radio_main_version':args.firmware if not args.simulate else None,
        'firmware_source':'owner report' if args.firmware!='Unknown' and not args.simulate else 'not supplied',
        'transmission_started':False,'cases':[],'wire':[],
        'source_hashes':{x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                        for x in (ROOT/'drivers/civi-ic7300/src/civi_ic7300').glob('*.py')}}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save()
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        def guarded(data):
            text=data.decode('ascii').strip()
            if any('?' not in part and part not in ('RAD:TXINHIBIT ON','RAD:TXINHIBIT OFF') for part in text.split(';')):
                raise RuntimeError('Unapproved mutation: '+text)
            report['wire'].append(text);save();return original(data)
        d._send=guarded
        def idle():
            return (not d.radio.transmitting and not d.operations.vox_enabled
                    and d.operations.break_in=='OFF' and d.operations.tuner=='OFF')
        def state():
            return {'tx_inhibited':d.operations.transmit_inhibited,
                'frequency_hz':d.radio.frequency_hz,'mode':asdict(d.vfos['SELECTED'].mode),
                'other_frequency_hz':d.vfos['OTHER'].frequency_hz,
                'other_mode':asdict(d.vfos['OTHER'].mode),'ptt':d.radio.transmitting}
        assert idle(), 'Radio is not in an idle receive-only state; no writes performed'
        report['identity']=asdict(d.ivi_utility.identification)
        report['baseline']=before=state();save()
        try:
            for value in [True,False]:
                assert idle(), 'Idle precondition changed'
                d.operations.transmit_inhibited=value
                actual=d.operations.transmit_inhibited
                passed=actual==value and not d.radio.transmitting
                report['cases'].append({'input':value,'readback':actual,'ptt':False if passed else d.radio.transmitting,'passed':passed});save()
                if not passed:raise AssertionError('TX inhibit readback mismatch')
            for value in [1,'ON',None]:
                count=len(report['wire'])
                try:d.operations.transmit_inhibited=value
                except (TypeError,ValueError):
                    assert count==len(report['wire'])
                    report['cases'].append({'invalid_input':value,'rejected_before_io':True,'passed':True});save()
                else:raise AssertionError('Invalid type accepted')
        except BaseException as e:
            report['failure']=type(e).__name__+': '+str(e);save();raise
        finally:
            try:
                assert idle(), 'Restore precondition changed; inspect radio before disabling inhibit'
                d.operations.transmit_inhibited=before['tx_inhibited']
                report['restored']=state();save()
                assert report['restored']==before,'Original state was not restored'
                report['error_queue_empty']=d.ivi_utility.error_query_all()==()
                assert report['error_queue_empty']
            except BaseException as e:
                report['restore_failure']=type(e).__name__+': '+str(e);save();raise
            report['ended_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({'simulation':args.simulate,'checks':len(report['cases']),
        'restored':report['restored']==before,'ptt':report['restored']['ptt'],'output':str(args.output)}))


if __name__=='__main__':main()
