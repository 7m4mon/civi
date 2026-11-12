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
    gap_text = (ROOT / 'docs/LXI_REMAINING_2026-11-10.md').read_text(encoding='utf-8')
    for row in data['rows']:
        if row['state'] not in STATES or not all(row[k] for k in ('finding', 'scope', 'evidence', 'page')):
            raise ValueError('Incomplete row: ' + row['clause'])
        if row['state'] in {'未達', '追加検証', '適用判定待ち', '手続待ち'} and not row['gaps']:
            raise ValueError('Open row without a tracked gap: ' + row['clause'])
        for path in row['evidence']:
            if not (ROOT / path).is_file():
                raise ValueError('Missing evidence reference: ' + path)
        for gap in row['gaps']:
            if f'### {gap} ' not in gap_text:
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
    counts = Counter(row['state'] for row in data['rows'])
    lines = [
        '# LXI 1.6.2 全必須条項の照合 — 2026-11-10', '',
        '**結論: 未達。LXI準拠・認証済みとは表示しない。**', '',
        '[最新の優先順位・必須ゲート再判定](LXI_READINESS_2026-11-11.md)。',
        '追加の信頼性試験と、規定の必須検証・登録手続きを区別する。', '',
        '対象はPi 4のeth0をLXI用NICとする手動起動構成、付属画面とローカル入力手段、',
        f"ゲートウェイ0.1.0と独立クライアント{data.get('fix_followup', {}).get('client_version', '0.13.0')}。WLANは管理経路として扱う計画。",
        ('初回は作業ツリーと既存記録の照合。その後、修正版を実Piへ反映し範囲付き実機確認を実施。'
         if data.get('physical_followup', {}).get('deployed') else
         '実行中Piの再取得監査ではなく作業ツリーと既存記録の照合。Pi反映・確認は別作業。'), '',
        '[確定した残件と完了条件](LXI_REMAINING_2026-11-10.md) · '
        '[機械可読データ](LXI_REQUIREMENTS_2026-11-10.json)', '',
        '初回監査後の[4件の修正・模擬検証](LXI_FIXES_2026-11-10.md)を反映。',
        'JSONのinitial_findings/initial_code_fingerprints/local_probesは初回監査の履歴で、',
        '現在の判定はrowsとcode_fingerprints。反映/実機確認は明記された範囲だけに限定する。',
        ('[Pi反映と実機確認の続報](RPI_LXI_FIXES_2026-11-10.md)あり。未試験条件は合格扱いにしない。'
         if data.get('physical_followup', {}).get('deployed') else '実Piへの反映・確認は未実施。'), '',
        '## 数え方と判定', '',
        f"Device本文の現行RULE見出し **{len(data['device_rule_inventory'])}件を全件収録**。",
        '目次は除外し、本文の小条項まで採用。廃止RULE4件は別行。撤回Permission、',
        '推奨節内の必須文、公式補足解釈8.14、識別APIから参照される要件、複合条項の',
        f"内訳を合わせて **{len(data['rows'])}行**。親子行は重複集計のため達成率には使わない。", '',
        '「実装確認」は記載したコード/限定的証拠の確認であり、規格全体の合格ではない。',
        '「追加検証」は機能があっても条項全体の証拠が不足。「未達」は確認した差異/未完成。',
        '「適用判定待ち」は装置構成やOS機能の採用範囲を確定しないと判定できない。',
        '「手続待ち」は登録・許諾・最終宣言等。「適用外」には採用時の条件を残す。', '',
        ' | '.join(f'{key}: {counts[key]}' for key in sorted(counts)), '',
        '## 出典と再現性', '',
        'ページ番号はPDFの1始まりのページ。条項原文を転載せず、CIVI側の観察・判断を記載。', '',
    ]
    for source in data['sources']:
        lines += [f"- [{source['name']}]({source['url']}) — SHA-256 `{source['sha256']}`"]
    lines += [
        '', 'Deviceは1.6.2（表紙2026-04-04、URL名2026-04-02）。APIは1.1（2025-03-10）。',
        '補足解釈は1.6.1向け2025-02-16版を1.6系列の補足として照合。',
        'API全体・Security・IPv6・HiSLIP等をコア必須には拡大しない。イベント/同期も未採用。',
        'ただし識別に関係するCommon Method/スキーマの必須意味要件は取り込む。',
        'RFC/IEEE/IVI参照文書の全必須文をここだけで検証済みとはせず、各依存要件の',
        '未確認を残件へ明記する。正式認証時は適用版と最新補足を再確認する。', '',
        '```text', 'python tools/lxi_audit_check.py --check',
        'python tools/lxi_audit_check.py --check --device-pdf <official-device-1.6.2.pdf>', '```', '',
        f"通常チェックは行漏れ/重複/参照先と{len(data['code_fingerprints'])}コード・設定・テスト入力の内容ハッシュを検査。",
        'PDF指定時はpypdfで本文を再抽出し101見出しと4廃止見出し・ページを再照合する。',
        'これは条項の意味的正しさやハード動作を自動判定する仕組みではない。', '',
    ]
    for source, title in [('Device', 'Device本文と条項内訳'), ('Interpretations', '公式補足解釈'), ('API', '識別に関係するAPI要件')]:
        lines += [f'## {title}', '', '| 条項 / PDF頁 | 適用条件 | 状態 | CIVIの証拠・判定 | 根拠ファイル | 残件 |', '|---|---|---|---|---|---|']
        def key(row):
            clause = row['clause'].split('/')[0]
            return tuple(int(n) for n in re.findall(r'\d+', clause))
        for row in sorted((r for r in data['rows'] if r['source'] == source), key=key):
            refs = '<br>'.join(f'[{Path(p).name}](../{p})' for p in row['evidence'])
            values = [f"{row['clause']} / p.{row['page']}", row['scope'], row['state'], row['finding'], refs, ', '.join(row['gaps']) or '—']
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
