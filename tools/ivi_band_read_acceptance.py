"""Manual band-record reads and rejection of simulator-only permission APIs."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,BandEdges


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'simulation':args.simulate,'band_record_writes':False,'cases':[],'wire':[],'records':[]}
    def save():args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def check(name,value):
        report['cases'].append({'name':name,'passed':bool(value)});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        def guarded(data):
            text=data.decode().strip()
            if any('?' not in c for c in text.split(';')):raise RuntimeError('Band test forbids writes')
            report['wire'].append(text);save();return original(data)
        d._send=guarded
        default=d.bands.default_edges;report['default_edges']=asdict(default)
        check('default_roundtrip',BandEdges.from_hex(default.to_hex())==default)
        report['counts']={'factory':d.bands.factory_count,'user':d.bands.user_count};save()
        for kind in ['factory','user']:
            for index in range(1,report['counts'][kind]+1):
                value=getattr(d.bands,'read_'+kind)(index)
                report['records'].append({'kind':kind,'index':index,'value':None if value is None else asdict(value)})
                check(kind+'_roundtrip_'+str(index),kind=='user' if value is None else BandEdges.from_hex(value.to_hex())==value)
        for name,call in [('factory_zero',lambda:d.bands.read_factory(0)),('factory_high',lambda:d.bands.read_factory(31)),
                          ('user_zero',lambda:d.bands.read_user(0)),('user_high',lambda:d.bands.read_user(31))]:
            count=len(report['wire'])
            try:call()
            except (ValueError,TypeError):check(name,len(report['wire'])==count)
            else:check(name,False)
        for group in ['memories','band_stacks','keyers','bands']:
            instance=getattr(d,group)
            method=getattr(instance,'set_simulated_calibration_permission' if group=='bands' else 'set_simulated_write_permission')
            count=len(report['wire'])
            if args.simulate:
                method(True);method(False);check('simulated_permission_'+group,len(report['wire'])==count)
            else:
                try:method(True)
                except RuntimeError:check('real_permission_api_rejected_'+group,len(report['wire'])==count)
                else:check('real_permission_api_rejected_'+group,False)
    save();print(json.dumps({'counts':report['counts'],'record_reads':len(report['records']),
                            'checks':len(report['cases']),'simulation':args.simulate}))


if __name__=='__main__':main()
