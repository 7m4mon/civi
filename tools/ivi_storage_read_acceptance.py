"""Opt-in addressed reads of all storage instances. Never writes stored data."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'drivers/civi-ic7300/src'))
from civi_ic7300 import CiviIc7300,MemoryRecord,MemorySettings,DeviceError,ProtocolError


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resource',default='TCPIP::192.168.73.2::5025::SOCKET')
    p.add_argument('--simulate',action='store_true')
    p.add_argument('--firmware',default='Unknown')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'simulation':args.simulate,
            'firmware_owner_reported':args.firmware,'stored_data_writes':False,'reads':[],'wire':[],'checks':[]}
    def save():args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def check(name,value):
        report['checks'].append({'name':name,'passed':bool(value)});save()
        if not value:raise AssertionError(name)
    with CiviIc7300(args.resource,options={'simulate':args.simulate,'query_instrument_status':True}) as d:
        original=d._send
        def query_only(data):
            text=data.decode().strip()
            if any('?' not in command for command in text.split(';')):raise RuntimeError('Storage read test forbids writes')
            report['wire'].append(text);save();return original(data)
        d._send=query_only
        for number in d.memories:
            item=d.memories[number];record={'api':'memories['+str(number)+'].record','number':number,'selector_name':item.name}
            try:
                value=item.record
                record.update(status='read',value=asdict(value) if value else None)
                check('memory_identity_'+str(number),item.number==number)
                if value is not None:
                    check('memory_roundtrip_'+str(number),MemoryRecord.from_bytes(value.to_bytes())==value and MemoryRecord.from_hex(value.to_hex())==value)
            except (DeviceError,ProtocolError) as e:record.update(status='error',error=str(e))
            report['reads'].append(record);save()
        check('memory_collection_length',len(d.memories)==101)
        check('memory_named_edges',d.memories['P1'].number==100 and d.memories['P2'].number==101)
        for band in d.band_stacks.bands:
            view=d.band_stacks.bands[band]
            check('band_identity_'+str(band),view.number==band and view.name==str(band) and view.slots.band==band and len(view.slots)==3)
            for slot in view.slots:
                item=view.slots[slot];record={'api':'band_stacks['+str(band)+'].slots['+str(slot)+'].settings'}
                try:
                    value=item.settings;record.update(status='read',value=asdict(value))
                    check('band_view_'+str(band)+'_'+str(slot),item is d.band_stacks[band,slot] and item is d.band_stacks[band].slots[slot] and item.band==band and item.slot==slot and item.name==str(slot))
                    check('band_roundtrip_'+str(band)+'_'+str(slot),MemorySettings.from_bytes(value.to_bytes())==value and MemorySettings.from_hex(value.to_hex())==value)
                except (DeviceError,ProtocolError) as e:record.update(status='error',error=str(e))
                report['reads'].append(record);save()
        check('band_collection_lengths',len(d.band_stacks)==33 and len(d.band_stacks.bands)==11 and len(list(d.band_stacks))==33)
        for number in d.keyers:
            item=d.keyers[number];record={'api':'keyers['+str(number)+'].text'}
            try:record.update(status='read',text=item.text)
            except (DeviceError,ProtocolError) as e:record.update(status='error',error=str(e))
            check('keyer_identity_'+str(number),item.number==number and item.name=='M'+str(number))
            report['reads'].append(record);save()
        check('keyer_length',len(d.keyers)==8)
        invalid=[('memory',lambda:d.memories[0]),('memory_high',lambda:d.memories[102]),
                 ('band',lambda:d.band_stacks[0]),('band_high',lambda:d.band_stacks[12]),
                 ('slot',lambda:d.band_stacks[1].slots[0]),('slot_high',lambda:d.band_stacks[1].slots[4]),
                 ('keyer',lambda:d.keyers[0]),('keyer_high',lambda:d.keyers[9])]
        for label,call in invalid:
            count=len(report['wire'])
            try:call()
            except (ValueError,TypeError):check('invalid_'+label,len(report['wire'])==count)
            else:check('invalid_'+label,False)
    report['ended_utc']=datetime.now(timezone.utc).isoformat();save()
    errors=[{'api':r['api'],'error':r['error']} for r in report['reads'] if r['status']=='error']
    print(json.dumps({'reads':len(report['reads']),'successful':len(report['reads'])-len(errors),'errors':errors,'local_checks':len(report['checks'])}))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
