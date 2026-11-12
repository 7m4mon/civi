"""Generate a frozen IVI completion checklist; never contact an instrument.

This checks inventory completeness, not conformance or successful execution.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs'
BASE = 'IVI_6_1_COMPLETION_2026-11-12'
PACKAGE = ROOT / 'drivers/civi-ic7300/src/civi_ic7300'


def digest(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest()


def csv_text(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def sources():
    return sorted(set([*PACKAGE.glob('*.py'), *PACKAGE.glob('*.json'),
                   *PACKAGE.glob('*.md'), *ROOT.glob('civi/**/*.py'),
                   *ROOT.glob('civi/profiles/*.json'),
                   ROOT/'drivers/civi-ic7300/README.md',
                   ROOT/'drivers/civi-ic7300/pyproject.toml',
                   ROOT/'civi/commands.py', ROOT/'civi/profiles/ic7300.json',
                   DOC/'IVI_VERIFICATION_WORKLIST_2026-11-11.csv',
                   DOC/'IVI_MENU_VERIFICATION_2026-11-12.csv']))


def example_inventory():
    rows = []
    for p in sorted((ROOT/'drivers/civi-ic7300').rglob('*.md')):
        start = None
        content = []
        language = ''
        for no, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            if line.startswith('```'):
                if start is None:
                    start = no
                    language = line[3:].strip()
                    content = []
                else:
                    rows.append(dict(id=f'E{len(rows)+1:03}', file=str(p.relative_to(ROOT)),
                                     lines=f'{start}-{no}', language=language,
                                     sha256=hashlib.sha256('\n'.join(content).encode()).hexdigest(),
                                     required_action='R-02: run executable example; classify syntax/output-only with reason',
                                     result='PENDING', setup_id='', evidence='', exclusion_reason=''))
                    start = None
            elif start is not None:
                content.append(line)
    return rows


def spec_inventory(path, name):
    """Enumerate mandatory prose without republishing copyrighted sentences."""
    heading = ''
    fenced = False
    rows = []
    buf = []
    start = 0

    def flush():
        nonlocal buf
        import re
        text = ' '.join(buf)
        excluded = ('Warranty', 'Trademarks', 'Abstract', 'Authorship', 'Table of Contents')
        if (buf and heading not in excluded and not text.startswith('>')
                and re.search(r'\b(shall|must|required|not permitted)\b', text, re.I)):
            rows.append(dict(spec=name, section=heading,
                             source_lines=f'{start}-{start+len(buf)-1}',
                             sha256=hashlib.sha256(text.encode()).hexdigest()))
        buf = []

    for no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('```'):
            flush()
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith('#'):
            flush()
            heading = line.lstrip('# ').strip()
            continue
        if not line.strip():
            flush()
            continue
        if not buf:
            start = no
        buf.append(line)
    flush()
    return rows


def members():
    classes = {}
    for p in PACKAGE.glob('*.py'):
        tree = ast.parse(p.read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes[node.name] = (p, node)
    classes['Radio'] = classes['ReceiverSettings']
    return classes


def contract(row, classes):
    typ, name = row['type'], row['entry']
    if typ not in classes:
        return '', ''
    path, cls = classes[typ]
    target = '__init__' if name == 'constructor' else name
    nodes = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == target]
    for n in cls.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return str(path.relative_to(ROOT))+':'+str(n.lineno), ast.unparse(n.value)
    if nodes:
        validations = []
        for n in nodes:
            for v in ast.walk(n):
                if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id in (
                    'integer', 'boolean', 'choice', 'mode_name', '_tone', '_memory_number', '_cw_quote'):
                    validations.append(ast.unparse(v))
        return str(path.relative_to(ROOT))+':'+str(nodes[0].lineno), '; '.join(dict.fromkeys(validations))
    return str(path.relative_to(ROOT))+':'+str(cls.lineno), ''


def profiles(row):
    """Explicit test families; both halves of a property are separate cases."""
    a = row['access']
    if a == 'constructor':
        return ['CONSTRUCT', 'INPUTS']
    if a == 'read/write':
        return ['GET', 'SET', 'INPUTS']
    if a in ('read-only', 'record field'):
        return ['GET_OR_FIELD']
    return ['CALL', 'INPUTS']


def domain(row):
    t, e = row['type'], row['entry']
    if t == 'Gains':
        return '整数0..255: 0,128,255,-1,256; bool/string拒否; 離散丸めはQ-01'
    if e.endswith('_enabled') or e in ('transmit_inhibited', 'enabled', 'streaming_enabled', 'simulate'):
        return 'bool False/True; 0,1,"ON",None等の不正型拒否（APIが明示許可する型は契約優先）'
    special = {
        'frequency_hz': 'profile 30000..60000000 Hz: 両端/中間/直外; bool/NaN/inf/単位文字列; 切捨て規則も確認',
        'mode': 'LSB,USB,AM,CW,RTTY,FM,CW-R,RTTY-R; DATA False/True; FIL1,2,3; 不正mode/filter/type; モード条件を記録',
        'data_filter': 'DataFilter(False/True, FIL1/2/3); filter0/4,不正型; 1A06の送出/復元',
        'attenuator_db': 'OFF=0 / ON=20 dB; -1,1,19,21と不正型を拒否',
        'span_hz': '2500,5000,10000,25000,50000,100000,250000,500000; 非メンバー/不正型拒否',
        'reference_db': '-20..20 dB,0.5刻み; 両端/0/各隣接刻み間の値/直外/NaN/inf; 非0.5刻み拒否',
        'write_fixed_edges': 'band1..13,edge1..4; 全52組; ScopeEdges 0..74800000 whole kHz, lower<=upper; profileのband別合法範囲を適用',
        'read_fixed_edges': 'band1..13×edge1..4=52組; band0/14,edge0/5;不正型',
        'text': 'キーヤー0..70文字; 空/1/35/70/71,全許可文字/不許可文字,不正型; contest *は状態を保存して別確認',
        'play_voice': 'slot1..8全件、0/9/不正型; T1..T8へ識別可能な試験音声を用意',
        'send_cw': '許可ASCII、長さ1/15/30、0/31、不許可文字、引用符escaping; CW実送出とSTOP',
        'speak': 'code0,1,2全件; -1/3/不正型; 各音声を実聴確認',
        'break_in': 'OFF,SEMI,FULL全件; 不正値/型; CW入力と実停止',
        'tuner': 'OFF,ON,TUNE全件; 不正値/型; 実チューニング開始/停止',
        'set_delta_span_hz': '5000,10000,20000,50000,100000,500000,1000000; 4999/1000001/非メンバー/不正型',
        'assign_selected_memory_group': 'group1,2,3; 0/4/不正型; addressed memory読戻し',
        'set_memory_group': 'group0,1,2,3; -1/4/不正型; 選択対象を実スキャンで確認',
        'start': 'PROGRAM,MEMORY,AUTO,DELTA,FINEPROGRAM,FINEDELTA,SELECTMEM; 不正値/型; AUTOはVFO/MEM両方',
        'io_timeout_ms': '正の整数; 最小1/代表5000/大きい合法値; 0/負/不正型; 既存実timeout模擬fixture併用',
    }
    if e in special:
        return special[e]
    if t in ('MemorySettings', 'MemoryRecord', 'MemoryItem', 'MemoryCollection'):
        return 'D-MEM / RC-02: 39byte record,通常1..99,P1/P2; 完全な型/長さ/値ベクトルは本文参照'
    if t.startswith('BandStack'):
        return 'D-MEM / RC-04: band1..11,slot1..3; legacy tupleも同値; 値域/型/復元'
    if t in ('KeyerItem', 'KeyerCollection'):
        return 'D-KEY / RC-03: M1..M8、text0..70;番号0/9と不正型'
    if t in ('MenuItem', 'MenuCollection', 'MenuDefinition', 'MenuKind'):
        return 'D-MENU / RC-05; 全216番号と型別ベクトルは同名MENU.csv（番号0074はread-only）'
    if t in ('Bands', 'BandEdges'):
        return 'D-BAND / RC-07: factory実count10,user実count30; serializer0..74800000,lower<=upper; instrument合法範囲別'
    if t in ('ScopeEdges', 'ScopeSweep'):
        return 'D-SCOPE: edge whole-kHz/順序/BCD; sweep475点0..160またはout-of-range空; 有限timestamp'
    if t in ('Vfo', 'VfoCollection', 'VfoMode'):
        return 'RC-01 / D-VFO: SELECTED/OTHER, A/B選択; alias,番号境界/不正指定; mode/data/FIL/frequency'
    if t in ('AudioFilter', 'Bandwidth', 'RgbColor', 'DataFilter'):
        return 'D-VALUES: AudioFilter HPF0..20/LPF5..25と大小/bypass; Bandwidth各0..3; RGB各0..255; DataFilter bool/FIL1..3'
    if t in ('DriverOptions', 'CiviIc7300', 'Utility', 'IviUtility', 'DirectIo', 'IviDirectIo'):
        return 'B-01..B-07: constructor/options/defaults/status/reset/Direct I/O/close/例外; 本文の固定手順'
    return 'D-LOCAL: signatureの各引数/各fieldの合法値・各制約境界・不正型・独立変換vector; 本文とsource_contract'


def menu_vectors(item):
    c = item['codec']; k = c['kind']
    if c['names'] == ['OFF', 'ON']:
        return 'False;True', '0;1;"ON";None (型契約に従う)'
    if k in ('number', 'repeater_offset'):
        lo, hi = c['minimum'], c['maximum']; step = 1000 if k == 'repeater_offset' else 1
        vals = c['choices'] or sorted(set([lo, lo+((hi-lo)//(2*step))*step, hi]))
        if c['names'] and not c['choices']:
            vals = list(range(lo, hi+1))
        return json.dumps(vals), json.dumps([lo-step, hi+step])+('; off-step' if step>1 else '')+'; wrong type'
    return {
        'hpf': ('(0,5);(0,25);(20,25);(10,15);各成分の範囲端と内部', 'HPF=-1/21,LPF=4/26; (10,10)/(11,10)非bypass;wrong type'),
        'bandwidth': ('各成分0,1,2,3（片側固定で一因子ずつ）', '各成分-1/4;wrong type'),
        'color': ('各成分0,128,255（他成分を固定）', '各成分-1/256;wrong type'),
        'menu_edge': ('合法band範囲内lower/upper端と中間;lower=upper;1000Hz刻み', '順序逆;1000Hz非整数倍;表現範囲外;wrong type'),
        'opening': ('空;1文字;5文字;10文字;許可文字A-Z0-9 ./@-', '11文字;小文字;非ASCII;wrong type'),
        'date': ('2000-01-01;2050-06-15;2099-12-31;2000-02-29', '1999/2100;無効日付;datetime混入;wrong type'),
        'time': ('00:00;12:00;23:59', '秒/μ秒/tzinfo/fold非0;無効時刻;wrong type'),
        'timezone': ('-14:00;00:00;+14:00;±00:01', '-14:01;+14:01;秒端数;wrong type'),
    }[k]


def generate(plan):
    current = {str(p.relative_to(ROOT)).replace('\\','/'): digest(p) for p in sources()}
    if current != plan['input_fingerprints']:
        raise SystemExit('Frozen API/source inputs changed: review and explicitly rebaseline the completion plan')
    rows = list(csv.DictReader((DOC/'IVI_VERIFICATION_WORKLIST_2026-11-11.csv').open(encoding='utf-8')))
    if len(rows) != 352 or len({(r['type'], r['entry']) for r in rows}) != 352:
        raise SystemExit('Reviewed 352-entry universe changed')
    public = json.loads((PACKAGE/'public-api.json').read_text(encoding='utf-8'))
    expected = set()
    for cls in public['classes']:
        name = cls['class']
        expected.update((name, m['name']) for m in cls['members'])
        expected.update((name, f['name']) for f in cls.get('fields', []))
        if 'constructor' in cls:
            expected.add((name, 'constructor'))
    if expected != {(r['type'], r['entry']) for r in rows}:
        raise SystemExit('Public API and completion universe differ')
    classes = members(); api = []
    for i, r in enumerate(rows, 1):
        loc, constraints = contract(r, classes)
        for direction in profiles(r):
            api.append(dict(id=f'A{i:03}-{direction}', api=r['type']+'.'+r['entry'],
                            access=r['access'], signature=r['signature'], direction=direction,
                            simulation='FINAL_RUN_REQUIRED',
                            instrument='CONCRETE_DELEGATE' if r['type'] in ('IviUtility','IviDirectIo') else 'FINAL_RUN_REQUIRED',
                            procedure='G-API + '+domain(r), source=loc, source_contract=constraints,
                            guide=r['guide'], earlier_classification=r['evidence_kind'],
                            earlier_evidence=r['evidence_refs'], earlier_gaps=r['followup_ids'],
                            result='PENDING', setup_id='', artifact_sha256='', evidence='', notes=''))
    menus = json.loads((PACKAGE/'menu-catalog.json').read_text(encoding='utf-8'))['items']
    assert len(menus) == 216
    menu_rows = []
    for m in menus:
        pos, neg = menu_vectors(m)
        menu_rows.append(dict(id=f'M{m["number"]:04}', header=m['header'], description=m['description'],
                              permission=m['permission'], access=m['access'], kind=m['codec']['kind'],
                              positive_vectors=pos, negative_vectors=neg,
                              operations='GET; property SET; write_and_read; restore' if m['access']=='rw' else 'GET; deny SET',
                              simulation='FINAL_RUN_REQUIRED', instrument='FINAL_RUN_REQUIRED',
                              result='PENDING', setup_id='', evidence='', restore_evidence=''))
    # Source paragraph IDs are frozen and all map to reviewed obligations.
    obligations={o['id'] for o in plan['obligations']}
    assert len(obligations)==len(plan['obligations'])
    for s in plan['spec_requirements']:
        assert s['case_ids'] and set(s['case_ids'])<=obligations, s
    assert {o['id'] for o in plan['obligations']} <= set(plan['order'])
    followups=json.loads((DOC/'IVI_VERIFICATION_RECONCILED_2026-11-12.json').read_text(encoding='utf-8'))['followups']
    assert set(followups) == set(plan['followup_cases'])
    assert all(set(v) <= obligations for v in plan['followup_cases'].values())
    lines = ['# LXI 6.1 / IVI適合検証の全件完了計画 — 2026-11-12', '', plan['scope'], '',
             '**状態：計画を確定した段階。試験の追加実行・実機操作・適合宣言は行っていない。**', '',
             '## 完了の定義', '', *['- '+s for s in plan['completion']], '',
             '## 固定した対象と規格', '', *['- '+s for s in plan['target']], '',
             *[f'- [{s["name"]} 1.0]({s["url"]}) · SHA-256 `{s["sha256"]}`' for s in plan['spec_sources']['sources']], '',
             '規格本文は再配布せず、固定commit・章・行・段落hashで要求を追跡する。', '',
             '## 実施順序と全チェック項目', '',
             '| ID | 確認するもの／手順 | 合格条件 | 環境・分類 |', '|---|---|---|---|']
    by_id={o['id']:o for o in plan['obligations']}
    for oid in plan['order']:
        o=by_id[oid]
        lines.append('| '+' | '.join([oid,o['procedure'],o['acceptance'],o['environment']])+' |')
    lines += ['', '## 全API・全メニューの実施台帳', '',
              f'- [API台帳]({BASE}_API.csv)：352項目を方向別に分けた**{len(api)}行**。setter/getterを別に記録し、全行に模擬と実接続の欄を持つ。',
              f'- [メニュー台帳]({BASE}_MENU.csv)：**216項目**。番号・権限・型・具体的な合法／非合法ベクトルを展開。',
              f'- [規格要求の照合台帳]({BASE}_REQUIREMENTS.csv)：**{len(plan["spec_requirements"])}段落**の必須語・禁止語を含む要求と確認IDの対応。表／箇条書きで定義されるAPI・検証条件は同じ章の確認IDで全体を確認する。',
              '- 数は試験成功数ではない。複合値・列挙値・instanceの展開実績を結果添付に残し、行だけPASSにしない。', '',
              '## 共通実行規則 G-API', '', *['- '+s for s in plan['api_rules']], '',
              '## 値域・レコード・instanceの全条件', '']
    for d in plan['domains']:
        lines += ['### '+d['id']+' '+d['title'], '', *['- '+s for s in d['cases']], '']
    lines += ['## 既存不足項目の全件対応', '', '以下は旧残件の完全な列挙。上の最終一式試験へ統合する。既存成功記録は削除しない。', '']
    for name, names in followups.items():
        lines += ['### '+name, '', '対応確認ID：'+', '.join(plan['followup_cases'][name]), '', *['- `'+n+'`' for n in names], '']
    if plan.get('lxi_groups'):
        lines += ['## LXI全体の最終照合・手続き', '',
                  'IVI以外の旧監査項目もここへ集約する。次は既存結果の条項照合であり、全組合せの追加実機試験を指示するものではない。', '']
        for group in plan['lxi_groups']:
            lines += ['### '+group['id']+' 確認の扱い', '', group['summary'], '']
        lines += ['元の条項別所見は同名JSONの `lxi_followup_rows` に保存。状態の変更や合格への読み替えは行っていない。', '']
    lines += ['## 判定・記録・範囲変更', '', *['- '+s for s in plan['judgement']], '',
              '## 台帳整合性の確認', '', '`python tools/ivi_completion_plan.py --check`', '',
              'このコマンドは在庫・リンク・hash・生成一致を検査するだけで、試験を実行せず、PASSや適合を認定しない。', '']
    req_rows=[dict(id=x['id'], specification=x['spec'], section=x['section'],
                   source_lines=x['source_lines'], paragraph_sha256=x['sha256'],
                   verification_ids=';'.join(x['case_ids']), result='PENDING_REVIEW', evidence='')
              for x in plan['spec_requirements']]
    examples = example_inventory()
    # All code blocks are inventoried: none disappears merely because it needs
    # a session fixture, an import, or is repeated in another guide.
    at = lines.index('- 数は試験成功数ではない。複合値・列挙値・instanceの展開実績を結果添付に残し、行だけPASSにしない。')
    lines.insert(at, f'- [同梱例の台帳]({BASE}_EXAMPLES.csv)：**{len(examples)}コードブロック**。実行例・前提sessionが必要な断片・出力/構文例を全件判別し、実行例を導入環境ごとに確認する。')
    # Refresh Markdown after adding the examples inventory link.
    return {DOC/(BASE+'.md'):'\n'.join(lines), DOC/(BASE+'_API.csv'):csv_text(api),
            DOC/(BASE+'_MENU.csv'):csv_text(menu_rows), DOC/(BASE+'_REQUIREMENTS.csv'):csv_text(req_rows),
            DOC/(BASE+'_EXAMPLES.csv'):csv_text(examples)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--core-spec', type=Path)
    parser.add_argument('--python-spec', type=Path)
    args=parser.parse_args()
    plan=json.loads((DOC/(BASE+'.json')).read_text(encoding='utf-8'))
    if bool(args.core_spec) != bool(args.python_spec):
        raise SystemExit('Supply both --core-spec and --python-spec')
    if args.core_spec:
        for name, path in [('core', args.core_spec), ('python', args.python_spec)]:
            expected = next(s for s in plan['spec_sources']['sources'] if s['name'] == name)
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
                raise SystemExit('Pinned specification bytes differ: '+name)
            expected_rows = [{k: x[k] for k in ('spec','section','source_lines','sha256')}
                             for x in plan['spec_requirements'] if x['spec'] == name]
            if spec_inventory(path, name) != expected_rows:
                raise SystemExit('Mandatory prose coverage differs: '+name)
    for p, text in generate(plan).items():
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8')!=text:
                raise SystemExit('Stale plan: '+str(p.relative_to(ROOT)))
        else:
            p.write_text(text,encoding='utf-8',newline='\n')
    print('Frozen API/source inventory, 352 APIs, 216 menus, requirement mapping and generated plan checked; no tests executed')


if __name__=='__main__':
    main()
