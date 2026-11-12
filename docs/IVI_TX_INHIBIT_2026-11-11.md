# TX Inhibit設定試験結果 — 2026-11-11

IC-7300 MAIN1.42、Python driver0.13.1、Pi gateway経由。利用者がFW更新後の版を確認。

| 確認項目 | 最終結果 |
|---|---|
| 初期値 | False |
| 設定/読戻し | True→True、False→False |
| 不正型 | 1,"ON",NoneをI/O前に拒否 |
| 結果 | 5チェック成功。元のFalseへ復元、queue空、PTTサンプルはOFF |

- この試験はTX Inhibitの設定・読戻し。送信開始操作は行っていない。

再現手順：`tools/ivi_tx_inhibit_acceptance.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
