"""Execute shipped Web scripts through failure/recovery; never use real radio/LAN."""
import base64
import json
import shutil
import subprocess

import pytest
from aiohttp.test_utils import TestClient, TestServer
from lxml import etree

from civi.indicator import LanIndicator
from civi.pi.network import NetworkError
from civi.server import make_web


DOM = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function element() {return {value:'',textContent:'',hidden:false,disabled:false,dataset:{},children:[],clears:0,
  addEventListener(name,fn){this[name]=fn;},reportValidity(){return true;},focus(){},scrollIntoView(){},
  append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},
  querySelector(){return this.eyebrow ||= element();},querySelectorAll(){return [];},
  getContext(){return {clearRect:()=>this.clears++};}};}
const nodes=new Map(),timers=[];
function byId(id) {if(!nodes.has(id)) nodes.set(id,element());return nodes.get(id);}
const document={getElementById:byId,createElement:element,
 querySelectorAll:()=>[byId('frequency-button'),byId('mode-button')]};
const flush=()=>new Promise(setImmediate);
function context(extra={}) {return vm.createContext({document,console,Date,URL,TextEncoder,btoa,
 AbortSignal:{timeout(){}},setInterval:(fn,ms)=>{timers.push({fn,ms});return timers.length;},
 clearInterval(){},setTimeout:(fn,ms)=>{timers.push({fn,ms});},window:{addEventListener(){}},...extra});}
'''


def javascript(code):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to execute shipped Web JavaScript')
    result = subprocess.run([node, '-e', DOM + '\n(async()=>{\n' + code +
                             '\n})().catch(e=>{console.error(e);process.exitCode=1;});'],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('state', ['disconnected', 'connecting', 'quarantined'])
def test_radio_transition_hides_cached_values_and_restores_controls(state):
    javascript(r'''
let state='disconnected';
const snapshot=()=>({connection:state,radio_model:'IC-7300',backend:'mock',tx_enabled:false,
 values:{frequency:774000,mode:'AM',ptt:false,smeter:100},network:{hostname:'civi',interfaces:[]},
 modes:['AM'],serial_settings:{baud:115200},logs:[]});
const ctx=context({fetch:async path=>({ok:true,json:async()=>path==='/health'?{radio:state}:snapshot()})});
vm.runInContext(fs.readFileSync('civi/static/app.js','utf8'),ctx);await flush();
byId('command-select').value='RAD:MODE';
vm.runInContext("catalog=[{header:'RAD:MODE',access:'rw'}]",ctx);
state='connected';await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'0.774000 MHz');
assert.equal(byId('command-read').disabled,false);
assert.equal(byId('scope-start').disabled,false);
state=STATE;await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'— MHz');
assert.equal(byId('mode-value').textContent,'—');
assert.equal(byId('ptt-value').textContent,'PTT unknown');
assert.equal(byId('smeter-value').textContent,'—');
for(const id of ['frequency-button','mode-button','ptt-on','scope-start','scope-stop','scope-refresh','command-read','command-write'])
 assert.equal(byId(id).disabled,true,id);
assert.ok(byId('scope-plot').clears>0 && byId('scope-waterfall').clears>0);
vm.runInContext('selectCommand()',ctx);assert.equal(byId('command-read').disabled,true);
state='connected';await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'0.774000 MHz');
assert.equal(byId('command-write').disabled,false);
assert.equal(byId('ptt-on').disabled,true); // Configuration still forbids transmission.
'''.replace('STATE', json.dumps(state)))


def test_health_and_authenticated_status_failure_hide_old_readings():
    javascript(r'''
let failHealth=false,failStatus=false;
const ctx=context({fetch:async path=>{
 if(path==='/health' && failHealth)throw new Error('Network unreachable');
 if(path==='/api/heartbeat')return {ok:true,json:async()=>({})};
 if(path==='/api/status' && failStatus)return {ok:false,status:503,json:async()=>({error:'Status unavailable'})};
 return {ok:true,json:async()=>({radio:'connected'})};
}});
vm.runInContext(fs.readFileSync('civi/static/app.js','utf8'),ctx);await flush();
failHealth=true;await vm.runInContext('refreshHealth()',ctx);
assert.equal(byId('radio-status-title').textContent,'CIVI server unavailable');
assert.equal(byId('frequency').textContent,'— MHz');
failHealth=false;failStatus=true;vm.runInContext("session='mock-session'",ctx);
await vm.runInContext('tick()',ctx);
assert.equal(byId('radio-status-title').textContent,'Radio status unavailable');
assert.equal(byId('frequency').textContent,'— MHz');
assert.equal(byId('scope-start').disabled,true);
''')


def test_empty_memory_clears_values_without_disabling_connected_controls():
    javascript(r'''
let empty=false;
const snapshot=()=>({connection:'connected',radio_model:'IC-7300',backend:'mock',tx_enabled:false,
 values:{frequency:empty?null:927000,mode:empty?null:'AM',ptt:false,smeter:0},
 unavailable_values:empty?['frequency','mode']:[],network:{hostname:'civi',interfaces:[]},
 modes:['AM'],serial_settings:{baud:115200},logs:[]});
const ctx=context({fetch:async path=>({ok:true,json:async()=>path==='/health'?{radio:'connected'}:snapshot()})});
vm.runInContext(fs.readFileSync('civi/static/app.js','utf8'),ctx);await flush();
await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'0.927000 MHz');
empty=true;await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'Not set (empty memory)');
assert.equal(byId('mode-value').textContent,'Not set');
assert.equal(byId('frequency-button').disabled,false);
assert.equal(byId('mode-button').disabled,false);
assert.equal(byId('ptt-value').textContent,'RECEIVING');
empty=false;await vm.runInContext('refresh()',ctx);
assert.equal(byId('frequency').textContent,'0.927000 MHz');
assert.equal(byId('mode-value').textContent,'AM');
''')


def test_indicator_poll_failure_does_not_keep_old_panel_acknowledgement():
    javascript(r'''
let failed=false;
const status={state:'normal',identify:true,display_connected:true,display_acknowledged:true,
 interface:'eth0',hostname:'civi',addresses:['192.0.2.7'],faults:[]};
const ctx=context({fetch:async()=>{
 if(failed)throw new Error('Disconnected');
 return {ok:true,json:async()=>status};
}});
vm.runInContext(fs.readFileSync('civi/static/indicator.js','utf8'),ctx);await flush();
assert.equal(byId('lan-lamp').className,'lan-lamp identifying');
assert.ok(byId('identify-state').textContent.includes('acknowledged'));
failed=true;await timers.shift().fn();
assert.equal(byId('lan-lamp').className,'lan-lamp unknown');
assert.ok(byId('identify-state').textContent.includes('unknown'));
failed=false;status.identify=false;await timers.shift().fn();
assert.equal(byId('lan-lamp').className,'lan-lamp normal');
assert.ok(byId('identify-state').textContent.includes('Identify is off'));
''')


def test_lan_trial_expiry_helper_failure_and_verified_restoration():
    javascript(r'''
let now=100000,failed=false;
const state={pending:{token:'mock-token',remaining_seconds:45,expected_ipv4:'192.0.2.8'},
 snapshot:{active_ipv4:'192.0.2.8/24',hostname:'civi',profile:{'ipv4.method':'manual'}}};
const ctx=context({Date:class extends Date {static now(){return now;}},
 location:{href:'https://192.0.2.7/network',hash:''},fetch:async()=>({ok:!failed,status:409,
 json:async()=>failed?{error:'LAN helper unavailable; start it manually on the Pi'}:state})});
byId('pi-prefix').value='24';byId('pi-password').value='mock-test-password';
vm.runInContext(fs.readFileSync('civi/static/network.js','utf8'),ctx);
await byId('pi-read').onclick();
assert.equal(byId('pi-guidance').hidden,false);
assert.equal(byId('pi-confirm').disabled,false);
assert.ok(byId('pi-guidance').children.some(x=>x.href==='https://192.0.2.8/network#pi-lan'));
const guide=timers.find(x=>x.ms===1000).fn;
now+=46000;guide();
assert.equal(byId('pi-confirm').disabled,true);assert.equal(byId('pi-rollback').disabled,true);
assert.equal(byId('pi-guidance').children[0].textContent,'Confirmation time expired');
assert.ok(byId('pi-guidance').children.some(x=>typeof x==='string'&&x.includes('unless you already confirmed')));
now=100000;await byId('pi-read').onclick();assert.equal(byId('pi-confirm').disabled,false);
failed=true;await byId('pi-read').onclick();
assert.equal(byId('pi-confirm').disabled,true);assert.equal(byId('pi-rollback').disabled,true);
assert.ok(byId('pi-result').textContent.includes('LAN helper unavailable'));
failed=false;state.pending=null;state.last_result={state:'recovery_required',verified:false};
await byId('pi-read').onclick();
assert.ok(byId('pi-result').textContent.includes('could not be verified'));
assert.equal(byId('pi-guidance').hidden,true);
state.last_result={state:'rolled_back',verified:true};await byId('pi-read').onclick();
assert.equal(byId('pi-result').textContent,'Previous LAN settings restored and verified.');
state.last_result={state:'confirmed'};await byId('pi-read').onclick();
assert.equal(byId('pi-result').textContent,'LAN settings confirmed and saved.');
''')


def test_lan_apply_connection_loss_keeps_reconnect_guidance():
    javascript(r'''
const ctx=context({location:{href:'https://192.0.2.7/network',hash:''},
 fetch:async()=>{throw new Error('Connection closed while applying');}});
byId('pi-prefix').value='24';byId('pi-mode').value='static';
byId('pi-address').value='192.0.2.8';byId('pi-password').value='mock-test-password';
byId('pi-confirm').disabled=byId('pi-rollback').disabled=true; // Initial HTML state.
vm.runInContext(fs.readFileSync('civi/static/network.js','utf8'),ctx);
await byId('pi-apply').onclick();
assert.equal(byId('pi-guidance').hidden,false);
assert.ok(byId('pi-guidance').children.some(x=>x.href==='https://192.0.2.8/network#pi-lan'));
assert.ok(byId('pi-result').textContent.includes('Connection closed'));
assert.equal(byId('pi-confirm').disabled,true); // No token was obtained.
// A network error must not fabricate a confirm token or send a confirm request.
''')


async def test_lan_pending_fault_and_helper_unavailable_do_not_break_identification(service, monkeypatch):
    network={'hostname':'civi','interfaces':[{'name':'eth0','ipv4':[],
             'mac':None,'up':False,'visa':[]}]}
    monkeypatch.setattr('civi.server.network_info',lambda port:network)
    service.config['pi_network']['enabled']=True
    indicator=LanIndicator()
    indicator.update({'present':True,'link':False,'addresses':[]})
    class Helper:
        failed=False
        def request(self,op,**values):
            assert op=='status'
            if self.failed:raise NetworkError('LAN helper unavailable; start it manually on the Pi')
            return {'pending':{'token':'mock-token','remaining_seconds':30,'expected_ipv4':'192.0.2.8'},
                    'snapshot':{'active_ipv4':''}}
    helper=Helper()
    auth={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}
    schema=etree.XMLSchema(etree.parse('civi/schemas/InstrumentIdentification-2.0.xsd'))
    async with TestClient(TestServer(make_web(service,'mock-test-password',lan_manager=helper,indicator=indicator))) as client:
        for failed in (False,True):
            helper.failed=failed
            response=await client.get('/api/pi/network',headers=auth)
            assert response.status==(409 if failed else 200)
            data=await response.json()
            assert ('error' in data) if failed else data['pending']['remaining_seconds']==30
            for path in ('/lxi','/network'):
                assert (await client.get(path)).status==200
            response=await client.get('/lxi/identification');assert response.status==200
            schema.assertValid(etree.fromstring(await response.read()))
            status=await (await client.get('/lan-status')).json()
            assert status['state']=='fault' and not status['identify']
