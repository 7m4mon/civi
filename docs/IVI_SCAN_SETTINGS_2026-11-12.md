# スキャン設定試験 — 2026-11-12

Python driver0.13.1、Pi、IC-7300 MAIN1.42。利用者が元のΔF=±10kHz、SELECT No.=★1を確認。

| 項目 | 結果 |
|---|---|
| ΔF | ±5/10/20/50/100/500kHz/1MHz、全7幅をLSB/DATA OFF/FIL1で確認 |
| ΔF結果 | 実機33・模擬41チェック成功。各開始後12サンプルは指定範囲内を移動、STOP後3サンプル安定 |
| select設定 | ON/OFF、番号1–3、filter ALL/★1/★2/★3 |
| select結果 | 実機34・模擬35チェック成功。実周波数が各groupの対象集合と一致 |
| 記憶番号 | 99番でOFF→group0、ON→元の有効group1。番号1/2/3の割当をrecord経由で読戻し |
| 復元 | ΔF±10kHz・filter★1への命令正常完了。memory94–99空、VFO7055650LSB/FIL2・他14100000USB/FIL2・DATA OFF、SQL65、PTT OFF |

- ΔFはフィルター帯域ではなくscan範囲。短時間のサンプリングで範囲内移動と停止を確認した。
- span/filterに直接queryはないため、元の目視値と復元命令の受理を記録。利用者も本体動作を確認。
- 使用手順：tools/ivi_scan_span_acceptance.py、tools/ivi_scan_select_acceptance.py。

[結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
