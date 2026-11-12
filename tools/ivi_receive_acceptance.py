"""Opt-in IVI receive/core acceptance with durable state and wire allowlist.

Not a complete IVI conformance procedure. Never invoked by pytest or startup.
No PTT/VOX/tuner/storage/calibration writes. Requires explicit --write-receive.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300, DeviceError, VfoMode, __version__


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulate',action='store_true')
    parser.add_argument('--write-receive',action='store_true')
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),
            'client_version':__version__,'simulation':args.simulate,
            'transmit_storage_calibration_writes':False,'cases':[],'wire':[],
            'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (ROOT/'drivers/civi-ic7300/src/civi_ic7300').glob('*.py')}}
    def save():
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def check(name,condition,detail=None):
        report['cases'].append({'name':name,'passed':bool(condition),'detail':detail})
        save()
        if not condition:raise AssertionError(name)
    def snapshot(d):
        return {'selected_frequency':d.vfos['SELECTED'].frequency_hz,
                'selected_mode':asdict(d.vfos['SELECTED'].mode),
                'other_frequency':d.vfos['OTHER'].frequency_hz,
                'other_mode':asdict(d.vfos['OTHER'].mode),
                'ptt':d.radio.transmitting,'vox':d.operations.vox_enabled,
                'break_in':d.operations.break_in,'tuner':d.operations.tuner}
    with CiviIc7300(args.resource,timeout_ms=5000,
                   options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original_send=d._send
        def constrained_send(data):
            text=data.decode('ascii').strip()
            for part in text.split(';'):
                if '?' not in part and not (part=='*CLS' or part=='CIVI:DRIVER:INVALID'
                    or (args.write_receive and part.startswith(('SENS:FREQ ','RAD:MODE ','RAD:VFO:MODE SELECTED,')))):
                    raise RuntimeError('Wire mutation outside allowlist: '+part)
            report['wire'].append(text);save()
            return original_send(data)
        d._send=constrained_send
        report['identity']=asdict(d.ivi_utility.identification)
        report['baseline']=baseline=snapshot(d);save()
        check('receive_only_preconditions',not baseline['ptt'] and not baseline['vox']
              and baseline['break_in']=='OFF' and baseline['tuner']=='OFF',baseline)
        try:
            utility=d.ivi_utility
            check('model_and_metadata',utility.instrument_model=='CIVI/IC-7300'
                  and utility.driver_version==__version__
                  and utility.simulation_enabled==args.simulate)
            report['utility']={'vendor':utility.driver_vendor,
                'manufacturer':utility.instrument_manufacturer,
                'models':list(utility.supported_instrument_models),
                'firmware_metadata':d.radio.firmware_revision}
            check('smeter_range',0<=d.radio.smeter_raw<=255)
            utility.clear_status();utility.wait_for_complete()
            check('initial_empty_error_queue',utility.error_query() is None and utility.error_query_all()==())
            io=d.ivi_direct_io
            timeout=io.io_timeout_ms
            try:
                for value in [1,1000,5000]:
                    io.io_timeout_ms=value
                    check('timeout_local_'+str(value),io.io_timeout_ms==value)
            finally:io.io_timeout_ms=timeout
            io.write_string('*IDN?')
            check('direct_io_string',report['identity']['model'] in io.read_string())
            io.write_bytes(b'*IDN?\n')
            check('direct_io_bytes',b'CIVI/IC-7300' in io.read_bytes())
            if args.simulate:
                # The logical simulator intentionally has no arbitrary raw
                # SCPI parser. Do not report physical/parser error injection.
                utility.raise_on_device_error()
                check('raise_on_empty_error_queue',True)
            else:
                io.write_string('CIVI:DRIVER:INVALID')
                error=utility.error_query()
                check('error_query_undefined_header',error is not None and error.code==-113)
                io.write_string('CIVI:DRIVER:INVALID')
                try:utility.raise_on_device_error()
                except DeviceError as e:check('raise_on_device_error',bool(e.errors) and e.errors[0].code==-113)
                else:check('raise_on_device_error',False)
            check('error_queue_drained',utility.error_query_all()==())
            for attr,values in [('frequency_hz',[29999,60000001,True]),('mode',['INVALID',1])]:
                for value in values:
                    sent=len(report['wire'])
                    try:setattr(d.radio,attr,value)
                    except (ValueError,TypeError):check('reject_'+attr+'_'+str(value),len(report['wire'])==sent)
                    else:check('reject_'+attr+'_'+str(value),False)
            if args.write_receive:
                for value in [30000,14000000,60000000]:
                    check('ptt_off_before_frequency',not d.radio.transmitting)
                    d.radio.frequency_hz=value
                    check('frequency_'+str(value),d.radio.frequency_hz==value)
                d.radio.frequency_hz=baseline['selected_frequency']
                for value in ['LSB','USB','AM','CW','RTTY','FM','CW-R','RTTY-R']:
                    check('ptt_off_before_mode',not d.radio.transmitting)
                    d.radio.mode=value
                    check('mode_'+value,d.radio.mode==value)
        except BaseException as e:
            report['failure']=type(e).__name__+': '+str(e)
            save()
            raise
        finally:
            if args.write_receive:
                try:
                    if d.radio.transmitting:raise RuntimeError('PTT unexpectedly ON; no further receive changes')
                    d.vfos['SELECTED'].mode=VfoMode(**baseline['selected_mode'])
                    d.radio.frequency_hz=baseline['selected_frequency']
                    report['restored']=snapshot(d)
                    check('full_baseline_restored',report['restored']==baseline)
                except BaseException as e:
                    report['restore_failure']=type(e).__name__+': '+str(e)
                    save()
                    raise
            report['ended_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({'simulation':args.simulate,'passed_cases':len(report['cases']),
                      'restored':report.get('restored')==report['baseline'],
                      'output':str(args.output)},ensure_ascii=False))


if __name__=='__main__':main()
