"""Render/check the dated requirements inventory; not a conformance test."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/LXI_REQUIREMENTS_2026-11-10.json'
OUTPUT = ROOT / 'docs/LXI_REQUIREMENTS_2026-11-10.md'
STATES = {'実装確認', '追加検証', '未達', '手続待ち', '適用外', '適用判定待ち', '廃止'}


def validate(data, pdf=None):
    keys = [(r['source'], r['clause']) for r in data['rows']]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate requirement row')
    covered = {clause for source, clause in keys if source == 'Device'}
    if set(data['device_rule_inventory']) - covered:
        raise ValueError('Missing Device rule rows')
    if set(data['deprecated_device_rules']) - covered:
        raise ValueError('Missing deprecated-rule decisions')
    plan = json.loads((ROOT / 'docs/IVI_6_1_COMPLETION_2026-11-12.json').read_text(encoding='utf-8'))
    gap_ids = {g['id'] for g in plan['lxi_groups']}
    for row in data['rows']:
        if row['state'] not in STATES or not all(row[k] for k in ('finding', 'scope', 'evidence', 'page')):
            raise ValueError('Incomplete row: ' + row['clause'])
        if row['state'] in {'未達', '追加検証', '適用判定待ち', '手続待ち'} and not row['gaps']:
            raise ValueError('Open row without a tracked gap: ' + row['clause'])
        for path in row['evidence']:
            if not (ROOT / path).is_file():
                raise ValueError('Missing evidence reference: ' + path)
        for gap in row['gaps']:
            if gap not in gap_ids:
                raise ValueError('Unknown gap reference: ' + gap)
    for path, expected in data['code_fingerprints'].items():
        actual = hashlib.sha256((ROOT / path).read_text(encoding='utf-8').encode()).hexdigest()
        if actual != expected:
            raise ValueError('Audit input changed; re-review required: ' + path)
    if pdf:
        from pypdf import PdfReader
        expected = next(s['sha256'] for s in data['sources'] if s['name'] == 'Device')
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != expected:
            raise ValueError('Source PDF revision/hash mismatch')
        found, deprecated = {}, {}
        for page_number, page in enumerate(PdfReader(pdf).pages, 1):
            if page_number < 10:
                continue  # Exclude contents/revision history.
            for line in page.extract_text(extraction_mode='layout').splitlines():
                match = re.match(r'^\s*(\d+(?:\.\d+)+)\s+(?:(Deprecated)\s+)?RULE\b', line, re.I)
                if match:
                    (deprecated if match[2] else found)[match[1]] = page_number
        if found != data['device_rule_inventory'] or deprecated != data['deprecated_device_rules']:
            raise ValueError('Device PDF rule/page inventory differs from audit')


def render(data):
    plan = 'IVI_6_1_COMPLETION_2026-11-12.md'
    lines = [
        '# LXI 1.6.2 条項対応表', '',
        '対象：Pi4/eth0、付属画面とローカル入力、手動起動のCIVI/helper/panel。',
        'gateway0.1.0、Python driver0.13.1。WLANは管理用。', '',
        f"Deviceの現行RULE{len(data['device_rule_inventory'])}件を含む{len(data['rows'])}行を照合。親子条項があるため達成率には換算しません。", '',
        '[実装・試験結果](IMPLEMENTATION_AND_TEST_RESULTS.md) · '
        f'[検証・手続きの完了条件]({plan})', '',
        '実装確認は記載された範囲の証拠、適用外は宣言構成による判定です。',
        '最終照合・手続きが必要な行の説明は完了計画へ集約しています。', '',
        '## 規格の出典', '',
    ]
    for source in data['sources']:
        lines += [f"- [{source['name']}]({source['url']}) — SHA-256 `{source['sha256']}`"]
    lines += ['', '`python tools/lxi_audit_check.py --check` で条項の在庫・参照先・入力hashを確認できます。', '']
    for source, title in [('Device', 'Device'), ('Interpretations', '補足解釈'), ('API', '識別API')]:
        lines += [f'## {title}', '', '| 条項 / PDF頁 | 適用条件 | 判定・結果 | 根拠 |', '|---|---|---|---|']
        def key(row):
            return tuple(int(n) for n in re.findall(r'\d+', row['clause'].split('/')[0]))
        for row in sorted((r for r in data['rows'] if r['source'] == source), key=key):
            refs = '<br>'.join(f'[{Path(p).name}](../{p})' for p in dict.fromkeys(row['evidence']))
            if row['state'] in {'未達', '追加検証', '適用判定待ち', '手続待ち'}:
                result = f"[完了計画]({plan}): " + ', '.join(row['gaps'])
            else:
                result = row['state'] + '：' + row['finding']
            values = [f"{row['clause']} / p.{row['page']}", row['scope'], result, refs]
            lines.append('| ' + ' | '.join(v.replace('|', '\\|') for v in values) + ' |')
        lines += ['']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--device-pdf', type=Path)
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding='utf-8'))
    validate(data, args.device_pdf)
    expected = render(data)
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != expected:
            raise SystemExit('Regenerate dated LXI table: python tools/lxi_audit_check.py')
    else:
        OUTPUT.write_text(expected, encoding='utf-8')
    print(f"{len(data['device_rule_inventory'])} active Device rules / {len(data['rows'])} rows checked; not a conformance verdict")


if __name__ == '__main__':
    main()
