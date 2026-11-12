"""Reconcile reviewed API evidence, without executing an instrument command.

This is a documentation consistency tool, not a test or conformance verdict.
Evidence rules below are deliberately reviewed mappings, not coverage inferred
from a matching word in source or from a successful mock being called hardware.
"""
import argparse
import ast
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT/'docs/IVI_VERIFICATION_WORKLIST_2026-11-11.csv'
OUT = ROOT/'docs/IVI_VERIFICATION_RECONCILED_2026-11-12.json'
MENU = ROOT/'docs/IVI_MENU_VERIFICATION_2026-11-12.csv'
CORE = 'docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md'
API = 'docs/IVI_API_ACCEPTANCE_2026-11-12.md'
READ = 'tools/ivi_readonly_acceptance.py'
HISTORY = 'docs/HARDWARE_2026-10-17.md'
STORAGE = 'docs/IVI_SCAN_STORAGE_2026-11-12.md'
COMMON_TEST = 'tests/test_python_status.py'


def evidence(kind, scope, refs, pending=''):
    return dict(evidence_kind=kind, verified_scope=scope,
                evidence_refs='; '.join(refs), followup_ids=pending)


def classify(row):
    t, e = row['type'], row['entry']
    old = row['legacy_status']
    def local(scope, refs, pending=''):
        return evidence('LOCAL', scope, refs, pending)
    def phy(scope, refs, pending=''):
        return evidence('PHYSICAL_SCOPED', scope, refs, pending)
    if t in ('IviUtility', 'IviDirectIo'):
        if e == 'constructor':
            return local('Abstract contract; not an independently instantiable instrument operation. Concrete implementation is tested.',
                         ['drivers/civi-ic7300/src/civi_ic7300/interfaces.py', 'tests/test_python_controls.py#test_utility_contracts_are_concrete_and_references_read_only'])
        concrete = 'Utility' if t == 'IviUtility' else 'DirectIo'
        item = classify(dict(row, type=concrete))
        item['verified_scope'] = f'Abstract contract implemented by {concrete}.{e}; '+item['verified_scope']
        item['evidence_refs'] += '; drivers/civi-ic7300/src/civi_ic7300/interfaces.py'
        return item
    if t == 'CiviIc7300':
        if e == 'constructor':
            return evidence('PARTIAL', 'Live construction/context use is recorded; id_query=True, reset=False, checks=True. Mock constructor option/traffic combinations exist; consolidate unrecorded live option/checked/reset paths.',
                            [CORE, 'tests/test_python_status.py#test_constructor_status_traffic', 'tests/test_python_release.py#test_typed_options_no_network'], 'R-CORE')
        if e == 'checked':
            return evidence('PARTIAL', 'Nested/context exception/locking policy tested locally and with mock TCP; no current live checked-block evidence found.',
                            [COMMON_TEST+'#test_checked_reports_denials_and_restores_off', COMMON_TEST+'#test_checked_nested_exception_and_thread_visibility'], 'R-CORE')
        return phy('Concrete reference/session/query path exercised in the recorded live tools; close is called by __exit__, and query by error/query helpers. No additional knob/RF experiment for these wrappers.',
                   [CORE, 'tools/ivi_receive_acceptance.py', API, 'tools/ivi_storage_read_acceptance.py'])
    if t in ('Utility', 'DirectIo'):
        if e == 'constructor':
            return local('Concrete helper constructed by every live/mock driver initialization; it only retains the session reference.',
                         ['drivers/civi-ic7300/src/civi_ic7300/driver.py', CORE])
        if t == 'Utility' and e == 'reset':
            return evidence('HISTORICAL', 'Typed utility reset succeeded on 2026-11-08 with normal timeout restored; this is older-client evidence, not a new current-source reset run.',
                            ['docs/PARTIAL_RESET_CAPTURE_2026-11-08.md', 'tests/test_receive_reset.py'], 'R-CORE')
        if e in ('query_instrument_status', 'query_instrument_status_enabled', 'simulate'):
            return local('Local status/simulation state; aliases share the same property implementation. Mock OFF/ON, checked scope and validation evidence exists. Collect live policy paths together in R-CORE; no separate receiver-setting test.',
                         [COMMON_TEST, 'drivers/civi-ic7300/src/civi_ic7300/driver.py'], '' if e=='simulate' else 'R-CORE')
        return phy('Concrete implementation exercised by the 2026-11-11 core procedure; inherited abstract declaration does not create a second transport implementation. Error injection is undefined-header SCPI, not corrupt serial/RF injection.',
                   [CORE, 'tools/ivi_receive_acceptance.py', 'tests/test_python_driver.py'])
    value_refs = {
        'DriverOptions': ['tests/test_python_release.py#test_typed_options_no_network'],
        'GatewayIdentification': [CORE, 'tests/test_python_driver.py'],
        'VfoMode': [API, 'tools/ivi_vfo_acceptance.py', 'tests/test_python_controls.py'],
        'ScopeEdges': [API, 'tools/ivi_scope_acceptance.py', 'tests/test_python_controls.py#test_scope_units_edges_waveform'],
        'ScopeSweep': [API, 'tools/ivi_scope_acceptance.py', 'tests/test_python_controls.py#test_scope_units_edges_waveform'],
        'DataFilter': ['tests/test_python_bands.py#test_band_and_data_independent_vectors'],
        'AudioFilter': ['tests/test_python_menus.py#test_menu_wire_vectors'],
        'Bandwidth': ['tests/test_python_menus.py#test_menu_wire_vectors'],
        'RgbColor': ['tests/test_python_menus.py#test_menu_wire_vectors'],
        'MemorySettings': ['tests/test_python_storage.py#test_independent_lossless_memory_vectors', API, STORAGE],
        'MemoryRecord': ['tests/test_python_storage.py#test_independent_lossless_memory_vectors', 'docs/IVI_MEMORY_WRITE_2026-11-12.md'],
        'BandEdges': ['tests/test_python_bands.py#test_band_and_data_independent_vectors', API],
        'ErrorQueryResult': [CORE, 'tools/ivi_receive_acceptance.py'],
        'DeviceError': [CORE, 'docs/IVI_SELECTED_MEMORY_2026-11-12.md', 'tests/test_python_storage.py#test_storage_failure_stops_readback'],
        'ProtocolError': ['tests/test_python_controls.py#test_bad_typed_replies_raise_protocol_error', 'tests/test_python_driver.py#test_timeout_closes_session_and_discards_late_reply'],
        'QueryError': [COMMON_TEST+'#test_raw_query_error_preserves_queue_regardless_of_policy'],
        'MenuDefinition': ['tests/test_python_menus.py#test_menu_types_validation_and_metadata_before_io', 'tests/test_python_menus.py#test_packaged_menu_schema_matches_gateway'],
    }
    if t in value_refs:
        return local('Value/record/exception/metadata operation, not an independent device command. Reuse cited vectors, equality/roundtrip/validation and recorded decoded results; does not imply untested hardware setting writes or all value combinations.', value_refs[t])
    if e == 'constructor':
        return local('View/control constructed by live driver or collection resolution. Valid-context construction is already exercised; no independent device command or separate hardware experiment.',
                     ['drivers/civi-ic7300/src/civi_ic7300/driver.py', API, 'tests/test_python_hierarchy.py'])
    if t == 'MenuCollection':
        if e == 'set_simulated_write_permissions':
            return local('Permission flags are simulation-only; mock validation/real-mode rejection exists. Include non-I/O rejection in the consolidated live contract record, never enable actual gateway permissions through this method.',
                         ['tests/test_python_menus.py#test_permissions_denied_in_checked_operations'], 'R-CORE')
        if e.endswith('_item'):
            if e in ('integer_item', 'text_item'):
                return local('Local typed view resolver; successful mock calls and wrong-kind/selector validation exist. Resolved MenuItem implementation is shared.',
                             [COMMON_TEST, 'tests/test_python_menus.py#test_text_normalization_and_atomic_write_read'])
            return evidence('LOCAL_PENDING', 'Factory is implemented and underlying typed codecs are tested, but a positive call to this particular convenience factory was not located. It requires no instrument mutation.',
                            ['drivers/civi-ic7300/src/civi_ic7300/menus.py', 'tests/test_python_menus.py#test_menu_types_validation_and_metadata_before_io'], 'L-FACTORIES')
        return phy('All 216 selectors iterated/resolved/read in current live read inventory; metadata resolution itself is local.',
                   [CORE, READ, 'tests/test_python_menus.py'])
    if t == 'MenuItem':
        if e in ('value', 'write_and_read'):
            return evidence('PARTIAL', 'Current typed path: 216 physical getters; 215 changed-write/restore cases are mock-only. Historical gateway SCPI changed-write/restore exists for 189 selectors, with unknown firmware and no then-current IVI wrapper. Per-selector evidence is in the companion menu table.',
                            [CORE, READ, HISTORY, 'tests/test_python_menus.py#test_all_216_reads_and_215_changed_writes_restore'], 'R-MENUS; C-MENU; C-LINK; C-CALIB')
        return local('Definition/name access is local; all menu views are constructed/read in live inventory, with exact metadata/readonly validation in software tests.',
                     [CORE, 'tests/test_python_menus.py#test_menu_types_validation_and_metadata_before_io'])
    if e == 'set_simulated_write_permission':
        return local('Inherited StoredControl method is shared by item/collection views. Canonical collection implementation was called in live mode and rejected before I/O; alias-specific scope/metadata is tested locally. No separate physical permission mutation is needed.',
                     [API, 'tools/ivi_band_read_acceptance.py', 'drivers/civi-ic7300/src/civi_ic7300/storage.py', 'tests/test_python_hierarchy.py#test_nested_permission_and_status_policy'])
    repeated = {'MemoryItem','MemoryCollection','KeyerItem','KeyerCollection','BandStackItem',
                'BandStackSlotCollection','BandStackBand','BandStackBandCollection','BandStackCollection'}
    if t in repeated:
        if t == 'MemoryItem' and e in ('record','clear','write_and_read'):
            return phy('Current physical property read: all 101 instances; changed-write/read/clear: ordinary 99 with eight full-record cases, plus 94-99 scratch roundtrips in scan trials. Original data restored. Control-method coverage for 1-93/P1/P2 and remaining boundary cases is not inherited from metadata/getitem calls.',
                       [API, 'docs/IVI_MEMORY_WRITE_2026-11-12.md', STORAGE, 'tests/test_python_storage.py'], 'R-STORAGE')
        if t == 'MemoryCollection' and e in ('select','enable','store_current_in_selected','copy_selected_to_vfo','clear_selected'):
            return phy('Current selected-memory actions: 29 live checks on 99, including required memory-mode clear; VFO/empty scratch restored. Selection/property reads cover 101 views; no new full action sequence on every channel is implied.',
                       ['docs/IVI_SELECTED_MEMORY_2026-11-12.md', API])
        if t == 'BandStackItem' and e in ('settings','write_and_read'):
            return phy('All 33 instances: complete 14-byte changed-write/read/immediate restore and final backup comparison. Remaining value-boundary cases are separate; not a request to repeat all 33 normal roundtrips.',
                       [STORAGE, 'tools/ivi_stack_keyer_write_acceptance.py', 'tests/test_python_storage.py'], 'R-STORAGE')
        if t == 'KeyerItem' and e in ('text','write_and_read'):
            return phy('All eight instances: changed text/read/immediate restore and final backup comparison. Physical max-length/empty/contest-marker cases not inferred from representative strings.',
                       [STORAGE, 'tools/ivi_stack_keyer_write_acceptance.py', 'tests/test_python_repeated.py'], 'R-STORAGE')
        return phy('All relevant collection/view identities, names, lengths and selectors are exercised by the live storage-read traversal; overloads/immutability/invalid arguments share explicit local tests. No independent RF or storage write is required for metadata alone.',
                   [API, 'tools/ivi_storage_read_acceptance.py', 'tests/test_python_hierarchy.py#test_nested_metadata_legacy_iteration_and_validation_without_io', 'tests/test_python_repeated.py#test_collection_names_without_io'])
    if t == 'Bands':
        if e in ('write_user','write_and_read_user'):
            return evidence('CONTROLLED_PENDING', 'Mock codecs/gates and 40 physical reads exist; user TX-band calibration writes have not been physically tested and were excluded by the owner. Empty-slot deletion/restoration is not supplied. Not a normal receiver batch.',
                            [API, 'tests/test_python_bands.py'], 'C-CALIB')
        return phy('Default/factory/user read paths and empty FF handling checked; simulation-only calibration permission rejected on real driver before I/O. No calibration writes inferred.',
                   [API, 'tools/ivi_band_read_acceptance.py', 'tests/test_python_bands.py'])
    if t in ('Radio', 'Gains', 'Meters'):
        if t == 'Radio' and e == 'data_filter':
            return evidence('HISTORICAL', 'RAD:DATA changed-write/read/restore succeeded on historical gateway SCPI; typed DataFilter read/write vectors are mock-tested. VFO mode DATA tests use a different command and do not replace this current typed path.',
                            [HISTORY, 'tests/test_python_bands.py#test_data_ipplus_and_wire'], 'R-RECEIVE')
        if row['access'] == 'read/write' and 'getter passed' in old:
            return evidence('GET_ONLY', 'Current live getter succeeds; setter/bounds/enums not covered by that read. Historical SCPI write evidence, if present for the header, is supplemental and not a current typed setter pass.',
                            [CORE, READ, HISTORY, 'tests/test_python_controls.py'], 'R-RECEIVE')
        pending='R-COERCION' if t=='Gains' and e in ('noise_reduction_raw','pbt_inner_raw','pbt_outer_raw') else ''
        return phy(old+'; read-only output ranges do not require driving meters to full scale or transmitting. Existing receiver-setting roundtrips retain their documented firmware/mode/coercion limits.',
                   [CORE, 'tools/ivi_receiver_settings_acceptance.py', READ], pending)
    if t == 'Scope':
        if e == 'write_fixed_edges':
            return evidence('GET_ONLY', 'All 52 fixed-edge records physically read; write/read/restore is mock-only. Test this write path and its legal/illegal band/edge/value bounds in applicable fixed mode, using saved edges.',
                            [API, 'tests/test_python_controls.py#test_scope_units_edges_waveform'], 'R-SCOPE')
        return phy(old+'; bulk control/sweep evidence does not imply full untested value combinations.',
                   [API, 'tools/ivi_scope_acceptance.py', 'tests/test_python_controls.py'])
    if t in ('Vfo', 'VfoCollection'):
        doc = 'docs/IVI_VFO_COPY_2026-11-12.md' if e == 'copy_selected_to_other' else API
        return phy(old+'; reuse these records, including explicit owner-known A selection, without scheduling duplicate COPY/swap/normal-mode trials.',
                   [doc, 'tools/ivi_vfo_acceptance.py', 'tests/test_python_controls.py'])
    if t == 'ScanControl':
        return phy(old+'; all start enum and setting cases now have physical evidence. No blanket all-signal/all-span-endpoint assertion.',
                   ['docs/IVI_SCAN_SETTINGS_2026-11-12.md', STORAGE, API, 'tests/test_python_scan.py'])
    if t == 'RadioOperations':
        if e == 'set_simulated_permissions':
            return local('Simulation-only flags/default-deny/type validation and rejection by a non-simulated mock-TCP client are tested. Collect the live no-I/O guard in R-CORE without enabling actual RF/power permissions.',
                         ['tests/test_python_operations.py#test_operation_permissions_default_off'], 'R-CORE')
        if e == 'transmit_inhibited':
            return phy('MAIN 1.42 get/set True/False and invalid inputs passed; original False restored. Does not prove RF suppression under actual PTT.',
                       ['docs/IVI_TX_INHIBIT_2026-11-11.md', 'tests/test_python_operations.py'])
        if e in ('speak','power_on','power_off'):
            return evidence('CONTROLLED_PENDING', 'Mock path/gates are tested; physical audio output or complete power cycle not tested. Separate an operator-visible audio/power procedure from ordinary silent receiver changes.',
                            ['tests/test_python_operations.py', HISTORY], 'C-POWER-AUDIO')
        if e == 'antenna_output_enabled':
            return evidence('GET_ONLY', 'Current live getter, mock setter/gate only; link/output behavior needs a separately scoped setup, not the ordinary receiver scalar batch.',
                            [CORE, 'tests/test_python_operations.py'], 'C-LINK')
        return evidence('CONTROLLED_PENDING', 'Physical idle/state getters or historical idle NAK may exist; mock permissions/start/stop/deadline/disconnect paths do not prove active RF operation or physical cessation. No TX start authorized by this evidence review.',
                        [CORE, 'docs/PARTIAL_RESET_CAPTURE_2026-11-08.md', 'tests/test_python_operations.py'], 'C-RF')
    raise ValueError('Unreviewed public row: '+t+'.'+e)


def csv_text(rows, fields):
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    w.writeheader();w.writerows(rows);return stream.getvalue()


def menu_rows():
    historical={}
    for line in (ROOT/HISTORY).read_text(encoding='utf-8').splitlines():
        m=re.match(r'\| `(RAD:MENU:\d{4})` \|.*\| ([^|]+)\|$',line)
        if m:historical[int(m[1].split(':')[-1])]='復元OK' in m[2]
    items=json.loads((ROOT/'drivers/civi-ic7300/src/civi_ic7300/menu-catalog.json').read_text(encoding='utf-8'))['items']
    assert len(historical)==216 and sum(historical.values())==189
    rows=[]
    for x in items:
        writable=x['access']=='rw'
        followup='' if not writable else {'menu':'R-MENUS','link':'C-LINK','calibration':'C-CALIB'}[x['permission']]
        if x['permission']=='menu' and not historical[x['number']]:followup='C-MENU'
        rows.append(dict(number=x['number'],header=x['header'],permission=x['permission'],access=x['access'],
                         current_typed_read='MAIN1.41;216/216; '+CORE,
                         historical_scpi_write='2026-10-17 changed/read/restored; firmware unknown' if historical[x['number']] else 'No positive write in historical record',
                         current_typed_write='Mock changed/read/restore only; not a physical IVI pass' if writable else 'Not applicable: read-only',
                         followup_ids=followup))
    return rows


def validate_ref(ref):
    path,_,symbol=ref.partition('#')
    f=ROOT/path
    if not f.is_file():raise ValueError('Missing evidence: '+ref)
    if symbol:
        symbols={n.name for n in ast.walk(ast.parse(f.read_text(encoding='utf-8'))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
        if symbol not in symbols:raise ValueError('Missing evidence function: '+ref)


def render():
    with CSV.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);original_fields=reader.fieldnames;rows=list(reader)
    keys={(r['type'],r['entry']) for r in rows}
    public=json.loads((ROOT/'drivers/civi-ic7300/src/civi_ic7300/public-api.json').read_text(encoding='utf-8'))
    expected=set()
    for c in public['classes']:
        if c.get('constructor'):expected.add((c['class'],'constructor'))
        expected.update((c['class'],m['name']) for m in c['members'])
        expected.update((c['class'],m['name']) for m in c.get('fields',[]))
    if keys!=expected:raise ValueError('Worklist/public API inventory mismatch: '+str(keys^expected))
    reviewed_digest=hashlib.sha256(json.dumps(sorted(keys)).encode()).hexdigest()
    if reviewed_digest != '20a5a220314ca4b41257f3891d3b9897154095df86d897854f439bb8dc973f32':
        raise ValueError('Public API keys changed; explicitly review the evidence rules before regenerating')
    fields=list(original_fields)
    for name in ['legacy_status','evidence_kind','verified_scope','evidence_refs','followup_ids']:
        if name not in fields:fields.append(name)
    for row in rows:
        row.setdefault('legacy_status',row['verification_status'])
        mapped=classify(row)
        for ref in mapped['evidence_refs'].split('; '):validate_ref(ref)
        row.update(mapped)
        row['verification_status']=mapped['evidence_kind']+': '+mapped['verified_scope']
    menus=menu_rows()
    summary={'date':'2026-11-12','claim':'Evidence reconciliation only; not an IVI/LXI conformance verdict',
             'rows':len(rows),'legacy_placeholder_rows':sum(r['legacy_status'].startswith('Evidence mapping required') for r in rows),
             'current_placeholder_rows':sum(r['verification_status'].startswith('Evidence mapping required') for r in rows),
             'evidence_kind_counts':dict(Counter(r['evidence_kind'] for r in rows)),
             'followups':{key:[r['type']+'.'+r['entry'] for r in rows if key in r['followup_ids'].split('; ')]
                          for key in ['L-FACTORIES','R-CORE','R-RECEIVE','R-COERCION','R-SCOPE','R-STORAGE','R-MENUS','C-MENU','C-POWER-AUDIO','C-RF','C-LINK','C-CALIB']},
             'menu_counts':{'read_instances':len(menus),'historical_scpi_written':sum('changed/read' in r['historical_scpi_write'] for r in menus),
                            'writable_by_permission':dict(Counter(r['permission'] for r in menus if r['access']=='rw')),
                            'followup_counts':dict(Counter(r['followup_ids'] or 'read_only' for r in menus))},
             'private_artifacts_are_not_embedded':True,
             'input_sha256_normalized_utf8_lf':{p:hashlib.sha256((ROOT/p).read_text(encoding='utf-8').encode()).hexdigest() for p in [HISTORY,'drivers/civi-ic7300/src/civi_ic7300/public-api.json']}}
    plan=json.loads((ROOT/'docs/IVI_6_1_COMPLETION_2026-11-12.json').read_text(encoding='utf-8'))
    for key in summary['followups']:
        if key not in plan['followup_cases']:raise ValueError('Missing reviewed followup description: '+key)
    return {CSV:csv_text(rows,fields),MENU:csv_text(menus,list(menus[0])),OUT:json.dumps(summary,indent=2,ensure_ascii=False)+'\n'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    outputs=render()
    for path,text in outputs.items():
        if args.check:
            if path.read_text(encoding='utf-8')!=text:raise SystemExit('Reconcile artifact is stale: '+str(path))
        else:path.write_text(text,encoding='utf-8')
    summary=json.loads(outputs[OUT]);print(json.dumps({k:summary[k] for k in ['rows','legacy_placeholder_rows','current_placeholder_rows','evidence_kind_counts','menu_counts']}))


if __name__=='__main__':main()
