# 選択メモリー操作の試験結果 — 2026-11-12

Python driver0.13.1 → Pi → IC-7300 MAIN1.42、空99番。

| 確認項目 | 最終結果 |
|---|---|
| 操作 | store09 / display08 / copy0A / clear0B |
| 結果 | 実機/模擬29チェック成功 |
| 実行条件 | 番号選択とMEM modeへの切替を分離。clear0Bの前にenable()でMEM modeを選択 |
| 読戻し | 保存record、表示、VFO転送、消去後の空recordを確認 |
| 復元 | 空99番・両VFO・memory書込禁止へ復元、PTT OFF・queue空 |

再現手順：`tools/ivi_selected_memory_acceptance.py`。

[実装・試験結果一覧](IMPLEMENTATION_AND_TEST_RESULTS.md)
