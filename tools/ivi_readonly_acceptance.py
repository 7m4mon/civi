"""Manual read-only driver inventory. No radio-setting commands are allowed."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,DeviceError,__version__
from civi_ic7300.controls import Setting


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--simulate',action='store_true')
    parser.add_argument('--menus',action='store_true')
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'client_version':__version__,'simulation':args.simulate,
            'started_utc':datetime.now(timezone.utc).isoformat(),
            'writes_performed':False,'reads':[],'wire':[],
            'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (ROOT/'drivers/civi-ic7300/src/civi_ic7300').glob('*.py')}}
    def save():args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        def query_only(data):
            text=data.decode('ascii').strip()
            if any('?' not in part for part in text.split(';')):
                raise RuntimeError('Read-only wire guard rejected '+text)
            report['wire'].append(text);save();return original(data)
        d._send=query_only
        try:
            for group in ['radio','gains','meters','operations','scope']:
                instance=getattr(d,group)
                definitions={name:value for cls in reversed(type(instance).__mro__)
                             for name,value in vars(cls).items() if isinstance(value,Setting)}
                for name,definition in definitions.items():
                    record={'api':group+'.'+name,'header':definition.header}
                    try:record.update(status='read',value=getattr(instance,name))
                    except DeviceError as e:
                        record.update(status='device_error',errors=[{'code':x.code,'message':x.message} for x in e.errors])
                    report['reads'].append(record);save()
            if args.menus:
                for number in d.menus:
                    menu=d.menus[number]
                    record={'api':'menus['+str(number)+'].value'}
                    try:record.update(status='read',value=menu.value)
                    except DeviceError as e:
                        record.update(status='device_error',errors=[{'code':x.code,'message':x.message} for x in e.errors])
                    report['reads'].append(record);save()
        except BaseException as e:
            report['failure']=type(e).__name__+': '+str(e);save();raise
        finally:
            report['ended_utc']=datetime.now(timezone.utc).isoformat();save()
    rejected=[r for r in report['reads'] if r['status']!='read']
    print(json.dumps({'reads':len(report['reads']),'successful':len(report['reads'])-len(rejected),
                      'device_errors':rejected,'output':str(args.output)},ensure_ascii=False))


if __name__=='__main__':main()
